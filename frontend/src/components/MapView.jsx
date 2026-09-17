import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";

// Default city center used when there's nothing to fit bounds to yet
// (matches the seeded Pune-area warehouse location).
const DEFAULT_CENTER = [18.5204, 73.8567];

const MARKER_COLORS = {
  warehouse: "#4f46e5",
  pickup: "#0284c7",
  delivery: "#ff5a36",
  driver: "#16a34a",
  default: "#6b7280",
};

function coloredIcon(type) {
  const color = MARKER_COLORS[type] || MARKER_COLORS.default;
  return L.divIcon({
    className: "",
    html: `<div class="map-marker-pin" style="background:${color};width:22px;height:22px;"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
  });
}

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points || points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 13);
    } else {
      map.fitBounds(points, { padding: [32, 32] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(points)]);
  return null;
}

/**
 * markers: [{ id, lat, lng, type, label, popup }]
 * route: [[lat, lng], ...] — optional polyline (e.g. a resolved route path)
 */
export default function MapView({ markers = [], route = null, height = 360, fitToMarkers = true }) {
  const points = useMemo(() => markers.map((m) => [m.lat, m.lng]), [markers]);
  const boundsPoints = route && route.length > 0 ? [...points, ...route] : points;

  return (
    <div className="map-shell" style={{ height }}>
      <MapContainer center={DEFAULT_CENTER} zoom={12} scrollWheelZoom style={{ width: "100%", height: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {fitToMarkers && boundsPoints.length > 0 && <FitBounds points={boundsPoints} />}
        {route && route.length > 1 && <Polyline positions={route} pathOptions={{ color: "#4f46e5", weight: 4, opacity: 0.75 }} />}
        {markers.map((m) => (
          <Marker key={m.id} position={[m.lat, m.lng]} icon={coloredIcon(m.type)}>
            {(m.label || m.popup) && (
              <Popup>
                <strong>{m.label}</strong>
                {m.popup && <div style={{ marginTop: 4 }}>{m.popup}</div>}
              </Popup>
            )}
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
