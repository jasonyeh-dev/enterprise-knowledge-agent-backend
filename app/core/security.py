import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# rate limiter using IP
limiter = Limiter(
    key_func=get_remote_address, 
    default_limits=["30/minute"],
    enabled=getattr(settings, "ENABLE_RATE_LIMIT", True),
    )

def get_password_hash(password: str) -> str:
    # 1. bcrypt 要求輸入必須是 bytes 格式
    pwd_bytes = password.encode('utf-8')
    # 2. bcrypt 進行加密
    hashed_bytes = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 驗證時，雙方都必須轉換為 bytes 格式
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # 交給 bcrypt 底層的 C 語言引擎去比對
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    #Avoid modifying the original memory address
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Use SECRET_KEY to generate signature
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt