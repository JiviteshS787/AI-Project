import json
import ollama


# ============================================================
# Load assistant data
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
# Ollama
# ============================================================

MODEL = "qwen3:8b"


# ============================================================
# Valid actions
# ============================================================

VALID_ACTIONS = [
    "open",
    "close",

    "create_alias",
    "delete_alias",
    "delete_all_aliases",

    "start_project",
    "stop_project",
    "run_script",

    "list_running_processes",
    "list_aliases",
    "show_history",
    "delete_history",

    "volume_up",
    "volume_down",
    "mute_volume",
    "unmute_volume",
    "set_volume",

    "brightness_up",
    "brightness_down",
    "set_brightness",

    "focus_window",
    "minimize_window",
    "maximize_window",
    "snap_window",

    "sleep_system",
    "lock_system",
    "restart_system",
    "shutdown_system",

    "get_clipboard",
    "set_clipboard",
    "clear_clipboard",

    "list_monitors",
    "move_window_to_monitor"
]


# ============================================================
# System instructions
# ============================================================


SYSTEM_PROMPT = """
You are a command parser for a desktop AI assistant.

Your ONLY job is to convert the user's command into valid JSON.

OUTPUT:
- Return ONLY a JSON array.
- No markdown.
- No explanations.
- No reasoning.
- Use ONLY the exact action names listed below.
- Never invent or rename an action.
- Every command must contain exactly:
  action, target, parameters
- Use null when target is not applicable.
- parameters must be {} when no parameters are needed.
- Numbers must be JSON numbers, not strings.

ACTIONS:
open
close
start_project
run_script
stop_project
focus_window
minimize_window
maximize_window
snap_window
move_window_to_monitor
volume_up
volume_down
mute_volume
unmute_volume
set_volume
brightness_up
brightness_down
set_brightness
get_clipboard
clear_clipboard
set_clipboard
sleep_system
lock_system
restart_system
shutdown_system
create_alias
delete_alias
delete_all_aliases
list_aliases
show_history
delete_history
list_monitors

RULES:

OPENING:
"open", "launch", "start", "bring up", "get ... up" + an app/folder → open.

PROJECTS:
"start", "launch", "run", "boot", "get ... running" + a project → start_project.

SCRIPTS:
"run", "execute" + a script → run_script.

CLOSING:
"close", "quit", "exit", "get ... out of here" + an app → close.

FOCUS:
"focus", "switch to" + an app → focus_window.

WINDOWS:
"minimize" → minimize_window.
"maximize", "full screen" → maximize_window.
"snap ... left/right" → snap_window with {"direction":"left/right"}.
"move ... to monitor/screen N" → move_window_to_monitor with {"monitor":N}.

IMPORTANT:
If an app is being OPENED on monitor N, use:
{"action":"open","target":"APP","parameters":{"monitor":N}}

Do NOT use move_window or move_window_to_monitor when the command is asking to open/launch an app on a monitor.

WEBSITES:
"open Chrome with YouTube" means open Chrome with:
{"websites":["youtube.com"]}

Always use the full domain.
YouTube → youtube.com
Netflix → netflix.com
GitHub → github.com

If multiple websites are requested, put them in the same websites array.
Do not create an additional open command for Chrome.

VOLUME:
"turn it up", "make it louder" → volume_up.
"turn it down", "make it quieter" → volume_down.
"mute" → mute_volume.
"unmute", "turn the sound back on" → unmute_volume.
"set volume to N" → set_volume with {"level":N}.

BRIGHTNESS:
"make the screen brighter" → brightness_up.
"screen is too bright" → brightness_down.
"set brightness to N" → set_brightness with {"level":N}.

CLIPBOARD:
"what's in my clipboard" → get_clipboard.
"clear my clipboard" → clear_clipboard.
"put/copy TEXT in my clipboard" → set_clipboard with {"text":"TEXT"}.

SYSTEM:
"put computer to sleep" → sleep_system.
"lock computer" → lock_system.
"restart computer" → restart_system.
"turn computer off"/"shut down" → shutdown_system.

ALIASES:
Creating an alias for multiple targets requires ONE create_alias command per target.

Example:
"create alias school for Chrome, Outlook and OneNote"

must become:
[
  {"action":"create_alias","target":"school","parameters":{"alias_for":"chrome"}},
  {"action":"create_alias","target":"school","parameters":{"alias_for":"outlook"}},
  {"action":"create_alias","target":"school","parameters":{"alias_for":"onenote"}}
]

The alias name must be copied exactly from the user's command.
Do not shorten, alter, or infer a different alias name.

HISTORY:
"what have I done recently" → show_history.
"clear my command history" → delete_history.

MONITORS:
"what monitors do I have" / "show my displays" → list_monitors.

When uncertain, choose the closest matching action from the allowed actions.
Never output an action that is not in the ACTIONS list.
"""



