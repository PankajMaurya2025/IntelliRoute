import { useEffect, useState } from "react";
import { Boxes, Sparkles } from "lucide-react";
import { listBatches, createBatches } from "../api/batches";
import BatchCard from "../components/BatchCard";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

export default function Batches() {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [ordersPerBatch, setOrdersPerBatch] = useState(4);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  async function loadBatches() {
    setLoading(true);
    setError("");
    try {
      const data = await listBatches();
      setBatches(data);
    } catch (err) {
      setError(err.message || "Could not load batches.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBatches();
  }, []);

  async function handleCreateBatches() {
    setCreating(true);
    setCreateError("");
    try {
      await createBatches(Number(ordersPerBatch));
      await loadBatches();
    } catch (err) {
      setCreateError(err.message || "Could not create batches — there may not be enough unbatched pending orders yet.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Batches</h1>
          <div className="page-subtitle">Group nearby pending orders with K-Means clustering, then route each batch.</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-pad" style={{ display: "flex", alignItems: "flex-end", gap: 14, flexWrap: "wrap" }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Target orders per batch</label>
            <input
              className="input"
              type="number"
              min="1"
              style={{ width: 140 }}
              value={ordersPerBatch}
              onChange={(e) => setOrdersPerBatch(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={handleCreateBatches} disabled={creating}>
            <Sparkles size={15} /> {creating ? "Clustering orders…" : "Create batches"}
          </button>
        </div>
        {createError && (
          <div className="card-pad" style={{ paddingTop: 0 }}>
            <div className="form-error" style={{ marginBottom: 0 }}>
              {createError}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <Loading label="Loading batches…" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadBatches} />
      ) : batches.length === 0 ? (
        <EmptyState
          icon={Boxes}
          title="No batches yet"
          message="Create batches to group nearby pending orders for a single driver run."
        />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
          {batches.map((b) => (
            <BatchCard key={b.id} batch={b} />
          ))}
        </div>
      )}
    </div>
  );
}
