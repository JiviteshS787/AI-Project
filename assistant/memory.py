import json

from datetime import datetime

memory_file = "data/memory.json"

past_actions = {
    "open": "Opened",
    "close": "Closed",
    "start_project": "Started",
    "stop_project": "Stopped",
    "run_script": "Ran",
    "list_running_processes": "Listed running processes",
    "show_history": "Viewed history",
    "delete_history": "Deleted history"
}

#Load in anything in the memory, if unable to read return None for both entries.
def load_memory():
    try:
        with open(memory_file, "r") as file: #Open with intent to read JSON
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
    memory = load_memory()

    if "history" not in memory:
        memory["history"] = []


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
    memory["history"].append(command)

    if len(memory["history"]) > 20:
        #forget some things if too many stored
        memory["history"].pop(0)

    #Update most recent action
    memory["last_action"] = command

    #Save new memory
    save_memory(memory)


#Find action with matching type
def find_action_type(action_type):
    memory = load_memory()

    last = memory.get("last_action")

    if last and last.get("action") == action_type:
        return last

    for entry in reversed(memory.get("history", [])): #if History doesn't exist return an empty list
        if entry and entry.get('action') == action_type:
            return entry

    return None


#Show history
def show_history():

    memory = load_memory()

    if "history" not in memory or not memory["history"]:
        print("No history found")
        return

    print("\n=== Command History ===")

    for command in memory["history"]:

        time = command.get("time", "")
        time = time[11:16]   # only HH:MM

        action = past_actions.get(command["action"], command["action"])

        print(f"{time} - {action} {command['target']}")

        parameters = command.get("parameters", {})

        if parameters:
            for key, value in parameters.items():
                print(f"   {key}: {value}")

    print()


#Delete history
def delete_history():
    memory = load_memory()

    memory["history"] = []

    memory["last_action"] = {
        "action": None,
        "target": None,
        "parameters": {},
        "time": None
    }

    save_memory(memory)


#Write to memory JSON
def save_memory(memory_data):
    with open(memory_file, "w") as file: #Open with intent to write to JSON
        json.dump(memory_data, file, indent=4) #4 lines of writing