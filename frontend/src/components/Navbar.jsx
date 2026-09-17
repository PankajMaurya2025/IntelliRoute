import { useState, useRef, useEffect } from "react";
import { Menu, Bell, LogOut, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar({ onToggleSidebar, title }) {
  const { user, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const userMenuRef = useRef(null);
  const notifRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) setUserMenuOpen(false);
      if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const initials = (user?.name || "?")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="navbar">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button className="hamburger-btn" onClick={onToggleSidebar} aria-label="Toggle navigation">
          <Menu size={22} />
        </button>
        <h2 style={{ fontSize: 16 }}>{title}</h2>
      </div>

      <div className="navbar-right">
        <div style={{ position: "relative" }} ref={notifRef}>
          <button className="navbar-icon-btn" onClick={() => setNotifOpen((o) => !o)} aria-label="Notifications">
            <Bell size={17} />
          </button>
          {notifOpen && (
            <div
              className="card"
              style={{ position: "absolute", right: 0, top: 44, width: 240, zIndex: 40, padding: 14 }}
            >
              <div style={{ fontSize: 12.5, color: "var(--ink-muted)" }}>
                Notifications aren't available yet — the backend doesn't currently expose a notifications endpoint.
              </div>
            </div>
          )}
        </div>

        <div style={{ position: "relative" }} ref={userMenuRef}>
          <div className="navbar-user" onClick={() => setUserMenuOpen((o) => !o)}>
            <div className="navbar-avatar">{initials}</div>
            <div className="navbar-user-meta">
              <span className="navbar-user-name">{user?.name}</span>
              <span className="navbar-user-role">{user?.role}</span>
            </div>
          </div>
          {userMenuOpen && (
            <div
              className="card"
              style={{ position: "absolute", right: 0, top: 48, width: 180, zIndex: 40, padding: 6 }}
            >
              <button
                className="btn btn-ghost btn-sm btn-block"
                style={{ justifyContent: "flex-start" }}
                onClick={() => {
                  setUserMenuOpen(false);
                }}
              >
                <User size={14} /> {user?.email}
              </button>
              <button
                className="btn btn-ghost btn-sm btn-block"
                style={{ justifyContent: "flex-start", color: "var(--danger)" }}
                onClick={logout}
              >
                <LogOut size={14} /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
