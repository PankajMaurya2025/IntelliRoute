import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  Truck,
  Route as RouteIcon,
  Boxes,
  Radio,
  BarChart3,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/orders", label: "Orders", icon: Package },
  { to: "/fleet", label: "Fleet", icon: Truck },
  { to: "/routes", label: "Routes", icon: RouteIcon },
  { to: "/batches", label: "Batches", icon: Boxes },
  { to: "/simulation", label: "Simulation", icon: Radio },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Sidebar({ mobileOpen }) {
  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">
          <RouteIcon size={18} />
        </div>
        <span className="sidebar-brand-name">IntelliRoute</span>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}>
            <item.icon size={17} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-foot">IntelliRoute · Phase 3</div>
    </aside>
  );
}
