from celery import Celery
from app.core.config import settings

celery_app = Celery("geofence", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {"app.workers.tasks.enqueue_geocode": {"queue": "geocode"}}

