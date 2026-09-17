import { useState } from "react";
import { ChevronDown, ChevronUp, Package, Route as RouteIcon, Clock } from "lucide-react";
import { getBatch } from "../api/batches";

export default function BatchCard({ batch }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function toggle() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (detail) return;
    setLoading(true);
    setError("");
    try {
      const data = await getBatch(batch.id);
      setDetail(data);
    } catch (err) {
      setError(err.message || "Could not load batch details.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-pad" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              className="stat-card-icon"
              style={{ background: "var(--primary-soft)", color: "var(--primary-dark)", width: 32, height: 32 }}
            >
              <Package size={15} />
            </span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>Batch #{batch.id}</div>
              <div style={{ fontSize: 11.5, color: "var(--ink-muted)" }}>
                {batch.num_orders} order{batch.num_orders === 1 ? "" : "s"}
                {batch.assigned_driver_id ? ` · Driver #${batch.assigned_driver_id}` : " · Unassigned"}
              </div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={toggle}>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        <div className="two-col">
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "var(--ink-muted)" }}>
            <RouteIcon size={13} /> {batch.total_distance_km} km
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "var(--ink-muted)" }}>
            <Clock size={13} /> {batch.estimated_time_min} min
          </div>
        </div>

        {expanded && (
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12 }}>
            {loading && <div style={{ fontSize: 12.5, color: "var(--ink-muted)" }}>Loading orders…</div>}
            {error && <div className="form-error">{error}</div>}
            {detail && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {detail.order_ids.map((id) => (
                  <span key={id} className="badge" style={{ background: "var(--surface-alt)", color: "var(--ink)" }}>
                    Order #{id}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
