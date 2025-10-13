from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db import SessionLocal
from app.models.models import Store, GeocodeJob
from app.services.geocoding import geocode_address

@shared_task(name="app.workers.tasks.enqueue_geocode", bind=True, max_retries=5, default_retry_delay=30)
def enqueue_geocode(self, store_id: int):
    db: Session = SessionLocal()
    try:
        store = db.get(Store, store_id)
        if not store:
            return

        job = GeocodeJob(store_id=store_id, status="running")
        db.add(job)
        db.commit()
        db.refresh(job)

        parts = [store.address_lines or "", store.city or "", store.state or "", store.country or "", store.postal_code or ""]
        address = ", ".join([p for p in parts if p])

        import asyncio
        coords = asyncio.get_event_loop().run_until_complete(geocode_address(address))

        if not coords:
            job.status = "failed"
            job.error_msg = "geocoder_no_result"
            store.geocode_status = "failed"
            db.commit()
            return

        lat, lng = coords
        db.execute(text("UPDATE stores SET location = ST_SetSRID(ST_MakePoint(:lng,:lat),4326)::geography, geocode_status = 'success' WHERE id = :id"),
                   {"lng": lng, "lat": lat, "id": store_id})
        job.status = "success"
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            self.retry(exc=e)
        except Exception:
            pass
        finally:
            fail = GeocodeJob(store_id=store_id, status="failed", error_msg=str(e))
            db.add(fail)
            db.commit()
    finally:
        db.close()

