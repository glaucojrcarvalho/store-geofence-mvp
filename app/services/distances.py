from sqlalchemy import text
from sqlalchemy.orm import Session

def within_radius_and_distance(db: Session, store_id: int, lat: float, lng: float, radius_m: int):
    sql = text('''
        SELECT
            CASE
              WHEN s.location IS NULL THEN NULL
              ELSE ST_DWithin(
                    s.location,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :radius
                  )
            END AS within,
            CASE
              WHEN s.location IS NULL THEN NULL
              ELSE ST_Distance(
                    s.location,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                  )
            END AS distance_m
        FROM stores s
        WHERE s.id = :store_id
        LIMIT 1;
    ''')
    row = db.execute(sql, {"store_id": store_id, "lat": lat, "lng": lng, "radius": radius_m}).mappings().first()
    if not row:
        return (False, None)
    if row["within"] is None:
        return (False, None)
    return (bool(row["within"]), float(row["distance_m"]))

