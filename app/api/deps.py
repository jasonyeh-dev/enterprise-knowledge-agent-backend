# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.security import SECRET_KEY, ALGORITHM

# 1. 宣告 OAuth2 鎖頭
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# 2. 建立共用的 Token 解密與驗證守衛
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        # 進行 JWT 解碼
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="無效的憑證"
            )
        return int(user_id_str)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="憑證已過期，請重新登入"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="憑證驗證失敗"
        )