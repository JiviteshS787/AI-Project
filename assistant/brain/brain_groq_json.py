import json
import os

from groq import Groq

from assistant.monitor.usage_tracker import UsageTracker


# ============================================================
# Groq
# ============================================================

#Both of these models work well and deliver promising results.
'''
GPT-OSS-20b -> 44/45 -> invalid action = 'again'
llama-3.1-8b-instant -> yet to test with new prompt
'''

#MODEL = "llama-3.1-8b-instant"
MODEL = "openai/gpt-oss-20b"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

tracker = UsageTracker()

# ============================================================
# Import assistant data
# ============================================================

with open("data/apps.json", "r") as file:
    apps = json.load(file)

with open("data/files.json", "r") as file:
    files = json.load(file)

with open("data/projects.json", "r") as file:
    projects = json.load(file)

with open("data/scripts.json", "r") as file:
    scripts = json.load(file)

with open("data/synonyms.json", "r") as file:
    synonyms = json.load(file)

with open("data/file_synonyms.json", "r") as file:
    file_synonyms = json.load(file)

with open("data/aliases.json", "r") as file:
    aliases = json.load(file)


# ============================================================
# System Prompt
# ============================================================

#SYSTEM_PROMPT = 
"""
You interpret spoken commands (from speech-to-text, so expect no punctuation,
filler words, false starts, and mis-transcribed words). Convert each request into:

  JSON: {"action":"...", "target":"...", "parameters":{}}

Output ONLY the JSON object. No markdown, no explanations, no extra text.

MATCH BY INTENT, NOT LITERAL WORDING:
The trigger phrases below are examples of the pattern, not exact strings to match.
Match the user's underlying intent even if their wording, word order, or phrasing
differs. However, the ACTION NAME in your output must ALWAYS be copied EXACTLY
from the canonical list below, character-for-character — never shortened,
renamed, merged, or paraphrased (e.g. always "move_window_to_monitor", never
"move_window"; always "delete_all_aliases", never "clear_aliases").

HANDLING SPEECH-TO-TEXT NOISE:
- Ignore filler words: "um", "uh", "like", "so", "yeah", "okay".
- Ignore false starts / self-corrections — use the FINAL stated intent.
  e.g. "open — actually no, close chrome" -> close chrome
- Watch for common STT mishears: "to/too/2", "for/four", "won/one", "write/right".
- No punctuation/capitalization should be assumed; don't require it to match.
- If a sentence contains multiple distinct commands, handle only the first
  clear command unless parameters clearly belong together.

CANONICAL ACTIONS (copy exactly, never renamed/shortened):
open, close, start_project, stop_project, run_script,
list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor

INTENT -> ACTION MAP (patterns, not exact strings):
open/launch/start up/get X running/pull up X -> open
close/quit/exit/shut X (window) -> close
start a project/task named X -> start_project
stop/end a project/task named X -> stop_project
run/execute a script named X -> run_script
switch to X/focus on X/go to X -> focus_window
minimize X -> minimize_window
maximize X/full screen X -> maximize_window
snap X left/right -> snap_window, {"direction":"left"/"right"}
move X to [second/third] monitor/screen -> move_window_to_monitor, {"monitor":2/3}
turn up/raise/increase volume (with or without saying "volume") -> volume_up
turn down/lower/decrease volume -> volume_down
mute (the volume/sound) -> mute_volume
unmute (the volume/sound) -> unmute_volume
set volume to N -> set_volume, {"level":N}
brighter/increase/raise/turn up brightness -> brightness_up
darker/decrease/lower/turn down brightness -> brightness_down
set brightness to N -> set_brightness, {"level":N} (ONLY with explicit number)
what's in / read / check clipboard -> get_clipboard
clear/empty clipboard -> clear_clipboard
create/make an alias named X for A, B, C -> create_alias, {"alias_for":["A","B","C"]}
delete/remove alias named X -> delete_alias
show/list/what are my aliases -> list_aliases
clear/delete/remove all aliases -> delete_all_aliases
lock (my) computer/screen -> lock_system
put (my) computer to sleep -> sleep_system
restart/reboot (my) computer -> restart_system
shutdown/turn off (my) computer -> shutdown_system
list/show running processes/apps -> list_running_processes
what monitors/screens are available/list monitors -> list_monitors
show history -> show_history
clear/delete history -> delete_history

TARGET RULES:
- Target = literal object being acted on.
- Strip filler words WHEREVER they appear — leading, trailing, or in the
  middle: "can you", "could you", "please", "my", "the", "that", "for me",
  "project", "script".
- Trailing filler must be stripped too, not just leading filler:
  e.g. "boot up the hand tracking project" -> target = "hand tracking"
  e.g. "stop the hand tracking project" -> target = "hand tracking"
  e.g. "run that hello script for me" -> target = "hello"
- NEVER use "it"/"that" as a target string.

NO-TARGET ACTIONS (always "target": null, never extract a target):
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
get_clipboard, set_clipboard, clear_clipboard,
list_aliases, delete_all_aliases, list_running_processes, list_monitors,
show_history, delete_history, sleep_system, lock_system, restart_system, shutdown_system

PARAMETERS:
- ONLY include a parameter key if it was actually mentioned in the input.
  NEVER include a key with a null/None value for something not mentioned —
  omit the key entirely instead. Example:
  "open chrome with youtube and netflix" ->
  {"action":"open","target":"chrome","parameters":{"websites":["youtube","netflix"]}}
  (no "monitor" key at all, since no monitor was mentioned)
- "with" introduces parameters. Websites after "with" -> {"websites":[...]}
- "second"/"third monitor" -> {"monitor":2}/{"monitor":3}
- Numeric volume/brightness -> {"level":N}
- Alias creation -> {"alias_for":[...]}
- Snap direction -> {"direction":"left"/"right"}
- Combine parameters when multiple are given in one utterance, e.g.
  "open chrome on my second monitor with youtube" ->
  {"action":"open","target":"chrome","parameters":{"monitor":2,"websites":["youtube"]}}

HISTORY / REPEAT COMMANDS:
These refer back to the previous command using words like "again",
"it again", "that again", "same thing", "once more" — with no NEW
target explicitly named. Always return normal JSON, target: null,
and ALWAYS include "history": true inside parameters, in addition to
anything else newly mentioned:

- If a verb/action is present alongside "again" -> use that action,
  target: null, parameters include "history": true plus anything else mentioned:
  "open it again" -> {"action":"open","target":null,"parameters":{"history":true}}
  "run again" -> {"action":"run_script","target":null,"parameters":{"history":true}}
  "start again" -> {"action":"start_project","target":null,"parameters":{"history":true}}
  "open it again with youtube and netflix" ->
    {"action":"open","target":null,"parameters":{"history":true,"websites":["youtube","netflix"]}}

- If there is NO verb/action word at all — just "do that again"/
  "again"/"same thing" — use the literal action "again":
  "do that again" -> {"action":"again","target":null,"parameters":{"history":true}}

- If the user names a NEW, different target (not "it"/"that"), this is
  NOT a history command — treat it as a normal fresh command instead,
  and do NOT include "history" in parameters.

FINAL RULES:
- Match intent flexibly; output the canonical action name exactly, always.
- No target on no-target actions. Never "it"/"that" as a literal target string.
- Output nothing but the JSON object — no exceptions.
"""

