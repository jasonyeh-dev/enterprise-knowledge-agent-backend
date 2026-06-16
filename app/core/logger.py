from app.core.config import settings
from app.core.context import current_user_account
from loguru import logger
import sys


def setup_logger()-> None:
    def inject_user_context(record):
            record["extra"]["user_account"] = current_user_account.get()
            user = current_user_account.get()
            print(f"PATCHER CALLED: {user}")

    logger.remove()
    logger.configure(
         extra={"request_id": "SYSTEM","client_ip": "SYSTEM" },
         #everytime before write log will call the patch function
         patcher=inject_user_context
         )


    Console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<yellow>{extra[request_id]}</yellow> | "
    "<magenta>{extra[client_ip]}</magenta> | "
    "<yellow>{extra[user_account]}</yellow> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
    )

    File_Format = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{extra[request_id]} | "
    "{extra[client_ip]} | "
    "{extra[user_account]} | "
    "{name}:{line} | "
    "{message}"
    )

    if settings.ENVIRONMENT == "production":
        # GCP Cloud mode
        logger.add(
            sys.stdout, 
            serialize=True, 
            level="INFO"
        )
    else:
        # Local mode
        logger.add(
            sys.stdout,
            colorize=True,
            level="INFO",
            format=Console_format
        )
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log", 
            rotation="00:00",    
            retention="7 days", 
            level="INFO",
            encoding="utf-8",
            compression="zip",
            format=File_Format
        )

