import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import  get_db
import app.repositories.document as document_sql  
from app.models.schemas import DocumentResponse, DeleteResponse
from app.services.document_service import process_pdf_and_embed
from typing import List
from loguru import logger

from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    prefix="/documents",
    tags=["Documents (Knowledge base management)"]
)


UPLOAD_DIR = os.environ.get("upload_DIR")



@router.post("/upload", response_model=DocumentResponse)
def upload_file(

    # Swagger generate upload buttom and input place
    # ... means required
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    uploader: str = Form(...),    
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        # 1. CRUD part
        saved_record = document_sql.create_document_record(
        db=db, 
        filename=file.filename, 
        file_path=file_path, 
        uploader=uploader
        )

        #2. Filesystem part
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
        # 3. return message 
        # automatically return the JSON format based on the response model
        #pydantic model

        background_tasks.add_task(process_pdf_and_embed, saved_record.id, file_path, db)

        return saved_record
    except Exception as e:
        db.rollback()
        logger.exception("upload file error")
        raise HTTPException(status_code=500, detail=f"Upload Fail: DB connection Error ({str(e)})")

@router.get("/GetAllDocuments", response_model=List[DocumentResponse])
def read_all_documents(db: Session = Depends(get_db)):
    
    # 呼叫 CRUD 取得所有資料 (此時拿到的是 SQLAlchemy 的 DB Models 陣列)
    db_documents = document_sql.list_all_document_record(db)
    
    # 直接回傳！FastAPI 會自動幫你把 DB Models 轉成乾淨的 JSON
    return db_documents

@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document_api(
    document_id: int, 
    db: Session = Depends(get_db)
):
    
    deleted_doc = document_sql.delete_document_record(db, document_id=document_id)
    

    if not deleted_doc:
        raise HTTPException(status_code=404, detail="can't find the specific file")
        

    #return dict then transfer to JSON format
    return {
        "message": "Delete successfully", 
        "deleted_id": document_id,
        "deleted_filename": deleted_doc.filename
    }