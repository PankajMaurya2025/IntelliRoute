import api from "./axios";

// POST /api/ml/predict-eta -> { predicted_eta_minutes }
// payload: { distance_km, traffic_level, num_stops, priority, package_weight_kg, hour_of_day, day_of_week }
export function predictEta(payload) {
  return api.post("/api/ml/predict-eta", payload).then((r) => r.data);
}

// GET /api/ml/model-info -> model metadata (mae_minutes, r2_score, feature_importances, ...)
export function getModelInfo() {
  return api.get("/api/ml/model-info").then((r) => r.data);
}

// POST /api/ml/train -> TrainModelResponse
export function retrainModel() {
  return api.post("/api/ml/train").then((r) => r.data);
}
