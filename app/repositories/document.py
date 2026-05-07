from sqlalchemy.orm import Session #for database communication
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

    # return DB model
    return db_document

def list_all_document_record(db: Session):
    return db.query(Document).all()


def delete_document_record(db: Session, document_id:int):
    # query which table then where clause, top 1
    db_document = db.query(Document).filter(Document.id == document_id).first()

    if not db_document:
        return None
    
    db.delete(db_document)
    db.commit()
    
    return db_document