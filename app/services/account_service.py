from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.account import account_repo
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.schemas import AccountCreateRequest
from loguru import logger


class AccountService:
    def create_account(self, db: Session, request: AccountCreateRequest):
        
        logger.info(f"Creating new account {request.account}...")
        
        # check the account in DB
        existing_user = account_repo.get_by_account(db, request.account)
        if existing_user:
            logger.warning(f"Create Failed, the account is occupied ({request.account})")
            raise HTTPException(status_code=400, detail="This account is existing")

        hashed_pw = get_password_hash(request.password)

        new_account = account_repo.create(
            db=db, 
            account=request.account, 
            password_hash=hashed_pw
        )
        logger.info(f"Create Account successful ID={new_account.id}, Account={new_account.account}")
        
        return new_account
    
    def authenticate_user(self, db: Session, account_name: str, plain_password: str) -> str:
        # 1. Query the user from DB
        
        logger.info(f"Receieve login request, Account={account_name}")

        user = account_repo.get_by_account(db, account_name=account_name)
        
        if not user or not verify_password(plain_password, user.password_hash):
            logger.warning(f"Login Fail, Wrong account or password (Account={account_name})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong account or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Login successful: ID={user.id}, Account={user.account}")
        
        # 2. put userid and account into payload then create signature
        token_data = {"sub": str(user.id), "account": user.account}
        access_token = create_access_token(data=token_data)
        
        return access_token

account_service = AccountService()