import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from core.database import  get_db
import repositories.document as document_sql  
from models.schemas import DocumentResponse


from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    prefix="/documents",
    tags=["Documents (Knowledge base management)"]
)


UPLOAD_DIR = os.environ.get("upload_DIR")



@router.post("/upload", response_model=DocumentResponse)
def upload_file(

    # Swagger generate upload buttom and input place
    file: UploadFile = File(...), 
    uploader: str = Form(...),    
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    
        
    # 3. CRUD part
    saved_record = document_sql.create_document_record(
        db=db, 
        filename=file.filename, 
        file_path=file_path, 
        uploader=uploader
    )
    
    # 4. return message
    return saved_record

