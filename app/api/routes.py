from fastapi import APIRouter
from app.core.config import settings
from .routers import auth, companies, stores, tasks, demo

router = APIRouter()
router.include_router(demo.router, tags=["public-demo"])

# Public production exposes ONLY stateless synthetic geofence calculations.
# The database-backed business API stays limited to local / private environments.
if settings.ENABLE_PRIVATE_API and settings.APP_ENV != "prod":
    router.include_router(auth.router, prefix="/auth", tags=["auth"])
    router.include_router(companies.router, prefix="/companies", tags=["companies"])
    router.include_router(stores.router, prefix="/stores", tags=["stores"])
    router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
