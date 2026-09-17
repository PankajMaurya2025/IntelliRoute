const STATUS_STYLES = {
  pending: { bg: "var(--warning-soft)", fg: "#92670a" },
  assigned: { bg: "var(--info-soft)", fg: "#075985" },
  picked_up: { bg: "var(--primary-soft)", fg: "var(--primary-dark)" },
  in_transit: { bg: "var(--primary-soft)", fg: "var(--primary-dark)" },
  delivered: { bg: "var(--success-soft)", fg: "#166534" },
  cancelled: { bg: "var(--danger-soft)", fg: "var(--danger)" },
  available: { bg: "var(--success-soft)", fg: "#166534" },
  on_route: { bg: "var(--primary-soft)", fg: "var(--primary-dark)" },
  offline: { bg: "#eceef2", fg: "var(--ink-muted)" },
  maintenance: { bg: "var(--warning-soft)", fg: "#92670a" },
  running: { bg: "var(--success-soft)", fg: "#166534" },
  paused: { bg: "var(--warning-soft)", fg: "#92670a" },
  stopped: { bg: "#eceef2", fg: "var(--ink-muted)" },
  completed: { bg: "var(--success-soft)", fg: "#166534" },
};

function formatLabel(value) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { bg: "#eceef2", fg: "var(--ink-muted)" };
  return (
    <span className="badge" style={{ background: style.bg, color: style.fg }}>
      <span className="badge-dot" />
      {formatLabel(status)}
    </span>
  );
}

const PRIORITY_META = {
  1: { label: "Emergency", var: "--priority-1", soft: "--priority-1-soft" },
  2: { label: "High", var: "--priority-2", soft: "--priority-2-soft" },
  3: { label: "Normal", var: "--priority-3", soft: "--priority-3-soft" },
  4: { label: "Low", var: "--priority-4", soft: "--priority-4-soft" },
};

export function PriorityBadge({ priority }) {
  const meta = PRIORITY_META[priority] || PRIORITY_META[3];
  return (
    <span
      className="badge"
      style={{ background: `var(${meta.soft})`, color: `var(${meta.var})` }}
    >
      <span className="badge-dot" />
      P{priority} · {meta.label}
    </span>
  );
}

export function priorityLabel(priority) {
  return (PRIORITY_META[priority] || PRIORITY_META[3]).label;
}

export function priorityColor(priority) {
  return `var(${(PRIORITY_META[priority] || PRIORITY_META[3]).var})`;
}
