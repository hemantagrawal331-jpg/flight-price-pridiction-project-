"""Vercel routes every non-file request to this Flask app."""
import sys
from pathlib import Path

from flask import send_from_directory

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app import create_app

app = create_app()
PUBLIC = ROOT / "public"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    """Serve the Vite build when the CDN does not."""
    if path.startswith("api"):
        return {"error": "Not found"}, 404
    target = PUBLIC / path
    if path and target.is_file():
        return send_from_directory(PUBLIC, path)
    return send_from_directory(PUBLIC, "index.html")
