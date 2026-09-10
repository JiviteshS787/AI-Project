from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os

TOKEN_PATH = "data/google_token.json"
CREDENTIALS_PATH = "data/credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]


def get_calendar_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def fetch_todays_events():
    service = get_calendar_service()

    toronto_tz = ZoneInfo("America/Toronto")
    now_local = datetime.now(toronto_tz)
    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    parsed_events = []
    for event in events:
        is_all_day = "date" in event["start"] and "dateTime" not in event["start"]
        start = event["start"].get("dateTime", event["start"].get("date"))

        if not is_all_day:
            start_dt = datetime.fromisoformat(start)
            if start_dt < now_local:
                continue

        parsed_events.append({
            "id": event["id"],
            "summary": event.get("summary", "(No title)"),
            "start": start,
            "location": event.get("location", ""),
            "description": event.get("description", "")
        })

    return parsed_events

 
if __name__ == "__main__":
    events = fetch_todays_events()
    for e in events:
        print(f"{e['start']} — {e['summary']}")