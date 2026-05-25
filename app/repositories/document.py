from sqlalchemy.orm import Session #for database communication
from app.models.models import Document  

def create_document(db: Session, filename: str, file_path: str, uploader: str):
    db_document = Document(
        filename=filename,
        file_path=file_path,
        uploader=uploader,
        status="PENDING"  
    )
    
    db.add(db_document)
    # return DB model
    return db_document

def get_upload_status_by_id(db: Session, doc_id:int):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    return {"status": doc.status} # 只會回傳 PENDING, COMPLETED 或 FAILED

def list_documents(db: Session):
    return db.query(Document).all()

def delete_document_by_List_ids(db: Session, document_list:list[int]):

    if document_list:
        db_document = db.query(Document).filter(Document.id.in_(document_list)).all()
    else:
        return None

    if not db_document:
        return None
    
    for document in db_document:
        db.delete(document)

    BackupDeletedDocument =[
        {
            "id": doc.id,
            "file_path": doc.file_path,
            "filename": doc.filename
        }
        for doc in db_document
    ]
    
    return BackupDeletedDocument