import api from "./axios";

// GET /api/routes/locations -> [{ name, lat, lng }]
export function listLocations() {
  return api.get("/api/routes/locations").then((r) => r.data);
}

// GET /api/routes/algorithms -> { algorithms: string[] }
export function listAlgorithms() {
  return api.get("/api/routes/algorithms").then((r) => r.data.algorithms);
}

// POST /api/routes/optimize -> RouteResponse
// payload: { start, destination, algorithm }
export function optimizeRoute({ start, destination, algorithm }) {
  return api.post("/api/routes/optimize", { start, destination, algorithm }).then((r) => r.data);
}

// POST /api/routes/multi-stop?warehouse_lat=&warehouse_lng=  body: stops[]
// -> { sequence, total_distance_km, num_stops }
export function multiStopRoute(stops, warehouseLat, warehouseLng) {
  return api
    .post("/api/routes/multi-stop", stops, {
      params: { warehouse_lat: warehouseLat, warehouse_lng: warehouseLng },
    })
    .then((r) => r.data);
}
