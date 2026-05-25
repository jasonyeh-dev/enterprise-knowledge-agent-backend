import fitz  # PyMuPDF
import google.generativeai as genai
import os
from sqlalchemy.orm import Session
from app.models.models import Document, DocumentChunk
from dotenv import load_dotenv
from loguru import logger
import app.repositories.document as document_sql  
from fastapi import HTTPException
import shutil
from fastapi import File, BackgroundTasks
from app.core.database import SessionLocal

load_dotenv()
UPLOAD_DIR = os.environ.get("upload_DIR")

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def embed_pdf_background_task(doc_id: int, file_path: str):
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
        chunk_size = 800 
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        # 3. Call Gemini Embedding API 並存入資料庫
        for index, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
                
            # 呼叫 Gemini 轉向量 (text-embedding-004 是目前最新且免費的)
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=chunk_text,
                task_type="retrieval_document", # 告訴 Gemini 這是要被存起來檢索的資料
                output_dimensionality=768
            )
            embedding_vector = result['embedding']
            
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
                logger.error(f"孤兒檔案產生，無法刪除實體檔案: {filepath}, 錯誤: {e}")

        #return dict then transfer to JSON format
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

def get_document_status_process( db: Session, doc_id: int):
    doc_status = document_sql.get_upload_status_by_id(db, doc_id)
    return doc_status

def upload_document_workflow(db: Session, file:File, uploader:str, background_tasks:BackgroundTasks):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # 1. CRUD part
        saved_record = document_sql.create_document(
        db=db, 
        filename=file.filename, 
        file_path=file_path, 
        uploader=uploader
        )

        db.commit()
        db.refresh(saved_record)

        #2. Filesystem part
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. return message 
        # automatically return the JSON format based on the response model
        #pydantic model
        background_tasks.add_task(embed_pdf_background_task, saved_record.id, file_path)

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

    
