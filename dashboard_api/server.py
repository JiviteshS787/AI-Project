from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

import json, os, time
import asyncio

from pydantic import BaseModel
from typing import Optional

from assistant.state import state

from assistant.monitor.usage_tracker import UsageTracker, DEFAULT_LIMITS

from assistant.brain.brain_groq_json import MODEL

from assistant.history import load_history, daily_summary, weekly_summary
from assistant.router import execute
from dashboard_api.push_updates import push_state_update

from assistant.brain.brain_groq_json import KEY_NAME


REMOTE_ALLOWED_ACTIONS = {
    "shutdown_system",
    "restart_system",
    "sleep_system",
    "lock_system",
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

    function = {"action": action, "target": None, "parameters": None}
    push_state_update("last_input", {"last_input": f"[Remote] {action.replace('_', ' ')}"})
    time.sleep(0.4)
    push_state_update("last_interpretation", {"last_interpretation": function})
    execute(function, skip_confirm=True)

    return {"status": "ok", "action": action}
