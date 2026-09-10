# token_refresher.py
import os
import time
import threading
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from dashboard_api.push_updates import push_state_update

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]

CREDENTIALS_PATH = "data/credentials.json"
TOKEN_PATH = "data/google_token.json"

CHECK_INTERVAL_SECONDS = 60 * 30  # check every 30 min


def ensure_fresh_token():
    """Check token validity and refresh if needed. Returns True if usable, False if dead."""
    if not os.path.exists(TOKEN_PATH):
        print("[token_refresher] No token file found.")
        push_state_update("google_auth_status", {"status": "missing"})
        return False

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.valid:
        return True

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            print(f"[token_refresher] Refreshed OK at {datetime.now(timezone.utc).isoformat()}")
            push_state_update("google_auth_status", {"status": "ok", "refreshed_at": datetime.now(timezone.utc).isoformat()})
            return True
        except Exception as e:
            print(f"[token_refresher] Refresh FAILED — refresh token is dead: {e}")
            push_state_update("google_auth_status", {"status": "dead", "error": str(e)})
            return False

    print("[token_refresher] Token invalid and no refresh_token present.")
    push_state_update("google_auth_status", {"status": "invalid"})
    return False


def background_loop():
    while True:
        ensure_fresh_token()
        time.sleep(CHECK_INTERVAL_SECONDS)


def start_background_refresher():
    """Call this once at server startup to run refresh checks forever in the background."""
    thread = threading.Thread(target=background_loop, daemon=True)
    thread.start()
    print("[token_refresher] Background refresher started.")


def interactive_reauth():
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    print("[token_refresher] Re-authenticated, new token saved.")


if __name__ == "__main__":
    import sys
    if "--interactive" in sys.argv:
        interactive_reauth()
    else:
        ok = ensure_fresh_token()
        print("Token is usable." if ok else "Token needs interactive reauth.")