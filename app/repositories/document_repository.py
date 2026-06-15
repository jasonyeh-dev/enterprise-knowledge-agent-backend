from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload  # for database communication

from app.models.models import Document, DocumentChunk
from app.models.schemas import DocumentStatus


class DocumentRepository:

    async def create_document(self, 
                              db: AsyncSession, 
                              filename: str, 
                              file_path: str, 
                              uploader_id: int) -> Document:
        
        db_document = Document(
            filename=filename,
            file_path=file_path,
            uploader_id=uploader_id,
            status="PENDING"  
        )
        db.add(db_document)

        return db_document

    async def list_documents(self, db: AsyncSession) -> list[Document]:
        stmt = (
            select(Document)
            .options(joinedload(Document.uploader))
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())
        
    async def get_documents_by_ids(
            self, db: AsyncSession, 
            document_list:list[int]) -> list[Document]:

        if not document_list:
            return []
        
        stmt = select(Document).where(Document.id.in_(document_list))
        
        #result type is tuple not an object
        result = await db.execute(stmt)
        
        return list(result.scalars().all())
        
    async def get_upload_status_by_id(self, db: AsyncSession, doc_id:int) -> DocumentStatus | None:   
        stmt = select(Document.status).where(Document.id == doc_id)
        result = await db.execute(stmt)
        # scalar() 會直接回傳第一個欄位的值 (字串)，如果找不到就會回傳 None
        status_str = result.scalar() 
    
        if status_str is None:
            return None
        return DocumentStatus(status_str)
    
    async def update_document_status(self, db: AsyncSession, doc_id: int, new_status: str) -> None:
        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(status=new_status)
        )
        
        await db.execute(stmt)
        await db.commit()

    async def get_similar_chunks_with_score(self, db: AsyncSession, question_embedding: list[float], 
                                            limit: int, threshold: float) -> list[tuple[DocumentChunk, float]]:
        # 1. 定義計算距離的欄位
        # 數值越接近 0，代表語意越一模一樣；數值越接近 1，代表兩句話的意思毫無關聯。
        distance_col = DocumentChunk.embedding.cosine_distance(question_embedding).label("distance")

        # results 的每一筆資料會是一個 Tuple: (DocumentChunk實體, distance分數)
        #只保留距離小於 threshold 的結果
        #eager loading
        stmt = (
            select(DocumentChunk, distance_col)
            .options(joinedload(DocumentChunk.document))
            .where(distance_col < threshold) 
            .order_by("distance")
            .limit(limit)
            
        )
        result = await db.execute(stmt)
        
        # select 了兩個東西 (實體, 欄位)，所以不用 scalars()，直接 .all() 拿回 tuple 列表
        return list(result.all())

    async def get_document_with_relations(self, db: AsyncSession, Doc_id: int)-> Document | None:
        #eager loading
        stmt = (
            select(Document)
            .options(joinedload(Document.uploader))
            .where(Document.id == Doc_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()
        


document_repo = DocumentRepository()