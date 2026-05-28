from sqlalchemy.orm import Session, joinedload #for database communication
from app.models.models import Document, DocumentChunk  
from sqlalchemy import select

def create_document(db: Session, filename: str, file_path: str, uploader_id: int):
    db_document = Document(
        filename=filename,
        file_path=file_path,
        uploader_id=uploader_id,
        status="PENDING"  
    )
    
    db.add(db_document)
    # return DB model
    return db_document

def get_upload_status_by_id(db: Session, doc_id:int):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    return {"status": doc.status} # 只會回傳 PENDING, COMPLETED 或 FAILED

def list_documents(db: Session):

    return (
            db.query(Document)
            # 一次性把關聯的 uploader (Account) 預先載入
            .options(joinedload(Document.uploader))
            .all()
        )

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

def get_similar_chunks_with_score(db: Session, question_embedding: list[float], limit: int = 3, threshold: float = 0.4):

        # 1. 定義計算距離的欄位，並幫它取個標籤名稱 "distance"
        # 數值越接近 0，代表語意越一模一樣；數值越接近 1（或更大），代表兩句話的意思毫無關聯。
        distance_col = DocumentChunk.embedding.cosine_distance(question_embedding).label("distance")

        stmt = (
            select(DocumentChunk, distance_col)
            .order_by("distance")
            .limit(limit)
        )
        
        results = db.execute(stmt).all()

        # 4. 實作防呆/精準度過濾：只保留距離小於 threshold 的結果
        # results 的每一筆資料會是一個 Tuple: (DocumentChunk實體, distance分數)
        filtered_chunks = []
        for chunk, distance in results:
            if distance < threshold:
                filtered_chunks.append((chunk, distance))

        return filtered_chunks
