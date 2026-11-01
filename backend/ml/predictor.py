"""Inference helpers: fair price, forecast curve, deal rating and buy/wait advice."""
import os

import joblib
import pandas as pd

from .train import CAT, MODEL_PATH, NUM, train_and_save

_bundle = None


def load():
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            if os.getenv("VERCEL"):
                raise RuntimeError(f"Trained model not found at {MODEL_PATH}")
            print("No trained model found - training one now (about a minute)...")
            train_and_save()
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def metrics():
    return load()["metrics"]


def _predict(rows):
    X = pd.DataFrame(rows)[CAT + NUM]
    return load()["pipeline"].predict(X)


def predict_price(features):
    return float(_predict([features])[0])


def forecast(features, horizon=60):
    """Model price for every remaining day before departure (today -> departure day)."""
    d0 = min(max(int(features["days_left"]), 1), horizon)
    days = list(range(d0, 0, -1))
    prices = _predict([{**features, "days_left": d} for d in days])
    return [{"days_left": d, "price": int(round(p))} for d, p in zip(days, prices)]


def deal_label(listed, fair):
    gap = (listed - fair) / fair
    if gap < -0.07:
        return "great_deal", gap
    if gap < -0.02:
        return "good_price", gap
    if gap <= 0.07:
        return "fair_price", gap
    return "overpriced", gap


def advise(features, listed):
    """Return BUY_NOW / WAIT / WATCH with a plain-language reason."""
    fc = forecast(features)
    d = fc[0]["days_left"]
    fair = fc[0]["price"]
    ahead = fc[min(7, len(fc) - 1)]["price"]  # price one week closer to departure
    rise = (ahead - fair) / fair
    label, gap = deal_label(listed, fair)

    if d <= 3:
        action, why = "BUY_NOW", "Departure is within 3 days; fares rarely fall this late."
    elif rise >= 0.05 and gap <= 0.07:
        action, why = "BUY_NOW", f"Fares on this route typically rise about {rise*100:.0f}% over the next week."
    elif gap > 0.07 and d > 10:
        action, why = "WAIT", f"This fare is {gap*100:.0f}% above the expected price. Check again in a few days."
    elif label in ("great_deal", "good_price"):
        action, why = "BUY_NOW", f"This fare is {abs(gap)*100:.0f}% below the expected price."
    else:
        action, why = "WATCH", "The fare is close to the expected price. Track it and book if it drops."
    return {"action": action, "reason": why, "fair_price": fair, "deal": label,
            "gap_pct": round(gap * 100, 1), "forecast": fc}
