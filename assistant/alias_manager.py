import json

from assistant.tools import projects, scripts, apps, files
from assistant.command_parser import synonyms, file_synonyms

alias_file = "data/aliases.json"


#Validate alias name
def valid_alias_name(alias):
    alias = alias.lower().strip()

    existing_names = set()

    existing_names.update(apps.keys())
    existing_names.update(files.keys())
    existing_names.update(projects.keys())
    existing_names.update(scripts.keys())

    existing_names.update(synonyms.keys())
    existing_names.update(file_synonyms.keys())

    if alias in existing_names:
        print(f"Cannot create alias '{alias}'. Name already exists.")
        return False

    return True


#Try to load alias file
def load_aliases():
    try:
        with open(alias_file, "r") as file:
            aliases = json.load(file)

            normalized = {}
            for alias, value in aliases.items():
                if isinstance(value, str):
                    item = value.lower().strip()
                    action = "open"
                    if item in scripts:
                        action = "run_script"
                    elif item in projects:
                        action = "start_project"

                    normalized[alias] = [{
                        "action": action,
                        "target": value,
                        "parameters": {}
                    }]
                else:
                    normalized[alias] = value
            return normalized

    except:
        return {}


#Save aliases file
def save_aliases(aliases):
    with open(alias_file, "w") as file:
        json.dump(aliases, file, indent=4)


#Create new alias
def create_alias(alias, target):
    aliases = load_aliases()

    if not valid_alias_name(alias):
        return False
    
    item = target.lower().strip()
    
    action = "open"
    if item in projects:
        action = "start_project"
    elif item in scripts:
        action = "run_script"

    new_command = {
        "action": action,
        "target": target,
        "parameters": {}
    }

    if alias in aliases:
        # Prevent duplicates
        if new_command not in aliases[alias]:
            aliases[alias].append(new_command)
    else:
        aliases[alias] = [new_command]

    save_aliases(aliases)

    print(f"Alias created: {alias} -> {target}")
    return True


#Delete an alias
def delete_alias(alias):
    aliases = load_aliases()

    if alias in aliases:
        del aliases[alias]
        save_aliases(aliases)

        print(f"Deleted alias: {alias}")
        return True

    print("Alias not found")
    return False


#Delete history
def delete_all_aliases():
    save_aliases({})
    print("All aliases cleared")
    return True


#List all aliases
def list_aliases():
    aliases = load_aliases()

    if not aliases:
        print("No aliases created")
        return

    print("\n=== Aliases ===")

    for alias, target in aliases.items():
        print(f"{alias} -> {target}")
