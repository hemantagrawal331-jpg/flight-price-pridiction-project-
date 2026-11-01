"""Synthetic fare model + dataset generator.

The pricing rules mimic well-known airline revenue-management behaviour:
fares climb steeply in the last two weeks, weekends and peak months cost more,
full-service carriers charge more, connecting flights are cheaper.
Replace the generated data with real scraped history (see train.py --csv) as it accumulates.
"""
import math

import numpy as np
import pandas as pd

from .constants import AIRLINES, CITIES, distance, flight_hours, time_bucket

TIME_MULT = {"Early_Morning": 0.97, "Morning": 1.08, "Afternoon": 1.0,
             "Evening": 1.10, "Night": 0.93, "Late_Night": 0.90}
PEAK_MONTHS = {5, 6, 10, 11, 12}
STOP_MULT = {0: 1.0, 1: 0.88, 2: 0.80}


def base_price(airline, source, destination, cls, stops, departure_time, days_left, dow, month):
    p = 2200 + distance(source, destination) * 2.6
    if cls == "Business":
        p *= 2.8
    p *= AIRLINES[airline]["mult"]
    p *= 0.85 + 1.2 * math.exp(-days_left / 9)
    p *= TIME_MULT[departure_time]
    p *= STOP_MULT[stops]
    if dow in (4, 6):
        p *= 1.08
    if month in PEAK_MONTHS:
        p *= 1.12
    return p


def generate(n=60000, seed=42):
    rng = np.random.default_rng(seed)
    airlines = list(AIRLINES)
    rows = []
    for _ in range(n):
        src, dst = rng.choice(CITIES, 2, replace=False)
        airline = airlines[rng.integers(len(airlines))]
        cls = "Business" if AIRLINES[airline]["full_service"] and rng.random() < 0.15 else "Economy"
        stops = int(rng.choice([0, 1, 2], p=[0.35, 0.55, 0.10]))
        bucket = time_bucket(int(rng.integers(0, 24)))
        days_left = int(rng.integers(1, 61))
        dow, month = int(rng.integers(0, 7)), int(rng.integers(1, 13))
        duration = flight_hours(src, dst, stops) + rng.normal(0, 0.25)
        price = base_price(airline, src, dst, cls, stops, bucket, days_left, dow, month)
        price *= rng.lognormal(0, 0.07)
        rows.append({"airline": airline, "source_city": str(src), "destination_city": str(dst),
                     "departure_time": bucket, "class": cls, "stops": stops,
                     "duration": round(max(duration, 0.8), 2), "days_left": days_left,
                     "dow": dow, "month": month, "price": int(round(price, -1))})
    return pd.DataFrame(rows)
