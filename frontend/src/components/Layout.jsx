import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

const TITLES = {
  "/dashboard": "Dashboard",
  "/orders": "Orders",
  "/fleet": "Fleet management",
  "/routes": "Route optimization",
  "/batches": "Order batching",
  "/simulation": "Live simulation",
  "/analytics": "Analytics",
};

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const title = TITLES[location.pathname] || "IntelliRoute";

  return (
    <div className="app-shell">
      <Sidebar mobileOpen={mobileOpen} />
      <div className="app-main">
        <Navbar onToggleSidebar={() => setMobileOpen((o) => !o)} title={title} />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
