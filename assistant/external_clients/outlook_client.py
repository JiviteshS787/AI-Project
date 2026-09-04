import os
import json
import msal
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CLIENT_ID = "fcc2a8c5-20d8-4f4b-83fb-033f4d2ff8a9"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Mail.Read"]

TOKEN_DIR = "data"


def _token_path(account_label):
    return os.path.join(TOKEN_DIR, f"outlook_token_{account_label}.json")


def get_outlook_token(account_label):
    token_path = _token_path(account_label)

    cache = msal.SerializableTokenCache()
    if os.path.exists(token_path) and os.path.getsize(token_path) > 0:
        cache.deserialize(open(token_path, "r").read())

    app = msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise Exception(f"Device flow failed to start: {flow.get('error')}: {flow.get('error_description')}")
        print(flow["message"])  # prints code + URL to enter it
        result = app.acquire_token_by_device_flow(flow)

    if cache.has_state_changed:
        with open(token_path, "w") as f:
            f.write(cache.serialize())

    if "access_token" not in result:
        raise Exception(f"Auth failed for {account_label}: {result.get('error_description')}")

    return result["access_token"]


def fetch_recent_emails(account_label, max_results=10):
    token = get_outlook_token(account_label)
    headers = {"Authorization": f"Bearer {token}"}

    toronto_tz = ZoneInfo("America/Toronto")
    now_local = datetime.now(toronto_tz)
    start_of_week_local = (now_local - timedelta(days=now_local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_of_week_utc = start_of_week_local.astimezone(ZoneInfo("UTC"))
    start_of_week_str = start_of_week_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        "https://graph.microsoft.com/v1.0/me/messages"
        f"?$top={max_results}"
        f"&$filter=receivedDateTime ge {start_of_week_str} and isRead eq false"
        "&$select=subject,from,receivedDateTime,bodyPreview,isRead"
        "&$orderby=receivedDateTime desc"
    )

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    emails = []
    for msg in data.get("value", []):
        emails.append({
            "id": msg.get("id"),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            "subject": msg.get("subject", ""),
            "date": msg.get("receivedDateTime", ""),
            "snippet": msg.get("bodyPreview", ""),
            "unread": not msg.get("isRead", True),
            "account": account_label
        })

    return emails


def fetch_all_accounts(account_labels, max_results=20):
    all_emails = []
    for label in account_labels:
        all_emails.extend(fetch_recent_emails(label, max_results))
    return all_emails


if __name__ == "__main__":
    emails = fetch_all_accounts(["personal"])
    #emails = fetch_all_accounts(["personal", "school"])
    for e in emails:
        print(f"[{e['account']}] [{'UNREAD' if e['unread'] else 'read'}] {e['from']} — {e['subject']}")