#SYSTEM_PROMPT = 
"""
You interpret spoken commands (from speech-to-text, so expect no punctuation,
filler words, false starts, and mis-transcribed words). Convert each request into:

  JSON: {"action":"...", "target":"...", "parameters":{}}

Output ONLY the JSON object. No markdown, no explanations, no extra text.

MATCH BY INTENT, NOT LITERAL WORDING:
The trigger phrases below are examples of the pattern, not exact strings to match.
Match the user's underlying intent even if their wording, word order, or phrasing
differs. However, the ACTION NAME in your output must ALWAYS be copied EXACTLY
from the canonical list below, character-for-character — never shortened,
renamed, merged, or paraphrased (e.g. always "move_window_to_monitor", never
"move_window"; always "delete_all_aliases", never "clear_aliases").

HANDLING SPEECH-TO-TEXT NOISE:
- Ignore filler words: "um", "uh", "like", "so", "yeah", "okay".
- Watch for common STT mishears: "to/too/2", "for/four", "won/one", "write/right".
- No punctuation/capitalization should be assumed; don't require it to match.

SELF-CORRECTIONS / CHANGING MIND — CRITICAL RULE:
Words like "wait", "no wait", "actually", "no", "I mean", "sorry" signal the
speaker is discarding what they just said and replacing it with what comes
next — EVEN IF the correction is small (a single number, a single website,
a single direction). A correction always fully overrides the corresponding
piece of the earlier command; never keep the old value "just in case" and
never merge old and new values together. Output ONLY ONE JSON object.

- Target-only correction (action stays, target changes):
  "open Chrome wait no Notion" -> {"action":"open","target":"notion","parameters":{}}
- Action AND target both change:
  "close Chrome no wait minimize Notion" ->
    {"action":"minimize_window","target":"notion","parameters":{}}
- Single-word/number correction — still replace fully, don't keep the old one:
  "turn the volume down wait no turn it up" -> {"action":"volume_up","target":null,"parameters":{}}
  "restart my computer wait no lock it" -> {"action":"lock_system","target":null,"parameters":{}}
- Parameter-only correction (action/target stay, a detail changes):
  "open Chrome on my second monitor actually third monitor" ->
    {"action":"open","target":"chrome","parameters":{"monitor":3}}
- Correction changes MULTIPLE parameters at once — replace ALL of them
  together, do not keep any part of the original set:
  "open Chrome on monitor two with YouTube no wait monitor three with Netflix" ->
    {"action":"open","target":"chrome","parameters":{"monitor":3,"websites":["netflix"]}}
  (note: "youtube" is fully dropped here, not merged with "netflix")
- If the correction cancels the action entirely with no replacement
  ("shut down my computer actually don't"), there is no valid final
  command — return {"action":"none","target":null,"parameters":{}}

COMPOUND COMMANDS ("and then", "and also", "and"):
This system only supports ONE command per response. If a sentence contains
multiple distinct commands joined by "and then"/"and also"/"and", extract
ONLY the FIRST command and completely ignore anything after the connector —
do not blend, combine, or pick the second one instead:
  "open Chrome and then minimize it" -> {"action":"open","target":"chrome","parameters":{}}
  "open Chrome on my second monitor with YouTube and then start hand tracking" ->
    {"action":"open","target":"chrome","parameters":{"monitor":2,"websites":["youtube"]}}
This is different from a SELF-CORRECTION: corrections replace a command with
a better version of the SAME command; compound connectors introduce a
SEPARATE, unrelated second command that should be dropped entirely.

CANONICAL ACTIONS (copy exactly, never renamed/shortened):
open, close, start_project, stop_project, run_script,
list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases, run_alias,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor,
none

INTENT -> ACTION MAP (patterns, not exact strings):
open/launch/start up/get X running/pull up X -> open
close/quit/exit/shut X (window) -> close
start a project/task named X -> start_project
stop/end a project/task named X -> stop_project
run/execute a script named X -> run_script
switch to X/focus on X/go to X -> focus_window
minimize X -> minimize_window
maximize X/full screen X -> maximize_window
snap X left/right -> snap_window, {"direction":"left"/"right"}
move X to [second/third] monitor/screen -> move_window_to_monitor, {"monitor":2/3}
turn up/raise/increase volume (with or without saying "volume") -> volume_up
turn down/lower/decrease volume -> volume_down
mute (the volume/sound) -> mute_volume
unmute (the volume/sound) -> unmute_volume
set volume to N -> set_volume, {"level":N}
brighter/increase/raise/turn up brightness -> brightness_up
darker/decrease/lower/turn down brightness -> brightness_down
set brightness to N -> set_brightness, {"level":N} (ONLY with explicit number)
what's in / read / check clipboard -> get_clipboard
clear/empty clipboard -> clear_clipboard
create/make an alias named X for A, B, C -> create_alias, target = X, {"alias_for":["A","B","C"]}
  "make an alias called school for Chrome Outlook and OneNote" ->
    {"action":"create_alias","target":"school","parameters":{"alias_for":["chrome","outlook","onenote"]}}
delete/remove alias named X -> delete_alias
show/list/what are my aliases -> list_aliases
clear/delete/remove all aliases -> delete_all_aliases
start/run/open/launch my [alias] setup, or the bare name of a known alias
(check the "aliases" list in the provided context) -> run_alias, target = alias name
  "can you start my school setup" -> {"action":"run_alias","target":"school","parameters":{}}
  "school" (when "school" appears in context.targets.aliases) ->
    {"action":"run_alias","target":"school","parameters":{}}
lock (my) computer/screen -> lock_system
put (my) computer to sleep -> sleep_system
restart/reboot (my) computer -> restart_system
shutdown/turn off (my) computer -> shutdown_system
list/show running processes/apps -> list_running_processes
what monitors/screens are available/list monitors -> list_monitors
show history -> show_history
clear/delete history -> delete_history

TARGET RULES:
- Target = literal object being acted on.
- Strip filler words WHEREVER they appear — leading, trailing, or in the
  middle: "can you", "could you", "please", "my", "the", "that", "for me",
  "project", "script".
- Trailing filler must be stripped too, not just leading filler:
  e.g. "boot up the hand tracking project" -> target = "hand tracking"
  e.g. "stop the hand tracking project" -> target = "hand tracking"
  e.g. "run that hello script for me" -> target = "hello"
- NEVER use "it"/"that" as a target string.

NO-TARGET ACTIONS (always "target": null, never extract a target):
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
get_clipboard, set_clipboard, clear_clipboard,
list_aliases, delete_all_aliases, list_running_processes, list_monitors,
show_history, delete_history, sleep_system, lock_system, restart_system, shutdown_system,
none

PARAMETERS:
- ONLY include a parameter key if it was actually mentioned in the input.
  NEVER include a key with a null/None value for something not mentioned —
  omit the key entirely instead. Example:
  "open chrome with youtube and netflix" ->
  {"action":"open","target":"chrome","parameters":{"websites":["youtube","netflix"]}}
  (no "monitor" key at all, since no monitor was mentioned)
- "with" introduces parameters. Websites after "with" -> {"websites":[...]}
- "second"/"third monitor" -> {"monitor":2}/{"monitor":3}
- Numeric volume/brightness -> {"level":N}
- Alias creation -> {"alias_for":[...]}
- Snap direction -> {"direction":"left"/"right"}
- Combine parameters when multiple are given in one utterance, e.g.
  "open chrome on my second monitor with youtube" ->
  {"action":"open","target":"chrome","parameters":{"monitor":2,"websites":["youtube"]}}

HISTORY / REPEAT COMMANDS:
These refer back to the previous command using words like "again",
"it again", "that again", "same thing", "once more" — with no NEW
target explicitly named. Always return normal JSON, target: null,
and ALWAYS include "history": true inside parameters, in addition to
anything else newly mentioned:

- If a verb/action is present alongside "again" -> use that action,
  target: null, parameters include "history": true plus anything else mentioned:
  "open it again" -> {"action":"open","target":null,"parameters":{"history":true}}
  "run again" -> {"action":"run_script","target":null,"parameters":{"history":true}}
  "start again" -> {"action":"start_project","target":null,"parameters":{"history":true}}
  "open it again with youtube and netflix" ->
    {"action":"open","target":null,"parameters":{"history":true,"websites":["youtube","netflix"]}}

- If there is NO verb/action word at all — just "do that again"/
  "again"/"same thing" — use the literal action "again":
  "do that again" -> {"action":"again","target":null,"parameters":{"history":true}}

- If the user names a NEW, different target (not "it"/"that"), this is
  NOT a history command — treat it as a normal fresh command instead,
  and do NOT include "history" in parameters.

FINAL RULES:
- Match intent flexibly; output the canonical action name exactly, always.
- No target on no-target actions. Never "it"/"that" as a literal target string.
- Output nothing but the JSON object — no exceptions.
"""

