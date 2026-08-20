import { useEffect, useState } from "react";


function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [data, ...prev]); // prepend newest
    };

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onclose = () => console.log("Disconnected");

    return () => ws.close();
  }, []);

  return (
    <div>
      <h1>Live Dashboard</h1>
      {events.map((e, i) => (
        <div key={i}>
          <pre>{JSON.stringify(e, null, 2)}</pre>
        </div>
      ))}
    </div>
  );
}

export default App;