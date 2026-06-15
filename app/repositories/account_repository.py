from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User


class AccountRepository:
    async def create(self, db: AsyncSession, account: str, password_hash: str) -> User:
        db_account = User(
            account=account, 
            password_hash=password_hash
        )
        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        
        return db_account
    
    async def get_by_account(self, db: AsyncSession, account_name:str) -> User | None:
        stmt = select(User).filter(
            User.account == account_name,
            User.is_active == True
        )
        result = await db.execute(stmt)
        user_account = result.scalars().first()

        return user_account
    
account_repo = AccountRepository()