SYSTEM_PROMPT = """
Interpret spoken commands (STT: no punctuation, filler, false starts, mishears).
Output ONLY: {"action":"...", "target":"...", "parameters":{}}
No markdown, no explanation, no extra text.

Match by intent, not literal wording. ACTION NAMES must be copied exactly
from the canonical list — never renamed/shortened/merged.

STT NOISE: ignore filler (um/uh/like/so/yeah/okay). Mishears: to/too/2,
for/four, won/one, write/right. No punctuation assumed.

CORRECTIONS ("wait"/"no wait"/"actually"/"no"/"I mean"/"sorry"): speaker
discards prior words, even for one word/number. Replace fully, never merge
old+new. One JSON object only.
  "open Chrome wait no Notion" -> open, target=notion
  "close Chrome no wait minimize Notion" -> minimize_window, target=notion
  "monitor two with YouTube no wait monitor three with Netflix" ->
    {"monitor":3,"websites":["netflix"]} (youtube dropped, not merged)
  Cancelled, no replacement ("shut down actually don't") -> action="none"

COMPOUND ("and then"/"and also"/"and"): ONE command per response. Take the
FIRST, drop the rest. ("open Chrome and then minimize it" -> just open chrome)

CANONICAL ACTIONS (exact, never renamed):
open, close, start_project, stop_project, run_script,
list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases, run_alias,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor, none

INTENT MAP (pattern -> action):
open/launch/start up/get X running -> open
close/quit/exit/shut X -> close
start project X -> start_project | stop project X -> stop_project
run/execute script X -> run_script
switch to/focus on X -> focus_window | minimize X -> minimize_window
maximize/full screen X -> maximize_window
snap X left/right -> snap_window {"direction":"left"/"right"}
move X to Nth monitor -> move_window_to_monitor {"monitor":N}
volume up/raise/increase -> volume_up | down/lower/decrease -> volume_down
mute -> mute_volume | unmute -> unmute_volume
set volume to N -> set_volume {"level":N}
brighter/turn up brightness -> brightness_up | darker/down -> brightness_down
set brightness to N -> set_brightness {"level":N} (only if number given)
clipboard read/check -> get_clipboard | clear/empty -> clear_clipboard
create alias X for A,B,C -> create_alias target=X {"alias_for":["A","B","C"]}
delete alias X -> delete_alias | list aliases -> list_aliases
clear all aliases -> delete_all_aliases
run/start my [alias] setup, or bare name matching context.targets.aliases
  -> run_alias target=alias name
lock computer -> lock_system | sleep computer -> sleep_system
restart computer -> restart_system | shutdown computer -> shutdown_system
list processes -> list_running_processes | list monitors -> list_monitors
show history -> show_history | clear history -> delete_history

TARGET: literal object acted on. Strip filler anywhere (leading/trailing/
middle): can you/could you/please/my/the/that/for me/project/script.
  "boot up the hand tracking project" -> target="hand tracking"
Never use "it"/"that" as target.

NO-TARGET ACTIONS (target always null): volume_up, volume_down, mute_volume,
unmute_volume, set_volume, brightness_up, brightness_down, set_brightness,
get_clipboard, set_clipboard, clear_clipboard, list_aliases,
delete_all_aliases, list_running_processes, list_monitors, show_history,
delete_history, sleep_system, lock_system, restart_system, shutdown_system, none

PARAMETERS: only include a key if mentioned — never send null, omit instead.
"with" -> websites. "second"/"third monitor" -> {"monitor":2/3}.
Numeric volume/brightness -> {"level":N}. Snap -> {"direction":"left"/"right"}.
Combine when multiple given in one utterance.

HISTORY/REPEAT ("again"/"it again"/"same thing"/"once more", no new target):
target=null, ALWAYS include "history":true plus anything new mentioned.
  "open it again" -> open, target=null, {"history":true}
  No verb at all ("do that again") -> action="again", {"history":true}
  New/different target named -> NOT history, treat as fresh command.

Match intent flexibly, output canonical action names exactly. No target on
no-target actions. Never "it"/"that" as target. Output ONLY the JSON object.
"""


