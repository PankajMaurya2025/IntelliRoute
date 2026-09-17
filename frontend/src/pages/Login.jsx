import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Route as RouteIcon, LogIn, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      const redirectTo = location.state?.from || "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "Could not log in.");
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
          <h2>Routing, batching, and dispatch — worked out for you, in real time.</h2>
          <p>
            Dijkstra, A*, and TSP optimize every route. K-Means groups nearby orders. A trained model predicts
            ETAs. Watch it all move live on the map.
          </p>
        </div>
        <div style={{ fontSize: 11.5, color: "rgba(255,255,255,0.5)" }}>Logistics control center</div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <h1>Welcome back</h1>
          <p className="subtitle">Log in to your IntelliRoute control center.</p>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>Email</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@intelliroute.com"
                required
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? <Loader2 size={14} className="spin-icon" /> : <LogIn size={14} />}
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>

          <div className="auth-divider">or</div>

          <button className="btn btn-outline btn-block" type="button" disabled title="Google login requires backend OAuth support, which isn't implemented yet">
            Continue with Google (backend configuration required)
          </button>

          <p className="auth-footer-link">
            Don't have an account? <Link to="/signup">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
