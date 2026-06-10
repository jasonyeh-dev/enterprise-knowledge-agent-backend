from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.config import settings
from app.core.context import current_user_account

# 1. 宣告 OAuth2 鎖頭，右上角加上一個 "Authorize" 鎖頭按鈕
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/auth")

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