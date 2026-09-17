import { Pencil, Star } from "lucide-react";
import { StatusBadge } from "./Badge";
import EmptyState from "./EmptyState";
import { Users } from "lucide-react";

export default function DriverTable({ drivers, vehicles = [], onEdit }) {
  if (!drivers || drivers.length === 0) {
    return <EmptyState icon={Users} title="No drivers yet" message="Add a driver to start assigning deliveries." />;
  }

  const vehicleLabel = (id) => {
    const v = vehicles.find((v) => v.id === id);
    return v ? `${v.vehicle_number} (${v.vehicle_type})` : "—";
  };

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Driver</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Vehicle</th>
            <th>Current order</th>
            <th>Deliveries</th>
            <th>Rating</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {drivers.map((d) => (
            <tr key={d.id}>
              <td>{d.name}</td>
              <td>{d.phone || "—"}</td>
              <td>
                <StatusBadge status={d.status} />
              </td>
              <td>{d.vehicle_id ? vehicleLabel(d.vehicle_id) : "—"}</td>
              <td>{d.current_order_id ? `#${d.current_order_id}` : "—"}</td>
              <td>{d.total_deliveries}</td>
              <td>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Star size={13} color="#f59e0b" fill="#f59e0b" /> {d.rating?.toFixed(1)}
                </span>
              </td>
              <td>
                <button className="btn btn-ghost btn-sm" onClick={() => onEdit(d)} aria-label="Edit driver">
                  <Pencil size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
