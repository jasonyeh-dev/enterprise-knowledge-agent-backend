from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import  get_db
from app.models.schemas import DocumentResponse, DeleteResponse, DeleteRequest, AskRequest, AskResponse, DocumentStatusResponse
from app.services.document_service import delete_document_workflow, list_document_workflow, get_document_status_process, upload_document_workflow, qa_service
from app.api.deps import get_current_user_id
from app.core.context import current_user_account

router = APIRouter(
    prefix="/documents",
    tags=["Documents (Knowledge base management)"]
)

@router.post("", response_model=DocumentResponse)
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
    
@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
def get_document_status_api(doc_id: int, db: Session = Depends(get_db)):
    doc_status_enum = get_document_status_process(db, doc_id)
    if doc_status_enum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Document with ID {doc_id} not found."
        )
    
    # 把 Enum 裝進 Pydantic 盒子裡！
    return DocumentStatusResponse(status=doc_status_enum)


@router.get("", response_model=List[DocumentResponse], dependencies=[Depends(get_current_user_id)])
def list_documents_api(db: Session = Depends(get_db)):
    db_documents = list_document_workflow(db)
    return db_documents

@router.delete("", response_model=DeleteResponse, dependencies=[Depends(get_current_user_id)])
def delete_documents_api(
    request: DeleteRequest,
    db: Session = Depends(get_db)
):
    DeletedDoc = delete_document_workflow(db, document_list = request.document_ids)  
    return {
        "message": "Delete successfully", 
        "deleted_documents": DeletedDoc
    }


@router.post("/query", response_model=AskResponse)
def ask_knowledge_base_api(request: AskRequest, db: Session = Depends(get_db)):
    answer_text = qa_service.answer_question(db=db, user_query=request.question)
    return answer_text
        
