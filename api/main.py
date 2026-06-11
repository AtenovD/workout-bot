from fastapi import FastAPI
from core.config import settings

app = FastAPI(title="Workout Bot API", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/")
async def root():
    return {"message": "Workout Bot API"}
