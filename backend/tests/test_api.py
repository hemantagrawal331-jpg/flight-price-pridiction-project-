import os
from datetime import date, timedelta

os.environ["MONGO_URI"] = "mock"
os.environ["SIM_BUCKET_MIN"] = "5"

import pytest

from app import create_app


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def future(days=20):
    return (date.today() + timedelta(days=days)).isoformat()


def test_search_returns_enriched_flights(client):
    r = client.get(f"/api/flights/search?source=Delhi&destination=Mumbai&date={future()}")
    assert r.status_code == 200
    flights = r.get_json()["flights"]
    assert len(flights) >= 5
    f = flights[0]
    assert {"flight_number", "price", "seats", "predicted_price", "deal"} <= set(f)


def test_validation(client):
    r = client.get(f"/api/flights/search?source=Delhi&destination=Delhi&date={future()}")
    assert r.status_code == 400


def test_predict_and_advice(client):
    r = client.post("/api/predict", json={"airline": "IndiGo", "source": "Delhi", "destination": "Chennai",
                                          "date": future(25), "departure_time": "08:30", "stops": 0,
                                          "class": "Economy", "price": 6000})
    body = r.get_json()
    assert r.status_code == 200 and body["action"] in {"BUY_NOW", "WAIT", "WATCH"}
    assert len(body["forecast"]) >= 20


def test_track_flow(client):
    h = {"X-Client-Id": "tester"}
    f = client.get(f"/api/flights/search?source=Mumbai&destination=Bangalore&date={future(15)}").get_json()["flights"][0]
    r = client.post("/api/track", json={"flight": f, "target_price": int(f["price"] * 1.3)}, headers=h)
    assert r.status_code == 201
    summary = client.post("/api/track/check", headers=h).get_json()
    assert summary["triggered"] == 1
    assert client.get("/api/alerts", headers=h).get_json()["unread"] == 1
    tid = client.get("/api/track", headers=h).get_json()["tracked"][0]["id"]
    assert client.delete(f"/api/track/{tid}", headers=h).status_code == 200
