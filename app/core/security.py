import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# rate limiter using IP
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

def get_password_hash(password: str) -> str:
    # 1. bcrypt 要求輸入必須是 bytes 格式
    pwd_bytes = password.encode('utf-8')
    # 2. bcrypt 進行加密
    hashed_bytes = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """登入時驗證密碼"""
    # 驗證時，雙方都必須轉換為 bytes 格式
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # 交給 bcrypt 底層的 C 語言引擎去比對
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    
    # 計算過期時間
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 將過期時間押入 Payload (exp)
    to_encode.update({"exp": expire})
    
    # 使用 SECRET_KEY 進行加密簽章
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt