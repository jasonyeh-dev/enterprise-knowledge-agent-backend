from sqlalchemy.orm import Session #for database communication
from app.models.models import User

class AccountRepository:
    def create(self, db: Session, account: str, password_hash: str) -> User:
        db_account = User(
            account=account, 
            password_hash=password_hash
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        
        return db_account
    
    def get_by_account(self, db: Session, account_name:str) -> User | None:
        user_account = db.query(User).filter(
            User.account == account_name,
            User.is_active== True
        ).first()
        return user_account

account_repo = AccountRepository()