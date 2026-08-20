import json
import os

INPUT_FILE = "data/history.json"
OUTPUT_FILE = "data/history.log"


def load_old_history():
    try:
        with open(INPUT_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Failed to load history.json:", e)
        return None


def normalize_event(event):
    """
    Ensures consistent structure for logging
    """
    return {
        "action": event.get("action"),
        "target": event.get("target"),
        "parameters": event.get("parameters", {}),
        "time": event.get("time")
    }


def write_log(events):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def migrate():
    data = load_old_history()
    if not data:
        print("No data found.")
        return

    events = []

    # 1. convert history list
    for item in data.get("history", []):
        if item:
            events.append(normalize_event(item))

    # 2. include last_action if it exists and is valid
    last = data.get("last_action")
    if last and last.get("action"):
        events.append(normalize_event(last))

    # 3. write to log file
    write_log(events)

    print(f"Migrated {len(events)} events to {OUTPUT_FILE}")


if __name__ == "__main__":
    migrate()