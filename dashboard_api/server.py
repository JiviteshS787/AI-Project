from fastapi import FastAPI

from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# simple in-memory log (we’ll upgrade later)
logs = []

@app.get("/")
def home():
    return {"status": "assistant dashboard running"}

@app.get("/logs")
def get_logs():
    return logs

class Event(BaseModel):
    type: str
    data: dict

@app.post("/event")
def receive_event(event: Event):
    logs.append({
        "time": datetime.now().isoformat(),
        "type": event.type,
        "data": event.data
    })
    return {"status": "ok"}