from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

from pydantic import BaseModel
from typing import Optional


app = FastAPI()

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

def classify(event: Event):
    if "error" in event.message.lower():
        event.severity = "error"
    elif "login" in event.type:
        event.severity = "info"
    return event



########## Endpoints ##########

@app.get("/")
def home():
    return {"status": "dashboard running"}


# REST endpoint
@app.post("/event")
async def receive_event(event: Event):
    event["time"] = datetime.now().isoformat()

    event = classify(event)
    
    logs.append(event)

    # push to all connected React clients
    for ws in clients[:]:
        try:
            await ws.send_text(json.dumps(event))
        except Exception:
            clients.remove(ws)
    return {"status": "ok"}


# WebSocket endpoint (React connects here)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)