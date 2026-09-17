import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from "recharts";
import { Package, Clock, Truck, CheckCircle2, Users, Gauge, Timer, MapPinned, Radio } from "lucide-react";
import { getAnalyticsSummary } from "../api/analytics";
import { listOrders, getPriorityQueue, dispatchNext } from "../api/orders";
import { listDrivers } from "../api/drivers";
import { getSimulationState } from "../api/simulation";
import StatCard from "../components/StatCard";
import PriorityQueue from "../components/PriorityQueue";
import MapView from "../components/MapView";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";
import { StatusBadge, PriorityBadge } from "../components/Badge";

const PRIORITY_COLORS = ["#dc2626", "#f59e0b", "#0284c7", "#6b7280"];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [orders, setOrders] = useState([]);
  const [queue, setQueue] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [simState, setSimState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dispatching, setDispatching] = useState(false);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [summaryData, ordersData, queueData, driversData] = await Promise.all([
        getAnalyticsSummary(),
        listOrders(),
        getPriorityQueue(),
        listDrivers(),
      ]);
      setSummary(summaryData);
      setOrders(ordersData);
      setQueue(queueData);
      setDrivers(driversData);
      try {
        setSimState(await getSimulationState());
      } catch {
        setSimState(null); // simulation state is a bonus panel, not fatal if it fails
      }
    } catch (err) {
      setError(err.message || "Could not load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDispatchNext() {
    setDispatching(true);
    try {
      await dispatchNext();
      await loadAll();
    } catch (err) {
      setError(err.message || "Could not dispatch the next order.");
    } finally {
      setDispatching(false);
    }
  }

  if (loading) return <Loading label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={loadAll} />;
  if (!summary) return null;

  const statusData = [
    { name: "Pending", value: summary.pending_orders },
    { name: "Active", value: summary.active_deliveries },
    { name: "Delivered", value: summary.delivered_orders },
    { name: "Cancelled", value: summary.cancelled_orders },
  ];

  const priorityData = [
    { name: "Emergency", value: summary.priority_breakdown.emergency },
    { name: "High", value: summary.priority_breakdown.high },
    { name: "Normal", value: summary.priority_breakdown.normal },
    { name: "Low", value: summary.priority_breakdown.low },
  ].filter((d) => d.value > 0);

  const utilizationData = [
    { name: "Drivers", value: summary.driver_utilization_pct },
    { name: "Vehicles", value: summary.vehicle_utilization_pct },
  ];

  const pendingOrders = orders.filter((o) => o.status === "pending");
  const mapMarkers = [
    ...drivers.map((d) => ({
      id: `driver-${d.id}`,
      lat: d.current_lat,
      lng: d.current_lng,
      type: "driver",
      label: d.name,
      popup: `Status: ${d.status.replace("_", " ")}`,
    })),
    ...pendingOrders.slice(0, 15).map((o) => ({
      id: `order-${o.id}`,
      lat: o.delivery_lat,
      lng: o.delivery_lng,
      type: "delivery",
      label: `Order #${o.id}`,
      popup: o.customer_name,
    })),
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <div className="page-subtitle">Live snapshot of every order, driver, and route in the system.</div>
        </div>
      </div>

      <div className="stat-grid">
        <StatCard icon={Package} label="Total orders" value={summary.total_orders} tone="primary" />
        <StatCard icon={Clock} label="Pending orders" value={summary.pending_orders} tone="warning" />
        <StatCard icon={Truck} label="Active deliveries" value={summary.active_deliveries} tone="info" />
        <StatCard icon={CheckCircle2} label="Delivered" value={summary.delivered_orders} tone="success" />
        <StatCard
          icon={Users}
          label="Available drivers"
          value={`${summary.available_drivers}/${summary.total_drivers}`}
          tone="primary"
        />
        <StatCard icon={Gauge} label="Driver utilization" value={summary.driver_utilization_pct} suffix="%" tone="accent" />
        <StatCard icon={Timer} label="Average ETA" value={summary.average_eta_min} suffix="min" tone="info" />
        <StatCard icon={MapPinned} label="Total distance" value={summary.total_distance_km} suffix="km" tone="primary" />
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="card-header">
            <h3>Order status</h3>
          </div>
          <div className="card-pad" style={{ height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Priority distribution</h3>
          </div>
          <div className="card-pad" style={{ height: 240 }}>
            {priorityData.length === 0 ? (
              <ErrorState message="No orders yet to chart." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={priorityData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                    {priorityData.map((_, i) => (
                      <Cell key={i} fill={PRIORITY_COLORS[i % PRIORITY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="two-col">
        <PriorityQueue queue={queue} orders={orders} onDispatchNext={handleDispatchNext} dispatching={dispatching} />

        <div className="card">
          <div className="card-header">
            <h3>Fleet utilization</h3>
          </div>
          <div className="card-pad" style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={utilizationData} layout="vertical" margin={{ left: 8 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} width={60} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="value" fill="#ff5a36" radius={[0, 6, 6, 0]} barSize={22} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <h3>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <Radio size={15} /> Live simulation
            </span>
          </h3>
          <Link to="/simulation" className="btn btn-outline btn-sm">
            Open simulation
          </Link>
        </div>
        <div className="card-pad">
          {simState ? (
            <div style={{ display: "flex", gap: 24, fontSize: 13, flexWrap: "wrap" }}>
              <span>
                Status: <StatusBadge status={simState.status} />
              </span>
              <span>Active legs: {simState.active_legs?.length ?? 0}</span>
              <span>Completed this session: {simState.completed_legs?.length ?? 0}</span>
            </div>
          ) : (
            <span style={{ fontSize: 12.5, color: "var(--ink-muted)" }}>Simulation state unavailable right now.</span>
          )}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <h3>Map</h3>
        </div>
        <div className="card-pad">
          <MapView markers={mapMarkers} height={340} />
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent orders</h3>
          <Link to="/orders" className="btn btn-outline btn-sm">
            View all
          </Link>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 6).map((o) => (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td>{o.customer_name}</td>
                  <td>
                    <PriorityBadge priority={o.priority} />
                  </td>
                  <td>
                    <StatusBadge status={o.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
