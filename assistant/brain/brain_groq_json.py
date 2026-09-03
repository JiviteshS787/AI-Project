import json
import os
import copy

from groq import Groq

from assistant.monitor.usage_tracker import UsageTracker
from assistant.state import update_usage_state, state

from dashboard_api.push_updates import push_state_update

from assistant.alias_manager import load_aliases


# ============================================================
# Groq
# ============================================================

MODEL = "openai/gpt-oss-20b"
KEY_NAME = 'GROQ_API_KEY_2'

client = Groq(api_key=os.environ.get(KEY_NAME))
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

#Original Testes Prompt
#SYSTEM_PROMPT =  
"""
Convert each request into a JSON OBJECT with a "commands" array containing
one or more command objects:

  {"commands": [{"action":"...", "target":"...", "parameters":{}}]}

Even a single command must be wrapped in the array with one element.
Output ONLY the JSON object. No markdown, no explanations, no extra text.

Match by intent, not literal wording. ACTION NAMES must be copied exactly
from the canonical list — never renamed/shortened/merged.

STT NOISE: ignore filler (um/uh/like/so/yeah/okay). Mishears: to/too/2,
for/four, won/one, write/right. No punctuation assumed.

CORRECTIONS ("wait"/"no wait"/"actually"/"no"/"I mean"/"sorry"): speaker
discards prior words, even for one word/number. Replace fully, never merge
old+new. This ALWAYS results in exactly ONE command in "commands" — NEVER
two. A correction is NOT a compound command, even though both a correction
and a compound sentence may contain two action-shaped phrases.
  EXAMPLES:
  "open Chrome wait no Notion" -> {"commands":[{"action":"open","target":"notion","parameters":{}}]} (CORRECT)
  WRONG (do NOT do this): {"commands":[{"action":"open","target":"chrome",...},{"action":"open","target":"notion",...}]} (WRONG)
  This is WRONG because it keeps the abandoned "chrome" as a separate command
  instead of discarding it. The word before "wait"/"no"/"actually" describes
  something the speaker is TAKING BACK, not a second thing they also want.

  "close Chrome no wait minimize it" -> {"commands":[{"action":"minimize_window","target":"chrome","parameters":{}}]}
  "turn the volume down wait no turn it up" -> {"commands":[{"action":"volume_up","target":null,"parameters":{}}]}
  "restart my computer wait no lock it" -> {"commands":[{"action":"lock_system","target":null,"parameters":{}}]}
  "open chrome on monitor two with YouTube no wait monitor three with Netflix" ->
    {"commands":[{"action":"open","target":"chrome","parameters":{"monitor":3,"websites":["netflix"]}}]}
    (youtube dropped, not merged, not kept as a second entry)
  Cancelled, no replacement ("shut down actually don't") ->
    {"commands":[{"action":"none","target":null,"parameters":{}}]}

HOW TO TELL A CORRECTION FROM A COMPOUND COMMAND:
- Correction: the second phrase REPLACES/CONTRADICTS the first (same action
  type, different target/param, OR "wait"/"no"/"actually" directly precedes
  it) -> ONE command only.
- Compound: the second phrase is joined by "and then"/"and also"/"and", and
  describes something ADDITIONAL the speaker still wants, not a replacement
  -> TWO (or more) commands, both kept.
- PAY ATTENTION TO THE TARGET, if not provided in second half keep the first otherwise KEEP THE NEW ONE IN THE SECOND HALF

COMPOUND COMMANDS ("and then"/"and also"/"and"): if the sentence contains
multiple distinct, separate commands, put ONE object per command in the
"commands" array, in the order spoken:
  "open Chrome and then minimize it" ->
    {"commands":[
      {"action":"open","target":"chrome","parameters":{}},
      {"action":"minimize_window","target":"chrome","parameters":{}}
    ]}
  "open Chrome on my second monitor with YouTube and then start hand tracking" ->
    {"commands":[
      {"action":"open","target":"chrome","parameters":{"monitor":2,"websites":["youtube"]}},
      {"action":"start_project","target":"hand tracking","parameters":{}}
    ]}
This is DIFFERENT from a SELF-CORRECTION: a correction replaces a command
with a better version of the SAME command (always ONE array element,
discarding the abandoned version). Compound connectors introduce genuinely
SEPARATE commands that both get executed (multiple array elements, both kept).

CANONICAL ACTIONS (exact, never renamed):
open, close, start_project, stop_project, run_script,
list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases, run_alias, stop_alias,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor, 
search, none

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
Any question seeking real-time/external information not covered by another
action (weather, scores, news, facts, "what is"/"who is"/"how much is") ->
search {"query":"<verbatim question>"}

create alias X for A,B,C -> create_alias target=X {"alias_for":["A","B","C"]}
  "make an alias called school for Chrome Outlook and OneNote" ->
    {"commands":[{"action":"create_alias","target":"school","parameters":{"alias_for":["chrome","outlook","onenote"]}}]}
  The alias NAME (after "called"/"named") always goes in "target". EVERY app
  listed after "for" goes in "alias_for" — including the first one. Never
  place an app name in "target" for create_alias.

delete/remove alias X permanently (explicit "delete"/"remove" + "alias") -> delete_alias
  ONLY trigger delete_alias when the word "delete" or "remove" is used
  together with "alias" explicitly, e.g. "delete alias school",
  "remove the school alias", "delete my school alias".

open/run/execute/start my X where X is a known alias 
 (in context.targets.aliases) -> run_alias, target=X
 This include "open school", "run school", "execute school", "get school started"
 DO NOT USE start_project, open, or run_script for something in context.targets.aliases
 EXAMPLES:
 "lets get microsoft running" -> {"commands":[{"action":"run_alias","target":"microsoft","parameters":{}}]}
 "start my school alias" -> {"commands":[{"action":"run_alias","target":"school","parameters":{}}]}
 "run my habits shortcut" -> {"commands":[{"action":"run_alias","target":"habits","parameters":{}}]}


stop/close/end/get rid of/shut down X, where X is a known alias
  (in context.targets.aliases) -> stop_alias target=X
  This covers "close school", "stop school", "get rid of school",
  "close my school alias", "end school", "shut down school" — ANY
  phrasing that does not contain the explicit word "delete"/"remove"
  paired with "alias". Do NOT use delete_alias for these.
  EXAMPLES:
  "let's get rid of school" -> {"commands":[{"action":"stop_alias","target":"school","parameters":{}}]}
  "close school" -> {"commands":[{"action":"stop_alias","target":"school","parameters":{}}]}
  "close my school alias" -> {"commands":[{"action":"stop_alias","target":"school","parameters":{}}]}
  "stop school" -> {"commands":[{"action":"stop_alias","target":"school","parameters":{}}]}
  "delete the school alias" -> {"commands":[{"action":"delete_alias","target":"school","parameters":{}}]}
  "remove alias school" -> {"commands":[{"action":"delete_alias","target":"school","parameters":{}}]}
Do NOT confuse stop_alias with stop_project — stop_project only applies
when X matches context.targets.projects, not context.targets.aliases.
  
list aliases -> list_aliases

clear all aliases -> delete_all_aliases
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
delete_history, sleep_system, lock_system, restart_system, shutdown_system, search, none

PARAMETERS: only include a key if mentioned — never send null, omit instead.
"with" -> websites. "second"/"third monitor" -> {"monitor":2/3}.
Numeric volume/brightness -> {"level":N}. Snap -> {"direction":"left"/"right"}.
Setting clipboard, copying something -> {"text": "copied text"}
Combine when multiple given in one utterance.
NEVER CREATE YOUR OWN PARAMETERS, only use:
monitor, history, alias_for, direction, level, websites, text, query

    COPY TEXT PARAMETERS
    copy X to clipboard / set clipboard to X -> set_clipboard {"text":"X"}
    "could you copy hello my name is jivitesh to my clipboard" ->
        {"commands":[{"action":"set_clipboard","target":null,"parameters":{"text":"hello my name is jivitesh"}}]}
    "copy link https monkey.com" ->
        {"commands":[{"action":"set_clipboard","target":null,"parameters":{"text":"https://monkey.com"}}]}
    Capture the FULL literal text/phrase/link the speaker wants copied — do not
    summarize, shorten, or paraphrase it.

    WEBSITE VS APP DISAMBIGUATION (words after "with"):
    Before adding a word to "websites", check it against context.targets.apps, context.targets.files,
    context.synonyms.apps and context.synonyms.files
    (the list of known app names in the provided context). If it matches a
    known app/file, it is NOT a website — it means the speaker also wants that
    app opened, as a SEPARATE command in "commands". Only words that do NOT
    match a known app should go into "websites".
    Given context.targets.apps includes "notion":
    "open chrome with youtube and notion" ->
        {"commands":[
        {"action":"open","target":"chrome","parameters":{"websites":["youtube"]}},
        {"action":"open","target":"notion","parameters":{}}
        ]}
    "open chrome with youtube and netflix" (neither is a known app) ->
        {"commands":[{"action":"open","target":"chrome","parameters":{"websites":["youtube","netflix"]}}]}
    If a monitor was specified for the original "open chrome" command, do NOT
    apply that same monitor to the second app unless it was also mentioned
    for that app specifically.

    PARAMETER DISTRIBUTION:
    "open chrome with youtube and notion on monitor 2"->
        {"commands":[
        {"action":"open","target":"chrome","parameters":{"websites":["youtube"]}},
        {"action":"open","target":"notion","parameters":{"monitor": 2}}
        ]}
    "open chrome and notion on monitor 2" ->
        {"commands": [
        {"action":"open","target":"chrome","parameters":{"monitor":2}},
        {"action":"open","target":"notion","parameters":{"monitor":2}}
        ]}

HISTORY/REPEAT: triggered whenever the speaker refers to a window/item by
PRONOUN ("it"/"that"/"this") instead of naming it, OR by "again"/"same
thing"/"once more", AND does not name a fresh target. In ALL these cases:
target=null, ALWAYS include "history":true, plus anything else mentioned
in the sentence (monitor, websites, direction, level, etc). This always
results in exactly ONE command in "commands".

  "open it again" -> {"commands":[{"action":"open","target":null,"parameters":{"history":true}}]}
  "run it again" -> {"commands":[{"action":"run_script","target":null,"parameters":{"history":true}}]}
  ("run" is a real action verb from the INTENT MAP — map it normally, do NOT
  use "again" just because the word "again" also appears in the sentence)

  Bare pronoun with a real action verb, no "again" needed:
  "shift it to the left" -> {"commands":[{"action":"snap_window","target":null,"parameters":{"history":true,"direction":"left"}}]}
  "move it to monitor 2" -> {"commands":[{"action":"move_window_to_monitor","target":null,"parameters":{"history":true,"monitor":2}}]}
  "focus it" -> {"commands":[{"action":"focus_window","target":null,"parameters":{"history":true}}]}

  History combined with other new parameters (e.g. websites) still keeps
  everything in ONE command with history:true — do not drop the extra
  parameters just because no fresh target was named:
  "open it again with youtube and netflix" ->
    {"commands":[{"action":"open","target":null,"parameters":{"history":true,"websites":["youtube","netflix"]}}]}

  No verb at all, or only a non-canonical filler-verb like "repeat"/"do that"
  ("do that again", "repeat that again") ->
    {"commands":[{"action":"again","target":null,"parameters":{"history":true}}]}
  ("repeat" is NOT a canonical action from the INTENT MAP, so this falls
  under the no-verb case, not a fresh action)

  New/different target named -> NOT history, treat as fresh command.

WEB SEARCH
    Any question the speaker is asking that requires outside/real-world
    knowledge and is NOT a system command (weather, sports scores, news,
    facts, definitions, "what is"/"who is"/"how much does X cost") -> search
    {"query": "<verbatim question, minus filler words>"}. target is always null.
    "whats the weather like today" ->
        {"commands":[{"action":"search","target":null,"parameters":{"query":"whats the weather like today"}}]}
    "whats the score to the barca game" ->
        {"commands":[{"action":"search","target":null,"parameters":{"query":"whats the score to the barca game"}}]}
    "how much does a tesla model 3 cost" ->
        {"commands":[{"action":"search","target":null,"parameters":{"query":"how much does a tesla model 3 cost"}}]}
    Do NOT confuse with clipboard/history/system actions — if the sentence
    doesn't match any canonical action's INTENT MAP pattern and is phrased as
    a question, it's a search.

Match intent flexibly, output canonical action names exactly. No target on
no-target actions. Never "it"/"that" as target. Output ONLY the JSON object
with the "commands" array — no exceptions.
"""


