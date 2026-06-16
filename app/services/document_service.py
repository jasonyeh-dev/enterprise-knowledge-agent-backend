import os
import shutil

import anyio
import fitz  # PyMuPDF
from fastapi import BackgroundTasks, HTTPException, UploadFile
from google import genai
from google.genai import types
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Document, DocumentChunk
from app.models.schemas import (AskResponse, DocumentDeleteInfo,
                                DocumentStatus, DocumentSummary, SourceItem)
from app.crud.document_repository import document_repo


class ChunkingService:
    def extract_pdf_text(self, file_path: str) -> str:
        pdf = fitz.open(file_path)
        return "".join(pdf.load_page(i).get_text() for i in range(len(pdf)))

    def get_overlapping_chunks(
        self, full_text: str, chunk_size: int, overlap: int
    ) -> list[str]:
        step = chunk_size - overlap
        if step <= 0:
            raise ValueError("Overlap 必須小於 Chunk Size")
        return [
            full_text[i: i + chunk_size]
            for i in range(0, len(full_text), step)
        ]

class EmbeddingService:
    def __init__(self, client: genai.Client):
        self.client = client
        self.embedding_model = settings.EMBEDDING_MODEL_NAME

    async def embed_for_query(self, text: str) -> list[float]:
        return await self._embed(text, task_type="RETRIEVAL_QUERY")

    async def embed_for_storage(self, text: str) -> list[float]:
        return await self._embed(text, task_type="RETRIEVAL_DOCUMENT")

    async def _embed(self, text: str, task_type: str) -> list[float]:
        response = await self.client.aio.models.embed_content(
            model=settings.EMBEDDING_MODEL_NAME,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.OUTPUT_DIMENSIONALITY,
            )
        )
        return response.embeddings[0].values

