import json

from datetime import datetime

history_file = "data/history.json"

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
    "lock_system": "Locked system"
}

#Load in anything in the memory, if unable to read return None for both entries.
def load_history():
    try:
        with open(history_file, "r") as file: #Open with intent to read JSON
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


#Update history
def update_history(command):
    #Load in memory
    history = load_history()

    if "history" not in history:
        history["history"] = []


    #Start addition
    # Normalize command
    command["parameters"] = command.get("parameters") or {}

    #Timestamp
    command["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Remove empty website lists
    if "websites" in command["parameters"]:
        if not command["parameters"]["websites"]:
            del command["parameters"]["websites"]
    #End addition


    #Add command to history
    history["history"].append(command)

    if len(history["history"]) > 40:
        #forget some things if too many stored
        history["history"].pop(0)

    #Update most recent action
    history["last_action"] = command

    #Save new memory
    save_history(history)


#Find action with matching type
def find_action_type(action_type):
    history = load_history()

    last = history.get("last_action")

    if last and last.get("action") == action_type:
        return last

    for entry in reversed(history.get("history", [])): #if History doesn't exist return an empty list
        if entry and entry.get('action') == action_type:
            return entry

    return None


#Show history
def show_history():
    history = load_history()

    if "history" not in history or not history["history"]:
        print("No history found")
        return

    print("\n=== Command History ===")

    current_date = None

    for command in history["history"]:

        timestamp = command.get("time", "")

        if timestamp:
            date = timestamp[:10]
            time = timestamp[11:16]
        else:
            date = "Unknown Date"
            time = ""

        # New date header
        if date != current_date:
            current_date = date
            print(f"\n{date}")
            print("-" * len(date))

        action = past_actions.get(command.get("action"),  command.get("action"))

        target = command.get("target", "")

        print(f"{time} - {action} {target}")

        parameters = command.get("parameters", {})

        if parameters:
            for key, value in parameters.items():
                # Format website lists nicely
                if key == "websites":
                    print(f"       Websites: {', '.join(value)}")
                else:
                    print(f"       {key.capitalize()}: {value}")
    print()


#Delete history
def delete_history():
    history = load_history()

    history["history"] = []

    history["last_action"] = {
        "action": None,
        "target": None,
        "parameters": {},
        "time": None
    }

    save_history(history)


#Write to memory JSON
def save_history(history_data):
    with open(history_file, "w") as file: #Open with intent to write to JSON
        json.dump(history_data, file, indent=4) #4 lines of writing