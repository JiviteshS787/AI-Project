import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import time

from assistant.brain import interpret

TESTS = [
    (
        "Open Chrome",
        "open chrome",
        [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    ),
    (
        "Get Chrome running",
        "get chrome up for me",
        [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    ),
    (
        "Start hand tracking",
        "start hand tracking",
        [
            {
                "action": "start_project",
                "target": "hand-tracking",
                "parameters": {}
            }
        ]
    ),
    (
        "Run hello",
        "run hello",
        [
            {
                "action": "run_script",
                "target": "hello",
                "parameters": {}
            }
        ]
    ),
    (
        "Close Chrome",
        "close chrome",
        [
            {
                "action": "close",
                "target": "chrome",
                "parameters": {}
            }
        ]
    ),
    (
        "Switch to Chrome",
        "switch over to Chrome",
        [
            {
                "action": "focus_window",
                "target": "chrome",
                "parameters": {}
            }
        ]
    ),
    (
        "Chrome with websites",
        "open chrome with youtube and netflix",
        [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "websites": [
                        "youtube.com",
                        "netflix.com"
                    ]
                }
            }
        ]
    ),
    (
        "Chrome on monitor 2",
        "open chrome on my second monitor",
        [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    ),
    (
        "Volume up",
        "turn it up",
        [
            {
                "action": "volume_up",
                "target": None,
                "parameters": {}
            }
        ]
    ),
    (
        "Set volume",
        "set the volume to 50",
        [
            {
                "action": "set_volume",
                "target": None,
                "parameters": {
                    "level": 50
                }
            }
        ]
    ),
    (
        "Brightness up",
        "make the screen brighter",
        [
            {
                "action": "brightness_up",
                "target": None,
                "parameters": {}
            }
        ]
    ),
    (
        "Read clipboard",
        "what's in my clipboard",
        [
            {
                "action": "get_clipboard",
                "target": None,
                "parameters": {}
            }
        ]
    ),
    (
        "Create school alias",
        "create alias school for Outlook, Chrome and OneNote",
        [
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    ),
]


def main():
    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0

    print("=" * 70)
    print("AI ASSISTANT — QUICK BRAIN TEST")
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

            if actual == expected:
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

        print()

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Runtime: {total_time:.2f} seconds")

    if total:
        print(f"Average: {total_time / total:.2f} seconds/test")

    print("=" * 70)


if __name__ == "__main__":
    main()