class DocumentService:
    def __init__(self, embedding_service: EmbeddingService, chunking_service:ChunkingService):
        self.embedding_service = embedding_service
        self.chunking_service = chunking_service

    async def upload_document_workflow(self, db: AsyncSession, file:UploadFile, uploader_id:int, background_tasks:BackgroundTasks)->Document:
        try:
            file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

            with open(file_path, "wb") as buffer:
                await anyio.to_thread.run_sync(shutil.copyfileobj, file.file, buffer)

            saved_record = await document_repo.create_document(
            db=db, 
            filename=file.filename, 
            file_path=file_path, 
            uploader_id=uploader_id
            )

            await db.commit()
            
            #eager loading
            completed_record = await document_repo.get_document_with_relations(
                db=db, Doc_id=saved_record.id)
            
            logger.info(f"Upload Successfully, Doc_id={completed_record.id}, filename: {file.filename}")

            background_tasks.add_task(self.embed_pdf_background_workflow, completed_record.id, file_path, file.filename)

            return completed_record
        
        except Exception as e:
            await db.rollback()

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as rm_error:
                    logger.error(f"Can't delete file: {rm_error}")
                    
            logger.exception(f"upload file error, Doc_id={completed_record.id}, filename: {file.filename}")
            raise HTTPException(status_code=500, detail=f"Upload Fail: ({str(e)})")

    async def get_document_status_process(self,  db: AsyncSession, doc_id: int) -> DocumentStatus | None:
        doc_status =await document_repo.get_upload_status_by_id(db, doc_id)
        logger.info(f"get document:{doc_id} status {doc_status.value}")
        return doc_status

    async def list_document_workflow(self, db: AsyncSession) -> list[Document]:
        db_documents = await document_repo.list_documents(db)
        logger.info("List all files")
        return db_documents

    async def embed_pdf_background_workflow(self, doc_id: int, file_path: str, filename: str) -> None:
        logger.info(f"開始向量化, Doc_id={doc_id}, filename:{filename}")
        async with AsyncSessionLocal() as bg_db:
            try:
                # 1. Read pdf
                pdf_text = await anyio.to_thread.run_sync(
                    self.chunking_service.extract_pdf_text, file_path
                )
                # 2. Chunk
                chunks = self.chunking_service.get_overlapping_chunks(
                    full_text=pdf_text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
                
                # 3. Call Gemini Embedding API 並存入資料庫
                for index, chunk_text in enumerate(chunks):
                    if not chunk_text.strip():
                        continue
                    vector = await self.embedding_service.embed_for_storage(chunk_text)

                    # 建立子表紀錄 (依靠 ORM 自動綁定)
                    new_chunk = DocumentChunk(
                        document_id=doc_id,
                        chunk_index=index,
                        content=chunk_text,
                        embedding=vector
                    )
                    bg_db.add(new_chunk)
                    
                # 4. 全部成功後，把主表的狀態更新為 COMPLETED
                await document_repo.update_document_status(bg_db, doc_id, "COMPLETED")

                logger.info(f"向量化完成 filename:{filename}, chunks={len(chunks)}")

            except Exception as e:
                # exception --> FAILED
                await bg_db.rollback()
                await document_repo.update_document_status(bg_db, doc_id, "FAILED")
                logger.exception(f"vectorize fail, Doc_id={doc_id}, filename:{filename} {e}")
            
    async def delete_document_workflow(self, db: AsyncSession, document_list: list[int]) -> list[DocumentSummary]:
        try:
            db_documents = await document_repo.get_documents_by_ids(db, document_list=document_list)

            if not db_documents:
                raise HTTPException(status_code=404, detail="can't find the specific file")
            
            backup_deleted_documents = []

            for doc in db_documents:
                await db.delete(doc)
                backup_obj = DocumentDeleteInfo.model_validate(doc)
                backup_deleted_documents.append(backup_obj)

            #----delete DB then delete local file-----------
            await db.commit()

            for file in backup_deleted_documents:
                try:
                    if os.path.exists(file.file_path):
                        os.remove(file.file_path)
                except Exception as e:
                    logger.error(f"Can't delete file, {file.file_path}, Error: {e}")


            deleted_filenames = ", ".join([file.filename for file in backup_deleted_documents])
            logger.info(f"Delete DB and file successfully. Files: {deleted_filenames}")

            return [DocumentSummary.model_validate(doc) for doc in backup_deleted_documents]

        except HTTPException:
            raise
            
        except Exception as e:
            await db.rollback() 
            logger.error(f"Database delete fail: {e}")
            raise HTTPException(status_code=500, detail="Database delete fail, file not change")
        
class RagService:

    def __init__(self, client: genai.Client, embedding_service: EmbeddingService):
        self.client = client
        self.embedding_service = embedding_service
        self.chat_model = settings.CHAT_MODEL_NAME

    def _build_context(self, chunks: list[tuple[DocumentChunk, float]]) -> tuple[str, list[SourceItem]]:
        sources = []
        texts = []
        for chunk, distance in chunks:
            texts.append(chunk.content)
            sources.append(SourceItem(
                filename=chunk.document.filename, #lazy loading async should be eager loading
                chunk_content=chunk.content,
                similarity_score=round(1 - distance, 4)
            ))
        return "\n---\n".join(texts), sources
    
    async def _generate_answer(self, user_query: str, context: str) -> str:
        prompt = f"""
        你是一位專業且嚴謹的企業內部知識庫助理。
        請「僅能」根據下方【參考資料】提供的內容，來回答使用者的【問題】。

        【參考資料】:
        {context}

        【問題】:
        {user_query}
        """
        response = await self.client.aio.models.generate_content(
            model=self.chat_model,
            contents=prompt,
        )
        return response.text

    async def answer_question(
        self, db: AsyncSession, user_query: str) -> AskResponse:

        logger.info(f"開始處理問題: {user_query}") 

        query_vector = await self.embedding_service.embed_for_query(user_query)

        similar_chunks = await document_repo.get_similar_chunks_with_score(
            db=db,
            question_embedding=query_vector,
            limit= settings.RETRIEVAL_TOP_K, 
            threshold= settings.RETRIEVAL_SCORE_THRESHOLD,
        )

        if not similar_chunks:
            logger.warning("找不到相關 chunks，回傳預設回答")
            return AskResponse(
                answer="目前知識庫中尚無相關文件可以回答您的問題。",
                sources=[]
            )

        context, sources = self._build_context(similar_chunks)
        answer = await self._generate_answer(user_query, context)

        logger.info(f"成功回答，引用 {len(sources)} 個來源")
        return AskResponse(answer=answer, sources=sources)
    