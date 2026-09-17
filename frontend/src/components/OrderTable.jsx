import { Pencil, Trash2 } from "lucide-react";
import { StatusBadge, PriorityBadge } from "./Badge";
import EmptyState from "./EmptyState";
import { Package } from "lucide-react";

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function OrderTable({ orders, drivers = [], onEdit, onDelete }) {
  if (!orders || orders.length === 0) {
    return <EmptyState icon={Package} title="No orders match your filters" message="Try clearing filters, or create a new order." />;
  }

  const driverName = (id) => drivers.find((d) => d.id === id)?.name || `#${id}`;

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Route</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Driver</th>
            <th>Distance</th>
            <th>ETA</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>#{o.id}</td>
              <td>{o.customer_name}</td>
              <td>
                <div style={{ fontSize: 12.5 }}>{o.pickup_location}</div>
                <div style={{ fontSize: 11, color: "var(--ink-faint)" }}>→ {o.delivery_location}</div>
              </td>
              <td>
                <PriorityBadge priority={o.priority} />
              </td>
              <td>
                <StatusBadge status={o.status} />
              </td>
              <td>{o.assigned_driver_id ? driverName(o.assigned_driver_id) : "—"}</td>
              <td>{o.distance_km != null ? `${o.distance_km} km` : "—"}</td>
              <td>{o.predicted_eta_min != null ? `${o.predicted_eta_min} min` : "—"}</td>
              <td>{fmtDate(o.created_at)}</td>
              <td>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn btn-ghost btn-sm" onClick={() => onEdit(o)} aria-label="Edit order">
                    <Pencil size={14} />
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => onDelete(o)} aria-label="Delete order">
                    <Trash2 size={14} color="var(--danger)" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
