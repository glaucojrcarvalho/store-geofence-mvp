"""Contract checks for the standalone Vercel static deployment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "public-demo"


def test_public_demo_contains_only_explicit_static_assets():
    names = {x.name for x in ROOT.iterdir() if x.is_file()}
    assert names == {"index.html", "app.js", "styles.css", "vercel.json", "README.md"}


def test_public_demo_is_locally_computed_with_no_external_network():
    html = (ROOT / "index.html").read_text()
    js = (ROOT / "app.js").read_text()
    assert 'src="./app.js"' in html
    assert 'href="./styles.css"' in html
    assert "haversine(" in js and "Math.asin" in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    assert "https://" not in js and "http://" not in js
    assert "geolocation" not in js
    assert "/auth/login" not in html and "/auth/login" not in js
    assert "/companies" not in html and "/tasks/" not in html


def test_vercel_headers_block_network_upload_and_inline_script():
    config = json.loads((ROOT / "vercel.json").read_text())
    headers = {x["key"]: x["value"] for x in config["headers"][0]["headers"]}
    assert "connect-src 'none'" in headers["Content-Security-Policy"]
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "geolocation=()" in headers["Permissions-Policy"]
