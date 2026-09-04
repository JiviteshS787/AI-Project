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

    return f"""You are writing a daily briefing formatted as Markdown, to be rendered as styled cards using Markdown tables.

    CALENDAR EVENTS TODAY:
    {calendar_block}

    GMAIL (unread, primary inbox):
    {gmail_block}

    OUTLOOK (unread, personal account):
    {outlook_block}

    Write a well-organized daily briefing using your judgment on what's most important. Use this structure as a guide:

    ## 📅 Today's Schedule (All Times Eastern – UTC-4)
    A 2-column Markdown table:
    | | |
    |---|---|
    | HH:MM | **Short action title** – one plain-text sentence description. |
    Use "ALL-DAY" instead of a time for all-day items. Omit this section if calendar data is "(none)".

    ## ✉️ Priority (Require Quick Attention)
    Pull from BOTH Gmail and Outlook. Include only emails that are genuinely time-sensitive or need action — security alerts, deadlines, direct asks. Tag each row with its source. 2-column table:
    | [Gmail/Outlook] Sender (Day DD Mon HH:MM timezone) | *"Subject line"* – why it matters or what to do. |
    Omit this section entirely if nothing qualifies as priority — don't include an empty or placeholder row.

    ## 💼 Job Search
    Optional section. If either inbox has job application confirmations, recruiter emails, or job alert/posting emails, group them here as a 2-column Markdown table, tagged with source:
    | [Gmail/Outlook] Sender (Day DD Mon HH:MM timezone) | *"Subject line"* – one short note. |
    Omit this section if there's nothing job-related.

    ## 📬 Other Notable Messages (Worth a Glance)
    Everything else from Gmail and Outlook not already used above — promotions, newsletters, FYIs — as a bullet list, tagged with source, same format as Job Search. Omit if empty.

    ## ✅ Quick Action Checklist
    A numbered list distilling the actionable items above into concrete steps, in a sensible order. End with one short encouraging closing line.

    FORMATTING RULES:
    - Every table row is a single email or event — never merge multiple items into one row.
    - Every email reference includes sender, timestamp, subject in italic quotes, and a plain-text note.
    - Tag every email with its source account: [Gmail] or [Outlook].
    - Do not invent information not present in the source data above.
    - Skip any section with no relevant content — don't write "none" or include placeholder rows.
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