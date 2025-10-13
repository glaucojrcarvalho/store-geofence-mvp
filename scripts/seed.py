from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.models import Company, Store, Task
from app.workers.tasks import enqueue_geocode

def run():
    db: Session = SessionLocal()
    try:
        acme = Company(name="Acme Inc", geofence_radius_m=100)
        db.add(acme); db.commit(); db.refresh(acme)
        st = Store(company_id=acme.id, name="Kyiv Center", address_lines="Khreshchatyk 1", city="Kyiv", country="Ukraine", postal_code="01001", geocode_status="pending")
        db.add(st); db.commit(); db.refresh(st)
        enqueue_geocode.delay(st.id)
        t = Task(store_id=st.id, title="Daily checklist")
        db.add(t); db.commit()
        print("Seed OK")
    finally:
        db.close()

if __name__ == "__main__":
    run()

