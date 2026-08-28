const WEEKLY_METRICS = [
    { key: "weekly_tokens", label: "Weekly Token Usage"},
    { key: "weekly_calls", label: "Weekly API Calls"}
];

function StatFormatting({data}){
   return(
    <div className="weekly-panel">
        {Object.entries(data).map(([model, weekly]) => {
            const weekly_tokens = weekly.weekly_tokens;
            const weekly_calls = weekly.weekly_calls;

            const avgTokensPerCall = weekly_tokens !== undefined && weekly_calls !== undefined && weekly_calls !== 0
             ? weekly_tokens / weekly_calls : null;

            return(
                <div key={model} className="weekly-card">
                    <h3 className="weekly-model">{model}</h3>
                    {WEEKLY_METRICS.map(({ key, label }) => {
                        const value = weekly[key];
                        if (value === undefined) {
                            return null;
                        }
                        return (
                            <div className="weekly-row" key={key}>
                                <span className="weekly-label">{label}</span>
                                <span className="weekly-value">{value.toLocaleString()}</span>
                            </div>
                            );
                        })}
                    {avgTokensPerCall !== null && (
                        <div className="weekly-row">
                            <span className="weekly-label">Avg Tokens / Call</span>
                            <span className="weekly-value"> {avgTokensPerCall.toFixed(2)}</span>
                        </div>
                    )}
                </div>
            );
        })}
    </div>
    );
}

export default function WeeklyTokenUsage({weekly_usage}){
    return (
        <div className="right-column">
            <StatFormatting data={weekly_usage}/>
        </div>
    );
}