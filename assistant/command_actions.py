import json
from difflib import get_close_matches


with open("data/actions.json", "r") as file:
    actions = json.load(file)

# Optional optimization
action_keys = list(actions.keys())

def find_action(words, index=0):
    for length in range(3, 0, -1):
        if index + length <= len(words):
            phrase = " ".join(words[index:index+length])          
            #print(f"Index: {index}, Length:{length}, Phrase: {phrase}")

            # Exact match first
            if phrase in actions:
                #print(f"Action found: {phrase}, Length: {length}, Words: {words}")
                return actions[phrase], length

    # Similar word matching
    if index < len(words):
        match = get_close_matches(words[index], action_keys, n=1, cutoff=0.7)

    if match:
        #print(f"Similar match: {match[0]}")
        return actions[match[0]], 1

    return None, 0