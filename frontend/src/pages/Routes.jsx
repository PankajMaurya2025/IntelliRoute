import { useEffect, useState } from "react";
import { listLocations, listAlgorithms } from "../api/routes";
import RoutePanel from "../components/RoutePanel";
import MapView from "../components/MapView";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";

export default function RoutesPage() {
  const [locations, setLocations] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [locationsData, algorithmsData] = await Promise.all([listLocations(), listAlgorithms()]);
      setLocations(locationsData);
      setAlgorithms(algorithmsData);
    } catch (err) {
      setError(err.message || "Could not load routing data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  if (loading) return <Loading label="Loading route network…" />;
  if (error) return <ErrorState message={error} onRetry={loadAll} />;

  const byName = Object.fromEntries(locations.map((l) => [l.name, l]));
  const routeLine = result?.found
    ? result.path.map((name) => [byName[name]?.lat, byName[name]?.lng]).filter((p) => p[0] != null)
    : null;
  const markers = result?.found
    ? result.path.map((name, i) => ({
        id: name,
        lat: byName[name].lat,
        lng: byName[name].lng,
        type: i === 0 ? "pickup" : i === result.path.length - 1 ? "delivery" : "default",
        label: name,
      }))
    : locations.map((l) => ({
        id: l.name,
        lat: l.lat,
        lng: l.lng,
        type: l.name === "Warehouse" ? "warehouse" : "default",
        label: l.name,
      }));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Routes</h1>
          <div className="page-subtitle">Compare routing algorithms across the live road network.</div>
        </div>
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="card-header">
            <h3>Network map</h3>
          </div>
          <div className="card-pad">
            <MapView markers={markers} route={routeLine} height={440} />
          </div>
        </div>

        <RoutePanel locations={locations} algorithms={algorithms} onResult={setResult} />
      </div>
    </div>
  );
}
