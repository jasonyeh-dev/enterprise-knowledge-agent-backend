import fitz  # PyMuPDF
import google.generativeai as genai
from google.generativeai.types.text_types import EmbeddingDict
from sqlalchemy.orm import Session
from app.models.models import Document, DocumentChunk
from loguru import logger
import app.repositories.document as document_sql  
from fastapi import HTTPException
import shutil
from fastapi import File, BackgroundTasks
from app.core.database import SessionLocal
from app.models.schemas import DocumentStatus
from app.core.config import settings
import os

genai.configure(api_key=settings.GEMINI_API_KEY)

def Gemini_Embedding_task(Content:str, Task:str):

    result: EmbeddingDict = genai.embed_content(
        model=settings.EMBEDDING_MODEL_NAME,
        content=Content,
        task_type=Task, # 告訴 Gemini 這是要被存起來檢索的資料
        output_dimensionality=settings.OUTPUT_DEMENSIONALITY
        )
    embedding_vector = result['embedding']
    return embedding_vector

def get_overlapping_chunks(full_text: str, chunk_size: int =800, overlap: int = 100) -> list[str]:
    step = chunk_size - overlap
    chunks = []
    
    if step <= 0:
        raise ValueError("Overlap 必須小於 Chunk Size")

    for i in range(0, len(full_text), step):
        chunk = full_text[i : i + chunk_size]
        chunks.append(chunk)
        
    return chunks

def embed_pdf_background_workflow(doc_id: int, file_path: str):
    # 1. 製造一個全新的、專屬於這個背景任務的連線
    db = SessionLocal()
    """background session"""
    try:
        # 1. 讀取 PDF 文字 (PyMuPDF)
        pdf_document = fitz.open(file_path)
        full_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text()
            
        # 2. (Chunking)
        chunks = get_overlapping_chunks(full_text=full_text)
        
        # 3. Call Gemini Embedding API 並存入資料庫
        for index, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
                
            embedding_vector = Gemini_Embedding_task(Content=chunk_text, Task="retrieval_document")

            # 建立子表紀錄 (依靠 ORM 自動綁定)
            new_chunk = DocumentChunk(
                document_id=doc_id,
                chunk_index=index,
                content=chunk_text,
                embedding=embedding_vector
            )
            db.add(new_chunk)
            
        # 4. 全部成功後，把主表的狀態更新為 COMPLETED
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.status = "COMPLETED"
            
        db.commit()

    except Exception as e:
        # 如果中間爆炸了，狀態改成 FAILED
        db.rollback()
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.status = "FAILED"
            db.commit()
        logger.exception(f"向量化失敗: {e}")
    
    finally:
        #2. 任務結束，自己關閉連線！
        db.close()

def delete_document_workflow(db: Session, document_list: list[int]):
    try:
        BackupDeletedDocument = document_sql.delete_document_by_List_ids(db, document_list=document_list)

        if not BackupDeletedDocument:
            raise HTTPException(status_code=404, detail="can't find the specific file")
         
        db.commit()

        for file in BackupDeletedDocument:
            try:
                filepath = file["file_path"]
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.error(f"無法刪除實體檔案: {filepath}, 錯誤: {e}")

        #return dict then transfer to JSON format
        logger.info("Delete file")
        return [
                {
                    "id":doc["id"],
                    "filename":doc["filename"]
                }
                for doc in BackupDeletedDocument
            ]
        

    except HTTPException:
        raise
        
    except Exception as e:
        db.rollback() 
        logger.error(f"資料庫刪除失敗: {e}")
        raise HTTPException(status_code=500, detail="資料庫刪除失敗，檔案未更動")
    
def list_document_workflow(db: Session):
    db_documents = document_sql.list_documents(db)

    return db_documents

def get_document_status_process( db: Session, doc_id: int) -> DocumentStatus | None:
    doc_status = document_sql.get_upload_status_by_id(db, doc_id)
    return doc_status

def upload_document_workflow(db: Session, file:File, uploader_id:int, background_tasks:BackgroundTasks):
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

        # 1. CRUD part
        saved_record = document_sql.create_document(
        db=db, 
        filename=file.filename, 
        file_path=file_path, 
        uploader_id=uploader_id
        )

        db.commit()
        db.refresh(saved_record)

        #2. Filesystem part
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info("Upload Successfully")

        # 3. return message 
        # automatically return the JSON format based on the response model
        #pydantic model
        background_tasks.add_task(embed_pdf_background_workflow, saved_record.id, file_path)

        return saved_record
    
    except Exception as e:
        db.rollback()

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as rm_error:
                logger.error(f"無法清除孤兒檔案: {rm_error}")
                
        logger.exception("upload file error")
        raise HTTPException(status_code=500, detail=f"Upload Fail: ({str(e)})")

class QAService:
    def __init__(self):
        self.embedding_model_name = settings.EMBEDDING_MODEL_NAME
        self.chat_model = genai.GenerativeModel(settings.CHAT_MODEL_NAME)

    def answer_question(self, db: Session, user_query: str) -> str:
        # ==========================================
        # Step 1. 將自然語言轉換成向量 (Embedding)
        # ==========================================
        embed_result = genai.embed_content(
            model=self.embedding_model_name,
            content=user_query,
            task_type="retrieval_query", # 標示這是一個用來檢索的查詢
            output_dimensionality=settings.OUTPUT_DEMENSIONALITY
        )
        query_vector = embed_result['embedding']

        # ==========================================
        # Step 2. 向量檢索 (呼叫 Repository)
        # ==========================================
        similar_chunks = document_sql.get_similar_chunks_with_score(
            db=db, 
            question_embedding=query_vector
        )
        
        # 如果資料庫是空的，或者沒撈到資料的防呆
        if not similar_chunks:
            return {
                "answer": "目前知識庫中尚無相關文件可以回答您的問題。",
                "sources": []
            }
        
        sources_metadata = []
        context_texts = []

        for chunk, distance in similar_chunks:
            # 組合給 Gemini 看的文本
            context_texts.append(chunk.content)
            
            sources_metadata.append({
                "filename": chunk.document.filename, 
                "chunk_content": chunk.content,
                "similarity_score": round(1 - distance, 4) # 轉換成相似度百分比
            })


        # 將撈出來的文本片段組合成一個大字串
        context_text = "\n---\n".join(context_texts)

        # ==========================================
        # Step 3. 組合 Prompt 並交給 LLM 總結
        # ==========================================
        # 這是防幻覺 (Hallucination) 最關鍵的 System Prompt
        prompt = f"""
        你是一位專業且嚴謹的企業內部知識庫助理。
        請「僅能」根據下方【參考資料】提供的內容，來回答使用者的【問題】。
        
        回答規則：
        1. 語氣請保持專業、友善。
        2. 如果【參考資料】中沒有提到能回答該問題的資訊，請誠實回答：「很抱歉，目前的知識庫中沒有關於此問題的規定。」，絕對不可以自己捏造答案。
        3. 回答請盡量精簡扼要，重點可以使用條列式。

        【參考資料】:
        {context_text}

        【問題】:
        {user_query}
        """

        # 呼叫 Gemini產生解答
        response = self.chat_model.generate_content(prompt)
        
        return {
                "answer": response.text,
                "sources": sources_metadata
            }


qa_service = QAService()    
