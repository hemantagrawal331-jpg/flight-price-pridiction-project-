"""Train the fare model.

    python -m ml.train                           # synthetic data
    python -m ml.train --csv Clean_Dataset.csv   # real data (Kaggle "Flight Price Prediction" layout)
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from . import synthetic

CAT = ["airline", "source_city", "destination_city", "departure_time", "class"]
NUM = ["stops", "duration", "days_left", "dow", "month"]
MODEL_PATH = Path(__file__).parent / "model.joblib"


def build_pipeline():
    pre = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)],
        remainder="passthrough",
    )
    reg = TransformedTargetRegressor(
        regressor=HistGradientBoostingRegressor(max_iter=400, learning_rate=0.08,
                                                max_depth=8, random_state=42),
        func=np.log1p, inverse_func=np.expm1,
    )
    return Pipeline([("pre", pre), ("reg", reg)])


def load_csv(path):
    df = pd.read_csv(path)
    df["stops"] = df["stops"].replace({"zero": 0, "one": 1, "two_or_more": 2})
    df["stops"] = pd.to_numeric(df["stops"], errors="coerce").fillna(1).astype(int)
    # the public dataset has no calendar columns; use neutral values (add real ones when you have them)
    if "dow" not in df:
        df["dow"] = 3
    if "month" not in df:
        df["month"] = 2
    return df[CAT + NUM + ["price"]].dropna()


def train_and_save(csv=None):
    df = load_csv(csv) if csv else synthetic.generate()
    X, y = df[CAT + NUM], df["price"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=7)
    pipe = build_pipeline().fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    metrics = {
        "mae": round(float(mean_absolute_error(y_te, pred)), 1),
        "mape_pct": round(float(mean_absolute_percentage_error(y_te, pred)) * 100, 2),
        "r2": round(float(r2_score(y_te, pred)), 4),
        "rows": int(len(df)),
        "source": "csv" if csv else "synthetic",
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump({"pipeline": pipe, "metrics": metrics}, MODEL_PATH)
    print("Saved", MODEL_PATH, metrics)
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="path to a real dataset")
    train_and_save(ap.parse_args().csv)
