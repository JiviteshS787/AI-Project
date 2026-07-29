import json

from assistant.memory import find_action_type, load_memory

from assistant.command_actions import find_action
from assistant.command_matcher import find_match
from assistant.command_parser import find_target, find_targets, find_parameters

with open("data/apps.json", "r") as file:
    apps = json.load(file) #Converts JSON to py dict

with open("data/projects.json", "r") as file:
    projects = json.load(file) #Converts JSON to py dict

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file) #Converts JSON to py dict

with open("data/scripts.json", "r") as file:
    scripts = json.load(file) #Converts JSON to py dict

with open("data/files.json", "r") as file:
    files = json.load(file)

with open("data/file_synonyms.json", "r") as file:
    file_synonyms = json.load(file)

openables = {**apps, **files}

openable_synonyms = {**synonyms, **file_synonyms}


def filter_parameters(target, parameters, data):
    accepted = data[target].get("accepted_parameters", {})

    filtered = {}

    for parameter, value in parameters.items():
        if accepted.get(parameter, False):
            filtered[parameter] = value
        else:
            print(f"Ignored unsupported parameter '{parameter}' for {target}")

    return filtered


def return_command(action, target = None, parameters=None):
    return{
        "action": action,
        "target": target,
        "parameters": parameters or {}
    }


def decipher(user_input):
    words = user_input.lower().replace(",", " , ").split()
    memory = load_memory()

    # Find parameters (for later, might not need)
    parameters = find_parameters(words)

    #Initialize
    app = None
    project = None

    #Get most recent executes action, if any for it or again commands
    last = memory.get("last_action")


    #If only again, repeat most recent action
    if user_input.strip() == "again" and last:
        return return_command(last.get("action"), last.get("target"), last.get("parameters", {}))

    #Find the action word, and extract information from return output, PRINT ACTION
    action_info = find_action(words,0)
    if not action_info:
        return None
    action = action_info[0]
    action_index = action_info[1]
    #print(f"Action: {action}, Action-index: {action_index}")

    #Type of action
    if action == "open":
        #Find the targeted apps, and their respective parameters
        app_targets = find_targets(words, action_index)
        
        #Find the most recently opened APP
        last_open = find_action_type("open")
        if last_open:
            #Extract the app name from the returned output
            app = last_open["target"]

        commands = []

        #Fore each app in the command
        for target in app_targets:
            #Find the app/file, ie check spelling get similar apps, basically confirm the app
            item = find_match(target["target"], openables, openable_synonyms)

            if not item:
                print(f"Open target not found: {' '.join(target['target'])}")
                continue
            
            #Find the return parameters
            parameters = {}

            if openables[item]["type"] == "app":
                parameters = filter_parameters(item, target["parameters"], openables)

            #Add to commands to execute
            commands.append(return_command("open", item, parameters))

        #Execute the commands based on text present
        if commands and not ("again" in words or "it" in words):
            return commands

        #Execute based on if 'again' or 'it' are in the command
        if "again" in words and parameters and last_open:
            parameters = filter_parameters(last_open["target"], parameters, apps)
            return return_command("open", last_open["target"], parameters)
        
        if "again" in words and last_open:
            return return_command("open", last_open["target"], last_open["parameters"])
        
        if "it" in words and last_open:
            return return_command("open", last_open["target"], last_open["parameters"])
        
        if parameters and last_open and not app_targets:
            parameters = filter_parameters(last_open["target"], parameters, apps)
            return return_command("open", last_open["target"], parameters)


    elif action == 'close_app':
        app_target = find_target(words, action_index)
        app = find_match(app_target, apps, synonyms)

        if app:
            return return_command("close_app", app)


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
            return return_command("stop_project", project, {})
        if "it" in words and last_stop:
            return return_command("stop_project", last_stop["target"])
        if "again" in words and last_stop:
            return return_command("stop_project", last_stop["target"])


    elif action == 'run_script':
        script_target = find_target(words, action_index)
        script = find_match(script_target, scripts, synonyms)

        last_script = find_action_type("run_script")

        if "again" in words and last_script:
            return return_command("run_script", last_script["target"])
        if "it" in words and last_script:
            return return_command("run_script", last_script["target"])

        return return_command("run_script", script, {})


    elif action == "list_running_processes":
        return return_command("list_running_processes")

    elif action == 'show_history':
        return return_command("show_history")

    elif action == 'delete_history':
        return return_command("delete_history")

    return None