import { useEffect, useMemo, useState } from "react";
import { Plus, Search, Zap, ArrowUpDown } from "lucide-react";
import { listOrders, createOrder, updateOrder, deleteOrder, dispatchNext } from "../api/orders";
import { listDrivers } from "../api/drivers";
import { listLocations } from "../api/routes";
import OrderTable from "../components/OrderTable";
import Modal from "../components/Modal";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";

const STATUS_OPTIONS = ["pending", "assigned", "picked_up", "in_transit", "delivered", "cancelled"];

function CreateOrderForm({ locations, onSubmit, submitting, error }) {
  const [form, setForm] = useState({
    customer_name: "",
    pickup_location: "",
    delivery_location: "",
    priority: 3,
    package_weight_kg: 1,
  });

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const pickup = locations.find((l) => l.name === form.pickup_location);
    const delivery = locations.find((l) => l.name === form.delivery_location);
    if (!pickup || !delivery) return;
    onSubmit({
      customer_name: form.customer_name,
      pickup_location: pickup.name,
      pickup_lat: pickup.lat,
      pickup_lng: pickup.lng,
      delivery_location: delivery.name,
      delivery_lat: delivery.lat,
      delivery_lng: delivery.lng,
      priority: Number(form.priority),
      package_weight_kg: Number(form.package_weight_kg),
    });
  }

  return (
    <form onSubmit={handleSubmit} id="create-order-form">
      {error && <div className="form-error">{error}</div>}
      <div className="field">
        <label>Customer name</label>
        <input className="input" value={form.customer_name} onChange={(e) => update("customer_name", e.target.value)} required />
      </div>
      <div className="field-row">
        <div className="field">
          <label>Pickup location</label>
          <select className="input" value={form.pickup_location} onChange={(e) => update("pickup_location", e.target.value)} required>
            <option value="">Select…</option>
            {locations.map((l) => (
              <option key={l.name} value={l.name}>
                {l.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Delivery location</label>
          <select className="input" value={form.delivery_location} onChange={(e) => update("delivery_location", e.target.value)} required>
            <option value="">Select…</option>
            {locations.map((l) => (
              <option key={l.name} value={l.name}>
                {l.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="field-row">
        <div className="field">
          <label>Priority</label>
          <select className="input" value={form.priority} onChange={(e) => update("priority", e.target.value)}>
            <option value={1}>1 · Emergency</option>
            <option value={2}>2 · High</option>
            <option value={3}>3 · Normal</option>
            <option value={4}>4 · Low</option>
          </select>
        </div>
        <div className="field">
          <label>Package weight (kg)</label>
          <input
            className="input"
            type="number"
            min="0.1"
            step="0.1"
            value={form.package_weight_kg}
            onChange={(e) => update("package_weight_kg", e.target.value)}
          />
        </div>
      </div>
      <button type="submit" style={{ display: "none" }} disabled={submitting} />
    </form>
  );
}

function EditOrderForm({ order, drivers, onSubmit, submitting, error }) {
  const [status, setStatus] = useState(order.status);
  const [driverId, setDriverId] = useState(order.assigned_driver_id || "");
  const [priority, setPriority] = useState(order.priority);

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit({
      status,
      assigned_driver_id: driverId ? Number(driverId) : null,
      priority: Number(priority),
    });
  }

  return (
    <form onSubmit={handleSubmit} id="edit-order-form">
      {error && <div className="form-error">{error}</div>}
      <div className="field">
        <label>Status</label>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>Assigned driver</label>
        <select className="input" value={driverId} onChange={(e) => setDriverId(e.target.value)}>
          <option value="">Unassigned</option>
          {drivers.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.status})
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>Priority</label>
        <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value={1}>1 · Emergency</option>
          <option value={2}>2 · High</option>
          <option value={3}>3 · Normal</option>
          <option value={4}>4 · Low</option>
        </select>
      </div>
      <button type="submit" style={{ display: "none" }} disabled={submitting} />
    </form>
  );
}

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [sortKey, setSortKey] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");

  const [showCreate, setShowCreate] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [deletingOrder, setDeletingOrder] = useState(null);
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [notice, setNotice] = useState("");

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [ordersData, driversData, locationsData] = await Promise.all([
        listOrders(statusFilter || undefined),
        listDrivers(),
        listLocations(),
      ]);
      setOrders(ordersData);
      setDrivers(driversData);
      setLocations(locationsData);
    } catch (err) {
      setError(err.message || "Could not load orders.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const visibleOrders = useMemo(() => {
    let result = [...orders];
    if (priorityFilter) {
      result = result.filter((o) => o.priority === Number(priorityFilter));
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(
        (o) =>
          o.customer_name.toLowerCase().includes(q) ||
          String(o.id).includes(q) ||
          o.delivery_location.toLowerCase().includes(q) ||
          o.pickup_location.toLowerCase().includes(q)
      );
    }
    result.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (sortKey === "created_at") {
        av = new Date(av).getTime();
        bv = new Date(bv).getTime();
      }
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return result;
  }, [orders, search, priorityFilter, sortKey, sortDir]);

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  async function handleCreate(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await createOrder(payload);
      setShowCreate(false);
      setNotice("Order created.");
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not create the order.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEdit(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await updateOrder(editingOrder.id, payload);
      setEditingOrder(null);
      setNotice("Order updated.");
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not update the order.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    setSubmitting(true);
    try {
      await deleteOrder(deletingOrder.id);
      setDeletingOrder(null);
      setNotice("Order deleted.");
      await loadAll();
    } catch (err) {
      setError(err.message || "Could not delete the order.");
      setDeletingOrder(null);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDispatchNext() {
    setDispatching(true);
    setError("");
    try {
      const result = await dispatchNext();
      setNotice(`Order #${result.assigned_order_id} dispatched to driver #${result.driver_id}.`);
      await loadAll();
    } catch (err) {
      setError(err.message || "Nothing to dispatch right now.");
    } finally {
      setDispatching(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Orders</h1>
          <div className="page-subtitle">{orders.length} total orders</div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-accent" onClick={handleDispatchNext} disabled={dispatching}>
            <Zap size={15} /> {dispatching ? "Dispatching…" : "Dispatch next"}
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={15} /> New order
          </button>
        </div>
      </div>

      {notice && (
        <div
          style={{
            background: "var(--success-soft)",
            color: "#166534",
            borderRadius: 10,
            padding: "10px 14px",
            fontSize: 12.5,
            marginBottom: 14,
          }}
        >
          {notice}
        </div>
      )}

      <div className="card">
        <div className="table-toolbar">
          <div className="navbar-search" style={{ maxWidth: 260 }}>
            <Search size={15} />
            <input placeholder="Search customer, location, order #" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="input" style={{ maxWidth: 160 }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
          <select className="input" style={{ maxWidth: 150 }} value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="">All priorities</option>
            <option value={1}>1 · Emergency</option>
            <option value={2}>2 · High</option>
            <option value={3}>3 · Normal</option>
            <option value={4}>4 · Low</option>
          </select>
          <button className="btn btn-ghost btn-sm" onClick={() => toggleSort("created_at")}>
            <ArrowUpDown size={13} /> Date
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => toggleSort("priority")}>
            <ArrowUpDown size={13} /> Priority
          </button>
        </div>

        {loading ? (
          <Loading label="Loading orders…" />
        ) : error ? (
          <ErrorState message={error} onRetry={loadAll} />
        ) : (
          <OrderTable orders={visibleOrders} drivers={drivers} onEdit={setEditingOrder} onDelete={setDeletingOrder} />
        )}
      </div>

      {showCreate && (
        <Modal
          title="Create order"
          onClose={() => setShowCreate(false)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="create-order-form" type="submit" disabled={submitting}>
                {submitting ? "Creating…" : "Create order"}
              </button>
            </>
          }
        >
          <CreateOrderForm locations={locations} onSubmit={handleCreate} submitting={submitting} error={formError} />
        </Modal>
      )}

      {editingOrder && (
        <Modal
          title={`Edit order #${editingOrder.id}`}
          onClose={() => setEditingOrder(null)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setEditingOrder(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="edit-order-form" type="submit" disabled={submitting}>
                {submitting ? "Saving…" : "Save changes"}
              </button>
            </>
          }
        >
          <EditOrderForm order={editingOrder} drivers={drivers} onSubmit={handleEdit} submitting={submitting} error={formError} />
        </Modal>
      )}

      {deletingOrder && (
        <Modal
          title="Delete order"
          onClose={() => setDeletingOrder(null)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setDeletingOrder(null)}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleDelete} disabled={submitting}>
                {submitting ? "Deleting…" : "Delete order"}
              </button>
            </>
          }
        >
          <p style={{ fontSize: 13 }}>
            Delete order #{deletingOrder.id} for {deletingOrder.customer_name}? This can't be undone.
          </p>
        </Modal>
      )}
    </div>
  );
}
