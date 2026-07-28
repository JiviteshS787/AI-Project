import json

from assistant.command_matcher import app_position
from assistant.command_actions import find_action

with open("data/apps.json", "r") as file:
    apps = json.load(file) #Converts JSON to py dict

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file) #Converts JSON to py dict


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

        elif word in ["and", "then", ","]:
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


def find_targets(words, action_length):
    targets = []
    current = []
    websites = []
    extra_apps = []

    remaining = words[action_length:]
    has_parameters = False

    i = 0
    while i < len(remaining):
        word = remaining[i]
        print(f"Word: {word}, i: {i}")

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
            possible_app, length = app_position(remaining,i)
            print(f"Length: {length}")

            if possible_app:
                extra_apps.append(possible_app)
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

    print(f"Target: {targets}, Current: {current}, Websites: {websites}")

    if current:
        targets.append({"target": current,"parameters": {
                    "websites": [
                        site if "." in site else site + ".com"
                        for site in websites
                ]
            }
        })

    if websites and not extra_apps:
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
