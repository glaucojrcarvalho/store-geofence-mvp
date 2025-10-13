from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Company
from app.schemas.schemas import CompanyCreate, CompanyOut, CompanyUpdate
from app.core.auth import require_role

router = APIRouter()

@router.post("", response_model=CompanyOut, dependencies=[Depends(require_role("admin"))])
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    c = Company(name=payload.name, geofence_radius_m=payload.geofence_radius_m)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.patch("/{company_id}", response_model=CompanyOut, dependencies=[Depends(require_role("admin"))])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    c.geofence_radius_m = payload.geofence_radius_m
    db.commit()
    db.refresh(c)
    return c

