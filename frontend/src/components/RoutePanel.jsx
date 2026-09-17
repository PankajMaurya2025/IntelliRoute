import { useState } from "react";
import { Navigation, Loader2 } from "lucide-react";
import { optimizeRoute } from "../api/routes";

const ALGORITHM_LABELS = {
  dijkstra: "Dijkstra",
  a_star: "A*",
  bfs: "BFS",
  dfs: "DFS",
  bellman_ford: "Bellman-Ford",
  floyd_warshall: "Floyd-Warshall",
};

export default function RoutePanel({ locations, algorithms, onResult }) {
  const [start, setStart] = useState("");
  const [destination, setDestination] = useState("");
  const [algorithm, setAlgorithm] = useState(algorithms[0] || "dijkstra");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!start || !destination) {
      setError("Choose both a start and a destination.");
      return;
    }
    if (start === destination) {
      setError("Start and destination must be different locations.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await optimizeRoute({ start, destination, algorithm });
      setResult(data);
      onResult?.(data);
    } catch (err) {
      setError(err.message || "Could not compute a route.");
      setResult(null);
      onResult?.(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Route optimizer</h3>
      </div>
      <div className="card-pad">
        {error && <div className="form-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Start</label>
            <select className="input" value={start} onChange={(e) => setStart(e.target.value)}>
              <option value="">Select a location</option>
              {locations.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Destination</label>
            <select className="input" value={destination} onChange={(e) => setDestination(e.target.value)}>
              <option value="">Select a location</option>
              {locations.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Algorithm</label>
            <select className="input" value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
              {algorithms.map((a) => (
                <option key={a} value={a}>
                  {ALGORITHM_LABELS[a] || a}
                </option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? <Loader2 size={14} className="spin-icon" /> : <Navigation size={14} />}
            {loading ? "Computing route…" : "Run optimization"}
          </button>
        </form>

        {result && (
          <div style={{ marginTop: 18, borderTop: "1px solid var(--border)", paddingTop: 16 }}>
            {result.found ? (
              <>
                <div className="two-col" style={{ marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 11.5, color: "var(--ink-muted)" }}>Distance</div>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700 }}>
                      {result.distance} km
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11.5, color: "var(--ink-muted)" }}>Travel time</div>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700 }}>
                      {result.travel_time} min
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: 11.5, color: "var(--ink-muted)", marginBottom: 6 }}>
                  {ALGORITHM_LABELS[result.algorithm] || result.algorithm} explored {result.nodes_explored} node
                  {result.nodes_explored === 1 ? "" : "s"}
                </div>
                <div style={{ fontSize: 12.5, lineHeight: 1.7 }}>{result.path.join(" → ")}</div>
              </>
            ) : (
              <div style={{ fontSize: 13, color: "var(--danger)" }}>No route was found between these locations.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
