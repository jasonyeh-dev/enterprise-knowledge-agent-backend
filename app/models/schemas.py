from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict


#Shared & Enums
class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

#Account Domain
class AccountBasicInfo(BaseModel):
    id: int
    account: str
    model_config = ConfigDict(from_attributes=True)

class AccountCreateRequest(BaseModel):
    account: str
    password: str

class AccountResponse(AccountBasicInfo):
    is_active: bool

#Document Domain
class DocumentStatusResponse(BaseModel):
    status: DocumentStatus

class DeleteRequest(BaseModel):
    document_ids: list[int]

class DocumentBase(BaseModel):
    id: int
    filename: str

class DocumentSummary(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

class DocumentDeleteInfo(DocumentSummary):
    file_path: str

class DeleteResponse(BaseModel):
    message: str
    deleted_documents: list[DocumentSummary]

class DocumentResponse(DocumentBase):
    uploader: AccountBasicInfo
    status: DocumentStatus
    uploaded_at: datetime
    #translate ORM object into JSON format
    model_config = ConfigDict(from_attributes=True)

#RAG Domain
class SourceItem(BaseModel):
    filename: str
    chunk_content: str
    similarity_score: float

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem]

#Auth Domain
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

