from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.core.config import settings
from app.api.routes import router as api_router
from app.core.db import engine

app = FastAPI(title="Store Geofence MVP", version="0.1.0")

@app.get("/healthz")
def healthz():
    # ensure DB is reachable before reporting healthy (helps CI e2e reliability)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")
    return {"status": "ok", "env": settings.APP_ENV}

app.include_router(api_router)
