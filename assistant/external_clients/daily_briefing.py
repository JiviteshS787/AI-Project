import os
from groq import Groq

from assistant.external_clients.gmail_client import fetch_recent_emails as fetch_gmail_emails
from assistant.external_clients.outlook_client import fetch_all_accounts as fetch_outlook_emails
from assistant.external_clients.calendar_client import fetch_todays_events


client = Groq(api_key=os.getenv("GROQ_API_KEY_2"))

BRIEFING_MODEL = "openai/gpt-oss-120b"


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


def build_prompt(data):
    return f"""You are summarizing today's schedule and inbox for a daily briefing.

    CALENDAR EVENTS TODAY:
    {data['calendar']}

    GMAIL (unread, primary inbox):
    {data['gmail']}

    OUTLOOK (unread, personal account):
    {data['outlook']}

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