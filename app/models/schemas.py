from pydantic import BaseModel
from datetime import datetime

# FrontEnd return format 
class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploader: str
    status: str
    uploaded_at: datetime

    
    class Config:
        #translate ORM object into JSON format
        from_attributes = True