import LiveSimulation from "../components/LiveSimulation";

export default function Simulation() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Live simulation</h1>
          <div className="page-subtitle">Drivers move along real routed paths, streamed live over WebSocket.</div>
        </div>
      </div>
      <LiveSimulation />
    </div>
  );
}
