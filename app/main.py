from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.core.config import settings
from app.api.routes import router as api_router
from app.core.db import engine

app = FastAPI(title="Store Geofence MVP", version="0.1.0")

@app.get("/healthz")
def healthz():
    # Liveness check: always return 200 quickly and include DB status for observability.
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "env": settings.APP_ENV, "db": db_status}


@app.get("/readyz")
def readyz():
    # Readiness check: report non-200 if DB isn't available.
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")
    return {"status": "ready", "env": settings.APP_ENV}

app.include_router(api_router)
