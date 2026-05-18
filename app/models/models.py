from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base 

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