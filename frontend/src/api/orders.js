import api from "./axios";

// GET /api/orders?status_filter=... -> OrderOut[]
export function listOrders(statusFilter) {
  const params = statusFilter ? { status_filter: statusFilter } : {};
  return api.get("/api/orders", { params }).then((r) => r.data);
}

// GET /api/orders/{id} -> OrderOut
export function getOrder(id) {
  return api.get(`/api/orders/${id}`).then((r) => r.data);
}

// POST /api/orders -> OrderOut
// payload: { customer_name, pickup_location, pickup_lat, pickup_lng,
//            delivery_location, delivery_lat, delivery_lng, priority, package_weight_kg }
export function createOrder(payload) {
  return api.post("/api/orders", payload).then((r) => r.data);
}

// PUT /api/orders/{id} -> OrderOut
// payload: { status?, assigned_driver_id?, priority? }
export function updateOrder(id, payload) {
  return api.put(`/api/orders/${id}`, payload).then((r) => r.data);
}

// DELETE /api/orders/{id} -> 204 No Content
export function deleteOrder(id) {
  return api.delete(`/api/orders/${id}`);
}

// GET /api/orders/priority-queue -> [{ order_id, priority }]
export function getPriorityQueue() {
  return api.get("/api/orders/priority-queue").then((r) => r.data);
}

// POST /api/orders/dispatch-next -> { assigned_order_id, driver_id }
export function dispatchNext() {
  return api.post("/api/orders/dispatch-next").then((r) => r.data);
}
