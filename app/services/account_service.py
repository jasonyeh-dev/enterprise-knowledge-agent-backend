from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.account import account_repo
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.schemas import AccountCreateRequest


class AccountService:
    def create_account(self, db: Session, request: AccountCreateRequest):
        # 🚧 防呆 1：這裡實務上會先去 DB 查這個 account 是不是已經被註冊了
        # existing_user = account_repo.get_by_account(db, request.account)
        # if existing_user:
        #     raise HTTPException(status_code=400, detail="此帳號已存在")

        hashed_pw = get_password_hash(request.password)

        # 把處理好的資料交給苦力 (Repository) 去存
        new_account = account_repo.create(
            db=db, 
            account=request.account, 
            password_hash=hashed_pw
        )
        
        return new_account
    
    def authenticate_user(self, db: Session, account_name: str, plain_password: str) -> str:
        # 1. 去資料庫找有沒有這個人
        user = account_repo.get_by_account(db, account_name=account_name)
        

        if not user or not verify_password(plain_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="帳號或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. 驗證成功！將使用者的關鍵 ID 綁進 Token 中 (通常使用 sub 欄位)
        token_data = {"sub": str(user.id), "account": user.account}
        access_token = create_access_token(data=token_data)
        
        return access_token

account_service = AccountService()