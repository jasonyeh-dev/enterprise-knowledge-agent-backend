from pydantic import BaseModel
from datetime import datetime

class DeleteDocument(BaseModel):
    id: int

class DeleteResponse(BaseModel):
    message: str
    deleted_id: int
    deleted_filename: str
    
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