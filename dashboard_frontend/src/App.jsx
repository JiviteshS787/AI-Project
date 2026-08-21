import { useEffect, useState } from "react";

function App() {
  // Separate full server state from raw event logs
  const [dashboardState, setDashboardState] = useState({last_input: "", last_interpretation: null, stats: {}});
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    // 1. Initial fetch for stats (optional fallback)
    fetch("http://localhost:8000/stats")
      .then((response) => response.json()) // Convert the returned data into JSON format. response -> raw HTTP response (metadata)
      .then((stats) => // Update stats with data
        setDashboardState((prev) => ({ ...prev, stats }))
      )
      .catch(() => {});

    // 2. Connect to WebSocket
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Handle real-time state broadcast from push_state()
      if (data.type === "state") {
        setDashboardState({
          last_input: data.last_input || "",
          last_interpretation: data.last_interpretation || null,
          stats: data.stats || {}
        });
      }

      // Always append to logs history for auditing
      setLogs((prev) => [data, ...prev]);
    };

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onclose = () => console.log("Disconnected");

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif", maxWidth: "900px", margin: "0 auto" }}>
      <h1>Assistant Real-Time Dashboard</h1>

      {/* LIVE STATE DISPLAY */}
      <div style={{ display: "grid", gap: "15px", marginBottom: "30px" }}>
        
        {/* Last Input & Interpretation Card */}
        <div style={{ border: "1px solid #ccc", borderRadius: "8px", padding: "15px", backgroundColor: "#f9f9f9" }}>
          <h3>User Input</h3>
          <p><strong>Input:</strong> {dashboardState.last_input || "No input yet"}</p>
          
          <div>
            <strong>Interpretation:</strong>
            {Array.isArray(dashboardState.last_interpretation) ? (
              <ul>
                {dashboardState.last_interpretation.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: "5px 0" }}>
                {dashboardState.last_interpretation || "None"}
              </p>
            )}
          </div>
        </div>

        {/* System Stats Card */}
        <div style={{ border: "1px solid #ccc", borderRadius: "8px", padding: "15px", backgroundColor: "#f9f9f9" }}>
          <h3>System Metrics & Stats</h3>
          <pre style={{ margin: 0 }}>
            {JSON.stringify(dashboardState.stats, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default App;