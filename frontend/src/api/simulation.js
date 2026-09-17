import api, { wsBaseUrl } from "./axios";

// POST /api/simulation/start -> SimulationControlResponse { status, active_legs, message }
export function startSimulation() {
  return api.post("/api/simulation/start").then((r) => r.data);
}

// POST /api/simulation/pause -> SimulationControlResponse
export function pauseSimulation() {
  return api.post("/api/simulation/pause").then((r) => r.data);
}

// POST /api/simulation/resume -> SimulationControlResponse
export function resumeSimulation() {
  return api.post("/api/simulation/resume").then((r) => r.data);
}

// POST /api/simulation/stop -> SimulationControlResponse
export function stopSimulation() {
  return api.post("/api/simulation/stop").then((r) => r.data);
}

// POST /api/simulation/reset -> SimulationControlResponse
export function resetSimulation() {
  return api.post("/api/simulation/reset").then((r) => r.data);
}

// GET /api/simulation/state -> engine snapshot { status, speed_multiplier, active_legs, completed_legs, timestamp }
export function getSimulationState() {
  return api.get("/api/simulation/state").then((r) => r.data);
}

// The WebSocket endpoint (/ws/simulation) does not require auth (see backend
// routers/simulation.py docstring) — it's a read-only broadcast of engine state.
export function simulationSocketUrl() {
  return `${wsBaseUrl()}/ws/simulation`;
}
