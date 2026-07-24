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
            
            for website in params:
                website = website.strip(",")

                if website in ["and", "then"]:
                    continue
                
                if "." not in website:
                    website += ".com"
                websites.append(website)

            if websites:
                parameters["websites"] = websites

    return parameters


def find_target(words, action_length):
    if "with" in words:
        end = words.index("with")
    else:
        end = len(words)

    return words[action_length:end]


def find_action(words):
    for length in range(2, 0, -1):
        if length <= len(words):
            phrase = " ".join(words[:length])

            # Exact match first
            if phrase in actions:
                #print(f"Action found: {phrase}")
                return actions[phrase], length

    # Similar word matching
    match = get_close_matches(words[0], actions.keys(), n=1, cutoff=0.7)

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
    

def decipher(user_input):
    words = user_input.lower().split()
    memory = load_memory()
    parameters = find_parameters(words)

    app = None
    project = None

    last = memory.get("last_action")

    # "again" with no action word
    if user_input.strip() == "again" and last:
        return return_command(last.get("action"), last.get("target"), last.get("parameters", {}))

    action_info = find_action(words)

    if not action_info:
        return None

    action = action_info[0]
    action_index = action_info[1]

    if action == "open_app":

        app_target = find_target(words, action_index)
        app = find_match(app_target, apps, synonyms)
        
        last_open = find_action_type("open_app")

        #If app name found
        if app:
            return return_command("open_app", app, parameters)
        #If again -> run previous exactly, with new params if existing
        if "again" in words and parameters and last_open:
            return return_command("open_app", last_open["target"], parameters)
        #Regular again -> no new params
        if "again" in words and last_open:
            return return_command("open_app", last_open["target"], last_open["parameters"])
        #If 'it' reference -> check memory
        if "it" in words and last_open:
            return return_command("open_app", last_open["target"], last_open["parameters"])
        #If no app name, use new parameters and old memory to open app
        if parameters and last_open:
            return return_command("open_app", last_open["target"], parameters)

    elif action == 'close_app':
        app_target = find_target(words, action_index)
        app = find_match(app_target, apps, synonyms)

        if app:
            return return_command("close_app", app, parameters)
        '''else:
            last_open = find_action_type("open_app")
            if last_open:
                return return_command("close_app", last_open["target"], last_open["parameters"])
        '''
    elif action == "start_project":

        proj_target = find_target(words, action_index)
        project = find_match(proj_target, projects, synonyms)

        last_run = find_action_type("start_project")

        if project:
            return return_command("start_project", project, parameters)
        if "it" in words and last_run:
                return return_command("start_project", last_run["target"], last_run["parameters"])
        if "again" in words and last_run:
            return return_command("start_project", last_run["target"], last_run["parameters"])

    elif action == "stop_project":

        stop_target = find_target(words, action_index)
        project = find_match(stop_target, projects, synonyms)

        last_stop = find_action_type("stop_project")

        if project:
            return return_command("stop_project", project, parameters)
        if "it" in words and last_stop:
            return return_command("stop_project", last_stop["target"])
        if "again" in words and last_stop:
            return return_command("stop_project", last_stop["target"])

    elif action == 'run_script':
        script_target = find_target(words, action_index)
        script = find_match(script_target, scripts, synonyms)

        return return_command("run_script", script)
    
    elif action == "list_running_processes":
        return return_command("list_running_processes")
    
    elif action == 'show_history':
        return return_command("show_history")
    
    elif action == 'delete_history':
        return return_command("delete_history")
        
    return None