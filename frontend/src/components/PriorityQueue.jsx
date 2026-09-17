import { Zap, ListOrdered } from "lucide-react";
import { PriorityBadge, priorityColor } from "./Badge";
import EmptyState from "./EmptyState";

export default function PriorityQueue({ queue, orders = [], onDispatchNext, dispatching }) {
  const orderMeta = (id) => orders.find((o) => o.id === id);

  return (
    <div className="card">
      <div className="card-header">
        <h3>Priority queue</h3>
        <button className="btn btn-accent btn-sm" onClick={onDispatchNext} disabled={dispatching || !queue?.length}>
          <Zap size={14} /> {dispatching ? "Dispatching…" : "Dispatch next"}
        </button>
      </div>
      <div className="card-pad">
        {!queue || queue.length === 0 ? (
          <EmptyState icon={ListOrdered} title="Queue is empty" message="Every pending order has been dispatched." />
        ) : (
          <div className="pq-list">
            {queue.map((entry, i) => {
              const order = orderMeta(entry.order_id);
              return (
                <div className="pq-row" key={entry.order_id} style={{ borderLeft: `3px solid ${priorityColor(entry.priority)}` }}>
                  <span className="pq-rank">{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>Order #{entry.order_id}</div>
                    <div style={{ fontSize: 11.5, color: "var(--ink-muted)" }}>
                      {order?.customer_name || "Customer details unavailable"}
                    </div>
                  </div>
                  <PriorityBadge priority={entry.priority} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
