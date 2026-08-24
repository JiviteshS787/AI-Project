import { useEffect, useState, useRef } from "react";
import "./App.css";

function App() {
  const [dashboardState, setDashboardState] = useState({
    last_input: "",
    last_interpretation: null,
    stats: {}
  });
  const [messages, setMessages] = useState([]);

  const prevInputRef = useRef("");
  const prevInterpretationRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:8000/stats")
      .then((response) => response.json())
      .then((stats) =>
        setDashboardState((prev) => ({ ...prev, stats }))
      )
      .catch(() => {});

    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "state") {
        setDashboardState(data);

        if (data.last_input && data.last_input !== prevInputRef.current) {
          prevInputRef.current = data.last_input;
          setMessages((prev) => [
            ...prev,
            { type: "user", text: data.last_input, id: Date.now() }
          ]);
        }

        if (
          Array.isArray(data.last_interpretation) &&
          data.last_interpretation !== prevInterpretationRef.current &&
          JSON.stringify(data.last_interpretation) !==
            JSON.stringify(prevInterpretationRef.current)
        ) {
          prevInterpretationRef.current = data.last_interpretation;
          data.last_interpretation.forEach((msg, i) => {
            setTimeout(() => {
              setMessages((prev) => [
                ...prev,
                { type: "ai", text: msg, id: Date.now() + i }
              ]);
            }, i * 400);
          });
        }
      }
    };

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onclose = () => console.log("Disconnected");

    return () => ws.close();
  }, []);

  // Metrics to render per model, in display order
  const METRICS = [
    { key: "tpm", label: "Tokens / Min" },
    { key: "tpd", label: "Tokens / Day" },
    { key: "rpm", label: "Requests / Min" },
    { key: "rpd", label: "Requests / Day" }
  ];

  return (
    <div className="app">
      <h1 className="title">AI Dashboard</h1>
      <div className="chat-container">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`bubble ${msg.type === "user" ? "user" : "ai"}`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="stats">
        {Object.entries(dashboardState.stats).map(([model, modelStats]) => (
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
    </div>
  );
}

export default App;