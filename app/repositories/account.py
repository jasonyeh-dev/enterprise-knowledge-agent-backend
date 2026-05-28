from sqlalchemy.orm import Session #for database communication
from app.models.models import User

class AccountRepository:
    def create(self, db: Session, account: str, password_hash: str) -> User:
        """無腦將資料寫入資料庫"""
        db_account = User(
            account=account, 
            password_hash=password_hash
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account) # 讓物件拿到資料庫自動產生的 ID
        
        return db_account
    
    def get_by_account(self, db: Session, account_name:str):
        user_account = db.query(User).filter(
            User.account == account_name,
            User.is_active== True
        ).first()
        return user_account

account_repo = AccountRepository()