#uvicorn main:app --reload
import sys
from fastapi import FastAPI
from app.api import document,account  # mount router
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

logger.add(sys.stderr, level="INFO")

logger.add(
    "logs/app_{time:YYYY-MM-DD}.log", 
    rotation="00:00", 
    retention="7 days", 
    level="INFO",
    encoding="utf-8"
)

app = FastAPI(title="Enterprise Knowledge Agent API")

# 加入 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    
    allow_credentials=False, 
    
    # GET, POST, PUT, DELETE, OPTIONS
    allow_methods=["*"], 
    
    allow_headers=["*"], 
)

# mount router
app.include_router(document.router)
app.include_router(account.router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")