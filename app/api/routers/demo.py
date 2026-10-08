from math import asin, cos, radians, sin, sqrt
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from app.core.ratelimit import public_rate_limit

router = APIRouter()
# Illustrative public coordinate only: not a real store or actual GPS claim.
DEMO_LAT, DEMO_LNG, DEMO_RADIUS_M = 50.4501, 30.5234, 100


class DemoCheck(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


def distance_m(lat: float, lng: float) -> float:
    lat1, lat2 = radians(DEMO_LAT), radians(lat)
    dlat, dlng = lat2 - lat1, radians(lng - DEMO_LNG)
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * 6371008.8 * asin(min(1.0, sqrt(max(0.0, a))))


@router.post("/demo/check", dependencies=[Depends(public_rate_limit("demo_check", 30, 60))])
def check_demo(payload: DemoCheck):
    distance = distance_m(payload.lat, payload.lng)
    return {"allowed": distance <= DEMO_RADIUS_M, "distance_m": round(distance, 2),
            "radius_m": DEMO_RADIUS_M, "synthetic": True,
            "disclaimer": "Illustration only. Client-supplied coordinates are not verified physical presence."}


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Try a synthetic geofence decision, powered by a FastAPI public demo.">
<title>Store Geofence — Interactive Demo</title>
<style>
:root { color-scheme: dark; font-family: system-ui, sans-serif; }
body { background: #0c1524; color: #f1f5f9; margin: 0; padding: 2rem 1rem; }
main { max-width: 750px; margin: 3rem auto; }
h1 { font-size: clamp(2rem, 6vw, 3.2rem); margin-bottom: .4rem; }
p { color: #b8c5d5; line-height: 1.65; }
.panel { border: 1px solid #30425c; background: #132338; border-radius: 16px; padding: 1.5rem; margin-top: 1.6rem; }
button { border: 1px solid #7396cd; border-radius: 9px; padding: .8rem 1.2rem;
 color: #f8fafc; background: #284977; cursor: pointer; margin: .4rem .5rem .4rem 0; }
button:focus-visible { outline: 3px solid #fff; }
output { display: block; padding: 1rem; margin-top: .8rem; border: 1px solid #64748b;
 border-radius: 8px; min-height: 2.5rem; }
small { color: #c0cbdc; } a { color: #9ec5ff; }
</style></head>
<body><main>
<small>BACKEND ENGINEERING / DEMONSTRATION</small>
<h1>Store Geofence</h1>
<p>Can a reported location fall inside a store's allowed radius? Try two synthetic locations and see the distance calculation.</p>
<section class="panel" aria-labelledby="demo-title">
<h2 id="demo-title">100-metre geofence</h2>
<p>Fictional store at an illustrative Kyiv city-centre coordinate. No GPS permissions, accounts, real store records or location history.</p>
<button type="button" id="inside">Try inside location</button>
<button type="button" id="outside">Try outside location</button>
<output id="result" role="status" aria-live="polite">Choose an example to run the check.</output>
</section>
<p><small>Location inputs are synthetic and no submissions are persisted. This demonstrates distance logic, not device attestation or anti-spoofing. The production demo does not expose administrative routes.</small></p>
<p><a href="/docs">Explore the API documentation</a></p>
</main>
<script>
const result = document.getElementById("result");
async function check(lat, lng) {
  result.textContent = "Checking synthetic location…";
  try {
    const response = await fetch("/demo/check", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({lat, lng})
    });
    if (!response.ok) { result.textContent = "Demo unavailable (" + response.status + ")."; return; }
    const data = await response.json();
    result.textContent = (data.allowed ? "INSIDE" : "OUTSIDE") + " — " +
      data.distance_m.toFixed(1) + " metres from the sample store (radius " +
      data.radius_m + " m).";
  } catch { result.textContent = "Network error. Please retry."; }
}
document.getElementById("inside").addEventListener("click", () => check(50.4502, 30.5234));
document.getElementById("outside").addEventListener("click", () => check(50.4540, 30.5234));
</script></body></html>"""


@router.get("/", response_class=HTMLResponse)
def index():
    return HTML
