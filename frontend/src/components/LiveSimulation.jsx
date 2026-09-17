import { useCallback, useEffect, useRef, useState } from "react";
import { Play, Pause, RotateCcw, Square, PlayCircle, Wifi, WifiOff, Truck } from "lucide-react";
import {
  simulationSocketUrl,
  startSimulation,
  pauseSimulation,
  resumeSimulation,
  stopSimulation,
  resetSimulation,
} from "../api/simulation";
import MapView from "./MapView";
import EmptyState from "./EmptyState";

const RECONNECT_BASE_MS = 1500;
const RECONNECT_MAX_MS = 15000;

export default function LiveSimulation() {
  const [simState, setSimState] = useState(null);
  const [wsStatus, setWsStatus] = useState("connecting"); // connecting | open | closed | error
  const [controlLoading, setControlLoading] = useState(false);
  const [controlError, setControlError] = useState("");

  const wsRef = useRef(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    setWsStatus("connecting");
    const ws = new WebSocket(simulationSocketUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setWsStatus("open");
      reconnectAttempt.current = 0;
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        setSimState(data);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setWsStatus("error");
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setWsStatus("closed");
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** reconnectAttempt.current, RECONNECT_MAX_MS);
      reconnectAttempt.current += 1;
      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, delay);
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  async function runControl(fn) {
    setControlError("");
    setControlLoading(true);
    try {
      const data = await fn();
      // Apply immediately for snappy UI feedback; the WebSocket will keep it live from here.
      setSimState((prev) => ({ ...(prev || {}), status: data.status }));
    } catch (err) {
      setControlError(err.message || "Could not update the simulation.");
    } finally {
      setControlLoading(false);
    }
  }

  const status = simState?.status || "stopped";
  const activeLegs = simState?.active_legs || [];
  const completedLegs = simState?.completed_legs || [];

  const markers = activeLegs.map((leg) => ({
    id: leg.leg_id,
    lat: leg.lat,
    lng: leg.lng,
    type: "driver",
    label: `${leg.driver_name} — Order #${leg.order_id}`,
    popup: `${leg.progress_pct}% complete · ${leg.remaining_km} km remaining`,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div
        className="card card-pad"
        style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            className="sim-status-pill"
            style={{
              background: status === "running" ? "var(--success-soft)" : status === "paused" ? "var(--warning-soft)" : "#eceef2",
              color: status === "running" ? "#166534" : status === "paused" ? "#92670a" : "var(--ink-muted)",
            }}
          >
            <span className="badge-dot" /> {status[0].toUpperCase() + status.slice(1)}
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--ink-muted)" }}>
            {wsStatus === "open" ? <Wifi size={14} color="var(--success)" /> : <WifiOff size={14} color="var(--danger)" />}
            {wsStatus === "open" ? "Live" : wsStatus === "connecting" ? "Connecting…" : "Reconnecting…"}
          </span>
          <span style={{ fontSize: 12, color: "var(--ink-muted)" }}>
            {activeLegs.length} active delivery{activeLegs.length === 1 ? "" : "ies"}
          </span>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-primary btn-sm" disabled={controlLoading} onClick={() => runControl(startSimulation)}>
            <Play size={14} /> Start
          </button>
          <button className="btn btn-outline btn-sm" disabled={controlLoading} onClick={() => runControl(pauseSimulation)}>
            <Pause size={14} /> Pause
          </button>
          <button className="btn btn-outline btn-sm" disabled={controlLoading} onClick={() => runControl(resumeSimulation)}>
            <PlayCircle size={14} /> Resume
          </button>
          <button className="btn btn-outline btn-sm" disabled={controlLoading} onClick={() => runControl(stopSimulation)}>
            <Square size={14} /> Stop
          </button>
          <button className="btn btn-ghost btn-sm" disabled={controlLoading} onClick={() => runControl(resetSimulation)}>
            <RotateCcw size={14} /> Reset
          </button>
        </div>
      </div>

      {controlError && <div className="form-error">{controlError}</div>}

      <MapView markers={markers} height={400} />

      <div className="card">
        <div className="card-header">
          <h3>Active deliveries</h3>
        </div>
        <div className="card-pad">
          {activeLegs.length === 0 ? (
            <EmptyState
              icon={Truck}
              title="No deliveries in motion"
              message="Assign an order to a driver, then press Start to begin the live simulation."
            />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
              {activeLegs.map((leg) => (
                <div className="sim-leg-card" key={leg.leg_id}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, fontWeight: 600 }}>
                    <span>{leg.driver_name}</span>
                    <span style={{ color: "var(--ink-muted)", fontWeight: 500 }}>Order #{leg.order_id}</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${leg.progress_pct}%` }} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--ink-muted)" }}>
                    <span>{leg.progress_pct}% complete</span>
                    <span>{leg.remaining_km} km left</span>
                    <span>{leg.speed_kmph} km/h</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {completedLegs.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Completed this session</h3>
          </div>
          <div className="card-pad" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {completedLegs.map((leg) => (
              <span key={leg.leg_id} className="badge" style={{ background: "var(--success-soft)", color: "#166534" }}>
                {leg.driver_name} · Order #{leg.order_id} delivered
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
