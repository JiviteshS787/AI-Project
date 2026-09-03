import os
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from groq import Groq

from assistant.external_clients.gmail_client import fetch_recent_emails as fetch_gmail_emails
from assistant.external_clients.outlook_client import fetch_all_accounts as fetch_outlook_emails
from assistant.external_clients.calendar_client import fetch_todays_events


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BRIEFING_MODEL = "openai/gpt-oss-120b"

SNIPPET_MAX_CHARS = 120
TORONTO_TZ = ZoneInfo("America/Toronto")


def gather_raw_data():
    data = {}

    try:
        data["calendar"] = fetch_todays_events()
    except Exception as e:
        data["calendar"] = []
        print(f"Calendar fetch failed: {e}")

    try:
        data["gmail"] = fetch_gmail_emails()
    except Exception as e:
        data["gmail"] = []
        print(f"Gmail fetch failed: {e}")

    try:
        data["outlook"] = fetch_outlook_emails(["personal"])  # university skipped — pending admin consent
    except Exception as e:
        data["outlook"] = []
        print(f"Outlook fetch failed: {e}")

    return data


def _clean_snippet(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) > SNIPPET_MAX_CHARS:
        text = text[:SNIPPET_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return text


def _short_sender(from_field):
    # "John Smith <john@example.com>" -> "John Smith"
    # "john@example.com" -> "john@example.com"
    match = re.match(r"^(.*?)<.*?>$", from_field.strip())
    return match.group(1).strip().strip('"') if match else from_field.strip()


def _format_gmail_date(raw_date):
    try:
        dt = parsedate_to_datetime(raw_date).astimezone(TORONTO_TZ)
        return dt.strftime("%-I:%M %p")
    except Exception:
        return raw_date


def _format_outlook_date(raw_date):
    try:
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(TORONTO_TZ)
        return dt.strftime("%-I:%M %p")
    except Exception:
        return raw_date


def _format_event_time(raw_start):
    try:
        dt = datetime.fromisoformat(raw_start)
        return dt.strftime("%-I:%M %p")
    except Exception:
        return raw_start  # all-day events are just a date string


def format_calendar(events):
    if not events:
        return ""
    lines = []
    for e in events:
        time_str = _format_event_time(e["start"])
        line = f"- {time_str} | {e['summary']}"
        if e.get("location"):
            line += f" | {e['location']}"
        if e.get("description"):
            line += f" | {_clean_snippet(e['description'])}"
        lines.append(line)
    return "\n".join(lines)


def format_gmail(emails):
    if not emails:
        return ""
    lines = []
    for e in emails:
        time_str = _format_gmail_date(e["date"])
        sender = _short_sender(e["from"])
        snippet = _clean_snippet(e["snippet"])
        lines.append(f"- {time_str} | {sender} | {e['subject']} | {snippet}")
    return "\n".join(lines)


def format_outlook(emails):
    if not emails:
        return ""
    lines = []
    for e in emails:
        time_str = _format_outlook_date(e["date"])
        sender = _short_sender(e["from"])
        snippet = _clean_snippet(e["snippet"])
        lines.append(f"- {time_str} | {sender} | {e['subject']} | {snippet}")
    return "\n".join(lines)


def build_prompt(data):
    calendar_block = format_calendar(data["calendar"]) or "(none)"
    gmail_block = format_gmail(data["gmail"]) or "(none)"
    outlook_block = format_outlook(data["outlook"]) or "(none)"

    return f"""You are summarizing today's schedule and inbox for a daily briefing.

CALENDAR EVENTS TODAY:
{calendar_block}

GMAIL (unread, primary inbox):
{gmail_block}

OUTLOOK (unread, personal account):
{outlook_block}

Write a concise, well-organized daily briefing.
Use your judgment on what's most important to surface first (e.g. urgent emails, upcoming events, anything time-sensitive).
Keep it natural and readable, not a raw data dump. If a category is empty, skip mentioning it rather than saying "no events."
"""


def generate_briefing():
    data = gather_raw_data()
    prompt = build_prompt(data)

    response = client.chat.completions.create(
        model=BRIEFING_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    print(generate_briefing())