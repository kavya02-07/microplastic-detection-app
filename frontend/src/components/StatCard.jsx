export default function StatCard({ title, value, subtitle, icon, isPlaceholder = true }) {
  return (
    <div className="stat-card-widget">
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        <span className="stat-icon-wrap">{icon}</span>
      </div>
      <div className="stat-body">
        <div className="stat-value-row">
          <span className="stat-number">{value}</span>
          {isPlaceholder && <span className="stat-placeholder-tag">Placeholder</span>}
        </div>
        <p className="stat-desc">{subtitle}</p>
      </div>
    </div>
  );
}
