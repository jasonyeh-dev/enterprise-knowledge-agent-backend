import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.context import current_user_account
from app.core.database import AsyncSessionLocal
from app.services.document_service import DocumentService, RagService


# async with will do the db.close() automatically
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

def get_rag_service(request: Request) -> RagService:
    return request.app.state.rag_service

def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service


# 1. 宣告 OAuth2 鎖頭，右上角加上一個 "Authorize" 鎖頭按鈕
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.AUTH_TOKEN_URL)

#async for let the main loop function know current_user_account has changed
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Certificate Invalid"
            )
        
        user_account: str = payload.get("account")

        current_user_account.set(user_account)


        return int(user_id)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Certificate expired, Please relogin"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Certificate failed"
        )