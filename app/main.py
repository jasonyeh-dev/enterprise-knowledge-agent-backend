#uvicorn main:app --reload --proxy-headers --forwarded-allow-ips="*"
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google import genai
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import account, document  # mount router
from app.core.config import settings
from app.core.logger import setup_logger

from app.core.security import limiter
from app.services.document_service import (ChunkingService, DocumentService,
                                           EmbeddingService, RagService)

setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System startup...")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    embedding_service = EmbeddingService(client=client)  
    chunking_service = ChunkingService()                  

    app.state.document_service = DocumentService(
        embedding_service=embedding_service,
        chunking_service=chunking_service,
    )
    app.state.rag_service = RagService(
        client=client,
        embedding_service=embedding_service,
    )

    yield
    await client.aio.aclose()

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
        logger.info(f"Request Completed | Status: {response.status_code} | Time-Consuming: {process_time:.4f}s")
        
        # response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = req_id
        return response



api_router = APIRouter(prefix=settings.API_V1_STR)
# mount router
api_router.include_router(document.router)
api_router.include_router(account.router)


app.include_router(api_router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")