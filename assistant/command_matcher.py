import json

from difflib import get_close_matches


def item_position(words, index, item_list, synonym_list):
    for length in range(len(words)-index, 0, -1):

        possible = words[index:index+length]
        
        item = check_name(possible, item_list, synonym_list)

        if item:
            return item, length

    return None, 0


def check_name(words, match_list, synonym_list):
    phrase = " ".join(words)

    #If any and, then or , in phrase -> ignore it
    if any(w in ["and", "then", ","] for w in words):
        return None

    # Exact match
    if phrase in match_list:
        return phrase

    # Synonym match
    if phrase in synonym_list:
        return synonym_list[phrase]

    #Similar match using apps/files
    matches = get_close_matches(phrase, match_list.keys(), n=1, cutoff=0.7)
    if matches:
        return matches[0]

    #Similar match using app/file synonyms
    matches = get_close_matches(phrase, synonym_list.keys(), n=1, cutoff=0.7)
    if matches:
        return synonym_list[matches[0]]

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