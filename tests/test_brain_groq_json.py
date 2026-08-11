import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import time

from assistant.brain.brain_groq_json import interpret


TESTS = [
    ("Open Chrome", "open chrome", {"action": "open", "target": "chrome", "parameters": {}}),
    ("Natural Chrome launch", "can you launch Chrome for me?", {"action": "open", "target": "chrome", "parameters": {}}),
    ("Get Chrome running", "get Chrome up for me", {"action": "open", "target": "chrome", "parameters": {}}),
    ("Start hand tracking", "start hand tracking", {"action": "start", "target": "hand tracking", "parameters": {}}),
    ("Boot hand tracking", "boot up the hand tracking project", {"action": "boot up", "target": "hand tracking", "parameters": {}}),
    ("Run hello", "run hello", {"action": "run", "target": "hello", "parameters": {}}),
    ("Run hello naturally", "can you run that hello script for me?", {"action": "run", "target": "hello", "parameters": {}}),
    ("Close Chrome", "close chrome", {"action": "close", "target": "chrome", "parameters": {}}),
    ("Quit Chrome", "quit chrome", {"action": "quit", "target": "chrome", "parameters": {}}),
    ("Switch to Chrome", "switch over to Chrome", {"action": "switch to", "target": "chrome", "parameters": {}}),
    ("Chrome with websites", "open chrome with youtube and netflix", {"action": "open", "target": "chrome", "parameters": {"websites": ["youtube.com", "netflix.com"]}}),
    ("Chrome on monitor 2", "open chrome on my second monitor", {"action": "open", "target": "chrome", "parameters": {"monitor": 2}}),
    ("Volume up", "turn it up", {"action": "turn volume up", "target": None, "parameters": {}}),
    ("Volume down", "turn the volume down", {"action": "turn volume down", "target": None, "parameters": {}}),
    ("Mute volume", "mute the volume", {"action": "mute", "target": None, "parameters": {}}),
    ("Unmute volume", "unmute the volume", {"action": "unmute", "target": None, "parameters": {}}),
    ("Set volume", "set the volume to 50", {"action": "set volume", "target": None, "parameters": {"level": 50}}),
    ("Brightness up", "make the screen brighter", {"action": "brightness up", "target": None, "parameters": {}}),
    ("Brightness down", "make the screen darker", {"action": "brightness down", "target": None, "parameters": {}}),
    ("Set brightness", "set the brightness to 70", {"action": "set brightness", "target": None, "parameters": {"level": 70}}),
    ("Read clipboard", "what's in my clipboard", {"action": "what is in my clipboard", "target": None, "parameters": {}}),
    ("Read clipboard alternate", "read my clipboard", {"action": "read clipboard", "target": None, "parameters": {}}),
    ("Create alias", "create alias school for Outlook, Chrome and OneNote", {"action": "create alias", "target": "school", "parameters": {"alias_for": ["outlook", "chrome", "onenote"]}}),
    ("Delete alias", "delete alias school", {"action": "delete alias", "target": "school", "parameters": {}}),
    ("List aliases", "show me my aliases", {"action": "show aliases", "target": None, "parameters": {}}),
    ("List processes", "list running processes", {"action": "list running processes", "target": None, "parameters": {}}),
    ("History", "show my history", {"action": "show history", "target": None, "parameters": {}}),
    ("Clear history", "clear my history", {"action": "clear", "target": None, "parameters": {}}),
    ("Open file", "open my project file", {"action": "open", "target": "project file", "parameters": {}}),
    ("Start project", "start the hand tracking project", {"action": "start", "target": "hand tracking", "parameters": {}}),
    ("Stop project", "stop the hand tracking project", {"action": "stop", "target": "hand tracking", "parameters": {}}),
    ("Run script", "run the hello script", {"action": "run", "target": "hello", "parameters": {}}),
    ("Focus window", "focus on Chrome", {"action": "focus on", "target": "chrome", "parameters": {}}),
    ("Minimize window", "minimize Chrome", {"action": "minimize", "target": "chrome", "parameters": {}}),
    ("Maximize window", "maximize Chrome", {"action": "maximize", "target": "chrome", "parameters": {}}),
    ("Snap window", "snap Chrome to the left", {"action": "snap", "target": "chrome", "parameters": {"direction": "left"}}),
    ("Move window", "move Chrome to my second monitor", {"action": "move", "target": "chrome", "parameters": {"monitor": 2}}),
    ("List monitors", "what monitors are available", {"action": "available monitors", "target": None, "parameters": {}}),
    ("Lock computer", "lock my computer", {"action": "lock", "target": None, "parameters": {}}),
    ("Sleep computer", "put my computer to sleep", {"action": "sleep", "target": None, "parameters": {}}),
]


def normalize(value):
    if isinstance(value, dict):
        return {
            key: normalize(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [normalize(item) for item in value]

    if isinstance(value, str):
        return " ".join(value.lower().strip().split())

    return value


def main():
    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0
    WAIT_TIME = 15

    print("=" * 70)
    print("AI ASSISTANT — GROQ JSON BRAIN TEST")
    print("=" * 70)
    print(f"Total tests: {total}")
    print()

    for i, (name, prompt, expected) in enumerate(TESTS, start=1):

        print("-" * 70)
        print(f"TEST {i}/{total}: {name}")
        print(f"Input: {prompt}")
        print()

        start = time.time()

        try:
            actual = interpret(prompt)

            elapsed = time.time() - start
            total_time += elapsed

            print("Brain returned:")
            print(json.dumps(actual, indent=2))

            if normalize(actual) == normalize(expected):
                print("PASS")
                passed += 1

            else:
                print("FAIL")
                failed += 1

                print()
                print("Expected:")
                print(json.dumps(expected, indent=2))

                print()
                print("Actual:")
                print(json.dumps(actual, indent=2))

            print(f"Request time: {elapsed:.3f} seconds")

        except Exception as e:
            elapsed = time.time() - start
            total_time += elapsed
            failed += 1

            print("ERROR")
            print(str(e))
            print(f"Request time: {elapsed:.3f} seconds")

        if i < total:
            print()
            print(f"Waiting {WAIT_TIME} seconds before next request...")
            time.sleep(WAIT_TIME)

        print()

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Runtime: {total_time:.2f} seconds")

    if total:
        print(f"Average: {total_time - (WAIT_TIME*(total-1)) / total:.2f} seconds/test")

    print("=" * 70)


if __name__ == "__main__":
    main()