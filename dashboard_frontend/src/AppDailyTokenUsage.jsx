const METRICS = [
    { key: "tpm", label: "Tokens / Min" },
    { key: "tpd", label: "Tokens / Day" },
    { key: "rpm", label: "Requests / Min" },
    { key: "rpd", label: "Requests / Day" }
];


export function ProgressFormatting({data}){
    return(
        <div>
            {Object.entries(data).map(([model, modelStats]) => (
                <div key={model} className="stats-card">
                    <h3 className="stats-model">{model}</h3>
                    {METRICS.map(({ key, label }) => {
                        const used = modelStats[`${key}_used`];
                        const limit = modelStats[`${key}_limit`];
                        if (used === undefined || limit === undefined || limit === 0) {
                            return null;
                        }
                        const pct = Math.min((used / limit) * 100, 100);
                        return (
                        <div className="stat-row" key={key}>
                                <div className="stat-label">
                                    <span>{label}</span>
                                    <span>
                                        {used.toLocaleString()} / {limit.toLocaleString()}
                                    </span>
                                </div>

                                <div className="progress-track">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${pct}%` }}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            ))}
        </div>
    )
}


export default function DailyTokenUsage({stats}){
    return(
        <div className="stats">
            <ProgressFormatting data={stats}/>
        </div>
    )
}