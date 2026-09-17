import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Route as RouteIcon, UserPlus, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      await signup(form.name, form.email, form.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Could not create your account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-visual">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="sidebar-brand-mark">
            <RouteIcon size={18} />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18 }}>IntelliRoute</span>
        </div>
        <div>
          <h2>Everything a logistics team needs, wired to one live backend.</h2>
          <p>Orders, fleet, priority dispatch, live simulation, and analytics — no mock data, no placeholders.</p>
        </div>
        <div style={{ fontSize: 11.5, color: "rgba(255,255,255,0.5)" }}>Logistics control center</div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <h1>Create an account</h1>
          <p className="subtitle">Set up your IntelliRoute admin account.</p>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>Full name</label>
              <input className="input" value={form.name} onChange={(e) => update("name", e.target.value)} required />
            </div>
            <div className="field">
              <label>Email</label>
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input
                className="input"
                type="password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                required
              />
              <span className="hint">At least 6 characters.</span>
            </div>
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? <Loader2 size={14} className="spin-icon" /> : <UserPlus size={14} />}
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="auth-footer-link">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
