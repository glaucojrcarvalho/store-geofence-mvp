from fastapi import APIRouter
from .routers import auth, companies, stores, tasks, demo

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(companies.router, prefix="/companies", tags=["companies"])
router.include_router(stores.router, prefix="/stores", tags=["stores"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(demo.router, tags=["demo"])

