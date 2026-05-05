#uvicorn main:app --reload

from fastapi import FastAPI
from api import document  # mount router
from fastapi.responses import RedirectResponse

app = FastAPI(title="Enterprise Knowledge Agent API")

# mount router
app.include_router(document.router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")