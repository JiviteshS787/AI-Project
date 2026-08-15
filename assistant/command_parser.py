import json

from assistant.command_matcher import item_position
from assistant.command_actions import find_action

with open("data/apps.json", "r") as file:
    apps = json.load(file)

with open("data/files.json", "r") as file:
    files = json.load(file)

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file)

with open("data/file_synonyms.json", "r") as file:
    file_synonyms = json.load(file)

openables = {**apps, **files}
openable_synonyms = {**synonyms, **file_synonyms}


def find_monitors(words):
    for i, word in enumerate(words):
        if word.isdigit():
            # check if next word is monitor
            if i + 1 < len(words) and words[i + 1] in ["monitor", "screen"]:
                return int(word)

        # handle "second monitor", "third screen"
        if word in ["first", "second", "third", "fourth"]:
            mapping = {"first": 1, "second": 2, "third": 3, "fourth": 4}

            if i + 1 < len(words) and words[i + 1] in ["monitor", "screen"]:
                return mapping[word]

    return None


def alias_start(words, index):
    for i in range(index + 1, len(words)):
        if words[i] == "means":
            return True

        # Stop if we hit another separator
        if words[i] in [","]:
            break

    return False


#Finding multiple aliases
def find_aliases(words, action_length):
    remaining = words[action_length:]

    groups = []
    current = []

    i = 0
    while i < len(remaining):
        word = remaining[i]
        if word == "and":
            if alias_start(remaining, i + 1):
                groups.append(current)
                current = []
                i += 1
                continue

        current.append(word)
        i += 1
    if current:
        groups.append(current)

    aliases = []

    for group in groups:
        if "means" not in group:
            continue

        means_index = group.index("means")

        alias_words = group[:means_index]
        target_words = group[means_index + 1:]

        targets = []
        current_target = []
        for word in target_words:
            if word in ["and", ","]:
                if current_target:
                    target_item, _ = item_position(current_target, 0, openables, openable_synonyms)
                    if target_item:
                        targets.append(target_item)
                    current_target = []
            else:
                current_target.append(word)

        # Add final target
        if current_target:
            target_item, _ = item_position(current_target, 0, openables, openable_synonyms)
            if target_item:
                targets.append(target_item)

        if not targets:
            continue


        alias_list = []
        current_alias = []
        for word in alias_words:
            if word in ["and", ","]:
                if current_alias:
                    alias_list.append(" ".join(current_alias))
                    current_alias = []
            else:
                current_alias.append(word)

        if current_alias:
            alias_list.append(" ".join(current_alias))

        for alias in alias_list:
            aliases.append({
                "alias": alias,
                "targets": targets
            })

    return aliases


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


def split_commands(user_input):
    words = user_input.lower().replace(",", " , ").split()
    #print(f"Words: {words}")

    commands = []
    current = []

    i = 0
    while i < len(words):
        word = words[i]
        #print(f"Word:{word}")
        action_info = find_action(words, i)

        if action_info[0] and action_info[1] > 1:
            action_words = words[i:i + action_info[1]]
            current.extend(action_words)
            i += action_info[1]
            continue

        if action_info[0] and current:
            #print(f"Action found: {action_info[0]}, Word: {word}")
            previous_action = find_action(words, 0)

            if action_info[0] != previous_action[0]:
                commands.append(" ".join(current))
                current = []

        elif word in ["and", "then", ","]:
            next_action = find_action(words, i+1)
            if next_action[0]:
                commands.append(" ".join(current))
                current = []
                i += 1
                continue

            current.append(word)
            i += 1
            continue
        
        current.append(word)
        i += 1

    if current:
        commands.append(" ".join(current))

    #print(f"Commands: {commands}")
    return commands


def find_targets(words, action_length):
    targets = []
    current = []
    websites = []
    extra_items = []

    remaining = words[action_length:]
    has_parameters = False

    i = 0
    while i < len(remaining):
        word = remaining[i]
        #print(f"Word: {word}, i: {i}")

        if word == "on":
            if i + 3 < len(remaining):
                if (remaining[i + 1] == "my" and remaining[i + 3] in ["monitor", "screen"]):
                    monitor_words = remaining[i + 2]

                    monitor_numbers = {"first": 1, "second": 2, "third": 3, "fourth": 4}

                    if monitor_words in monitor_numbers:
                        if current:
                            targets.append({
                                "target": current,
                                "parameters": {
                                    "monitor": monitor_numbers[monitor_words]
                                }
                            })

                        current = []
                        i += 4
                        continue

                    if monitor_words.isdigit():
                        if current:
                            targets.append({
                                "target": current,
                                "parameters": {
                                    "monitor": int(monitor_words)
                                }
                            })

                        current = []
                        i += 4
                        continue

        # Start parameters
        if word == "with":
            has_parameters = True
            websites = []
            i += 1
            continue

        if has_parameters:
            #Ignore and, then and commas
            if word in ["and", "then", ","]:
                i += 1
                continue

            #Could be an app instead of a website(if it is an app, do not try app_name.com/.ca)
            possible_item, length = item_position(remaining, i, openables, openable_synonyms)
            #print(f"Item: {possible_item}, Length: {length}")

            if possible_item:
                extra_items.append(possible_item)
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
                current = possible_item.split()
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

    #print(f"Target: {targets}, Current: {current}, Websites: {websites}")

    if current:
        targets.append({"target": current,"parameters": {
                    "websites": [
                        site if "." in site else site + ".com"
                        for site in websites
                ]
            }
        })

    if websites and not extra_items:
        websites = [
            site if "." in site else site + ".com"
            for site in websites
        ]

        for target in targets:
            target["parameters"]["websites"] = websites

    return targets


def find_target(words, action_length):

    if "with" in words:
        end = words.index("with")
    else:
        end = len(words)

    return words[action_length:end]
