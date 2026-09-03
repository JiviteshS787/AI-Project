from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi import Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse

from datetime import datetime

import json, os, time
import asyncio

from pydantic import BaseModel
from typing import Optional

from markupsafe import escape

from assistant.state import state

from assistant.monitor.usage_tracker import UsageTracker, DEFAULT_LIMITS

from assistant.brain.brain_groq_json import MODEL

from assistant.history import load_history, daily_summary, weekly_summary
from assistant.router import execute
from dashboard_api.push_updates import push_state_update

from assistant.external_clients.daily_briefing import generate_briefing

from assistant.brain.brain_groq_json import KEY_NAME

SERVER_START_TIME = time.time()


REMOTE_ALLOWED_ACTIONS = {
    "shutdown_system",
    "restart_system",
    "sleep_system",
    "lock_system",
    "set_clipboard"
}

API_KEY_NAMES = ["GROQ_API_KEY", "GROQ_API_KEY_2"]

REMOTE_SECRET = os.environ["REMOTE_KEY"]


########## Handle Lifespan ##########
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on server startup
    state["stats"] = get_formatted_stats()
    state["history"] = get_history()
    state["weekly_stats"] = get_weekly_stats()
    state["daily_summary"] = get_daily_summary()
    state["weekly_summary"] = get_weekly_summary()
    state["aliases"] = None
    state["last_input"] = None
    state["last_interpretation"] = None
    state["last_alias_update"] = None
    state["active_key"] = KEY_NAME

    task = asyncio.create_task(periodic_stats_refresh())

    yield

    # Code after yield runs on server shutdown (if needed)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


########## Initialize App ##########
app = FastAPI(lifespan=lifespan)

#React connection enabler
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

logs = []
clients = []


########## Classes ##########
class Event(BaseModel):
    type: str
    source: Optional[str] = None   # app/system that generated it
    message: Optional[str] = None
    data: Optional[dict] = None
    severity: Optional[str] = "info"
    timestamp: Optional[str] = None



########## Methods ##########

BACKGROUND_CHECK_INTERVAL = 5 #seconds
async def periodic_stats_refresh():
    while True:
        await asyncio.sleep(BACKGROUND_CHECK_INTERVAL)
        tracker.reload()
        state["stats"] = get_formatted_stats()
        state["weekly_stats"] = get_weekly_stats()
        await broadcast({
            "type": "state",
            **{k: v for k, v in state.items() if k not in ("aliases", "last_alias_update")}
        })


def classify(event: Event):
    if event.message and "error" in event.message.lower():
        event.severity = "error"
    elif "login" in event.type:
        event.severity = "info"
    return event


async def push_state():
    await broadcast({"type": "state", **state})


async def broadcast(payload: dict):
    for ws in clients[:]:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            clients.remove(ws)


tracker = UsageTracker()
def get_formatted_stats() -> dict:
    tracker.reload()
    tracker.reset_if_needed()

    stats = {}

    if MODEL in DEFAULT_LIMITS or any(
        m.startswith(f"{MODEL}::") for m in tracker.tracked_models()
    ):
        stats[MODEL] = {}
        for key_id in API_KEY_NAMES:
            snap = tracker.snapshot(MODEL, key_id)
            stats[MODEL][key_id] = {
                "rpm_used": snap["rpm"][0],
                "rpm_limit": snap["rpm"][1],
                "rpd_used": snap["rpd"][0],
                "rpd_limit": snap["rpd"][1],
                "tpm_used": snap["tpm"][0],
                "tpm_limit": snap["tpm"][1],
                "tpd_used": snap["tpd"][0],
                "tpd_limit": snap["tpd"][1],
            }

    return stats


def get_weekly_stats() -> dict:
    tracker.reload()
    tracker.reset_if_needed()

    weekly_stats = {}

    if MODEL in DEFAULT_LIMITS or any(
        m.startswith(f"{MODEL}::") for m in tracker.tracked_models()
    ):
        weekly_stats[MODEL] = {}
        for key_id in API_KEY_NAMES:
            snap = tracker.snapshot(MODEL, key_id)
            weekly_stats[MODEL][key_id] = {
                "weekly_tokens": snap["weekly_tokens"],
                "weekly_calls": snap["weekly_calls"],
            }

    return weekly_stats


