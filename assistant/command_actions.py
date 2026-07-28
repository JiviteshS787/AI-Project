from difflib import get_close_matches


actions = {
        "open": "open_app",
        "launch": "open_app",
        "fire up": "open_app",

        "close": "close_app",
        "exit": "close_app",
        "quit": "close_app",

        "start": "start_project",
        "boot": "start_project",

        "stop": "stop_project",
        "terminate": "stop_project",

        "run": "run_script",

        "list running processes": "list_running_processes",
        "list": "list_running_processes",
        "processes": "list_running_processes",
        "list processes": "list_running_processes",

        "history": "show_history",
        "show history": "show_history",
        "delete history": "delete_history",
        "delete": "delete_history",
        "clear": "delete_history",
    }

def find_action(words, index=0):
    for length in range(3, 0, -1):
        if index + length <= len(words):
            phrase = " ".join(words[index:index+length])

            # Exact match first
            if phrase in actions:
                #print(f"Action found: {phrase}")
                return actions[phrase], length

    # Similar word matching
    if index < len(words):
        match = get_close_matches(words[index], actions.keys(), n=1, cutoff=0.7)

    if match:
        #print(f"Similar match: {match[0]}")
        return actions[match[0]], 1

    return None, 0