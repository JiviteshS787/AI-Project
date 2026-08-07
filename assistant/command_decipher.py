import json

from assistant.history import find_action_type, load_history

from assistant.command_actions import find_action
from assistant.command_matcher import find_match
from assistant.command_parser import find_target, find_targets, find_parameters, find_aliases
from assistant.alias_manager import load_aliases, valid_alias_name

#Convert JSONs to py dicts

with open("data/apps.json", "r") as file:
    apps = json.load(file)

with open("data/projects.json", "r") as file:
    projects = json.load(file)

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file) #Converts JSON to py dict

with open("data/scripts.json", "r") as file:
    scripts = json.load(file) #Converts JSON to py dict

with open("data/files.json", "r") as file:
    files = json.load(file)

with open("data/file_synonyms.json", "r") as file:
    file_synonyms = json.load(file)

#Combine known app and file names
openables = {**apps, **files}
open_synonyms = {**synonyms, **file_synonyms}

#Inverse commands
inverse_actions = {
    "open": "close",
    "start_project": "stop_project"
}


def filter_parameters(target, parameters, data):
    accepted = data[target].get("accepted_parameters", {})

    filtered = {}

    for parameter, value in parameters.items():
        if accepted.get(parameter, False):
            filtered[parameter] = value
        else:
            print(f"Ignored unsupported parameter '{parameter}' for {target}")

    return filtered


def return_command(action, target=None, parameters=None):
    return{
        "action": action,
        "target": target,
        "parameters": parameters or {}
    }


def check_alias(words, inverse=False):
    phrase = " ".join(words).lower().strip()
    aliases = load_aliases()

    if phrase not in aliases:
        return None
    commands = aliases[phrase]

    if inverse:
        return invert_commands(commands)

    return commands


def invert_commands(commands):
    inverse = []

    for command in commands:
        action = command["action"]
        inverse_action = inverse_actions.get(action)

        #No inverse found
        if not inverse_action:
            print(f"No inverse action for {action}")
            continue
        inverse.append({
            "action": inverse_action,
            "target": command["target"],
            "parameters": command.get("parameters", {})
        })
    return inverse


