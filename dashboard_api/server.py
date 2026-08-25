from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

import json
import asyncio

from pydantic import BaseModel
from typing import Optional

from assistant.state import state

from assistant.monitor.usage_tracker import UsageTracker, DEFAULT_LIMITS

from assistant.brain.brain_groq_json import MODEL

from assistant.history import load_history


########## Handle Lifespan ##########
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on server startup
    state["stats"] = get_formatted_stats()

    state["history"] = get_history()

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
        tracker.reload()  # re-read .groq_usage.json from disk, then prune stale entries
        state["stats"] = get_formatted_stats()
        await push_state()


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

    # Check if the active MODEL is tracked or in fallback defaults
    if MODEL in tracker.tracked_models() or MODEL in DEFAULT_LIMITS:
        snap = tracker.snapshot(MODEL)
        stats[MODEL] = {
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


def get_history():
    return load_history()

########## Endpoints ##########

@app.get("/")
def home():
    return {"status": "dashboard running"}


@app.get("/stats")
def get_stats():
    return state["stats"]


@app.on_event("startup")
async def startup_event():
    state["stats"] = get_formatted_stats()


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
        stats = event.data.get("stats")
        if model and stats is not None:
            state["stats"][model] = stats
    elif event.type == "aliases":
        state["aliases"] = event.data.get("aliases", {})
    elif event.type == "history":
        state["history"] = event.data.get("history", [])

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

    try:
        await websocket.send_text(json.dumps({"type": "state", **state}))
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)