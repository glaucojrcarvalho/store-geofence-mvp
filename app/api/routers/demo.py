from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Store Geofence MVP</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }
    code { background: #f6f8fa; padding: .15rem .35rem; border-radius: 4px; }
    pre { background: #f6f8fa; padding: 1rem; border-radius: 6px; overflow:auto; }
    .tag { display:inline-block; background:#eef; padding:.2rem .5rem; border-radius:6px; margin-right:.5rem; }
  </style>
</head>
<body>
  <h1>Store Geofence MVP</h1>
  <p>Backend-only demo using FastAPI, PostGIS, Celery, and Redis. Use the API docs at <a href="/docs">/docs</a>.</p>
  <p><span class="tag">Default radius: 100m</span><span class="tag">Demo token supported</span></p>
  <h2>Quick Start</h2>
  <ol>
    <li><strong>Login</strong>: <code>POST /auth/login</code> with <code>{"email":"you@company.com","role":"admin"}</code></li>
    <li><strong>Create company</strong>: <code>POST /companies</code></li>
    <li><strong>Create store</strong> (address only) → geocoding queued</li>
    <li><strong>Create task</strong> for the store</li>
    <li><strong>Run task</strong>: <code>POST /tasks/{id}/run</code> sending <code>{ "lat": 50.4501, "lng": 30.5234 }</code></li>
  </ol>
  <h2>Demo Token</h2>
  <p>Set <code>DEMO_TOKEN</code> in <code>.env</code>, then call endpoints with header <code>X-Demo-Token: &lt;value&gt;</code>.</p>
</body>
</html>"""

@router.get("/", response_class=HTMLResponse)
def index():
    return HTML