def get_history():
    return load_history()


def get_weekly_summary():
    return weekly_summary()


def get_daily_summary():
    return daily_summary()



########## Endpoints ##########

@app.get("/")
def home():
    return {"status": "dashboard running"}


@app.get("/logs")
def get_logs(): 
    return {"status": logs}




#######################################
#            Status View              #
#######################################
@app.get("/status/data")
def get_status_data(x_remote_secret: str = Header(None)):
    if x_remote_secret != REMOTE_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    uptime_seconds = int(time.time() - SERVER_START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {"uptime": f"{hours:02}:{minutes:02}:{seconds:02}"}


@app.get("/status/view", response_class=HTMLResponse)
def status_view(secret: str = ""):
    if secret != REMOTE_SECRET:
        return HTMLResponse("<h1>Unauthorized</h1>", status_code=401)

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Laptop Status</title>
        <style>
            body {{
                background: #0d0d0d;
                color: #e0e0e0;
                font-family: -apple-system, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }}
            .dot {{
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #2ecc71;
                margin-bottom: 20px;
                box-shadow: 0 0 12px #2ecc71;
            }}
            h1 {{ font-weight: 300; letter-spacing: 1px; margin: 0 0 10px; }}
            #uptime {{ font-size: 48px; font-weight: 200; letter-spacing: 2px; }}
        </style>
    </head>
    <body>
        <div class="dot"></div>
        <h1>Laptop Online</h1>
        <div id="uptime">--:--:--</div>

        <script>
            const secret = "{secret}";
            async function updateUptime() {{
                try {{
                    const res = await fetch("/status/data", {{
                        headers: {{ "X-Remote-Secret": secret }}
                    }});
                    const data = await res.json();
                    document.getElementById("uptime").textContent = data.uptime;
                }} catch (e) {{
                    document.getElementById("uptime").textContent = "offline";
                }}
            }}
            updateUptime();
            setInterval(updateUptime, 1000);
        </script>
    </body>
    </html>
    """


#######################################
#           Briefing View             #
#######################################
@app.get("/briefing", response_class=PlainTextResponse)
def get_briefing(x_remote_secret: str = Header(None)):
    if x_remote_secret != REMOTE_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        summary = generate_briefing()
        return summary
    except Exception as e:
        return f"Briefing generation failed: {e}"


@app.get("/briefing/view", response_class=HTMLResponse)
def briefing_view(secret: str = ""):
    if secret != REMOTE_SECRET:
        return HTMLResponse("<h1>Unauthorized</h1>", status_code=401)

    try:
        summary_markdown = generate_briefing()
    except Exception as e:
        summary_markdown = f"Briefing generation failed: {e}"

    safe_json = json.dumps(summary_markdown)

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Briefing</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.2/marked.min.js"></script>
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                background: #0a0a0c;
                color: #e8e8ea;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
            }}

            .header {{
                position: sticky;
                top: 0;
                background: linear-gradient(180deg, #0a0a0c 80%, transparent);
                padding: 24px 20px 16px;
                z-index: 10;
            }}

            .header .date {{
                color: #7a7a82;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                margin-bottom: 4px;
            }}

            .header h1 {{
                font-size: 26px;
                font-weight: 650;
                margin: 0;
                letter-spacing: -0.4px;
            }}

            #content {{
                padding: 4px 16px 60px;
            }}

            /* Card wrapper for each section */
            #content h2, #content h3 {{
                font-size: 15px;
                font-weight: 650;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                color: #9a9aa5;
                margin: 28px 4px 10px;
            }}

            #content h2:first-child {{ margin-top: 4px; }}

            /* Turn tables into stacked cards instead of horizontal tables */
            table {{
                width: 100%;
                border-collapse: collapse;
                display: block;
            }}

            thead {{ display: none; }}

            table, tbody, tr {{ display: block; width: 100%; }}

            tr {{
                background: #16161a;
                border-radius: 14px;
                margin-bottom: 10px;
                padding: 14px 16px;
                border: 1px solid #232328;
            }}

            td {{
                display: block;
                padding: 2px 0;
                border: none;
            }}

            td:first-child {{
                font-size: 12px;
                color: #7a7a82;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.4px;
                margin-bottom: 2px;
            }}

            td:last-child {{
                font-size: 15px;
                color: #e8e8ea;
                line-height: 1.4;
            }}

            p {{
                font-size: 15px;
                line-height: 1.6;
                color: #d0d0d5;
                margin: 8px 4px 16px;
            }}

            ul, ol {{
                margin: 8px 4px 16px;
                padding-left: 20px;
            }}

            li {{
                font-size: 15px;
                line-height: 1.7;
                color: #d0d0d5;
                margin-bottom: 6px;
            }}

            strong {{ color: #fff; font-weight: 650; }}

            a {{ color: #5aa9ff; text-decoration: none; }}

            hr {{
                border: none;
                border-top: 1px solid #1e1e22;
                margin: 8px 4px 8px;
            }}

            .loading {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 80px 20px;
                color: #6a6a72;
                font-size: 14px;
            }}

            .spinner {{
                width: 24px;
                height: 24px;
                border: 2.5px solid #232328;
                border-top-color: #5aa9ff;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin-bottom: 14px;
            }}

            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="date" id="today"></div>
            <h1>Daily Briefing</h1>
        </div>
        <div id="content">
            <div class="loading">
                <div class="spinner"></div>
                Loading your briefing...
            </div>
        </div>

        <script>
            document.getElementById("today").textContent = new Date().toLocaleDateString('en-US', {{
                weekday: 'long', month: 'long', day: 'numeric'
            }});

            const raw = {safe_json};
            document.getElementById("content").innerHTML = marked.parse(raw);
        </script>
    </body>
    </html>
    """


@app.get("/stats")
def get_stats():
    return state["stats"]


@app.get("/weekly-stats")
def get_wstats():
    return state["weekly_stats"]


# REST endpoint
@app.post("/event")
async def receive_event(event: Event):
    event = classify(event)

    # merge incoming data into server's state
    if event.type == "last_input":
        state["last_input"] = event.data.get("last_input")

    elif event.type == "last_interpretation":
        state["last_interpretation"] = event.data.get("last_interpretation")

    elif event.type == "stats":
        model = event.data.get("model")
        key_id = event.data.get("key_id")
        stats = event.data.get("stats")
        if model and stats is not None:
            state["stats"].setdefault(model, {})[key_id] = stats

    elif event.type == "active_key":
        active_key = event.data.get("active_key")
        state["active_key"] = active_key

    elif event.type == "weekly_stats":
        model = event.data.get("model")
        key_id = event.data.get("key_id")
        weekly_stats = event.data.get("weekly_stats")
        if model and weekly_stats is not None:
            state["weekly_stats"].setdefault(model, {})[key_id] = weekly_stats

    elif event.type == "aliases":
        state["aliases"] = event.data.get("aliases", {})
        state["last_alias_update"] = event.data.get("last_alias_update")
        
    elif event.type == "history":
        state["history"] = event.data.get("history", [])

    elif event.type == "daily_summary":
        state["daily_summary"] = event.data.get("daily_summary", {})
    
    elif event.type == "weekly_summary":
        state["weekly_summary"] = event.data.get("weekly_summary", {})

    payload = event.model_dump()
    payload["time"] = datetime.now().isoformat()
    logs.append(payload)

    await push_state()  # broadcast the updated, merged state
    return {"status": "ok"}


# WebSocket endpoint (React connects here)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    initial_state = {k: v for k, v in state.items() if k not in ("aliases", "last_alias_update")}
    try:
        await websocket.send_text(json.dumps({"type": "state", **initial_state}))
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)



########## Remote Endpoint ##########
@app.post("/command")
async def remote_command(payload: dict = Body(...)):
    if payload.get("secret") != REMOTE_SECRET:
        return {"status": "unauthorized"}

    action = payload.get("action")

    if action not in REMOTE_ALLOWED_ACTIONS:
        return {"status": "rejected", "reason": f"'{action}' not allowed remotely"}

    function = {
        "action": action,
        "target": payload.get("target"),
        "parameters": payload.get("parameters") or {},
    }

    print(f"{function}")

    push_state_update("last_input", {"last_input": f"[Remote] {action.replace('_', ' ')}"})
    time.sleep(0.4)
    push_state_update("last_interpretation", {"last_interpretation": function})
    execute(function, skip_confirm=True)

    return {"status": "ok", "action": action}