# ============================================================
# Context provided to Gemini
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
# Validation
# ============================================================

def validate_command(command):
    if not isinstance(command, dict):
        return False, "Command is not an object"

    action = command.get("action")
    target = command.get("target")
    parameters = command.get("parameters", {})

    if not isinstance(parameters, dict):
        return False, "Parameters must be an object"

    # History command is explicitly marked by the LLM.
    history_command = parameters.get("history") is True

    if action not in VALID_ACTIONS:
        return False, f"Invalid action: {action}"

    # Actions that don't use a target
    no_target_actions = {
        "volume_up",
        "volume_down",
        "mute_volume",
        "unmute_volume",
        "set_volume",
        "brightness_up",
        "brightness_down",
        "set_brightness",
        "sleep_system",
        "lock_system",
        "restart_system",
        "shutdown_system",
        "get_clipboard",
        "set_clipboard",
        "clear_clipboard",
        "list_monitors",
        "list_running_processes",
        "list_aliases",
        "show_history",
        "delete_history",
        "delete_all_aliases"
    }

    if action in no_target_actions:
        if target not in [None, ""]:
            return False, f"{action} should not have a target"

    # Actions that require a target
    target_actions = {
        "open",
        "close",
        "focus_window",
        "minimize_window",
        "maximize_window",
        "snap_window",
        "move_window_to_monitor",
        "start_project",
        "stop_project",
        "run_script",
        "delete_alias"
    }

    if action in target_actions:

        # History commands are allowed to have no target
        if not target and not history_command:
            return False, f"{action} requires a target"

        valid_targets = (
            set(apps.keys())
            | set(files.keys())
            | set(projects.keys())
            | set(scripts.keys())
            | set(aliases.keys())
        )

        # Window actions can refer to currently open windows,
        # so don't restrict them exclusively to configured items.
        if action not in {
            "focus_window",
            "minimize_window",
            "maximize_window",
            "snap_window",
            "move_window_to_monitor"
        }:

            # History commands don't need their target validated,
            # because the history manager will recover it.
            if not history_command:
                if target not in valid_targets:
                    return False, f"Unknown target: {target}"

    # Validate specific target types
    if action in {"open", "start_project", "run_script"}:

        if action == "open":
            if not history_command:
                if target not in apps and target not in files:
                    return False, f"{target} cannot be opened"

        elif action == "start_project":
            if not history_command:
                if target not in projects:
                    return False, f"{target} is not a known project"

        elif action == "run_script":
            if not history_command:
                if target not in scripts:
                    return False, f"{target} is not a known script"

    # Numeric validation
    if action in {"set_volume", "set_brightness"}:
        level = parameters.get("level")

        if not isinstance(level, (int, float)):
            return False, f"{action} requires a numeric level"

        if not 0 <= level <= 100:
            return False, f"{action} level must be between 0 and 100"

    # Monitor validation
    if action in {"open", "move_window_to_monitor"}:
        if "monitor" in parameters:
            monitor = parameters["monitor"]

            if not isinstance(monitor, int) or monitor < 1:
                return False, "Monitor must be a positive integer"

    # Snap validation
    if action == "snap_window":
        if parameters.get("direction") not in {"left", "right"}:
            return False, "Snap direction must be left or right"

    # Clipboard validation
    if action == "set_clipboard":
        if not isinstance(parameters.get("text"), str):
            return False, "Clipboard text must be a string"

    return True, None


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
        response = ollama.chat(
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
            options={
                "temperature": 0
            },
            think = False
        )

    except Exception as e:
        return {
            "error": "Ollama request failed",
            "details": str(e)
        }

    response_text = response["message"]["content"].strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError:
        return {
            "error": "Ollama returned invalid JSON",
            "raw_response": response_text
        }

    # --------------------------------------------------------
    # Normalize single command to a list
    # --------------------------------------------------------

    if isinstance(result, dict):
        result = [result]

    if not isinstance(result, list):
        return {
            "error": "Ollama response must be a command or list of commands"
        }

    # --------------------------------------------------------
    # Validate every command
    # --------------------------------------------------------

    for command in result:

        valid, error = validate_command(command)

        if not valid:
            return {
                "error": error,
                "command": command
            }

    return result