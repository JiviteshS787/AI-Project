import time

from assistant.brain.brain import validate_command
from assistant.brain.brain_groq_json import interpret, MODEL, SYSTEM_PROMPT


'''TESTS = [
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

    # --- HISTORY ---
    ("Repeat", "do that again"),
    ("Open again", "open it again"),
    ("Run again", "run again"),
    ("Start again", "start again"),
]

'''


TESTS = [
    # --- OPEN / CLOSE ---
    ("Open natural", "can you go ahead and bring Chrome up"),
    ("Close natural", "I'm done with Chrome, close it"),

    # --- SELF CORRECTION / CHANGING MIND ---
    ("Correction app", "open Chrome wait no Notion"),
    ("Correction action", "close Chrome no wait minimize Notion"),
    ("Correction monitor", "open Chrome on my second monitor actually third monitor"),
    ("Correction multiple", "open Chrome on monitor two with YouTube no wait monitor three with Netflix"),

    # --- PROJECTS / SCRIPTS ---
    ("Start project filler", "uh boot up hand tracking"),
    ("Run script natural", "can you go ahead and run hello"),

    # --- WINDOW CONTROL ---
    ("Focus natural", "bring Chrome to the front"),
    ("Minimize natural", "get Chrome out of the way"),
    ("Maximize natural", "make Chrome full screen"),
    ("Snap natural", "put Chrome on the left"),
    ("Move monitor filler", "can you move Chrome uh to monitor two"),

    # --- PARAMETERS ---
    ("Chrome websites 3", "launch Chrome with YouTube Netflix and Gmail"),
    ("Chrome complex", "can you launch Chrome on monitor two with YouTube and Netflix"),

    # --- VOLUME / BRIGHTNESS ---
    ("Volume up natural", "it's a little quiet, turn it up"),
    ("Set volume natural", "set my volume to fifty"),
    ("Volume correction", "turn the volume down wait no turn it up"),
    ("Brightness down natural", "that's too bright, make it darker"),
    ("Brightness correction", "make it brighter actually darker"),

    # --- CLIPBOARD ---
    ("Clipboard natural", "what did I just copy"),
    ("Clear clipboard natural", "get rid of whatever is in my clipboard"),

    # --- ALIASES ---
    ("Create alias natural", "make an alias called school for Chrome Outlook and OneNote"),
    ("Run alias direct", "school"),
    ("Run alias natural", "can you start my school setup"),
    ("Delete alias natural", "get rid of the school alias"),

    # --- SYSTEM / POWER ---
    ("Lock natural", "I'm stepping away, lock my computer"),
    ("Shutdown natural", "I'm done for today, shut down my computer"),
    ("Power correction", "restart my computer wait no lock it"),
    ("Shutdown correction", "shut down my computer actually don't"),

    # --- LISTING ---
    ("Processes natural", "what's currently running"),

    # --- CONTEXT / HISTORY ---
    ("Context minimize", "open Chrome and then minimize it"),

    # --- IMPLICIT COMMANDS ---
    ("Implicit app", "I need Chrome"),
    ("Implicit volume", "a little louder"),
    ("Implicit brightness", "it's too dark"),

    # --- LONG / COMPLEX ---
    ("Complex setup", "open Chrome on my second monitor with YouTube and then start the hand tracking project"),
    ("Complex correction", "open Chrome on monitor two with YouTube actually no monitor three with Netflix"),
]


WAIT_TIME = 20


def main():
    #print(f"[prompt size] {len(SYSTEM_PROMPT)} chars")

    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0
    name = "GPT-OSS-20b"
    if "llama" in MODEL:
        name = "LLAMA-3.1-8b"

    print("=" * 70)
    print(f"AI ASSISTANT — {name} — VALIDATION TEST")
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

            validity_time = time.time()
            if valid:
                print()
                print("PASS")
                passed += 1
            else:
                print("FAIL")
                print("Reason:", error)
                failed += 1
            validity_time_elapsed = time.time() - validity_time

            print(f"Request time: {elapsed:.3f} seconds")
            print(f"Validity check time: {validity_time_elapsed:.3f} seconds")

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