import time

from assistant.brain.brain import validate_command
from assistant.brain.brain_groq_json import interpret, MODEL, SYSTEM_PROMPT

'''
TESTS = [
    # --- OPEN / CLOSE ---
    ("Open natural", "can you go ahead and bring Chrome up"),
    ("Close natural", "I'm done with Chrome, close it"),

    # --- SELF CORRECTION / CHANGING MIND ---
    ("Correction app", "open Chrome wait no Notion"),
    ("Correction action", "close Chrome no wait minimize Chrome"),
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

    # --- NATURAL LANG. HISTORY ---
    ("History", "Could you uh run it again"),
    ("History Test 2", "Lets open that again"),
    ("History Test 3", "Could you repeat that again, thanks")
]
'''

'''
TESTS = [
    # --- Known app mistaken for website ---
    ("App mistaken for website", "open chrome with youtube and notion on monitor 2"),
    ("App mistaken for website, reordered", "open chrome on monitor two with spotify and outlook"),
    ("Known app as second item", "launch chrome with gmail and slack"),
    ("Only known apps, no real websites", "open chrome with notion and onenote"),

    # --- Genuine websites only (control cases — should NOT regress) ---
    ("Pure websites control", "open chrome with youtube and netflix"),
    ("Pure websites three", "launch chrome with youtube netflix and gmail"),

    # --- Mixed: one real website, one real app ---
    ("Mixed website and app", "open chrome with youtube and open notion too"),
    ("Mixed explicit and", "open chrome with youtube and also start notion"),

    # --- Ambiguous single word after "with" ---
    ("Single ambiguous target", "open chrome with notion"),
    ("Single ambiguous target 2", "open chrome with discord"),

    # --- App name that's also a plausible website ---
    ("App/website overlap word", "open chrome with spotify"),
    ("App/website overlap on monitor", "open chrome with spotify on my second monitor"),

    # --- Compound phrasing forcing two opens ---
    ("Explicit two opens with monitor", "open chrome and notion on monitor 2"),
    ("Explicit two opens, no with", "open chrome and spotify"),

    # --- Parameter Distribution ---
    ("Parameter test", "Open chrome with youtube, open notion on monitor 2")
]
'''

TESTS = [
    ("Open again", "Focus chrome on monitor 2")
]


WAIT_TIME = 35


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

            if isinstance(raw, dict) and "error" in raw:
                accepted = False
                error = raw.get("details", raw.get("error", "Unknown error"))
            else:
                accepted = True
                error = None
                for entry in raw:
                    valid, err = validate_command(entry)
                    if not valid:
                        accepted = False
                        error = err
                        break

            elapsed = time.time() - start
            total_time += elapsed

            print("LLM Output:")
            print(raw)

            validity_time = time.time()
            if accepted:
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


'''
======================================================================
AI ASSISTANT — GPT-OSS-20b — VALIDATION TEST
======================================================================
----------------------------------------------------------------------
TEST 1/5: Moving
Input: Shift it to the left

[context size] 1896 chars
[tokens] prompt=2957 completion=91 total=3048
LLM Output:
[{'action': 'snap_window', 'target': None, 'parameters': {'direction': 'left'}}]
FAIL
Reason: snap_window requires a target
Request time: 1.168 seconds
Validity check time: 0.001 seconds

Waiting 35s...

----------------------------------------------------------------------
TEST 2/5: Moving monitors
Input: Move it to monitor 2

[context size] 1896 chars
[tokens] prompt=2958 completion=313 total=3271
LLM Output:
[{'action': 'move_window_to_monitor', 'target': None, 'parameters': {'monitor': 2}}]
FAIL
Reason: move_window_to_monitor requires a target
Request time: 0.795 seconds
Validity check time: 0.000 seconds

Waiting 35s...

----------------------------------------------------------------------
TEST 3/5: Opening
Input: Open it again with youtube and netflix

[context size] 1896 chars
[tokens] prompt=2959 completion=121 total=3080
LLM Output:
[{'action': 'open', 'target': None, 'parameters': {'history': True}}]

PASS
Request time: 0.639 seconds
Validity check time: 0.000 seconds

Waiting 35s...

----------------------------------------------------------------------
TEST 4/5: Opening
Input: Open it again on monitor 2

[context size] 1896 chars
[tokens] prompt=2959 completion=131 total=3090
LLM Output:
[{'action': 'open', 'target': None, 'parameters': {'history': True, 'monitor': 2}}]

PASS
Request time: 0.839 seconds
Validity check time: 0.000 seconds

Waiting 35s...

----------------------------------------------------------------------
TEST 5/5: Repeating
Input: Repeat that

[context size] 1896 chars
[tokens] prompt=2954 completion=100 total=3054
LLM Output:
[{'action': 'again', 'target': None, 'parameters': {'history': True}}]
FAIL
Reason: Invalid action: again
Request time: 0.636 seconds
Validity check time: 0.000 seconds

======================================================================
RESULTS
======================================================================
Total:   5
Passed:  2
Failed:  3
Runtime: 4.08s
Average: 0.82s/test
======================================================================
'''