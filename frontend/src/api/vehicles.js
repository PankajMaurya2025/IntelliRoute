import api from "./axios";

// GET /api/vehicles -> VehicleOut[]
export function listVehicles() {
  return api.get("/api/vehicles").then((r) => r.data);
}

// POST /api/vehicles -> VehicleOut
// payload: { vehicle_number, vehicle_type, capacity_kg }
export function createVehicle(payload) {
  return api.post("/api/vehicles", payload).then((r) => r.data);
}

// PUT /api/vehicles/{id} -> VehicleOut
// payload: { status?, fuel_level?, current_lat?, current_lng? }
export function updateVehicle(id, payload) {
  return api.put(`/api/vehicles/${id}`, payload).then((r) => r.data);
}
