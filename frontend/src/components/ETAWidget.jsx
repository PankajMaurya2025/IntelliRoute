import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { predictEta } from "../api/ml";

const TRAFFIC_LEVELS = ["low", "medium", "high", "severe"];

const DEFAULT_FORM = {
  distance_km: 5,
  traffic_level: "low",
  num_stops: 1,
  priority: 3,
  package_weight_kg: 1,
  hour_of_day: new Date().getHours(),
  day_of_week: (new Date().getDay() + 6) % 7, // JS: 0=Sun -> backend: 0=Mon
};

export default function ETAWidget({ compact = false }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [eta, setEta] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        ...form,
        distance_km: Number(form.distance_km),
        num_stops: Number(form.num_stops),
        priority: Number(form.priority),
        package_weight_kg: Number(form.package_weight_kg),
        hour_of_day: Number(form.hour_of_day),
        day_of_week: Number(form.day_of_week),
      };
      const data = await predictEta(payload);
      setEta(data.predicted_eta_minutes);
    } catch (err) {
      setError(err.message || "Could not get a prediction.");
      setEta(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>ETA prediction</h3>
        <Sparkles size={16} color="var(--accent)" />
      </div>
      <div className="card-pad">
        {error && <div className="form-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field-row">
            <div className="field">
              <label>Distance (km)</label>
              <input
                className="input"
                type="number"
                min="0.1"
                step="0.1"
                value={form.distance_km}
                onChange={(e) => update("distance_km", e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label>Traffic</label>
              <select className="input" value={form.traffic_level} onChange={(e) => update("traffic_level", e.target.value)}>
                {TRAFFIC_LEVELS.map((t) => (
                  <option key={t} value={t} style={{ textTransform: "capitalize" }}>
                    {t[0].toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {!compact && (
            <>
              <div className="field-row">
                <div className="field">
                  <label>Stops on route</label>
                  <input
                    className="input"
                    type="number"
                    min="1"
                    value={form.num_stops}
                    onChange={(e) => update("num_stops", e.target.value)}
                  />
                </div>
                <div className="field">
                  <label>Priority</label>
                  <select className="input" value={form.priority} onChange={(e) => update("priority", e.target.value)}>
                    <option value={1}>1 · Emergency</option>
                    <option value={2}>2 · High</option>
                    <option value={3}>3 · Normal</option>
                    <option value={4}>4 · Low</option>
                  </select>
                </div>
              </div>
              <div className="field-row">
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
                <div className="field">
                  <label>Hour of day</label>
                  <input
                    className="input"
                    type="number"
                    min="0"
                    max="23"
                    value={form.hour_of_day}
                    onChange={(e) => update("hour_of_day", e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? <Loader2 size={14} className="spin-icon" /> : <Sparkles size={14} />}
            {loading ? "Predicting…" : "Predict ETA"}
          </button>
        </form>

        {eta != null && (
          <div
            style={{
              marginTop: 16,
              padding: "14px 16px",
              borderRadius: 12,
              background: "var(--accent-soft)",
              display: "flex",
              alignItems: "baseline",
              justifyContent: "space-between",
            }}
          >
            <span style={{ fontSize: 12.5, color: "var(--ink-muted)" }}>Predicted ETA</span>
            <span style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>
              {eta} min
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
