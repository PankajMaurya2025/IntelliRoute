export default function StatCard({ icon: Icon, label, value, tone = "primary", suffix }) {
  const toneStyles = {
    primary: { bg: "var(--primary-soft)", fg: "var(--primary-dark)" },
    accent: { bg: "var(--accent-soft)", fg: "var(--accent)" },
    success: { bg: "var(--success-soft)", fg: "#166534" },
    warning: { bg: "var(--warning-soft)", fg: "#92670a" },
    info: { bg: "var(--info-soft)", fg: "#075985" },
  }[tone];

  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <span className="stat-card-label">{label}</span>
        {Icon && (
          <span className="stat-card-icon" style={{ background: toneStyles.bg, color: toneStyles.fg }}>
            <Icon size={17} />
          </span>
        )}
      </div>
      <span className="stat-card-value">
        {value}
        {suffix && <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink-muted)", marginLeft: 4 }}>{suffix}</span>}
      </span>
    </div>
  );
}
