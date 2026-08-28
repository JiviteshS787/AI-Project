
export function HistoryFormatting({data, historyPanelRef}){
    return(
        <div className="history-container">
            <h3 className="panel-title">Today's History</h3>
            <div className="history-panel" ref={historyPanelRef}>
            {(() => {
                const now = new Date();
                const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
                const todaysCommands = data.filter(
                    (cmd) => cmd.time?.slice(0, 10) === today
                );
                return todaysCommands.length === 0 ? (
                <p className="empty-note">No history found</p>
                ) : (
                todaysCommands.map((cmd, i) => (
                    <div key={i} className="history-entry">
                    <span className="history-time">{cmd.time?.slice(11, 16)}</span>
                    <span className="history-action">{cmd.action}</span>
                    <span className="history-target">{cmd.target}</span>
                    {cmd.parameters && Object.keys(cmd.parameters).length > 0 && (
                    <div className="history-params">
                        {Object.entries(cmd.parameters).map(([k, v]) => (
                        <span key={k} className="history-param">{k}: {String(v)}</span>
                        ))}
                    </div>
                    )}
                    </div>
                ))
                );
            })()}
            </div>
        </div>
    )
}



export default function AppHistory({history, panelRef}){
    return(
        <HistoryFormatting 
            data={history}
            historyPanelRef={panelRef}
        />
    )
}