SYSTEM_PROMPT = """
Convert each request into {"commands": [{"action":"...", "target":"...", "parameters":{}}]}.
Always wrap in the array, even a single command. Output ONLY the JSON object — no markdown, no explanations.

Match by intent, not literal wording. Action names must be copied exactly from the canonical list — never renamed/shortened/merged.

STT NOISE: ignore filler (um/uh/like/so/yeah/okay). Mishears: to/too/2, for/four, won/one, write/right. No punctuation assumed.

CORRECTIONS ("wait"/"no wait"/"actually"/"no"/"I mean"/"sorry"): speaker discards prior words, even one word/number. Replace fully, never merge old+new. Always exactly ONE command — never two, even if both halves look action-shaped.
  "open Chrome wait no Notion" -> {"commands":[{"action":"open","target":"notion","parameters":{}}]}
  "open chrome on monitor two with YouTube no wait monitor three with Netflix" ->
    {"commands":[{"action":"open","target":"chrome","parameters":{"monitor":3,"websites":["netflix"]}}]}
  (youtube dropped, not merged, not kept as second entry)
  Cancelled, no replacement ("shut down actually don't") -> {"commands":[{"action":"none","target":null,"parameters":{}}]}

CORRECTION VS COMPOUND:
- Correction: second phrase REPLACES/CONTRADICTS the first (same action type, different target/param, OR directly preceded by "wait"/"no"/"actually") -> ONE command.
- Compound ("and then"/"and also"/"and"): second phrase is something ADDITIONAL, not a replacement -> TWO+ commands, both kept, in spoken order.
- If target isn't restated in the second half, keep the first target; otherwise use the new one.
  "open Chrome and then minimize it" ->
    {"commands":[{"action":"open","target":"chrome","parameters":{}},{"action":"minimize_window","target":"chrome","parameters":{}}]}

CANONICAL ACTIONS (exact, never renamed):
open, close, start_project, stop_project, run_script,
list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases, run_alias, stop_alias,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor, search, again, none

INTENT MAP:
open/launch/start up X -> open | close/quit/exit X -> close
start project X -> start_project | stop project X -> stop_project
run/execute script X -> run_script
switch to/focus on X -> focus_window | minimize X -> minimize_window
maximize/full screen X -> maximize_window
snap X left/right -> snap_window {"direction":"left"/"right"}
move X to Nth monitor -> move_window_to_monitor {"monitor":N}
volume up/down -> volume_up/volume_down | mute/unmute -> mute_volume/unmute_volume
set volume to N -> set_volume {"level":N}
brighter/darker -> brightness_up/brightness_down
set brightness to N -> set_brightness {"level":N} (only if number given)
clipboard read/check -> get_clipboard | clear -> clear_clipboard
lock/sleep/restart/shutdown computer -> lock_system/sleep_system/restart_system/shutdown_system
show/clear history -> show_history/delete_history
list processes/monitors -> list_running_processes/list_monitors
  Includes question phrasing referring to the system itself, not outside knowledge:
  "how many monitors do I have" -> {"commands":[{"action":"list_monitors","target":null,"parameters":{}}]}
  "what's running right now" -> {"commands":[{"action":"list_running_processes","target":null,"parameters":{}}]}
  Distinguish from SEARCH: if the question is about the system/device itself (monitors, processes, clipboard, history), it's a canonical action, not search. SEARCH is only for outside/real-world knowledge (weather, news, facts, people, prices).

ALIASES:
create alias X for A,B,C -> create_alias target=X {"alias_for":["A","B","C"]}. Name after "called/named" -> target. Every app after "for" (including the first) -> alias_for. Never put an app name in target for create_alias.
  "make an alias called school for Chrome Outlook and OneNote" ->
    {"commands":[{"action":"create_alias","target":"school","parameters":{"alias_for":["chrome","outlook","onenote"]}}]}
delete_alias: ONLY when "delete"/"remove" is used explicitly with "alias" ("delete alias school", "remove the school alias").
run_alias: open/run/execute/start my X where X is a known alias (context.targets.aliases). Never use start_project/open/run_script for a known alias.
  "let's get microsoft running" -> {"commands":[{"action":"run_alias","target":"microsoft","parameters":{}}]}
stop_alias: any stop/close/end phrasing for a known alias that does NOT explicitly pair "delete"/"remove" with "alias" ("close school", "stop school", "get rid of school", "close my school alias").
  Do not confuse stop_alias with stop_project — stop_project only applies to context.targets.projects, not aliases.
list aliases -> list_aliases | clear all aliases -> delete_all_aliases

WEB SEARCH: any question needing outside/real-world knowledge, not a system command (weather, news, facts, "what is"/"who is"/cost questions) -> search {"query":"<verbatim question, minus filler>"}, target always null.
  "how much does a tesla model 3 cost" -> {"commands":[{"action":"search","target":null,"parameters":{"query":"how much does a tesla model 3 cost"}}]}
  If it doesn't match any INTENT MAP pattern and is phrased as a question, it's a search.

TARGET: literal object acted on. Strip filler anywhere: can you/could you/please/my/the/that/for me/project/script. Never use "it"/"that" as target. Even if the target is not a recognized app/alias/script name, still output it literally as the target — do NOT fall back to "none" just because you don't recognize the word.
  "boot up the hand tracking project" -> target="hand tracking"
  "run my backup script" -> target="backup"
  "quit Spotify" -> {"commands":[{"action":"close","target":"spotify","parameters":{}}]}

NO-TARGET ACTIONS (target always null): volume_up, volume_down, mute_volume, unmute_volume, set_volume, brightness_up, brightness_down, set_brightness, get_clipboard, set_clipboard, clear_clipboard, list_aliases, delete_all_aliases, list_running_processes, list_monitors, show_history, delete_history, sleep_system, lock_system, restart_system, shutdown_system, search, again, none

PARAMETERS: only include a key if mentioned — never send null, omit instead.
"with" -> websites. "second"/"third monitor" -> {"monitor":2/3}. Numeric volume/brightness -> {"level":N}. Snap -> {"direction":"left"/"right"}. Copying text -> {"text":"..."}. Combine when multiple given in one utterance.
Only use these keys: monitor, history, alias_for, direction, level, websites, text, check, query.

COPY TEXT: capture the FULL literal text/phrase/link, never summarize or shorten.
  "copy link https monkey.com" -> {"commands":[{"action":"set_clipboard","target":null,"parameters":{"text":"https://monkey.com"}}]}

WEBSITE VS APP (words after "with"): check each word against context.targets.apps/files and context.synonyms.apps/files. If it matches a known app/file, it's NOT a website — it's a separate "open" command instead. Only unmatched words go into "websites".
  Given "notion" is a known app:
  "open chrome with youtube and notion" ->
    {"commands":[{"action":"open","target":"chrome","parameters":{"websites":["youtube"]}},{"action":"open","target":"notion","parameters":{}}]}
  "open chrome with youtube and netflix" (neither is a known app) ->
    {"commands":[{"action":"open","target":"chrome","parameters":{"websites":["youtube","netflix"]}}]}
  A monitor specified for the first app does not carry over to a second app unless also stated for it.
  "open chrome and notion on monitor 2" ->
    {"commands":[{"action":"open","target":"chrome","parameters":{"monitor":2}},{"action":"open","target":"notion","parameters":{"monitor":2}}]}

HISTORY/REPEAT: triggered when the speaker uses a pronoun ("it"/"that"/"this") instead of naming a target, OR says "again"/"same thing"/"once more", with no fresh target named. Always: target=null, "history":true, plus any other mentioned params. Always ONE command. This rule applies even when the sentence also contains STT mishears (to/too, for/four, won/one) — normalize the mishear AND still apply history:true if a pronoun is present. Do not let a mishear distract you from the pronoun.
  "open it again" -> {"commands":[{"action":"open","target":null,"parameters":{"history":true}}]}
  "run it again" -> {"commands":[{"action":"run_script","target":null,"parameters":{"history":true}}]}
  ("run" is a real action verb — map it normally, don't treat as "again" just because the word appears)
  "shift it to the left" -> {"commands":[{"action":"snap_window","target":null,"parameters":{"history":true,"direction":"left"}}]}
  "open it again with youtube and netflix" ->
    {"commands":[{"action":"open","target":null,"parameters":{"history":true,"websites":["youtube","netflix"]}}]}
  "move it won monitor over" -> {"commands":[{"action":"move_window_to_monitor","target":null,"parameters":{"history":true,"monitor":1}}]}
  No verb at all, or a non-canonical filler-verb ("repeat", "do that") -> action="again":
    "do that again" -> {"commands":[{"action":"again","target":null,"parameters":{"history":true}}]}
  New/different target named -> NOT history, treat as fresh command.

Output ONLY the JSON object with the "commands" array — no exceptions.
"""


