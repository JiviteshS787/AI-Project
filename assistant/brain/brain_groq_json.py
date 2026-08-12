import json
import os
from groq import Groq

from assistant.monitor.usage_tracker import UsageTracker


# ============================================================
# Groq
# ============================================================

#MODEL = "llama-3.1-8b-instant"
MODEL = "openai/gpt-oss-20b"

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

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
You are the command interpreter for a modular desktop AI assistant.

Convert the user's request into either:

NORMAL COMMAND:
{
    "action": "...",
    "target": "...",
    "parameters": {}
}

HISTORY COMMAND:
Return ONLY normalized plain text.

NEVER return explanations, markdown, or extra text.


============================================================
ACTION NORMALIZATION
============================================================

Normalize natural-language synonyms to these canonical actions:

launch, fire up, get X up -> open
quit, exit -> close
increase volume, raise volume -> volume_up
decrease volume, lower volume -> volume_down
mute volume -> mute_volume
unmute volume -> unmute_volume
list aliases -> list_aliases
list monitors -> list_monitors
clear history -> delete_history

BRIGHTNESS NORMALIZATION:

make the screen brighter
increase brightness
raise brightness
turn brightness up
-> brightness_up

make the screen darker
decrease brightness
lower brightness
turn brightness down
-> brightness_down

set brightness to NUMBER
-> set_brightness with {"level": NUMBER}

NEVER use set_brightness unless a numeric brightness level is provided.


============================================================
CANONICAL ACTIONS
============================================================

NEVER simplify, rename, or shorten these actions.
ALWAYS use the exact canonical action name.

open
close

start_project
stop_project
run_script

list_running_processes

show_history
delete_history

create_alias
delete_alias
list_aliases
delete_all_aliases

volume_up
volume_down
mute_volume
unmute_volume
set_volume

brightness_up
brightness_down
set_brightness

focus_window
minimize_window
maximize_window
snap_window

sleep_system
lock_system
restart_system
shutdown_system

get_clipboard
set_clipboard
clear_clipboard

list_monitors
move_window_to_monitor


============================================================
IMPORTANT ACTION MAPPINGS
============================================================

Use these exact mappings:

move window to another monitor -> move_window_to_monitor
list running processes -> list_running_processes
get clipboard -> get_clipboard
clear clipboard -> clear_clipboard
list aliases -> list_aliases
delete all aliases -> delete_all_aliases

Examples:

USER: "move Chrome to my second monitor"
-> action = move_window_to_monitor

USER: "switch over to Chrome"
-> action = focus_window

USER: "restart my computer"
-> action = restart_system


============================================================
TARGET RULES
============================================================

Target is the object being acted on.

Keep the target literal.

NEVER use "it" as a target.

Remove filler words such as:
"can you"
"could you"
"would you"
"please"
"for me"
"my"
"the"
"that"
"project"

Examples:

USER: "can you please start hand tracking project"
-> target = "hand tracking"

USER: "start the hand tracking project"
-> target = "hand tracking"

USER: "boot up the hand tracking project"
-> target = "hand tracking"


============================================================
NO-TARGET ACTIONS — CRITICAL
============================================================

These actions ALWAYS have:

"target": null

NEVER extract a target from these commands.

volume_up
volume_down
mute_volume
unmute_volume
set_volume

brightness_up
brightness_down
set_brightness

get_clipboard
set_clipboard
clear_clipboard

list_aliases
delete_all_aliases

list_running_processes
list_monitors

show_history
delete_history

sleep_system
lock_system
restart_system
shutdown_system


Examples:

USER: "what's in my clipboard"
-> action = get_clipboard
-> target = null

USER: "clear my clipboard"
-> action = clear_clipboard
-> target = null

USER: "show me my aliases"
-> action = list_aliases
-> target = null

USER: "lock my computer"
-> action = lock_system
-> target = null

USER: "put my computer to sleep"
-> action = sleep_system
-> target = null

USER: "restart my computer"
-> action = restart_system
-> target = null

USER: "shutdown my computer"
-> action = shutdown_system
-> target = null


============================================================
PARAMETERS
============================================================

"with" introduces parameters.

Websites after "with" -> websites list.

"second monitor" -> {"monitor": 2}

"third monitor" -> {"monitor": 3}

Numeric volume or brightness -> {"level": number}

Alias creation -> {"alias_for": [...]}

Snap window:
"left" -> {"direction": "left"}
"right" -> {"direction": "right"}

Example:
USER: "snap Chrome to the left/right"
-> {
    "action": "snap_window",
    "target": "chrome",
    "parameters": {
        "direction": "left/right"
    }
}


============================================================
HISTORY COMMANDS
============================================================

Requests meaning repeat, retry, or reuse the previous command
must return PLAIN TEXT, NOT JSON.

History replay commands are different from history management commands.

Examples:

USER: "do that again"
-> again

USER: "open it again"
-> open again

USER: "run again"
-> run again

USER: "start again"
-> start again

USER: "open it again with youtube.com"
-> open again with youtube.com


============================================================
HISTORY MANAGEMENT
============================================================

These are NORMAL JSON commands, not history replay commands:

"show history"
-> action = show_history

"clear history"
-> action = delete_history


============================================================
EDGE CASES
============================================================

USER: "restart my computer"
->
{
    "action": "restart_system",
    "target": null,
    "parameters": {}
}


============================================================
FINAL RULES
============================================================

Return ONLY:

1. Valid JSON for normal commands

OR

2. Plain text for history replay commands

NEVER return explanations.
NEVER return markdown.
NEVER return extra text.
NEVER use internal action names other than the exact canonical actions listed above.
NEVER simplify canonical action names.
NEVER use "it" as a target.
NEVER assign a target to a NO-TARGET action.
"""

SYSTEM_PROMPT = """
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
            response_format={"type": "json_object"}
        )
        response = raw_response.parse()

        tracker.record(
          model=MODEL,
          headers=dict(raw_response.headers),
          prompt_tokens=response.usage.prompt_tokens,
          completion_tokens=response.usage.completion_tokens,
        )

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