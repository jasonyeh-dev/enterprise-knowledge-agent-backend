import ssl

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# engine = create_async_engine(settings.DATABASE_URL, echo=False)
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    connect_args={
        "ssl": ssl_context
    }
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass    