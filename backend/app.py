"""Flask API for the flight price predictor & tracker."""
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from db import clean, get_db, init_indexes
from ml import predictor
from ml.constants import AIRLINES, AIRPORT_CODES, CITIES, CLASSES, flight_hours, time_bucket
from services import flights as flight_service
from services import tracker


def _validate_route(source, destination, date_str, cls):
    if source not in CITIES or destination not in CITIES:
        raise ValueError(f"Cities must be one of: {', '.join(CITIES)}")
    if source == destination:
        raise ValueError("Source and destination must be different")
    if cls not in CLASSES:
        raise ValueError("Class must be Economy or Business")
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Date must be YYYY-MM-DD")
    if d < date.today():
        raise ValueError("Departure date is in the past")
    return d


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})
    init_indexes()
    predictor.load()

    def client_id():
        return request.headers.get("X-Client-Id", "anonymous")[:64]

    @app.errorhandler(ValueError)
    def bad_request(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(Exception)
    def server_error(err):
        app.logger.exception(err)
        return jsonify(error="Something went wrong on the server"), 500

    @app.get("/api/health")
    def health():
        get_db().command("ping") if config.MONGO_URI != "mock" else None
        return jsonify(status="ok", provider=config.PROVIDER, model=predictor.metrics())

    @app.get("/api/meta")
    def meta():
        return jsonify(cities=CITIES, airport_codes=AIRPORT_CODES, classes=CLASSES,
                       airlines=list(AIRLINES), provider=config.PROVIDER,
                       departure_hours=list(range(5, 23)))

    @app.get("/api/flights/search")
    def search():
        a = request.args
        source, destination = a.get("source"), a.get("destination")
        cls, date_str = a.get("class", "Economy"), a.get("date")
        _validate_route(source, destination, date_str, cls)
        results = flight_service.search_flights(source, destination, date_str, cls, a.get("sort", "price"))
        return jsonify(count=len(results), flights=results)

    @app.post("/api/predict")
    def predict():
        """What-if prediction. Pass `price` to also get a deal rating and buy/wait advice."""
        b = request.get_json(force=True, silent=True) or {}
        source, destination = b.get("source"), b.get("destination")
        cls = b.get("class", "Economy")
        _validate_route(source, destination, b.get("date"), cls)
        airline = b.get("airline")
        if airline not in AIRLINES:
            raise ValueError("Unknown airline")
        stops = int(b.get("stops", 0))
        if stops not in (0, 1, 2):
            raise ValueError("Stops must be 0, 1 or 2")
        hhmm = b.get("departure_time", "09:00")
        flight = {"airline": airline, "source": source, "destination": destination, "date": b["date"],
                  "class": cls, "stops": stops, "departure_time": hhmm,
                  "duration": float(b.get("duration") or flight_hours(source, destination, stops))}
        feats = flight_service.features_for(flight)
        fair = predictor.predict_price(feats)
        listed = float(b["price"]) if b.get("price") else fair
        advice = predictor.advise(feats, listed)
        return jsonify(predicted_price=int(round(fair)), departure_bucket=feats["departure_time"],
                       days_left=feats["days_left"], **advice)

    @app.get("/api/history")
    def history():
        key = request.args.get("flight_key")
        if not key:
            raise ValueError("flight_key is required")
        return jsonify(history=flight_service.price_history(key))

    @app.get("/api/track")
    def track_list():
        return jsonify(tracked=tracker.list_for(client_id()))

    @app.post("/api/track")
    def track_add():
        b = request.get_json(force=True, silent=True) or {}
        flight, target = b.get("flight"), b.get("target_price")
        if not flight or not target or float(target) <= 0:
            raise ValueError("flight and a positive target_price are required")
        item = tracker.add(client_id(), flight, int(float(target)))
        return jsonify(tracked=item), 201

    @app.delete("/api/track/<tracked_id>")
    def track_remove(tracked_id):
        if not tracker.remove(client_id(), tracked_id):
            return jsonify(error="Tracked flight not found"), 404
        return jsonify(ok=True)

    @app.post("/api/track/check")
    def track_check():
        return jsonify(tracker.run_checks(client_id()))

    @app.get("/api/alerts")
    def alerts():
        items = tracker.alerts_for(client_id())
        return jsonify(alerts=items, unread=sum(1 for i in items if not i["read"]))

    @app.post("/api/alerts/read")
    def alerts_read():
        tracker.mark_alerts_read(client_id())
        return jsonify(ok=True)

    return app


def start_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(tracker.run_checks, "interval", minutes=config.CHECK_INTERVAL_MIN,
                  max_instances=1, id="price-check")
    sched.start()
    return sched


if __name__ == "__main__":
    application = create_app()
    start_scheduler()
    # use_reloader=False so the scheduler is not started twice
    application.run(host="0.0.0.0", port=config.PORT, debug=True, use_reloader=False)
