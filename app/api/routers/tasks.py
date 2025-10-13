from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db import get_db
from app.models.models import Task, Store, Company
from app.schemas.schemas import TaskCreate, TaskOut, TaskRunRequest, TaskRunOut
from app.core.auth import get_current_user, require_role
from app.core.ratelimit import rate_limit
from app.services.distances import within_radius_and_distance

router = APIRouter()

@router.post("", response_model=TaskOut, dependencies=[Depends(require_role("admin"))])
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    store = db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    t = Task(store_id=payload.store_id, title=payload.title, description=payload.description, created_by="admin")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.get("", response_model=list[TaskOut])
def list_tasks(store_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.store_id == store_id).all()

@router.post("/{task_id}/run", response_model=TaskRunOut, dependencies=[Depends(rate_limit('task_run', 10, 60))])
def run_task(task_id: int, payload: TaskRunRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task or not task.active:
        raise HTTPException(status_code=404, detail="Task not found")

    store = db.get(Store, task.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if store.geocode_status != "success" or store.location is None:
        raise HTTPException(status_code=409, detail="Store location not ready")

    company = db.get(Company, store.company_id)
    effective_radius = store.custom_radius_m or company.geofence_radius_m

    within, distance = within_radius_and_distance(db, store.id, payload.lat, payload.lng, effective_radius)
    if distance is None:
        raise HTTPException(status_code=409, detail="Store location not ready")

    # Insert the task run atomically with the client location to avoid NULL constraint issues
    insert_sql = text(
        "INSERT INTO task_runs (task_id, worker_id, client_location, distance_m, allowed) "
        "VALUES (:task_id, :worker_id, ST_SetSRID(ST_MakePoint(:lng,:lat),4326)::geography, :distance_m, :allowed) RETURNING id"
    )
    params = {
        "task_id": task.id,
        "worker_id": user.sub,
        "lng": payload.lng,
        "lat": payload.lat,
        "distance_m": distance,
        "allowed": bool(within),
    }
    res = db.execute(insert_sql, params)
    # consume the returned id to ensure the INSERT executed successfully
    res.scalar_one()
    db.commit()

    return TaskRunOut(allowed=bool(within), distance_m=distance)
