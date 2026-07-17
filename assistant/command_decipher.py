import json
from difflib import get_close_matches

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
        "run": "run_project"
    }

def find_action(word):
    matches = get_close_matches(word, actions.keys(), n=1, cutoff=0.5)
    
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

def decipher (user_input):
    words = user_input.lower().split()
    app = None
    project = None

    for index, word in enumerate(words):

        action = find_action(word)

        if action == 'open_app':
            app = find_match(words, index, apps, synonyms)
            if app:
                return {
                    "action": "open_app",
                    "value": app
                }
        
        elif action == 'run_project':
            project = find_match(words, index, projects, synonyms)
            if project:
                return {
                    "action": "run_project",
                    "value": project
                }
    return None