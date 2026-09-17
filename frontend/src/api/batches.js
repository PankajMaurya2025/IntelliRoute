import api from "./axios";

// GET /api/batches -> BatchOut[]
export function listBatches() {
  return api.get("/api/batches").then((r) => r.data);
}

// GET /api/batches/{id} -> BatchDetailOut (includes order_ids)
export function getBatch(id) {
  return api.get(`/api/batches/${id}`).then((r) => r.data);
}

// POST /api/batches/create -> BatchOut[]
// payload: { orders_per_batch }
export function createBatches(ordersPerBatch) {
  return api.post("/api/batches/create", { orders_per_batch: ordersPerBatch }).then((r) => r.data);
}
