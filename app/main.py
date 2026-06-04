#uvicorn main:app --reload
import sys
from fastapi import FastAPI, APIRouter, Depends
from app.api import document,account  # mount router
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter
from slowapi.middleware import SlowAPIMiddleware

logger.add(sys.stderr, level="INFO")

logger.add(
    "logs/app_{time:YYYY-MM-DD}.log", 
    rotation="00:00", 
    retention="7 days", 
    level="INFO",
    encoding="utf-8"
)

app = FastAPI(title="Enterprise Knowledge Agent API")


origins = [
    "http://localhost:5173",             
    "https://speedy-rite-466709-f1.web.app", 
    "https://speedy-rite-466709-f1.firebaseapp.com"
]

# 加入 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=False, 
    # GET, POST, PUT, DELETE, OPTIONS
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

api_router = APIRouter(prefix="/api")
# mount router
api_router.include_router(document.router)
api_router.include_router(account.router)


app.include_router(api_router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")