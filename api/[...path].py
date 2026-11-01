"""Send every /api/* request to the Flask app."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import create_app

_flask = create_app()


class _ApiPrefix:
    """Keep Flask routes working if Vercel strips the /api prefix."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO") or ""
        script = environ.get("SCRIPT_NAME") or ""
        if path.startswith("/api/") or path == "/api":
            full = path
        elif script == "/api" or script.rstrip("/").endswith("/api"):
            full = script.rstrip("/") + (path if path.startswith("/") else f"/{path}")
        else:
            rest = path if path.startswith("/") else f"/{path}"
            full = "/api" if rest == "/" else "/api" + rest
        environ["SCRIPT_NAME"] = ""
        environ["PATH_INFO"] = full
        return self.app(environ, start_response)


app = _ApiPrefix(_flask)