#Experimental gpt-oss-120b Prompt
#SYSTEM_PROMPT =
"""
Output ONLY: {"commands":[{"action":"...","target":"...","parameters":{}}]}
No markdown, no explanation. Match intent, not literal wording. Action names copied exactly from CANONICAL ACTIONS.

STT NOISE: ignore filler (um/uh/like/so/yeah/okay). Common mishears: to/too/2, for/four, won/one, write/right.

CORRECTIONS ("wait"/"no wait"/"actually"/"no"/"I mean"): speaker discards prior words entirely, even one word. Always ONE command, never two — never keep the abandoned version.
  "open Chrome wait no Notion" -> {"commands":[{"action":"open","target":"notion","parameters":{}}]}
  "open chrome on monitor 2 with youtube no wait monitor 3 with netflix" -> {"commands":[{"action":"open","target":"chrome","parameters":{"monitor":3,"websites":["netflix"]}}]}
  Cancelled with no replacement -> {"commands":[{"action":"none","target":null,"parameters":{}}]}
Correction = second phrase REPLACES first (same action type, or preceded by wait/no/actually) -> ONE command.
Compound = joined by "and"/"and then"/"and also", describes something ADDITIONAL -> multiple commands, order spoken.
  "open Chrome and then minimize it" -> {"commands":[{"action":"open","target":"chrome","parameters":{}},{"action":"minimize_window","target":"chrome","parameters":{}}]}

CANONICAL ACTIONS:
open, close, start_project, stop_project, run_script, list_running_processes, show_history, delete_history,
create_alias, delete_alias, list_aliases, delete_all_aliases, run_alias, stop_alias,
volume_up, volume_down, mute_volume, unmute_volume, set_volume,
brightness_up, brightness_down, set_brightness,
focus_window, minimize_window, maximize_window, snap_window,
sleep_system, lock_system, restart_system, shutdown_system,
get_clipboard, set_clipboard, clear_clipboard,
list_monitors, move_window_to_monitor, search, none

INTENT MAP:
open/launch/start up X -> open | close/quit/exit X -> close
start/stop project X -> start_project/stop_project | run/execute script X -> run_script
switch to/focus X -> focus_window | minimize X -> minimize_window | maximize/full screen X -> maximize_window
snap X left/right -> snap_window {"direction":"left"/"right"}
move X to Nth monitor -> move_window_to_monitor {"monitor":N}
volume up/down -> volume_up/volume_down | mute/unmute -> mute_volume/unmute_volume | set volume to N -> set_volume {"level":N}
brightness up/down -> brightness_up/brightness_down | set brightness to N -> set_brightness {"level":N} (only if number given)
clipboard read/check -> get_clipboard | clear/empty -> clear_clipboard | copy X / set clipboard to X -> set_clipboard {"text":"X"} (capture full literal text, no paraphrase)
create alias X for A,B,C -> create_alias target=X {"alias_for":["A","B","C"]} (name after "called"/"named" is target; ALL apps after "for" incl. first go in alias_for)
delete/remove alias X (must say "delete"/"remove" + "alias" explicitly) -> delete_alias
open/run/start my X where X in context.targets.aliases -> run_alias (never start_project/open/run_script for a known alias)
stop/close/end/get rid of X where X in context.targets.aliases, WITHOUT explicit delete+alias -> stop_alias
list aliases -> list_aliases | clear all aliases -> delete_all_aliases
lock/sleep/restart/shutdown computer -> lock_system/sleep_system/restart_system/shutdown_system
list processes -> list_running_processes | list monitors -> list_monitors
show/clear history -> show_history/delete_history
Real-time/external info question not covered above (weather, scores, news, facts, "what is"/"who is"/"how much") -> search {"query":"<verbatim question>"}
  "whats the score to the barca game" -> {"commands":[{"action":"search","target":null,"parameters":{"query":"whats the score to the barca game"}}]}

TARGET: literal object acted on, filler stripped (can you/could you/please/my/the/that/for me/project/script). Never "it"/"that" as target.
NO-TARGET (always null): volume_up, volume_down, mute_volume, unmute_volume, set_volume, brightness_up, brightness_down, set_brightness, get_clipboard, set_clipboard, clear_clipboard, list_aliases, delete_all_aliases, list_running_processes, list_monitors, show_history, delete_history, sleep_system, lock_system, restart_system, shutdown_system, search, none

PARAMETERS: include only if mentioned, never null (omit instead). Allowed keys ONLY: monitor, history, alias_for, direction, level, websites, text, query.
"with" -> websites, UNLESS the word matches a known app in context.targets.apps/files or synonyms — then it's a separate "open" command, not a website.
  Given "notion" is a known app: "open chrome with youtube and notion" -> {"commands":[{"action":"open","target":"chrome","parameters":{"websites":["youtube"]}},{"action":"open","target":"notion","parameters":{}}]}
  Monitor specified for first command doesn't carry to a second app unless stated for it too.
Second/third monitor -> {"monitor":2/3}. Combine multiple params given in one utterance.

HISTORY/REPEAT: pronoun ("it"/"that"/"this") or "again"/"same thing"/"once more" with no fresh target -> target=null, always include "history":true plus any other mentioned params. One command.
  "open it again" -> {"commands":[{"action":"open","target":null,"parameters":{"history":true}}]}
  "shift it to the left" -> {"commands":[{"action":"snap_window","target":null,"parameters":{"history":true,"direction":"left"}}]}
  No verb / only "repeat"/"do that" -> {"commands":[{"action":"again","target":null,"parameters":{"history":true}}]}
  New/different target named -> not history, fresh command.

Output ONLY the JSON object with "commands" array.
"""

# ============================================================
# Context
# ============================================================

def build_context():
    aliases = load_aliases()
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
            key_id = KEY_NAME,
            headers=dict(raw_response.headers),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

        update_usage_state(MODEL, KEY_NAME, tracker)
        #state["active_key"] = KEY_NAME
        #push_state_update("active_key", {"active_key": KEY_NAME})
        #push_state_update("stats", {"model": MODEL, "key_id": KEY_NAME, "stats": copy.deepcopy(state["stats"][MODEL])})
        #push_state_update("weekly_stats", {"model": MODEL, "key_id": KEY_NAME, "weekly_stats": copy.deepcopy(state["weekly_stats"][MODEL])})


        print(f"[tokens] prompt={response.usage.prompt_tokens}"
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

    if not isinstance(result, dict) or "commands" not in result:
        return {
            "error": "Expected a JSON object with a 'commands' array",
            "raw_response": response_text
        }

    commands = result["commands"]

    if not isinstance(commands, list) or len(commands) == 0:
        return {
            "error": "'commands' must be a non-empty array",
            "raw_response": response_text
        }

    return commands