# ============================================================
# Context
# ============================================================

def build_context():
    return {
        "targets": {
            "apps": list(apps.keys()),
            "files": list(files.keys()),
            "projects": list(projects.keys()),
            "scripts": list(scripts.keys()),
            "aliases": list(aliases.keys())
        },
        "synonyms": {
            "apps": synonyms,
            "files": file_synonyms
        }
    }


# ============================================================
# Brain
# ============================================================

def interpret(user_input):
    context = build_context()
    context_json = json.dumps(context, indent=2)
    print(f"[context size] {len(context_json)} chars")


    prompt = f"""
        Available assistant context:

        {json.dumps(context, indent=2)}

        User command:

        {user_input}
    """

    try:
        raw_response = client.chat.completions.with_raw_response.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            reasoning_effort="low",
            response_format={"type": "json_object"}
        )
        response = raw_response.parse()

        tracker.record(
            model=MODEL,
            headers=dict(raw_response.headers),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

        print(f"[tokens] prompt={response.usage.prompt_tokens} "
              f"completion={response.usage.completion_tokens} "
              f"total={response.usage.total_tokens}")
        
    except Exception as e:
        return {
            "error": "Groq request failed",
            "details": str(e)
        }

    response_text = response.choices[0].message.content.strip()

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError:
        return {
            "error": "Groq returned invalid JSON",
            "raw_response": response_text
        }

    return result
    