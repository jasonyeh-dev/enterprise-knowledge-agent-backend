#uvicorn main:app --reload --proxy-headers --forwarded-allow-ips="*"
import sys
from fastapi import FastAPI, APIRouter, Request
from app.api import document,account  # mount router
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager
import time
import uuid
from app.core.config import settings
from app.core.context import current_user_account


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



setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System startup...")
    # ready to receive http request
    yield
    logger.info("System shutdown...")

app = FastAPI(lifespan=lifespan, title="Enterprise Knowledge Agent API")

origins = [
    "http://localhost:5173",             
    "https://speedy-rite-466709-f1.web.app", 
    "https://speedy-rite-466709-f1.firebaseapp.com"
]

#CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=False, 
    # GET, POST, PUT, DELETE, OPTIONS
    allow_methods=["*"], 
    allow_headers=["*"], 
)

#rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

#response time and so on...
@app.middleware("http")
async def add_process_time_uuid(request: Request, call_next):
    req_id = str(uuid.uuid4())[:8]
    client_ip = request.client.host if request.client else "Unknown"

    with logger.contextualize(request_id=req_id, client_ip=client_ip):
        start_time = time.perf_counter()

        logger.info(f"Request | {request.method} {request.url.path}")

        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(f"Request Completed | Status: {response.status_code} | Time-Consuming: {process_time :.2f}ms")
        
        # response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = req_id
        return response



api_router = APIRouter(prefix="/api")
# mount router
api_router.include_router(document.router)
api_router.include_router(account.router)


app.include_router(api_router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")