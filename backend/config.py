import json
import os

from dotenv import load_dotenv

load_dotenv()


def _env(name, default):
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value


# Vercel has no local MongoDB. Search and predictions still work with the
# in-memory database; set MONGO_URI to Atlas if tracked fares should persist.
_on_vercel = os.getenv("VERCEL") == "1"
MONGO_URI = _env("MONGO_URI", "mock" if _on_vercel else "mongodb://localhost:27017")
DB_NAME = _env("DB_NAME", "flight_tracker")
PORT = int(_env("PORT", "5000"))
CORS_ORIGINS = [o.strip() for o in _env("CORS_ORIGINS", "*" if _on_vercel else "http://localhost:5173").split(",") if o.strip()]

PROVIDER = os.getenv("PROVIDER", "simulated").lower()
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "15"))
SIM_BUCKET_MIN = int(os.getenv("SIM_BUCKET_MIN", "5"))
SNAPSHOT_MIN_GAP_SEC = int(os.getenv("SNAPSHOT_MIN_GAP_SEC", "120"))

SCRAPE_URL_TEMPLATE = os.getenv("SCRAPE_URL_TEMPLATE", "")
SCRAPE_DELAY_SEC = float(os.getenv("SCRAPE_DELAY_SEC", "2"))
try:
    SCRAPE_SELECTORS = json.loads(os.getenv("SCRAPE_SELECTORS", "{}"))
except json.JSONDecodeError:
    SCRAPE_SELECTORS = {}
