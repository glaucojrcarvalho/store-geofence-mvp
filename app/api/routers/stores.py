from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Store, Company, GeocodeJob
from app.schemas.schemas import StoreCreate, StoreOut
from app.core.auth import require_role
from app.workers.tasks import enqueue_geocode

router = APIRouter()

@router.post("", response_model=StoreOut, dependencies=[Depends(require_role("admin"))])
def create_store(payload: StoreCreate, db: Session = Depends(get_db)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    s = Store(
        company_id=payload.company_id,
        name=payload.name,
        address_lines="; ".join(payload.address_lines),
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        geocode_status="pending"
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    job = GeocodeJob(store_id=s.id, status="queued")
    db.add(job)
    db.commit()

    enqueue_geocode.delay(s.id)
    return s

@router.get("/{store_id}", response_model=StoreOut)
def get_store(store_id: int, db: Session = Depends(get_db)):
    s = db.get(Store, store_id)
    if not s:
        raise HTTPException(status_code=404, detail="Store not found")
    return s

@router.post("/{store_id}/geocode:retry", dependencies=[Depends(require_role("admin"))])
def retry_geocode(store_id: int, db: Session = Depends(get_db)):
    s = db.get(Store, store_id)
    if not s:
        raise HTTPException(status_code=404, detail="Store not found")
    s.geocode_status = "pending"
    db.commit()
    enqueue_geocode.delay(s.id)
    return {"status": "queued"}

