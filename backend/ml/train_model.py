"""
Trains a RandomForestRegressor to predict delivery ETA (minutes) from
order/route features, and saves the trained model + feature order + test
metrics to model.pkl via joblib.

Run directly:  python -m ml.train_model
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from ml.generate_data import generate_dataset, save_dataset, OUTPUT_PATH, TRAFFIC_LEVELS

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

FEATURE_COLUMNS = [
    "distance_km", "traffic_encoded", "num_stops",
    "priority", "package_weight_kg", "hour_of_day", "day_of_week",
]
TARGET_COLUMN = "eta_minutes"


def load_or_generate_dataset() -> pd.DataFrame:
    if os.path.exists(OUTPUT_PATH):
        return pd.read_csv(OUTPUT_PATH)
    df = generate_dataset()
    save_dataset(df)
    return df


def train(save: bool = True) -> dict:
    df = load_or_generate_dataset()

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))

    feature_importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.round(4).tolist()))

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "traffic_levels": TRAFFIC_LEVELS,
        "mae_minutes": round(mae, 3),
        "r2_score": round(r2, 4),
        "num_train_samples": int(len(X_train)),
        "num_test_samples": int(len(X_test)),
        "feature_importances": feature_importances,
    }

    if save:
        joblib.dump({"model": model, "metadata": metadata}, MODEL_PATH)
        with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Model saved to {MODEL_PATH}")

    print(f"MAE: {mae:.2f} minutes | R2: {r2:.4f}")
    print("Feature importances:", feature_importances)

    return metadata


if __name__ == "__main__":
    train()
