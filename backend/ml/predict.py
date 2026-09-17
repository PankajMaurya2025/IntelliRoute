"""
Loads the trained ETA model (training it first if model.pkl doesn't exist
yet) and exposes predict_eta() for use by the API layer.
"""
import os
import joblib
import pandas as pd
from typing import Optional

from ml.train_model import MODEL_PATH, FEATURE_COLUMNS, train
from ml.generate_data import TRAFFIC_LEVELS

_cached = None  # {"model": ..., "metadata": ...}


def _load():
    global _cached
    if _cached is not None:
        return _cached
    if not os.path.exists(MODEL_PATH):
        train()  # trains and saves model.pkl on first use
    _cached = joblib.load(MODEL_PATH)
    return _cached


def get_metadata() -> dict:
    return _load()["metadata"]


def predict_eta(
    distance_km: float,
    traffic_level: str = "low",
    num_stops: int = 1,
    priority: int = 3,
    package_weight_kg: float = 1.0,
    hour_of_day: int = 12,
    day_of_week: int = 1,
) -> float:
    if traffic_level not in TRAFFIC_LEVELS:
        raise ValueError(f"traffic_level must be one of {TRAFFIC_LEVELS}")
    if not (1 <= priority <= 4):
        raise ValueError("priority must be between 1 and 4")

    bundle = _load()
    model = bundle["model"]

    traffic_encoded = TRAFFIC_LEVELS.index(traffic_level)
    row = pd.DataFrame([{
        "distance_km": distance_km,
        "traffic_encoded": traffic_encoded,
        "num_stops": num_stops,
        "priority": priority,
        "package_weight_kg": package_weight_kg,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
    }])[FEATURE_COLUMNS]  # enforce exact training column order

    prediction = model.predict(row)[0]
    return round(float(prediction), 2)


def reload_model():
    """Force the next predict_eta() call to re-read model.pkl from disk (e.g. after retraining)."""
    global _cached
    _cached = None

