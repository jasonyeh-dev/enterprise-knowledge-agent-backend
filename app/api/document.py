import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import  get_db
from app.models.schemas import DocumentResponse, DeleteResponse, DeleteRequest, AskRequest, AskResponse
from app.services.document_service import delete_document_workflow, list_document_workflow, get_document_status_process, upload_document_workflow, qa_service
from typing import List
from loguru import logger
from app.api.deps import get_current_user_id

from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    prefix="/documents",
    tags=["Documents (Knowledge base management)"]
)


UPLOAD_DIR = os.environ.get("upload_DIR")


@router.post("/upload", response_model=DocumentResponse)
def upload_file_api(
    # Swagger generate upload buttom and input place
    # ... means required
    # JWT decipher to uploader
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    uploader_id: int = Depends(get_current_user_id)
):
    saved_record = upload_document_workflow(
        db=db, 
        file=file, 
        uploader_id=uploader_id,
        background_tasks=background_tasks)
    return saved_record
    
@router.get("/{doc_id}/status")
def get_document_status_api(doc_id: int, db: Session = Depends(get_db)):
    doc_status = get_document_status_process(db, doc_id)
    return doc_status

@router.get("/ListAllDocuments", response_model=List[DocumentResponse], dependencies=[Depends(get_current_user_id)])
def list_documents_api(db: Session = Depends(get_db)):
    db_documents = list_document_workflow(db)
    # 直接回傳！FastAPI 會自動幫你把 DB Models 轉成乾淨的 JSON
    return db_documents

@router.delete("/list", response_model=DeleteResponse, dependencies=[Depends(get_current_user_id)])
def delete_documents_api(
    request: DeleteRequest,
    db: Session = Depends(get_db)
):
    DeletedDoc = delete_document_workflow(db, document_list = request.document_ids)  
    return {
        "message": "Delete successfully", 
        "deleted_documents": DeletedDoc
    }


@router.post("/ask", response_model=AskResponse)
async def ask_knowledge_base_api(request: AskRequest, db: Session = Depends(get_db)):
    answer_text = await qa_service.answer_question(db=db, user_query=request.question)
    return answer_text
        
