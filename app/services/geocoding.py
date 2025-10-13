import httpx
from app.core.config import settings

GOOGLE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

async def geocode_address(address: str) -> tuple[float, float] | None:
    params = {"address": address, "key": settings.GOOGLE_MAPS_API_KEY}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(GOOGLE_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "OK" and data.get("results"):
            res = data["results"][0]
            loc = res["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    return None

