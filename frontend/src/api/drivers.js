import api from "./axios";

// GET /api/drivers -> DriverOut[]
export function listDrivers() {
  return api.get("/api/drivers").then((r) => r.data);
}

// POST /api/drivers -> DriverOut
// payload: { name, phone, vehicle_id?, current_lat, current_lng }
export function createDriver(payload) {
  return api.post("/api/drivers", payload).then((r) => r.data);
}

// PUT /api/drivers/{id} -> DriverOut
// payload: { status?, current_lat?, current_lng?, vehicle_id? }
export function updateDriver(id, payload) {
  return api.put(`/api/drivers/${id}`, payload).then((r) => r.data);
}
