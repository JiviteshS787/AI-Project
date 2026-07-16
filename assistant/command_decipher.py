import json
from difflib import get_close_matches

with open("data/apps.json", "r") as file:
    apps = json.load(file) #Converts JSON to py dict

with open("data/projects.json", "r") as file:
    projects = json.load(file)

actions = {
        "open": "open_app",
        "start": "run_project"
    }

def find_action(word):
    matches = get_close_matches(word, actions.keys(), n=1, cutoff=0.5)
    
    if(matches):
        return actions[matches[0]]
    
    return None

def find_match(match_name, match_list):
    matches = get_close_matches(match_name, match_list.keys(), n=1, cutoff=0.6)
    if(matches):
        return matches[0]
    return None

def decipher (user_input):
    words = user_input.lower().split()
    app = None
    project = None

    for index, word in enumerate(words):

        action = find_action(word)

        if action == 'open_app':
            if index + 1 < len(words):
                app = find_match(words[index + 1], apps)
            if app:
                return {
                    "action": "open_app",
                    "value": app
                }
        
        elif action == 'run_project':
            if index + 1 < len(words):
                project = find_match(words[index + 1], projects)
            if project:
                return {
                    "action": "run_project",
                    "value": project
                }
    return None