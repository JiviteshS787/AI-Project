import json
from datetime import datetime

from dashboard_api.push_updates import push_state_update
from assistant.brain.brain_groq_json import apps, files, projects, scripts, aliases

log_file = "data/history.log"

past_actions = {
    "open": "Opened",
    "close": "Closed",
    "start_project": "Started",
    "stop_project": "Stopped",
    "run_script": "Ran",
    "list_running_processes": "Listed running processes",
    "show_history": "Viewed history",
    "delete_history": "Cleared history",
    "delete_alias": "Deleted Alias",
    "create_alias": "Created Alias",
    "delete_all_aliases": "Deleted all aliases",
    "sleep_system": "Entered Sleep mode",
    "restart_system": "Restarted",
    "shutdown_system": "ShutDown",
    "lock_system": "Locked system",
    "focus_window": "Focused window",
    "maximize_window": "Maximized window",
    "minimize_window": "Minimized window",
    "move_window_to_monitor": "Moved window to monitor",
    "snap_window": "Snapped window"
}

ignore_actions = [
    "move_window_to_monitor",
    "snap_window",
    "focus_window",
    "minimize_window",
    "maximize window",
    "create_alias",
    "delete_alias"
]

def top_n_by_type(summary, n=3):
    grouped = {}
    for target, data in summary.items():
        type_ = data.get("type")
        if type_ is None or data.get("opens", 0) == 0:
            continue
        grouped.setdefault(type_, []).append((target, data))

    top = {t: [] for t in ("app", "file", "project", "script", "alias")}
    for type_, entries in grouped.items():
        entries.sort(key=lambda item: -item[1]["opens"])
        top[type_] = entries[:n]

    return top

def counting(summary, entry):
    target = entry.get("target")
    action = entry.get("action")

    if action not in ignore_actions and not target is None:
        if target not in summary:
            summary[target] = {
                "opens": 0,
                "closes": 0,
                "type": None
            }

        if target in apps:
            summary[target]["type"] = "app"
        elif target in files and (action == "open" or action =="close)"):
            summary[target]["type"] = "file"
        elif target in projects:
            summary[target]["type"] = "project"
        elif target in scripts:
            summary[target]["type"] = "script"
        elif target in aliases:
            summary[target]["type"] = "alias"
        
        if action == "open" or action == "run_script" or action == "start_project":
            summary[target]["opens"] += 1
        
        elif action == "close" or action == "stop_project":
            summary[target]["closes"] += 1

    return summary

def is_in_current_week(time_str: str) -> bool:
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    return dt.isocalendar()[:2] == now.isocalendar()[:2]

def daily_summary():
    summary = {}
    history = load_history()

    today_str = datetime.now().strftime("%Y-%m-%d")

    for entry in reversed(history):
        time = entry.get("time", "")

        if time[:10] != today_str:
            break
    
        counting(summary, entry)

    top_usage = top_n_by_type(summary)
    return top_usage
                
def weekly_summary():
    week_summary = {}
    history = load_history()

    for entry in reversed(history):
        time = entry.get("time", "")
        if is_in_current_week(time):
            counting(week_summary, entry)
        else:
            break

    top_usage = top_n_by_type(week_summary)
    return top_usage



def load_history():
    try:
        with open(log_file, "r") as f:
            return [json.loads(line) for line in f if line.strip()]
    except:
        return []

def append_history(command: dict):
    """
    Writes a single event to history.log
    Format:
    {action, target, parameters, time}
    """

    event = command.copy()

    # ensure structure consistency
    event["action"] = event.get("action")
    event["target"] = event.get("target")
    event["parameters"] = event.get("parameters") or {}

    # ALWAYS enforce timestamp
    event["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # cleanup empty fields
    if "websites" in event["parameters"] and not event["parameters"]["websites"]:
        del event["parameters"]["websites"]

    with open(log_file, "a") as f:
        f.write(json.dumps(event) + "\n")

    push_state_update("history", {"history": load_history()})
    push_state_update("daily_summary", {"daily_summary": daily_summary()})
    push_state_update("weekly_summary", {"weekly_summary": weekly_summary()})


def get_last_action():
    history = load_history()
    return history[-1] if history else None


def find_action_type(action_type: str):
    history = load_history()

    for entry in reversed(history):
        if entry.get("action") == action_type:
            return entry

    return None


def show_history():
    history = load_history()
    if not history:
        print("No history found")
        push_state_update("history", {"history": []})
        return

    print("\n=== Command History ===")

    current_date = None

    for command in history:
        timestamp = command.get("time", "")

        date = timestamp[:10] if len(timestamp) >= 10 else "Unknown Date"
        time = timestamp[11:16] if len(timestamp) >= 16 else ""

        # date grouping
        if date != current_date:
            current_date = date
            print(f"\n{date}")
            print("-" * len(date))

        action = past_actions.get(command.get("action"), command.get("action"))
        target = command.get("target", "")

        print(f"{time} - {action} {target}")

        params = command.get("parameters", {})
        if params:
            for k, v in params.items():
                print(f"       {k}: {v}")

    print()
    #push_state_update("history", {"history": history})


def delete_history():
    with open(log_file, "w") as f:
        f.write("")

# =========================
# OLD SYSTEM (COMMENTED OUT - KEPT FOR REFERENCE)
# =========================

"""
def load_history():
    try:
        with open(history_file, "r") as file:
            return json.load(file)
    except:
        return {
            "history": [],
            "last_action": {
                "action": None,
                "target": None,
                "parameters": {},
                "time": None
            }
        }


def update_history(command):
    history = load_history()

    if "history" not in history:
        history["history"] = []

    command["parameters"] = command.get("parameters") or {}
    command["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "websites" in command["parameters"]:
        if not command["parameters"]["websites"]:
            del command["parameters"]["websites"]

    history["history"].append(command)

    if len(history["history"]) > 40:
        history["history"].pop(0)

    history["last_action"] = command

    save_history(history)


def save_history(history_data):
    with open(history_file, "w") as file:
        json.dump(history_data, file, indent=4)
"""