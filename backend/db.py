"""MongoDB access. Set MONGO_URI=mock to use an in-memory mongomock database."""
from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient

import config

_client = None


def get_db():
    global _client
    if _client is None:
        if config.MONGO_URI == "mock":
            import mongomock

            _client = mongomock.MongoClient()
        else:
            _client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[config.DB_NAME]


def init_indexes():
    db = get_db()
    db.price_history.create_index([("flight_key", ASCENDING), ("ts", DESCENDING)])
    db.tracked.create_index([("client_id", ASCENDING), ("status", ASCENDING)])
    db.alerts.create_index([("client_id", ASCENDING), ("ts", DESCENDING)])
    db.flights.create_index("flight_key", unique=True)


def clean(doc):
    """Make a Mongo document JSON-serialisable."""
    if doc is None:
        return None
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = str(v)
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat() + "Z"
        else:
            out[k] = v
    return out


def oid(value):
    try:
        return ObjectId(value)
    except Exception:
        raise ValueError("Invalid id")
