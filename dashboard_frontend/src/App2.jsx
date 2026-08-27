import { useEffect, useState, useRef } from "react";
import TopStatsPanel from "./AppUsagePanel";
import WeeklyTokenUsage from "./AppWeeklyTokenUsage";
import DailyTokenUsage from "./AppDailyTokenUsage";
import AppAliasVisibility from "./AppAliasVisibility";

import "./App.css";

function App() {
  const [dashboardState, setDashboardState] = useState({
    last_input: "",
    last_interpretation: null,
    stats: {},
    weekly_stats: {},
    aliases: null,
    history: null,
    daily_summary: {},
    weekly_summary: {}
  });

  const [messages, setMessages] = useState([]);

  const prevInputRef = useRef("");
  const prevInterpretationRef = useRef(null);

  const [aliasesVisible, setAliasesVisible] = useState(false);
  const aliasesTimerRef = useRef(null);
  const prevAliasesRef = useRef(null);

  const chatContainerRef = useRef(null);
  const historyPanelRef = useRef(null);
  const chatAutoScrollRef = useRef(true);
  const historyAutoScrollRef = useRef(true);

  const messageLimit = 20

  const isNearBottom = (el, threshold = 80) => {
      return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  };

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
          ].slice(-messageLimit)
        );
        }

        if (data.aliases !== null && data.aliases !== undefined &&
            JSON.stringify(data.aliases) !== JSON.stringify(prevAliasesRef.current)) {
              prevAliasesRef.current = data.aliases;
              setAliasesVisible(true);
              clearTimeout(aliasesTimerRef.current);
              aliasesTimerRef.current = setTimeout(() => setAliasesVisible(false), 7000);
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
              ].slice(-messageLimit)
            );
            }, i * 400);
          });
        }
      }
    };

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onclose = () => console.log("Disconnected");

    const chatEl = chatContainerRef.current;
    const historyEl = historyPanelRef.current;

    const handleChatScroll = () => {
      if (chatEl) chatAutoScrollRef.current = isNearBottom(chatEl);
    };

    const handleHistoryScroll = () => {
      if (historyEl) historyAutoScrollRef.current = isNearBottom(historyEl);
    };

    chatEl?.addEventListener("scroll", handleChatScroll);
    historyEl?.addEventListener("scroll", handleHistoryScroll);

    return () => {
      ws.close();
      chatEl?.removeEventListener("scroll", handleChatScroll);
      historyEl?.removeEventListener("scroll", handleHistoryScroll);
    };
    
  }, []);


  useEffect(() => {
    if (chatAutoScrollRef.current && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (historyAutoScrollRef.current && historyPanelRef.current) {
      historyPanelRef.current.scrollTop = historyPanelRef.current.scrollHeight;
    }
  }, [dashboardState.history]);


  const METRICS = [
    { key: "tpm", label: "Tokens / Min" },
    { key: "tpd", label: "Tokens / Day" },
    { key: "rpm", label: "Requests / Min" },
    { key: "rpd", label: "Requests / Day" }
  ];


  return (
    <div className="app">
      <h1 className="title">AI Dashboard</h1>
      <div className="dashboard">
        <TopStatsPanel
          topDaily={dashboardState.daily_summary}
          topWeekly={dashboardState.weekly_summary}
        />

        <div className="middle-column">
          <div className="chat-container" ref={chatContainerRef}>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`bubble ${msg.type === "user" ? "user" : "ai"}`}
              >
                {msg.text}
              </div>
            ))}
          </div>

          <DailyTokenUsage 
            stats={dashboardState.stats}
          />

          {dashboardState.aliases !== null && aliasesVisible && (
            <AppAliasVisibility
              aliases={dashboardState.aliases}
            />

          )}

          
          {dashboardState.history !== null && (
            <div className="history-container">
              <h3 className="panel-title">Today's History</h3>
              <div className="history-panel" ref={historyPanelRef}>
                {(() => {
                  const now = new Date();
                  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
                  const todaysCommands = dashboardState.history.filter(
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
          )}
        </div>

        <WeeklyTokenUsage 
          weekly_usage = {dashboardState.weekly_stats}
        />
        
      </div>
    </div>
  );
}

export default App;


/*
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
*/

/*
{dashboardState.aliases !== null && aliasesVisible && (
            <div className="aliases-panel">
              <h3 className="panel-title">Aliases</h3>
              {Object.keys(dashboardState.aliases).length === 0 ? (
                <p className="empty-note">No aliases created</p>
              ) : (
                <ul className="alias-list">
                  {Object.entries(dashboardState.aliases).map(([alias, commands]) => (
                    <li key={alias} className="alias-item">
                      <span className="alias-name">
                        {alias.charAt(0).toUpperCase() + alias.slice(1)}
                      </span>
                      <span className="alias-arrow">→</span>
                      <span className="alias-targets">
                        {commands
                          .map((cmd) =>
                            cmd.target.charAt(0).toUpperCase() + cmd.target.slice(1)
                          )
                          .join(", ")}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
*/