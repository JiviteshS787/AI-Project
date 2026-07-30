import json

from difflib import get_close_matches


def item_position(words, index, item_list, synonym_list):
    for length in range(len(words)-index, 0, -1):

        possible = words[index:index+length]
        
        app = check_name(possible, item_list, synonym_list)
        if(index == 4):
            print(f"Possible app: {possible}, Length: {length}, App: {app}")

        if app:
            return app, length

    return None, 0


def check_name(words, match_list, synonym_list):
    phrase = " ".join(words)

    if phrase in match_list:
        return phrase

    if phrase in synonym_list:
        return synonym_list[phrase]

    return None


def find_match(words, match_list, synonym_list):
    best_match = None
    best_score = 0

    # Try longer phrases first (IMPORTANT)
    for i in range(len(words), 0, -1):
        phrase = " ".join(words[:i])

        #Check app list
        if phrase in match_list:
            return phrase

        #Check synonym list
        if phrase in synonym_list:
            #print(f"Synonym found: {phrase}")
            return synonym_list[phrase]

        #Close word matching in apps
        matches = get_close_matches(phrase, match_list.keys(), n=1, cutoff=0.7)
        if matches:
            score = len(phrase)
            if score > best_score:
                best_score = score
                best_match = matches[0]

        #Close word matching in synonyms
        matches = get_close_matches(phrase, synonym_list.keys(), n=1, cutoff=0.7)
        if matches:
            score = len(phrase)
            if score > best_score:
                best_score = score
                best_match = synonym_list[matches[0]]

    return best_match