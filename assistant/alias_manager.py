import json

alias_file = "data/aliases.json"


#Try to load alias file
def load_aliases():
    try:
        with open(alias_file, "r") as file:
            return json.load(file)

    except:
        return {}


#Save aliases file
def save_aliases(aliases):
    with open(alias_file, "w") as file:
        json.dump(aliases, file, indent=4)


#Create new alias
def create_alias(alias, target):
    aliases = load_aliases()

    aliases[alias] = target

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


#List all aliases
def list_aliases():
    aliases = load_aliases()

    if not aliases:
        print("No aliases created")
        return

    print("\n=== Aliases ===")

    for alias, target in aliases.items():
        print(f"{alias} -> {target}")
