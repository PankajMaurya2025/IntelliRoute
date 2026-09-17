from fastapi import APIRouter, Depends, HTTPException

from models import User
from schemas.schemas import ETARequest, ETAResponse, TrainModelResponse
from utils.auth import get_current_user
from ml.predict import predict_eta, get_metadata, reload_model
from ml.train_model import train
from ml.generate_data import TRAFFIC_LEVELS

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])


@router.post("/predict-eta", response_model=ETAResponse)
def predict_eta_endpoint(payload: ETARequest, current_user: User = Depends(get_current_user)):
    if payload.traffic_level not in TRAFFIC_LEVELS:
        raise HTTPException(status_code=422, detail=f"traffic_level must be one of {TRAFFIC_LEVELS}")
    if not (1 <= payload.priority <= 4):
        raise HTTPException(status_code=422, detail="priority must be between 1 and 4")
    if payload.distance_km <= 0:
        raise HTTPException(status_code=422, detail="distance_km must be positive")

    try:
        eta = predict_eta(
            distance_km=payload.distance_km,
            traffic_level=payload.traffic_level,
            num_stops=payload.num_stops,
            priority=payload.priority,
            package_weight_kg=payload.package_weight_kg,
            hour_of_day=payload.hour_of_day,
            day_of_week=payload.day_of_week,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=503, detail="ML model is currently unavailable. Please try again shortly.")

    return ETAResponse(predicted_eta_minutes=eta)


@router.get("/model-info")
def model_info(current_user: User = Depends(get_current_user)):
    try:
        return get_metadata()
    except Exception:
        raise HTTPException(status_code=503, detail="ML model is currently unavailable.")


@router.post("/train", response_model=TrainModelResponse)
def retrain_model(current_user: User = Depends(get_current_user)):
    """Regenerates training data-derived model and hot-reloads it for future predictions."""
    metadata = train()
    reload_model()
    return TrainModelResponse(
        trained=True,
        mae_minutes=metadata["mae_minutes"],
        r2_score=metadata["r2_score"],
        num_train_samples=metadata["num_train_samples"],
        num_test_samples=metadata["num_test_samples"],
        feature_importances=metadata["feature_importances"],
    )
