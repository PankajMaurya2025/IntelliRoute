import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { listDrivers, createDriver, updateDriver } from "../api/drivers";
import { listVehicles, createVehicle, updateVehicle } from "../api/vehicles";
import DriverTable from "../components/DriverTable";
import VehicleTable from "../components/VehicleTable";
import Modal from "../components/Modal";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";

const DRIVER_STATUSES = ["available", "assigned", "on_route", "offline"];
const VEHICLE_STATUSES = ["available", "assigned", "on_route", "maintenance", "offline"];
const VEHICLE_TYPES = ["bike", "car", "van", "truck"];

function DriverForm({ mode, driver, vehicles, onSubmit, submitting, error }) {
  const [name, setName] = useState(driver?.name || "");
  const [phone, setPhone] = useState(driver?.phone || "");
  const [vehicleId, setVehicleId] = useState(driver?.vehicle_id || "");
  const [status, setStatus] = useState(driver?.status || "available");
  const [lat, setLat] = useState(driver?.current_lat ?? 18.5204);
  const [lng, setLng] = useState(driver?.current_lng ?? 73.8567);

  function handleSubmit(e) {
    e.preventDefault();
    if (mode === "create") {
      onSubmit({
        name,
        phone,
        vehicle_id: vehicleId ? Number(vehicleId) : null,
        current_lat: Number(lat),
        current_lng: Number(lng),
      });
    } else {
      onSubmit({
        status,
        vehicle_id: vehicleId ? Number(vehicleId) : null,
        current_lat: Number(lat),
        current_lng: Number(lng),
      });
    }
  }

  return (
    <form id="driver-form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}
      {mode === "create" && (
        <>
          <div className="field">
            <label>Name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="field">
            <label>Phone</label>
            <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
        </>
      )}
      {mode === "edit" && (
        <div className="field">
          <label>Status</label>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            {DRIVER_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="field">
        <label>Vehicle</label>
        <select className="input" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
          <option value="">None</option>
          {vehicles.map((v) => (
            <option key={v.id} value={v.id}>
              {v.vehicle_number} ({v.vehicle_type})
            </option>
          ))}
        </select>
      </div>
      <div className="field-row">
        <div className="field">
          <label>Current lat</label>
          <input className="input" type="number" step="0.0001" value={lat} onChange={(e) => setLat(e.target.value)} />
        </div>
        <div className="field">
          <label>Current lng</label>
          <input className="input" type="number" step="0.0001" value={lng} onChange={(e) => setLng(e.target.value)} />
        </div>
      </div>
      <button type="submit" style={{ display: "none" }} disabled={submitting} />
    </form>
  );
}

function VehicleForm({ mode, vehicle, onSubmit, submitting, error }) {
  const [vehicleNumber, setVehicleNumber] = useState(vehicle?.vehicle_number || "");
  const [vehicleType, setVehicleType] = useState(vehicle?.vehicle_type || "bike");
  const [capacity, setCapacity] = useState(vehicle?.capacity_kg || 20);
  const [status, setStatus] = useState(vehicle?.status || "available");
  const [fuel, setFuel] = useState(vehicle?.fuel_level ?? 100);

  function handleSubmit(e) {
    e.preventDefault();
    if (mode === "create") {
      onSubmit({ vehicle_number: vehicleNumber, vehicle_type: vehicleType, capacity_kg: Number(capacity) });
    } else {
      onSubmit({ status, fuel_level: Number(fuel) });
    }
  }

  return (
    <form id="vehicle-form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}
      {mode === "create" ? (
        <>
          <div className="field">
            <label>Vehicle number</label>
            <input className="input" value={vehicleNumber} onChange={(e) => setVehicleNumber(e.target.value)} required />
          </div>
          <div className="field-row">
            <div className="field">
              <label>Type</label>
              <select className="input" value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
                {VEHICLE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Capacity (kg)</label>
              <input className="input" type="number" value={capacity} onChange={(e) => setCapacity(e.target.value)} />
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="field">
            <label>Status</label>
            <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
              {VEHICLE_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Fuel level (%)</label>
            <input className="input" type="number" min="0" max="100" value={fuel} onChange={(e) => setFuel(e.target.value)} />
          </div>
        </>
      )}
      <button type="submit" style={{ display: "none" }} disabled={submitting} />
    </form>
  );
}

export default function Fleet() {
  const [tab, setTab] = useState("drivers");
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showCreateDriver, setShowCreateDriver] = useState(false);
  const [editingDriver, setEditingDriver] = useState(null);
  const [showCreateVehicle, setShowCreateVehicle] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [driversData, vehiclesData] = await Promise.all([listDrivers(), listVehicles()]);
      setDrivers(driversData);
      setVehicles(vehiclesData);
    } catch (err) {
      setError(err.message || "Could not load fleet data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function handleCreateDriver(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await createDriver(payload);
      setShowCreateDriver(false);
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not create the driver.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEditDriver(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await updateDriver(editingDriver.id, payload);
      setEditingDriver(null);
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not update the driver.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateVehicle(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await createVehicle(payload);
      setShowCreateVehicle(false);
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not create the vehicle.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEditVehicle(payload) {
    setSubmitting(true);
    setFormError("");
    try {
      await updateVehicle(editingVehicle.id, payload);
      setEditingVehicle(null);
      await loadAll();
    } catch (err) {
      setFormError(err.message || "Could not update the vehicle.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Fleet</h1>
          <div className="page-subtitle">
            {drivers.length} drivers · {vehicles.length} vehicles
          </div>
        </div>
        {tab === "drivers" ? (
          <button className="btn btn-primary" onClick={() => setShowCreateDriver(true)}>
            <Plus size={15} /> Add driver
          </button>
        ) : (
          <button className="btn btn-primary" onClick={() => setShowCreateVehicle(true)}>
            <Plus size={15} /> Add vehicle
          </button>
        )}
      </div>

      <div className="tabs">
        <button className={`tab-btn ${tab === "drivers" ? "active" : ""}`} onClick={() => setTab("drivers")}>
          Drivers
        </button>
        <button className={`tab-btn ${tab === "vehicles" ? "active" : ""}`} onClick={() => setTab("vehicles")}>
          Vehicles
        </button>
      </div>

      <div className="card">
        {loading ? (
          <Loading label="Loading fleet…" />
        ) : error ? (
          <ErrorState message={error} onRetry={loadAll} />
        ) : tab === "drivers" ? (
          <DriverTable drivers={drivers} vehicles={vehicles} onEdit={setEditingDriver} />
        ) : (
          <VehicleTable vehicles={vehicles} onEdit={setEditingVehicle} />
        )}
      </div>

      {showCreateDriver && (
        <Modal
          title="Add driver"
          onClose={() => setShowCreateDriver(false)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setShowCreateDriver(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="driver-form" type="submit" disabled={submitting}>
                {submitting ? "Adding…" : "Add driver"}
              </button>
            </>
          }
        >
          <DriverForm mode="create" vehicles={vehicles} onSubmit={handleCreateDriver} submitting={submitting} error={formError} />
        </Modal>
      )}

      {editingDriver && (
        <Modal
          title={`Edit ${editingDriver.name}`}
          onClose={() => setEditingDriver(null)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setEditingDriver(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="driver-form" type="submit" disabled={submitting}>
                {submitting ? "Saving…" : "Save changes"}
              </button>
            </>
          }
        >
          <DriverForm
            mode="edit"
            driver={editingDriver}
            vehicles={vehicles}
            onSubmit={handleEditDriver}
            submitting={submitting}
            error={formError}
          />
        </Modal>
      )}

      {showCreateVehicle && (
        <Modal
          title="Add vehicle"
          onClose={() => setShowCreateVehicle(false)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setShowCreateVehicle(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="vehicle-form" type="submit" disabled={submitting}>
                {submitting ? "Adding…" : "Add vehicle"}
              </button>
            </>
          }
        >
          <VehicleForm mode="create" onSubmit={handleCreateVehicle} submitting={submitting} error={formError} />
        </Modal>
      )}

      {editingVehicle && (
        <Modal
          title={`Edit ${editingVehicle.vehicle_number}`}
          onClose={() => setEditingVehicle(null)}
          footer={
            <>
              <button className="btn btn-outline" onClick={() => setEditingVehicle(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" form="vehicle-form" type="submit" disabled={submitting}>
                {submitting ? "Saving…" : "Save changes"}
              </button>
            </>
          }
        >
          <VehicleForm mode="edit" vehicle={editingVehicle} onSubmit={handleEditVehicle} submitting={submitting} error={formError} />
        </Modal>
      )}
    </div>
  );
}
