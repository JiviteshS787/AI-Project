import json
from difflib import get_close_matches

from assistant.memory import find_action_type, load_memory

with open("data/apps.json", "r") as file:
    apps = json.load(file) #Converts JSON to py dict

with open("data/projects.json", "r") as file:
    projects = json.load(file) #Converts JSON to py dict

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file) #Converts JSON to py dict

with open("data/scripts.json", "r") as file:
    scripts = json.load(file) #Converts JSON to py dict

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


def find_parameters(words):
    parameters = {}

    if "with" in words:
        index = words.index("with")
        if index + 1 < len(words):
            websites = []

            params = words[index+1:]
            
            for word in params:
                word = word.strip(",").lower()

                if word in ["and", "then"]:
                    continue
                
                if "." not in word:
                    word += ".com"
                websites.append(word)

            if websites:
                parameters["websites"] = websites

    return parameters


def app_position(words, index):

    for length in range(len(words)-index, 0, -1):

        possible = words[index:index+length]

        app = find_match(possible, apps, synonyms)

        if app:
            return app, length

    return None, 0



def find_targets(words, action_length):
    targets = []
    current = []
    websites = []

    remaining = words[action_length:]
    has_parameters = False

    i = 0
    while i < len(remaining):
        word = remaining[i]

        # Start parameters
        if word == "with":
            has_parameters = True
            i += 1
            continue

        if has_parameters:
            if word in ["and", "then", ","]:
                i += 1
                continue

            possible_app, length = app_position(remaining,i)

            if possible_app:
                # save previous app
                if current:
                    targets.append({"target": current,"parameters": {
                            "websites": [
                                site if "." in site else site + ".com"
                                for site in websites
                            ]
                        }
                    })


                # start new app
                current = possible_app.split()
                websites = []
                has_parameters = False

                i += length
                continue
            else:
                websites.append(word.strip(","))
        else:

            if word in ["and", "then", ","]:
                if current:
                    targets.append({"target": current, "parameters": {}})
                current = []
            else:
                current.append(word)
        i += 1

    if current:
        targets.append({"target": current, "parameters": {}})

    if websites:
        websites = [
            site if "." in site else site + ".com"
            for site in websites
        ]

        for target in targets:
            target["parameters"]["websites"] = websites

    return targets


'''
def find_target(words, action_length):
    if "with" in words:
        end = words.index("with")
    else:
        end = len(words)

    return words[action_length:end]
'''


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


def find_match(words, match_list, synonym_list):
    best_match = None
    best_score = 0

    # Try longer phrases first (IMPORTANT)
    for i in range(len(words), 0, -1):
        phrase = " ".join(words[:i])

        #Check app list
        if phrase in match_list:
            return phrase

        #Check synonym list
        if phrase in synonym_list:
            #print(f"Synonym found: {phrase}")
            return synonym_list[phrase]

        #Close word matching in apps
        matches = get_close_matches(phrase, match_list.keys(), n=1, cutoff=0.7)
        if matches:
            score = len(phrase)
            if score > best_score:
                best_score = score
                best_match = matches[0]

        #Close word matching in synonyms
        matches = get_close_matches(phrase, synonym_list.keys(), n=1, cutoff=0.7)
        if matches:
            score = len(phrase)
            if score > best_score:
                best_score = score
                best_match = synonym_list[matches[0]]

    return best_match


def return_command(action, target = None, parameters=None):
    return{
        "action": action,
        "target": target,
        "parameters": parameters or {}
    }


'''
def split_commands(user_input):
    words = user_input.lower().strip().split()

    commands = []
    current_command = []

    for word in words:
        #If action word found
        if word in actions and current_command:
            commands.append(" ".join(current_command))
            current_command = []

        #If no action word found, add word to current command
        current_command.append(word)

    if current_command:
        commands.append(" ".join(current_command))

    return commands
'''


def split_commands(user_input):
    words = user_input.lower().replace(",", " , ").split()

    commands = []
    current = []

    i = 0
    while i < len(words):
        word = words[i]

        # Check if this position starts an action?
        action_info = find_action(words, i)
        if action_info[0] and current:
            commands.append(" ".join(current))
            current = []

        elif word == ["and", "then", ","]:
            # Look after "and"
            next_action = find_action(words, i+1)
            if next_action[0]:
                commands.append(" ".join(current))
                current = []
                i += 1
                continue

            # Otherwise keep "and" as part of parameters
            current.append(word)
            i += 1
            continue

        current.append(word)
        i += 1

    if current:
        commands.append(" ".join(current))
    return commands


def decipher(user_input):
    words = user_input.lower().replace(",", " , ").split()
    memory = load_memory()
    parameters = find_parameters(words)

    app = None
    project = None

    last = memory.get("last_action")

    if user_input.strip() == "again" and last:
        return return_command(last.get("action"), last.get("target"), last.get("parameters", {}))

    action_info = find_action(words,0)

    if not action_info:
        return None

    action = action_info[0]
    action_index = action_info[1]

    if action == "open_app":
        app_targets = find_targets(words, action_index)
        last_open = find_action_type("open_app")
        commands = []

        for target in app_targets:
            app = find_match(target["target"], apps, synonyms)

            if app:
                app_parameters = target["parameters"]

                if not apps[app]["parameters"]:
                    app_parameters = {}

                commands.append(return_command("open_app", app, app_parameters))

        if commands and not ("again" in words or "it" in words):
            return commands
        
        if "again" in words and parameters and last_open:
            return return_command("open_app", last_open["target"], parameters)
        if "again" in words and last_open:
            return return_command("open_app", last_open["target"], last_open["parameters"])
        if "it" in words and last_open:
            return return_command("open_app", last_open["target"], last_open["parameters"])
        if parameters and last_open:
            return return_command("open_app", last_open["target"], parameters)


    elif action == 'close_app':
        app_targets = find_targets(words, action_index)

        if app_targets:
            app = find_match(app_targets[0]["target"], apps, synonyms)
        if app:
            return return_command("close_app", app, parameters)


    elif action == "start_project":
        proj_targets = find_targets(words, action_index)
        last_run = find_action_type("start_project")

        if proj_targets:
            project = find_match(proj_targets[0]["target"], projects, synonyms)

        if project:
            return return_command("start_project", project, parameters)
        if "it" in words and last_run:
            return return_command("start_project", last_run["target"], last_run["parameters"])
        if "again" in words and last_run:
            return return_command("start_project", last_run["target"], last_run["parameters"])


    elif action == "stop_project":
        stop_targets = find_targets(words, action_index)
        last_stop = find_action_type("stop_project")

        if stop_targets:
            project = find_match(stop_targets[0]["target"], projects, synonyms)

        if project:
            return return_command("stop_project", project, parameters)
        if "it" in words and last_stop:
            return return_command("stop_project", last_stop["target"])
        if "again" in words and last_stop:
            return return_command("stop_project", last_stop["target"])


    elif action == 'run_script':
        script_targets = find_targets(words, action_index)
        last_script = find_action_type("run_script")

        if script_targets:
            script = find_match(script_targets[0]["target"], scripts, synonyms)
        else:
            script = None

        if "again" in words and last_script:
            return return_command("run_script", last_script["target"])
        if "it" in words and last_script:
            return return_command("run_script", last_script["target"])

        return return_command("run_script", script)


    elif action == "list_running_processes":
        return return_command("list_running_processes")

    elif action == 'show_history':
        return return_command("show_history")

    elif action == 'delete_history':
        return return_command("delete_history")

    return None