"""Ponto de entrada FastAPI."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api import router
from core.logger import get_logger

log = get_logger()

app = FastAPI(title="OSINT Username Finder", version="1.0.0")

app.include_router(router)

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(FRONTEND / "index.html"))


@app.on_event("startup")
async def startup():
    log.info("OSINT Username Finder iniciado")
