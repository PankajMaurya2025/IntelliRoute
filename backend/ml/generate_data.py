"""
Generates synthetic (but realistically-structured) delivery training data
for the ETA regression model, since no historical delivery dataset is
available. The relationship between features and target is deliberately
non-trivial (multiplicative traffic effect, rush-hour surcharge, per-stop
overhead, diminishing weight penalty, some noise) so a linear model would
underperform and a RandomForest has something real to learn.

Run directly:  python -m ml.generate_data
"""
import os
import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_SAMPLES = 4000

TRAFFIC_MULTIPLIER = {"low": 1.0, "medium": 1.3, "high": 1.7, "severe": 2.3}
TRAFFIC_LEVELS = list(TRAFFIC_MULTIPLIER.keys())

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data.csv")

# Average urban delivery speed used to derive a base travel time from distance.
AVG_SPEED_KMPH = 28.0


def _traffic_encoded(level: str) -> int:
    """Ordinal encoding used as a model feature (0=low ... 3=severe)."""
    return TRAFFIC_LEVELS.index(level)


def generate_dataset(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    distance_km = rng.uniform(0.5, 25.0, n_samples)
    traffic_level = rng.choice(TRAFFIC_LEVELS, n_samples, p=[0.4, 0.3, 0.2, 0.1])
    num_stops = rng.integers(1, 6, n_samples)  # this delivery is stop N of a multi-stop batch
    priority = rng.integers(1, 5, n_samples)  # 1=Emergency ... 4=Low
    package_weight_kg = rng.uniform(0.2, 25.0, n_samples)
    hour_of_day = rng.integers(0, 24, n_samples)
    day_of_week = rng.integers(0, 7, n_samples)  # 0=Monday ... 6=Sunday

    eta = np.zeros(n_samples)
    for i in range(n_samples):
        base_time = (distance_km[i] / AVG_SPEED_KMPH) * 60.0  # minutes
        traffic_mult = TRAFFIC_MULTIPLIER[traffic_level[i]]

        stop_overhead = (num_stops[i] - 1) * 4.0  # 4 min per extra stop on the route
        weight_overhead = max(0.0, package_weight_kg[i] - 5.0) * 0.4  # heavier parcels slow handling
        priority_adjustment = {1: -2.0, 2: -1.0, 3: 0.0, 4: 2.0}[priority[i]]

        is_rush_hour = hour_of_day[i] in (8, 9, 17, 18, 19)
        rush_surcharge = base_time * 0.20 if is_rush_hour else 0.0

        is_weekend = day_of_week[i] in (5, 6)
        weekend_discount = base_time * -0.08 if is_weekend else 0.0

        noise = rng.normal(0, 2.5)

        eta[i] = max(
            3.0,
            base_time * traffic_mult + stop_overhead + weight_overhead
            + priority_adjustment + rush_surcharge + weekend_discount + noise,
        )

    df = pd.DataFrame({
        "distance_km": distance_km,
        "traffic_level": traffic_level,
        "traffic_encoded": [_traffic_encoded(t) for t in traffic_level],
        "num_stops": num_stops,
        "priority": priority,
        "package_weight_kg": package_weight_kg,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "eta_minutes": eta,
    })
    return df


def save_dataset(df: pd.DataFrame, path: str = OUTPUT_PATH):
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    dataset = generate_dataset()
    save_dataset(dataset)
    print(dataset.describe())
