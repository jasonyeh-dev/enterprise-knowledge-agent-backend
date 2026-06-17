import ssl

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

def get_db_engine(db_url: str):
    connect_args = {}
    
    # 判斷是否為 NeonDB (連線字串會包含 neon.tech)
    # run remote NeonDB or localDB
    if "neon.tech" in db_url:
        ssl_context = ssl.create_default_context()
        # ssl_context.check_hostname = False
        # ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args=connect_args
    )
    return engine


engine = get_db_engine(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass    