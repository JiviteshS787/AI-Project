import time

from assistant.brain.brain import validate_command
from assistant.brain.brain_deepseek import interpret, MODEL

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
    # --- OPEN / CLOSE ---
    ("Open natural", "can you go ahead and bring Chrome up"),
    ("Close natural", "I'm done with Chrome, close it"),
    ("Open with filler", "um could you like open up Notion for me"),
    ("Close terse", "quit Spotify"),

    # --- PROJECTS / SCRIPTS ---
    ("Start project", "boot up the hand tracking project"),
    ("Stop project", "stop the hand tracking project"),
    ("Run script", "run my backup script"),
    ("Run script natural", "go ahead and execute the cleanup script"),

    # --- SELF CORRECTION / CHANGE OF MIND ---
    ("Correction simple", "open Chrome wait no Notion"),
    ("Correction with params", "open chrome on monitor two with YouTube no wait monitor three with Netflix"),
    ("Correction same action diff target", "close Chrome no wait minimize it"),
    ("Correction volume", "turn the volume down wait no turn it up"),
    ("Correction system action", "restart my computer wait no lock it"),
    ("Correction cancelled no replacement", "shut down actually don't"),
    ("Correction with I mean", "set volume to 50 I mean 70"),
    ("Correction with sorry", "open Outlook sorry I meant Gmail"),

    # --- COMPOUND COMMANDS ---
    ("Compound open+minimize", "open Chrome and then minimize it"),
    ("Compound open+project", "open Chrome on my second monitor with YouTube and then start hand tracking"),
    ("Compound three actions", "open Notion and mute the volume and then lock my computer"),
    ("Compound vs correction lookalike", "open Chrome and open Notion"),

    # --- ALIASES ---
    ("Create alias basic", "make an alias called school for Chrome Outlook and OneNote"),
    ("Create alias natural", "can you set up a shortcut named work that opens Slack and Gmail"),
    ("Run alias known", "let's get microsoft running"),
    ("Run alias phrase 2", "start my school alias"),
    ("Run alias phrase 3", "run my habits shortcut"),
    ("Stop alias natural", "let's get rid of school"),
    ("Stop alias explicit", "close school"),
    ("Stop alias with word alias", "close my school alias"),
    ("Delete alias explicit", "delete the school alias"),
    ("Delete alias remove", "remove alias school"),
    ("Stop vs delete disambiguation", "shut down school"),
    ("List aliases", "what aliases do I have"),
    ("Delete all aliases", "clear all my aliases"),

    # --- WEBSITE VS APP DISAMBIGUATION ---
    ("Website only", "open chrome with youtube and netflix"),
    ("App mixed with website", "open chrome with youtube and notion"),
    ("Multiple known apps after with", "open chrome with notion and outlook"),
    ("Monitor scoping single app", "open chrome with youtube and notion on monitor 2"),
    ("Monitor scoping both apps", "open chrome and notion on monitor 2"),

    # --- HISTORY / REPEAT / PRONOUN ---
    ("History open again", "open it again"),
    ("History run again", "run it again"),
    ("History snap pronoun", "shift it to the left"),
    ("History move monitor pronoun", "move it to monitor 2"),
    ("History focus pronoun", "focus it"),
    ("History with extra params", "open it again with youtube and netflix"),
    ("History no verb repeat", "do that again"),
    ("History no verb same thing", "same thing again"),
    ("History filler verb", "repeat that again"),
    ("Fresh target overrides history", "open it again but actually open Spotify instead"),

    # --- WINDOW MANAGEMENT ---
    ("Snap left", "snap Chrome to the left"),
    ("Snap right natural", "put Notion on the right side of the screen"),
    ("Maximize", "full screen Spotify"),
    ("Minimize natural", "get Chrome out of my way"),
    ("Move to monitor", "move Notion to the third monitor"),
    ("Focus window", "switch to Chrome"),

    # --- VOLUME / BRIGHTNESS ---
    ("Volume up", "turn the volume up"),
    ("Volume down natural", "it's too loud, lower it"),
    ("Mute", "mute the volume"),
    ("Unmute", "unmute it"),
    ("Set volume numeric", "set the volume to 40"),
    ("Brightness up", "make the screen brighter"),
    ("Brightness down natural", "it's too bright in here"),
    ("Set brightness numeric", "set brightness to 80"),
    ("Brightness no number given", "turn up the brightness"),

    # --- CLIPBOARD ---
    ("Get clipboard", "what's on my clipboard"),
    ("Clear clipboard", "clear my clipboard"),
    ("Set clipboard basic", "could you copy hello my name is jivitesh to my clipboard"),
    ("Set clipboard link", "copy link https monkey.com"),
    ("Set clipboard long phrase", "set clipboard to remember to call mom at 5pm tomorrow"),

    # --- SYSTEM ---
    ("Lock system", "lock my computer"),
    ("Sleep system", "put the computer to sleep"),
    ("Restart system", "restart my pc"),
    ("Shutdown system", "shut down the computer"),
    ("List processes", "what's currently running"),
    ("List monitors", "how many monitors do I have"),
    ("Show history", "show me my history"),
    ("Delete history", "clear my history"),

    # --- SEARCH / WEB KNOWLEDGE ---
    ("Search weather", "whats the weather like today"),
    ("Search cost", "how much does a tesla model 3 cost"),
    ("Search who is", "who is the ceo of openai"),
    ("Search what is", "what is the capital of mongolia"),
    ("Search vs system action lookalike", "how do I lock my computer"),

    # --- STT NOISE / MISHEARS ---
    ("Mishear to/too", "open chrome and go too notion"),
    ("Mishear for/four", "set volume for 40"),
    ("Mishear won/one", "move it won monitor over"),
    ("Filler heavy", "um so like could you uh open Chrome for me okay"),
    ("No punctuation run-on", "open chrome and then close spotify and then lock my computer"),

    # --- EDGE CASES / AMBIGUITY ---
    ("Ambiguous pronoun no history context", "close it"),
    ("Action with no target given", "open"),
    ("Non-canonical verb only", "do that"),
    ("Empty-ish filler only", "um yeah okay so"),
    ("Correction across compound", "open chrome and notion wait no just chrome"),
]


WAIT_TIME = 5


def main():
    total = len(TESTS)
    passed = 0
    failed = 0
    total_time = 0
    name = MODEL

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
