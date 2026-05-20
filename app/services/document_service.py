import fitz  # PyMuPDF
import google.generativeai as genai
import os
from sqlalchemy.orm import Session
from app.models.models import Document, DocumentChunk
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def process_pdf_and_embed(doc_id: int, file_path: str, db: Session):
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