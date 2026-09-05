import json
import os

from openai import OpenAI  # DeepSeek exposes an OpenAI-compatible endpoint

from assistant.alias_manager import load_aliases


# ============================================================
# DeepSeek
# ============================================================

MODEL = "deepseek-v4-flash"
KEY_NAME = 'DEEPSEEK_API_KEY'

client = OpenAI(api_key=os.environ.get(KEY_NAME), base_url="https://api.deepseek.com")

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
        response = client.chat.completions.create(
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
            response_format={"type": "json_object"},
            max_tokens = 300,
            extra_body={"thinking": {"type": "disabled"}}
        )

        cache_hit = getattr(response.usage, "prompt_cache_hit_tokens", None)
        cache_miss = getattr(response.usage, "prompt_cache_miss_tokens", None)

        print(f"[tokens] prompt={response.usage.prompt_tokens} "
              f"completion={response.usage.completion_tokens} "
              f"total={response.usage.total_tokens} "
              f"cache_hit={cache_hit} cache_miss={cache_miss}")

    except Exception as e:
        return {
            "error": "DeepSeek request failed",
            "details": str(e)
        }

    response_text = response.choices[0].message.content.strip()

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError:
        return {
            "error": "DeepSeek returned invalid JSON",
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