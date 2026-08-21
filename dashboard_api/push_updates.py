import requests
import threading

DASHBOARD_URL = "http://localhost:8000"

def _send_post(event_type: str, data: dict):
    try:
        with requests.Session() as session:
            session.post(
                f"{DASHBOARD_URL}/event",
                json={"type": event_type, "data": data},
                headers={"Connection": "close"},  # Force connection termination
                timeout=1.0
            )
    except requests.RequestException as e:
        print("Failed to push state:", e)

def push_state_update(event_type: str, data: dict):
    # Spawn in background so main loop never waits for HTTP response
    threading.Thread(target=_send_post, args=(event_type, data), daemon=True).start()