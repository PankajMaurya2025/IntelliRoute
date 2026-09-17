import { useEffect, useState } from "react";
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
  Legend,
} from "recharts";
import { Timer, MapPinned, Users, Truck } from "lucide-react";
import { getAnalyticsSummary } from "../api/analytics";
import StatCard from "../components/StatCard";
import ETAWidget from "../components/ETAWidget";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";

const PRIORITY_COLORS = ["#dc2626", "#f59e0b", "#0284c7", "#6b7280"];

export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setSummary(await getAnalyticsSummary());
    } catch (err) {
      setError(err.message || "Could not load analytics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Loading label="Loading analytics…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
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
    { name: "Drivers", available: summary.available_drivers, busy: summary.total_drivers - summary.available_drivers },
    { name: "Vehicles", available: summary.available_vehicles, busy: summary.total_vehicles - summary.available_vehicles },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <div className="page-subtitle">Live performance metrics across the whole fleet.</div>
        </div>
      </div>

      <div className="stat-grid">
        <StatCard icon={Timer} label="Average ETA" value={summary.average_eta_min} suffix="min" tone="info" />
        <StatCard icon={MapPinned} label="Total distance" value={summary.total_distance_km} suffix="km" tone="primary" />
        <StatCard icon={Users} label="Driver utilization" value={summary.driver_utilization_pct} suffix="%" tone="accent" />
        <StatCard icon={Truck} label="Vehicle utilization" value={summary.vehicle_utilization_pct} suffix="%" tone="warning" />
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="card-header">
            <h3>Delivery performance by status</h3>
          </div>
          <div className="card-pad" style={{ height: 260 }}>
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
          <div className="card-pad" style={{ height: 260 }}>
            {priorityData.length === 0 ? (
              <ErrorState message="No orders yet to chart." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={priorityData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {priorityData.map((_, i) => (
                      <Cell key={i} fill={PRIORITY_COLORS[i % PRIORITY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-header">
            <h3>Fleet availability</h3>
          </div>
          <div className="card-pad" style={{ height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={utilizationData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="available" stackId="a" fill="#16a34a" name="Available" radius={[0, 0, 0, 0]} />
                <Bar dataKey="busy" stackId="a" fill="#ff5a36" name="Busy" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <ETAWidget compact />
      </div>
    </div>
  );
}
