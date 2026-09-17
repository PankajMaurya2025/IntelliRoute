"""
ML ETA prediction tests, split into two groups:

1. Pure unit tests against ml/predict.py directly — these need no database
   and no FastAPI, only scikit-learn/pandas/joblib, so they can be run
   standalone to sanity-check the model itself.
2. API integration tests against POST /api/ml/predict-eta and
   POST /api/ml/train — these need the `client`/`auth_headers` fixtures
   (Postgres-backed, see conftest.py).
"""
import pytest


class TestMLPredictUnit:
    """No DB required — exercises ml/predict.py directly."""

    def test_model_trains_and_predicts_without_error(self):
        from ml.predict import predict_eta
        eta = predict_eta(distance_km=5.0, traffic_level="low", num_stops=1,
                           priority=3, package_weight_kg=2.0, hour_of_day=10, day_of_week=1)
        assert isinstance(eta, float)
        assert eta > 0

    def test_higher_traffic_increases_eta_for_same_distance(self):
        from ml.predict import predict_eta
        low = predict_eta(distance_km=15.0, traffic_level="low", num_stops=1,
                           priority=3, package_weight_kg=2.0, hour_of_day=11, day_of_week=1)
        severe = predict_eta(distance_km=15.0, traffic_level="severe", num_stops=1,
                              priority=3, package_weight_kg=2.0, hour_of_day=11, day_of_week=1)
        assert severe > low

    def test_longer_distance_increases_eta(self):
        from ml.predict import predict_eta
        short = predict_eta(distance_km=2.0, traffic_level="low")
        long = predict_eta(distance_km=20.0, traffic_level="low")
        assert long > short

    def test_invalid_traffic_level_raises(self):
        from ml.predict import predict_eta
        with pytest.raises(ValueError):
            predict_eta(distance_km=5.0, traffic_level="not_a_real_level")

    def test_invalid_priority_raises(self):
        from ml.predict import predict_eta
        with pytest.raises(ValueError):
            predict_eta(distance_km=5.0, priority=9)

    def test_get_metadata_reports_reasonable_accuracy(self):
        from ml.predict import get_metadata
        meta = get_metadata()
        assert meta["mae_minutes"] < 10  # sanity bound, not a strict regression gate
        assert meta["r2_score"] > 0.8
        assert "distance_km" in meta["feature_importances"]


class TestMLPredictAPI:
    def test_predict_eta_endpoint(self, client, auth_headers):
        resp = client.post("/api/ml/predict-eta", json={
            "distance_km": 8.0, "traffic_level": "medium", "num_stops": 2,
            "priority": 2, "package_weight_kg": 3.0, "hour_of_day": 14, "day_of_week": 2,
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "predicted_eta_minutes" in body
        assert body["predicted_eta_minutes"] > 0

    def test_predict_eta_rejects_invalid_traffic_level(self, client, auth_headers):
        resp = client.post("/api/ml/predict-eta", json={
            "distance_km": 5.0, "traffic_level": "extreme",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_predict_eta_rejects_negative_distance(self, client, auth_headers):
        resp = client.post("/api/ml/predict-eta", json={
            "distance_km": -3.0, "traffic_level": "low",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_predict_eta_requires_auth(self, client):
        resp = client.post("/api/ml/predict-eta", json={"distance_km": 5.0})
        assert resp.status_code == 401

    def test_model_info_endpoint(self, client, auth_headers):
        resp = client.get("/api/ml/model-info", headers=auth_headers)
        assert resp.status_code == 200
        assert "mae_minutes" in resp.json()

    def test_retrain_endpoint(self, client, auth_headers):
        resp = client.post("/api/ml/train", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["trained"] is True
        assert body["r2_score"] > 0.5
