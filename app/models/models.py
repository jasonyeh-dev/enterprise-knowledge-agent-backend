from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.sql import func
from app.core.database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import enum

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    #DataBase MetaData
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), index=True, nullable=False)   
    file_path = Column(String(1024), nullable=False)              
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    uploader = relationship("User")
    # Only PENDING, COMPLETED, FAILED
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False) 
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
     
class User(Base):
    #DataBase MetaData
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account = Column(String(50), index=True, nullable=False, unique=True)   
    password_hash = Column(String(255), nullable=False)              
    is_active = Column(Boolean, nullable=False, default=True)   

    document = relationship("Document")