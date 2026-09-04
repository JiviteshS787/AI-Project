import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]

CREDENTIALS_PATH = "data/credentials.json"
TOKEN_PATH = "data/google_token.json"


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def fetch_recent_emails(read="unread", category="primary", where = "inbox", max_results=10):
    service = get_gmail_service()

    toronto_tz = ZoneInfo("America/Toronto")
    now_local = datetime.now(toronto_tz)
    start_of_week_local = (now_local - timedelta(days=now_local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    after_str = start_of_week_local.strftime("%Y/%m/%d")

    category_tab = f"category:{category.lower()}"
    filter_read = f"is:{read.lower()}"
    tab = f"in:{where.lower()}"

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
        q=f"after:{after_str} {category_tab} {tab} {filter_read}"
    ).execute()

    message_refs = results.get("messages", [])

    emails = []
    for ref in message_refs:
        msg = service.users().messages().get(
            userId="me",
            id=ref["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        snippet = msg.get("snippet", "")

        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": snippet,
            "unread": "UNREAD" in msg.get("labelIds", [])
        })

    return emails


if __name__ == "__main__":
    emails = fetch_recent_emails()
    for e in emails:
        print(f"[{'UNREAD' if e['unread'] else 'read'}] {e['from']} — {e['subject']}")