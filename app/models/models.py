from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship


class Document(Base):
    #DataBase MetaData
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, index=True, nullable=False)   
    file_path = Column(String, nullable=False)              
    uploader = Column(String, nullable=False) 
    # PENDING, PROCESSING, COMPLETED, FAILED              
    status = Column(String, default="PENDING")
    
    # get the time from the database
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship(
        "DocumentChunk", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 主表刪掉、子表也會跟著被刪掉
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'))
    
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # 💡 Gemini 768
    embedding = Column(Vector(768)) 
    
    # 讓子表也能反向找到主文件
    document = relationship("Document", back_populates="chunks")