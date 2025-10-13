from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router

app = FastAPI(title="Store Geofence MVP", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "env": settings.APP_ENV}

app.include_router(api_router)

