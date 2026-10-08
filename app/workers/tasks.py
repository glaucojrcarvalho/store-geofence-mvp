import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db import SessionLocal
from app.models.models import Store, GeocodeJob
from app.services.geocoding import geocode_address
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.enqueue_geocode", bind=True,
                 max_retries=5, default_retry_delay=30)
def enqueue_geocode(self, store_id: int):
    db: Session = SessionLocal()
    try:
        store = db.get(Store, store_id)
        if not store:
            return

        job = (db.query(GeocodeJob)
               .filter(GeocodeJob.store_id == store_id, GeocodeJob.status == "queued")
               .order_by(GeocodeJob.id.desc()).first())
        if job is None:
            job = GeocodeJob(store_id=store_id, status="queued")
            db.add(job)
        job.status = "running"
        job.attempts = self.request.retries + 1
        db.commit()

        parts = [store.address_lines or "", store.city or "", store.state or "",
                 store.country or "", store.postal_code or ""]
        address = ", ".join(p for p in parts if p)
        coords = asyncio.run(geocode_address(address))

        if coords is None:
            job.status = "failed"
            job.error_msg = "geocoder_no_result"
            store.geocode_status = "failed"
            db.commit()
            return

        lat, lng = coords
        db.execute(text(
            "UPDATE stores SET location = ST_SetSRID(ST_MakePoint(:lng,:lat),4326)::geography, "
            "geocode_status = 'success' WHERE id = :id"
        ), {"lng": lng, "lat": lat, "id": store_id})
        job.status = "success"
        job.error_msg = None
        db.commit()

    except Exception as exc:
        db.rollback()
        if self.request.retries >= self.max_retries:
            store = db.get(Store, store_id)
            if store:
                store.geocode_status = "failed"
            job = (db.query(GeocodeJob)
                   .filter(GeocodeJob.store_id == store_id)
                   .order_by(GeocodeJob.id.desc()).first())
            if job:
                job.status = "failed"
                job.error_msg = "geocoding_failed_after_retries"
            db.commit()
            raise
        raise self.retry(exc=exc)
    finally:
        db.close()
