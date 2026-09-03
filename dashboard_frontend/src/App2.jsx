import { useEffect, useState, useRef } from "react";
import TopStatsPanel from "./AppUsagePanel";
import WeeklyTokenUsage from "./AppWeeklyTokenUsage";
import DailyTokenUsage from "./AppDailyTokenUsage";
import AppAliasVisibility from "./AppAliasVisibility";
import AppHistory from "./AppHistory";

import "./App.css";

function App() {
  const [dashboardState, setDashboardState] = useState({
    last_input: "",
    last_interpretation: null,
    stats: {},
    weekly_stats: {},
    aliases: null,
    last_alias_update: null,
    history: null,
    daily_summary: {},
    weekly_summary: {},
    active_key: null
  });

  const [messages, setMessages] = useState([]);

  const prevInputRef = useRef("");
  const prevInterpretationRef = useRef(null);

  const [aliasesVisible, setAliasesVisible] = useState(false);
  const aliasesTimerRef = useRef(null);
  const prevAliasesRef = useRef(null);
  const prevAliasCommandRef = useRef(null);

  const chatContainerRef = useRef(null);
  const historyPanelRef = useRef(null);
  const chatAutoScrollRef = useRef(true);
  const historyAutoScrollRef = useRef(true);

  const MODEL = "openai/gpt-oss-20b";

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

    fetch("http://localhost:8000/weekly_stats")
      .then((response) => response.json())
      .then((weekly_stats) =>
        setDashboardState((prev) => ({ ...prev, weekly_stats }))
      )
      .catch(() => {});
    
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "state") {
        setDashboardState((prev) => ({ ...prev, ...data }));

        if (data.last_input && data.last_input !== prevInputRef.current) {
          prevInputRef.current = data.last_input;
          setMessages((prev) => [
            ...prev,
            { type: "user", text: data.last_input, id: Date.now() }
          ].slice(-messageLimit)
        );
        }

        if (data.last_alias_update && data.last_alias_update !== prevAliasCommandRef.current) {
          prevAliasCommandRef.current = data.last_alias_update;
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
            stats={
              dashboardState.stats?.[MODEL]?.[dashboardState.active_key]
                ? { [MODEL]: dashboardState.stats[MODEL][dashboardState.active_key] }
                : {}
            }
          />

          {dashboardState.aliases !== null && aliasesVisible && (
            <AppAliasVisibility
              aliases={dashboardState.aliases}
            />
          )}

          {dashboardState.history !== null && (
            <AppHistory
              history={dashboardState.history}
              panelRef={historyPanelRef}
            />
          )}

          
          
        </div>

        <WeeklyTokenUsage 
          weekly_usage={
            dashboardState.weekly_stats?.[MODEL]?.[dashboardState.active_key]
              ? { [MODEL]: dashboardState.weekly_stats[MODEL][dashboardState.active_key] }
              : {}
          }
        />
        
      </div>
    </div>
  );
}

export default App;
