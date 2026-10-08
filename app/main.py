from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.api.routes import router as api_router
from app.core.db import engine
from app.core.config import settings

app = FastAPI(
    title="Store Geofence — Public Demonstration",
    version="0.2.0",
    description="Synthetic demonstration only; caller-supplied GPS coordinates are not proof of physical presence.",
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if settings.APP_ENV == "prod":
        # Public demo uses Redis for rate limiting but no customer database.
        from app.core.ratelimit import _redis
        try:
            if _redis is None or not _redis.ping():
                raise RuntimeError("Redis unavailable")
        except Exception:
            raise HTTPException(status_code=503, detail="Dependency not ready") from None
        return {"status": "ready"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Dependency not ready") from None
    return {"status": "ready"}


app.include_router(api_router)
