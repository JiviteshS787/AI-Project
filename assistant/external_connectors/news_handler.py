import requests
import os

API_KEY = os.environ["GUARDIAN_API_KEY"]

def handle_news(topic: str | None) -> str:
    params = {
        "api-key": API_KEY,
        "order-by": "newest",
        "page-size": 3,
        "show-fields": "trailText",
    }
    if topic:
        params["q"] = topic

    try:
        r = requests.get("https://content.guardianapis.com/search", params=params, timeout=5)
        r.raise_for_status()
    except requests.RequestException:
        return "I couldn't reach the news service right now."

    results = r.json().get("response", {}).get("results", [])

    if not results:
        return f"I couldn't find any news on {topic}." if topic else "I couldn't find any news right now."

    headlines = [item["webTitle"] for item in results]
    label = f"on {topic}" if topic else "today"
    return f"Here's the latest {label}: " + "; ".join(headlines)