import api from "./axios";

// GET /api/analytics/summary -> AnalyticsSummary
export function getAnalyticsSummary() {
  return api.get("/api/analytics/summary").then((r) => r.data);
}
