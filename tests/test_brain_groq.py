import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time

from assistant.brain.brain_groq import interpret


TESTS = [
    ("Open Chrome", "open chrome", "open chrome"),
    ("Natural Chrome launch", "can you launch Chrome for me?", "open chrome"),
    ("Get Chrome running", "get Chrome up for me", "open chrome"),
    ("Start hand tracking", "start hand tracking", "start hand tracking"),
    ("Boot hand tracking", "boot up the hand tracking project", "boot up hand tracking"),
    ("Run hello", "run hello", "run hello"),
    ("Run hello naturally", "can you run that hello script for me?", "run hello"),
    ("Close Chrome", "close chrome", "close chrome"),
    ("Quit Chrome", "quit chrome", "quit chrome"),
    ("Switch to Chrome", "switch over to Chrome", "switch to chrome"),
    ("Chrome with websites", "open chrome with youtube and netflix", "open chrome youtube.com netflix.com"),
    ("Chrome on monitor 2", "open chrome on my second monitor", "open chrome monitor=2"),
    ("Volume up", "turn it up", "turn volume up"),
    ("Set volume", "set the volume to 50", "set volume 50"),
    ("Brightness up", "make the screen brighter", "brightness up"),
    ("Read clipboard", "what's in my clipboard", "what is in my clipboard"),
    ("Create alias", "create alias school for Outlook, Chrome and OneNote", "create alias school outlook chrome onenote"),
    ("Repeat last action", "do that again", "again"),
    ("Repeat last action", "do it again", "again"),
    ("Repeat last action", "repeat my last action", "again"),
    ("Start again", "start again", "start again"),
    ("Run again", "run again", "run again"),
    ("Open again", "open it again", "open again"),
    ("Open that again", "open that again", "open again"),
]


def normalize(cmd: str):
    return " ".join(cmd.lower().strip().split())


def main():
    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0
    WAIT_TIME = 10

    print("=" * 70)
    print("AI ASSISTANT — GROQ BRAIN TEST")
    print("=" * 70)
    print(f"Model: llama-3.1-8b-instant")
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
            print(actual)

            if normalize(actual) == normalize(expected):
                print("PASS")
                passed += 1
            else:
                print("FAIL")
                failed += 1

                print()
                print("Expected:")
                print(expected)

                print()
                print("Actual:")
                print(actual)

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
    print(f"Total runtime: {total_time:.2f} seconds")

    if total:
        print(f"Average:       {total_time / total:.2f} seconds/test")

    print("=" * 70)


if __name__ == "__main__":
    main()