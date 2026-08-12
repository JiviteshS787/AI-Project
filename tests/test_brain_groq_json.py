import time

from assistant.brain.brain import validate_command
from assistant.brain.brain_groq_json import interpret


TESTS = [
    # --- OPEN / CLOSE ---
    ("Open Chrome", "open chrome"),
    ("Natural Chrome launch", "can you launch Chrome for me?"),
    ("Get Chrome running", "get chrome up for me"),
    ("Close Chrome", "close chrome"),
    ("Quit Chrome", "quit chrome"),
    ("Exit Chrome", "exit chrome"),

    # --- PROJECTS ---
    ("Start hand tracking", "start hand tracking"),
    ("Boot hand tracking", "boot up the hand tracking project"),
    ("Stop hand tracking", "stop the hand tracking project"),

    # --- SCRIPTS ---
    ("Run hello", "run hello"),
    ("Run hello naturally", "can you run that hello script for me?"),

    # --- WINDOW CONTROL ---
    ("Switch to Chrome", "switch over to Chrome"),
    ("Focus Chrome", "focus on Chrome"),
    ("Minimize Chrome", "minimize Chrome"),
    ("Maximize Chrome", "maximize Chrome"),
    ("Snap left", "snap Chrome to the left"),
    ("Move to monitor", "move Chrome to my second monitor"),

    # --- PARAMETERS ---
    ("Chrome with websites", "open chrome with youtube and netflix"),
    ("Chrome monitor 2", "open chrome on my second monitor"),
    ("Chrome monitor 2 and youtube", "open chrome on my second monitor with youtube"),

    # --- VOLUME ---
    ("Volume up", "turn it up"),
    ("Volume down", "turn the volume down"),
    ("Mute", "mute the volume"),
    ("Unmute", "unmute the volume"),
    ("Set volume", "set the volume to 50"),

    # --- BRIGHTNESS ---
    ("Brightness up", "make the screen brighter"),
    ("Brightness down", "make the screen darker"),
    ("Set brightness", "set the brightness to 70"),

    # --- CLIPBOARD ---
    ("Clipboard question", "what's in my clipboard"),
    ("Read clipboard alt", "read my clipboard"),
    ("Clear clipboard", "clear my clipboard"),

    # --- ALIASES ---
    ("Create alias", "create alias school for Outlook, Chrome and OneNote"),
    ("Delete alias", "delete alias school"),
    ("List aliases", "show me my aliases"),
    ("Clear aliases", "clear all aliases"),

    # --- SYSTEM ---
    ("Lock computer", "lock my computer"),
    ("Sleep computer", "put my computer to sleep"),
    ("Restart computer", "restart my computer"),
    ("Shutdown computer", "shutdown my computer"),

    # --- LISTING ---
    ("List processes", "list running processes"),
    ("List monitors", "what monitors are available"),

    # --- HISTORY (should NOT go through validator) ---
    ("Repeat", "do that again"),
    ("Open again", "open it again"),
    ("Run again", "run again"),
    ("Start again", "start again"),
]


WAIT_TIME = 20


def main():
    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0

    print("=" * 70)
    print("AI ASSISTANT — VALIDATION TEST")
    print("=" * 70)

    for i, (name, prompt) in enumerate(TESTS, start=1):

        print("-" * 70)
        print(f"TEST {i}/{total}: {name}")
        print(f"Input: {prompt}")
        print()

        start = time.time()

        try:
            raw = interpret(prompt)

            valid, error = validate_command(raw)

            elapsed = time.time() - start
            total_time += elapsed

            print("LLM Output:")
            print(raw)

            if valid:
                print()
                print("PASS")
                passed += 1
            else:
                print("FAIL")
                print("Reason:", error)
                failed += 1

            print(f"Request time: {elapsed:.3f} seconds")

        except Exception as e:
            elapsed = time.time() - start
            total_time += elapsed
            failed += 1

            print("ERROR:", str(e))
            print(f"Request time: {elapsed:.3f} seconds")

        print()

        if i < total:
            print(f"Waiting {WAIT_TIME}s...\n")
            time.sleep(WAIT_TIME)

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Runtime: {total_time:.2f}s")
    print(f"Average: {total_time / total:.2f}s/test")
    print("=" * 70)


if __name__ == "__main__":
    main()