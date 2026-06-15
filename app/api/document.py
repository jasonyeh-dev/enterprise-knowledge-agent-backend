from typing import List

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile, status)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (get_current_user_id, get_db, get_document_service,
                          get_rag_service)
from app.models.schemas import (AskRequest, AskResponse, DeleteRequest,
                                DeleteResponse, DocumentResponse,
                                DocumentStatusResponse)
from app.services.document_service import DocumentService, RagService

router = APIRouter(
    prefix="/documents",
    tags=["Documents (Knowledge base management)"]
)

@router.post("", response_model=DocumentResponse)
async def upload_file_api(
    # Swagger generate upload buttom and input place
    # ... means required
    # JWT decipher to uploader
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db),
    uploader_id: int = Depends(get_current_user_id),
    document_service: DocumentService = Depends(get_document_service),
):
    saved_record = await document_service.upload_document_workflow(
        db=db, 
        file=file, 
        uploader_id=uploader_id,
        background_tasks=background_tasks)
    
    return saved_record
    
@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status_api(
    doc_id: int, 
    db: AsyncSession = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),):

    doc_status_enum = await document_service.get_document_status_process(db, doc_id)
    if doc_status_enum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Document with ID {doc_id} not found."
        )
    
    return DocumentStatusResponse(status=doc_status_enum)

@router.get("", response_model=List[DocumentResponse], dependencies=[Depends(get_current_user_id)])
async def list_documents_api(
    db: AsyncSession = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),):

    db_documents =await document_service.list_document_workflow(db)
    return [DocumentResponse.model_validate(doc) for doc in db_documents]

@router.delete("", response_model=DeleteResponse, dependencies=[Depends(get_current_user_id)])
async def delete_documents_api(
    request: DeleteRequest,
    db: AsyncSession = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    DeletedDoc = await document_service.delete_document_workflow(db, document_list = request.document_ids)  

    return DeleteResponse(message="Delete successfully", deleted_documents=DeletedDoc)

@router.post("/query", response_model=AskResponse)
async def ask_knowledge_base_api(
    request: AskRequest, 
    db: AsyncSession = Depends(get_db),
    rag_service: RagService = Depends(get_rag_service),):

    answer_text = await rag_service.answer_question(db=db, user_query=request.question)
    return answer_text
        
