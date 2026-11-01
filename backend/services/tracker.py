"""Price tracking: users watch a flight with a target price; a background job re-checks fares."""
from datetime import date, datetime

from db import clean, get_db, oid
from services.flights import flight_key, price_history, record_snapshot, enrich
from scraper.providers import get_provider


def add(client_id, flight, target_price):
    db = get_db()
    key = flight["flight_key"]
    existing = db.tracked.find_one({"client_id": client_id, "flight_key": key, "status": {"$ne": "removed"}})
    if existing:
        db.tracked.update_one({"_id": existing["_id"]},
                              {"$set": {"target_price": target_price, "status": "active"}})
        return clean(db.tracked.find_one({"_id": existing["_id"]}))
    now = datetime.utcnow()
    doc = {"client_id": client_id, "flight_key": key, "target_price": target_price, "status": "active",
           "initial_price": flight["price"], "last_price": flight["price"], "created_at": now, "updated_at": now,
           **{k: flight[k] for k in ("flight_number", "airline", "source", "destination", "date", "class",
                                     "departure_time")}}
    res = db.tracked.insert_one(doc)
    return clean(db.tracked.find_one({"_id": res.inserted_id}))


def list_for(client_id):
    rows = get_db().tracked.find({"client_id": client_id, "status": {"$ne": "removed"}}).sort("created_at", -1)
    out = []
    for r in rows:
        item = clean(r)
        item["history"] = price_history(r["flight_key"])[-30:]
        out.append(item)
    return out


def remove(client_id, tracked_id):
    res = get_db().tracked.update_one({"_id": oid(tracked_id), "client_id": client_id},
                                      {"$set": {"status": "removed"}})
    return res.matched_count > 0


def alerts_for(client_id):
    rows = get_db().alerts.find({"client_id": client_id}).sort("ts", -1).limit(50)
    return [clean(r) for r in rows]


def mark_alerts_read(client_id):
    get_db().alerts.update_many({"client_id": client_id, "read": False}, {"$set": {"read": True}})


def run_checks(client_id=None):
    """Re-fetch every active tracked flight, store the new fare, raise alerts. Returns a summary."""
    db = get_db()
    query = {"status": "active"}
    if client_id:
        query["client_id"] = client_id
    provider = get_provider()
    checked = triggered = 0
    cache = {}
    for t in db.tracked.find(query):
        if datetime.strptime(t["date"], "%Y-%m-%d").date() < date.today():
            db.tracked.update_one({"_id": t["_id"]}, {"$set": {"status": "expired"}})
            continue
        route = (t["source"], t["destination"], t["date"], t["class"])
        try:
            if route not in cache:
                cache[route] = provider.search(*route)
        except Exception as exc:
            print("[tracker] fetch failed:", exc)
            continue
        match = next((f for f in cache[route] if flight_key(f) == t["flight_key"]), None)
        if not match:
            continue
        f = enrich(match)
        record_snapshot(f)
        checked += 1
        update = {"last_price": f["price"], "last_seats": f.get("seats"), "updated_at": datetime.utcnow()}
        if f["price"] <= t["target_price"]:
            update["status"] = "triggered"
            triggered += 1
            db.alerts.insert_one({
                "client_id": t["client_id"], "tracked_id": str(t["_id"]), "read": False, "ts": datetime.utcnow(),
                "message": f"{t['airline']} {t['flight_number']} {t['source']} to {t['destination']} "
                           f"on {t['date']} is now Rs {f['price']:,} (your target: Rs {t['target_price']:,}).",
            })
        db.tracked.update_one({"_id": t["_id"]}, {"$set": update})
    return {"checked": checked, "triggered": triggered}
