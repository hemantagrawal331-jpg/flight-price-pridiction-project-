"""Vercel routes every non-static request to this Flask app."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app import create_app

app = create_app()
