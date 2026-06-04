from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import  get_db
from app.models.schemas import AccountCreateRequest, AccountResponse, TokenResponse
from app.services.account_service import account_service
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_current_user_id
from app.core.security import limiter

router = APIRouter(
    prefix="/user",
    tags=["user related"]
)

@router.post("", response_model=AccountResponse,  dependencies=[Depends(get_current_user_id)])
async def create_user(
    request: AccountCreateRequest, 
    db: Session = Depends(get_db)
):
    new_user = account_service.create_account(db=db, request=request)
    return new_user

@router.post("/auth", response_model=TokenResponse)
@limiter.limit("5/minute")
def login_for_access_token(
    # FastAPI 內建的表單工具，會自動去解析前端傳來的 username 與 password 欄位
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 呼叫 Service 進行雙重驗證並取得加密字串
    token_str = account_service.authenticate_user(
        db=db, 
        account_name=form_data.username, 
        plain_password=form_data.password
    )
    
    # 完美回傳合約定義的格式
    return {"access_token": token_str, "token_type": "bearer"}