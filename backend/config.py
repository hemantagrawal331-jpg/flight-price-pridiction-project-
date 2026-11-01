import json
import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "flight_tracker")
PORT = int(os.getenv("PORT", "5000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]

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
