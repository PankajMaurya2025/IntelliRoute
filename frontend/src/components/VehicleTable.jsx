import { Pencil, Truck } from "lucide-react";
import { StatusBadge } from "./Badge";
import EmptyState from "./EmptyState";

export default function VehicleTable({ vehicles, onEdit }) {
  if (!vehicles || vehicles.length === 0) {
    return <EmptyState icon={Truck} title="No vehicles yet" message="Add a vehicle to build out your fleet." />;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Vehicle #</th>
            <th>Type</th>
            <th>Capacity</th>
            <th>Status</th>
            <th>Fuel</th>
            <th>Deliveries</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((v) => (
            <tr key={v.id}>
              <td>{v.vehicle_number}</td>
              <td style={{ textTransform: "capitalize" }}>{v.vehicle_type}</td>
              <td>{v.capacity_kg} kg</td>
              <td>
                <StatusBadge status={v.status} />
              </td>
              <td>
                <div className="progress-track" style={{ width: 70 }}>
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.max(0, Math.min(100, v.fuel_level))}%`,
                      background: v.fuel_level < 20 ? "var(--danger)" : "var(--primary)",
                    }}
                  />
                </div>
              </td>
              <td>{v.total_deliveries}</td>
              <td>
                <button className="btn btn-ghost btn-sm" onClick={() => onEdit(v)} aria-label="Edit vehicle">
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
