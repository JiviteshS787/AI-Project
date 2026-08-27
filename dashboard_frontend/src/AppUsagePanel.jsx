const TYPE_LABELS = {
  app: "Apps",
  alias: "Aliases",
  file: "Files",
  project: "Projects",
  script: "Scripts"
};

function AppStatsGroup({ title, data }) {
  const hasAny = data && Object.values(data).some((entries) => entries.length > 0);

  return (
    <div className="top-stats-group">
      <h3 className="panel-title">{title}</h3>
      {!hasAny ? (
        <p className="empty-note">No activity found</p>
      ) : (
        Object.entries(TYPE_LABELS).map(([type, label]) => {
          const entries = data?.[type] || [];
          if (entries.length === 0) return null;

          return (
            <div key={type} className="top-stats-type">
              <span className="top-stats-type-label">{label}</span>
              <ul className="top-stats-list">
                {entries
                    .map(([target, info]) => (
                        <li key={target} className="top-stats-item">
                        <span className="top-stats-name">{target}</span>
                        <span className="top-stats-count">{info.opens}</span>
                        </li>
                    ))}
              </ul>
            </div>
          );
        })
      )}
    </div>
  );
}

export default function TopStatsPanel({ topDaily, topWeekly }) {
  return (
    <div className="left-column">
      <AppStatsGroup title="Top Today" data={topDaily} />
      <AppStatsGroup title="Top This Week" data={topWeekly} />
    </div>
  );
}