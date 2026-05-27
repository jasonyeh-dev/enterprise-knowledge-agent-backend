from pydantic import BaseModel
from datetime import datetime
from typing import List

class DeleteRequest(BaseModel):
    document_ids: list[int]

class DeletedDocument(BaseModel):
    id: int
    filename: str

class DeleteResponse(BaseModel):
    message: str
    deleted_documents: list[DeletedDocument]
    
# decide which format you want to return to the FrontEnd
class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploader: str
    status: str
    uploaded_at: datetime

    
    class Config:
        #translate ORM object into JSON format
        from_attributes = True

class SourceItem(BaseModel):
    filename: str
    chunk_content: str
    similarity_score: float

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem]