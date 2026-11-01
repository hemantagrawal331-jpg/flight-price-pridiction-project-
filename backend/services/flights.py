"""Search flights, enrich with ML predictions, and keep price history in MongoDB."""
from datetime import date, datetime, timedelta

import config
from db import get_db
from ml import predictor
from ml.constants import time_bucket
from scraper.providers import get_provider


def flight_key(f):
    return f"{f['flight_number']}|{f['source']}|{f['destination']}|{f['date']}|{f['class']}"


def features_for(f):
    d = datetime.strptime(f["date"], "%Y-%m-%d").date()
    hour = int(f["departure_time"][:2])
    return {
        "airline": f["airline"], "source_city": f["source"], "destination_city": f["destination"],
        "departure_time": time_bucket(hour), "class": f["class"], "stops": int(f["stops"]),
        "duration": float(f["duration"]), "days_left": min(max((d - date.today()).days, 1), 60),
        "dow": d.weekday(), "month": d.month,
    }


def enrich(f):
    fair = predictor.predict_price(features_for(f))
    label, gap = predictor.deal_label(f["price"], fair)
    return {**f, "flight_key": flight_key(f), "predicted_price": int(round(fair)),
            "deal": label, "gap_pct": round(gap * 100, 1)}


def record_snapshot(f):
    """Store the observed fare unless we already stored one very recently."""
    db = get_db()
    now = datetime.utcnow()
    last = db.price_history.find_one({"flight_key": f["flight_key"]}, sort=[("ts", -1)])
    if last and (now - last["ts"]).total_seconds() < config.SNAPSHOT_MIN_GAP_SEC:
        return
    db.price_history.insert_one({
        "flight_key": f["flight_key"], "flight_number": f["flight_number"], "price": f["price"],
        "seats": f.get("seats"), "predicted_price": f["predicted_price"], "ts": now,
    })
    db.flights.update_one(
        {"flight_key": f["flight_key"]},
        {"$set": {**{k: f[k] for k in ("flight_number", "airline", "source", "destination", "date", "class",
                                       "departure_time", "arrival_time", "duration", "stops")},
                  "last_price": f["price"], "last_seats": f.get("seats"), "updated_at": now},
         "$setOnInsert": {"first_seen": now}},
        upsert=True)


def search_flights(source, destination, date_str, cls="Economy", sort="price"):
    raw = get_provider().search(source, destination, date_str, cls)
    flights = [enrich(f) for f in raw]
    for f in flights:
        record_snapshot(f)
    keys = {"price": lambda x: x["price"], "duration": lambda x: x["duration"],
            "departure": lambda x: x["departure_time"], "deal": lambda x: x["gap_pct"]}
    return sorted(flights, key=keys.get(sort, keys["price"]))


def price_history(flight_key_value):
    rows = get_db().price_history.find({"flight_key": flight_key_value}).sort("ts", 1).limit(500)
    return [{"ts": r["ts"].isoformat() + "Z", "price": r["price"], "seats": r.get("seats"),
             "predicted_price": r.get("predicted_price")} for r in rows]
