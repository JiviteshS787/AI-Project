import json
from difflib import get_close_matches
from assistant.memory import load_memory

with open("data/apps.json", "r") as file:
    apps = json.load(file) #Converts JSON to py dict

with open("data/projects.json", "r") as file:
    projects = json.load(file) #Converts JSON to py dict

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file) #Converts JSON to py dict

actions = {
        "open": "open_app",
        "launch": "open_app",
        "start": "run_project",
        "run": "run_project",
        "stop": "stop_project",
        "list running processes": "list_running_processes",
        "list": "list_running_processes",
        "processes": "list_running_processes"
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

            parameters["websites"] = websites

    return parameters


def find_action(word):
    matches = get_close_matches(word, actions.keys(), n=1, cutoff=0.7)
    
    if(matches):
        return actions[matches[0]]
    
    return None


def find_match(words, index, match_list, synonym_list):
    best_match = None
    best_score = 0

    for i in range (index + 2, len(words)+1):
        phrase = " ".join(words[index+1:i])
        matches = get_close_matches(phrase, match_list.keys(), n=1, cutoff=0.6)
        if(matches):
            score = len(phrase)
            if score > best_score:
                best_score = score
                best_match = matches[0]
        matches = get_close_matches(phrase, synonym_list.keys(), n=1, cutoff=0.6)
        if(matches):
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
    
    '''
    separators = [" and ", " then ", "," ]

    commands = [user_input]

    for separator in separators:
        new_commands = []

        for command in commands:
            new_commands.extend(command.split(separator))

        commands = new_commands

    output = []

    for command in commands:
        if command.strip():
            output.append(command.strip())

    return output
    '''


def decipher(user_input):
    words = user_input.lower().split()
    memory = load_memory()
    parameters = find_parameters(words)

    app = None
    project = None

    # "again" with no action word
    if user_input.strip() == "again":
        if memory["last_action"] == "open_app" and memory["last_app"]:
            return return_command("open_app", memory["last_app"], memory["app_params"])

        elif memory["last_action"] == "run_project" and memory["last_project"]:
            return return_command("run_project", memory["last_project"], memory["project_params"])

        elif memory["last_action"] == "stop_project" and memory["last_project"]:
            return return_command("stop_project", memory["last_project"])


    for index, word in enumerate(words):
        action = find_action(word)

        if action == "open_app":
            app = find_match(words, index, apps, synonyms)

            #If app name found
            if app:
                return return_command("open_app", app, parameters)
            #If again -> run previous exactly, with new params if existing
            if "again" in words and parameters and memory["last_app"]:
                return return_command("open_app", memory["last_app"], parameters)
            #Regular again -> no new params
            if "again" in words and memory["last_app"]:
                return return_command("open_app", memory["last_app"], memory["app_params"])
            #If 'it' reference -> check memory
            if "it" in words and memory["last_app"]:
                return return_command("open_app", memory["last_app"], parameters)
            #If no app name, use new parameters and old memory to open app
            if parameters and memory['last_app']:
                return return_command("open_app", memory["last_app"], parameters)


        elif action == "run_project":
            project = find_match(words, index, projects, synonyms)

            if project:
                return return_command("run_project", project, parameters)
            if "it" in words and memory["last_project"]:
                return return_command("run_project", memory["last_project"], memory["project_params"])
            if "again" in words and memory["last_project"]:
                return return_command("run_project", memory["last_project"], memory["project_params"])

        elif action == "stop_project":
            project = find_match(words, index, projects, synonyms)

            if project:
                return return_command("stop_project", project, parameters)
            if "it" in words and memory["last_project"]:
                return return_command("stop_project", memory["last_project"])
            if "again" in words and memory["last_project"]:
                return return_command("stop_project", memory["last_project"])

        elif action == "list_running_processes":
            return return_command("list_running_processes")

    return None