from sqlalchemy.orm import Session
from models.models import Document  

def create_document_record(db: Session, filename: str, file_path: str, uploader: str):
    db_document = Document(
        filename=filename,
        file_path=file_path,
        uploader=uploader,
        status="PENDING"  
    )
    
    db.add(db_document)
    db.commit()
    
    db.refresh(db_document)
    return db_document