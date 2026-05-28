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

class AccountBasicInfo(BaseModel):
    id: int
    account: str

# decide which format you want to return to the FrontEnd
class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploader: AccountBasicInfo
    status: str
    uploaded_at: datetime

    class Config:
        #translate ORM object into JSON format
        # 物件可以自行讀取
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

class AccountCreateRequest(BaseModel):
    account: str
    password: str

class AccountResponse(BaseModel):
    id: int
    account: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