def decipher(user_input):
    words = user_input.lower().replace(",", " , ").split()

    #aliases = load_aliases()

    history = load_history()

    #print("Checking alias: 1")
    alias_command = check_alias(words)
    if alias_command:
        return alias_command

    # Find parameters (for later, might not need)
    parameters = find_parameters(words)

    #Initialize
    item = None
    project = None

    #Get most recent executes action, if any for it or again commands
    last = history.get("last_action")


    #If only again, repeat most recent action
    if user_input.strip() == "again" and last:
        return return_command(last.get("action"), last.get("target", None), last.get("parameters", {}))

    #Find the action word, and extract information from return output, PRINT ACTION
    action_info = find_action(words,0)
    if not action_info:
        return None
    action = action_info[0]
    action_index = action_info[1]
    #print(f"Action: {action}, Action-index: {action_index}")


    #######################################
    # Open and Close Apps, Files, Aliases #
    #######################################
    if action == "open":
        #Find the targeted apps, and their respective parameters
        item_targets = find_targets(words, action_index)
        
        #Find the most recently opened APP
        last_open = find_action_type("open")
        if last_open:
            #Extract the app name from the returned output
            item = last_open["target"]

        commands = []

        #Fore each app in the command
        for target in item_targets:
            #Check if alias in command
            alias_command = check_alias(target["target"])

            if alias_command:
                commands.extend(alias_command)
                continue

            #Find the app/file, ie check spelling get similar apps, basically confirm the app
            item = find_match(target["target"], openables, open_synonyms)

            if not item:
                suggestion = find_match(target["target"], openables, open_synonyms)
                print(f"Open target not found: {' '.join(target['target'])}")
                if suggestion:
                    print(f"Did you mean: {suggestion}?")
                continue
            
            #Find the return parameters
            item_parameters = {}

            if openables[item]["type"] == "app":
                item_parameters = filter_parameters(item, target["parameters"], openables)

            #Add to commands to execute
            commands.append(return_command("open", item, item_parameters))

        #Execute the commands based on text present
        if commands and not ("again" in words or "it" in words):
            return commands

        #Execute based on if 'again' or 'it' are in the command
        if "again" in words and parameters and last_open:
            parameters = filter_parameters(last_open["target"], parameters, openables)
            return return_command("open", last_open["target"], parameters)
        
        if "again" in words and last_open:
            return return_command("open", last_open["target"], last_open["parameters"])
        
        if "it" in words and last_open:
            return return_command("open", last_open["target"], last_open["parameters"])
        
        if parameters and last_open and not item_targets:
            parameters = filter_parameters(last_open["target"], parameters, apps)
            return return_command("open", last_open["target"], parameters)

    elif action == "close":
        targets = find_targets(words, action_index)
        commands = []

        for target in targets:
            alias_command = check_alias(target["target"], inverted = True)

            if alias_command:
                commands.extend(alias_command)
                continue
            item = find_match(target["target"], openables, open_synonyms)

            if not item:
                print(f"Close target not found: {' '.join(target['target'])}")
                continue
            commands.append(return_command("close", item))

        if commands:
            return commands


    #######################################
    #      Create and Delete Aliases      #
    #######################################
    elif action == "create_alias":
        alias_commands = []

        aliases_to_create = find_aliases(words, action_index)
        #print(f"Aliases identified: {aliases_to_create}")

        for alias in aliases_to_create:
            
            # Check alias name BEFORE creating command
            if not valid_alias_name(alias["alias"]):
                continue

            for target in alias["targets"]:
                target_item = find_match(target.split(), openables, open_synonyms)

                if not target_item:
                    continue

                alias_commands.append(return_command("create_alias",
                        alias["alias"],
                        {
                            "alias_for": target_item
                        }
                    )
                )

        if alias_commands:
            return alias_commands

    elif action == "delete_alias":
        alias = find_target(words, action_index)

        if not alias:
            print("Delete format: delete <alias>")
            return None

        alias_name = " ".join(alias)

        return return_command("delete_alias", alias_name)

    elif action == "delete_all_aliases":
        return return_command("delete_all_aliases")


    #######################################
    #       Start and Stop Projects       #
    #######################################
    elif action == "start_project":
        proj_target = find_target(words, action_index)

        alias_command = check_alias(proj_target)
        if alias_command:
            return alias_command

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


    #######################################
    #             Run Scripts             #
    #######################################
    elif action == 'run_script':
        script_target = find_target(words, action_index)

        alias_command = check_alias(script_target)
        if alias_command:
            return alias_command

        script = find_match(script_target, scripts, synonyms)

        last_script = find_action_type("run_script")

        if "again" in words and last_script:
            return return_command("run_script", last_script["target"])
        if "it" in words and last_script:
            return return_command("run_script", last_script["target"])

        return return_command("run_script", script, {})


    #######################################
    #       Show and Delete History       #
    #######################################
    elif action == 'show_history':
            return return_command("show_history")
    
    elif action == 'delete_history':
        return return_command("delete_history")


    #######################################
    #              Listing                #
    #######################################
    elif action == "list_running_processes":
        return return_command("list_running_processes")

    elif action == "list_aliases":
        return return_command("list_aliases")

    #######################################
    #           Volume Control            #
    #######################################
    elif action == "volume_up":
        return return_command("volume_up")

    elif action == "volume_down":
        return return_command("volume_down")

    elif action == "mute_volume":
        return return_command("mute_volume")

    elif action == "unmute_volume":
        return return_command("unmute_volume")

    elif action == "set_volume":
        # Example: set volume 50

        level = None

        for word in words:
            if word.isdigit():
                level = int(word)
                break

        if level is None:
            print("Please specify a volume level")
            return None

        # Clamp value between 0-100
        level = max(0, min(100, level))

        return return_command("set_volume", parameters={"level": level})

    return None