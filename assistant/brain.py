import json
from google import genai
from google.genai import types


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
# Gemini
# ============================================================

client = genai.Client()

MODEL = "gemini-3.6-flash"


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
You are the natural-language interpretation layer of a Python desktop AI assistant.

Your ONLY task is to convert the user's natural-language request into one or more
JSON commands for the assistant router.

DO NOT execute anything.
DO NOT explain your reasoning.
DO NOT respond conversationally.
Return ONLY valid JSON.

Every command must have this structure:

{
    "action": "...",
    "target": "...",
    "parameters": {}
}

If the user requests multiple independent actions, return a JSON array.

============================================================
TARGET TYPES
============================================================

The available targets are provided in the context under:

- apps
- files
- projects
- scripts
- aliases

Use those lists to determine what the user is referring to.

IMPORTANT:

Apps and files use:
    "open"

Projects use:
    "start_project"

Scripts use:
    "run_script"

Closing an application/file uses:
    "close"

Stopping a project uses:
    "stop_project"

The user's wording does NOT determine the action by itself.

For example:

"launch Chrome"
"start Chrome"
"fire up Chrome"
"bring up Chrome"

all mean:

{
    "action": "open",
    "target": "chrome",
    "parameters": {}
}

because Chrome is an app.

Likewise:

"run hand tracking"

should NOT automatically become run_script.

Determine the target type from the provided context.

============================================================
NATURAL LANGUAGE
============================================================

Understand normal conversational language.

The user does not need to use exact command words.

Examples:

"get Chrome up"
"fire up my browser"
"bring up VS Code"
"show me my downloads"

should be interpreted according to the target's type.

Use the supplied synonyms to resolve references such as:

"browser" -> chrome
"google" -> chrome
"vscode" -> visual studio
"code" -> visual studio
"calc" -> calculator
"mail" -> outlook
"downloads folder" -> downloads

Do not invent targets.

============================================================
OPENING
============================================================

For an app or file:

"open"
"launch"
"start"
"fire up"
"bring up"
"get ... up"
"show me"

may all indicate:

"action": "open"

provided the target is an app or file.

============================================================
PROJECTS
============================================================

For a known project, use:

"start_project"

when the user means to start/launch/run/boot the project.

Examples:

"start hand tracking"
"launch my hand tracking project"
"boot the hand tracking project"
"get hand tracking running"

All should use:

"action": "start_project"

============================================================
SCRIPTS
============================================================

For a known script, use:

"run_script"

when the user wants to execute it.

Examples:

"run hello"
"execute hello"
"launch my hello script"
"get the hello script running"

============================================================
WINDOW ACTIONS
============================================================

Focus/switch/bring to front:
    focus_window

Minimize:
    minimize_window

Maximize:
    maximize_window

Snap:
    snap_window

Move an existing window to another monitor:
    move_window_to_monitor

Examples:

"focus Chrome"
"switch to Chrome"
"bring Chrome to the front"

-> focus_window

"minimize Chrome"
-> minimize_window

"maximize Chrome"
-> maximize_window

"snap Chrome to the left"
-> snap_window with:
{
    "direction": "left"
}

"put Chrome on my second monitor"
-> move_window_to_monitor with:
{
    "monitor": 2
}

============================================================
MONITORS
============================================================

Recognize natural references:

"second monitor"
"monitor 2"
"second screen"
"screen 2"
"second display"
"on my second monitor"

as:

{
    "monitor": 2
}

Monitor numbering starts at 1.

If an app/file is being opened on a monitor, put the monitor in
the command's parameters.

Example:

"open Chrome on my second monitor"

{
    "action": "open",
    "target": "chrome",
    "parameters": {
        "monitor": 2
    }
}

============================================================
WEBSITES
============================================================

If an app accepts websites and the user specifies websites, include:

{
    "websites": [...]
}

Example:

"open Chrome with YouTube and Netflix"

{
    "action": "open",
    "target": "chrome",
    "parameters": {
        "websites": [
            "youtube.com",
            "netflix.com"
        ]
    }
}

If both websites and a monitor are specified:

"open Chrome with YouTube and Netflix on my second monitor"

return:

{
    "action": "open",
    "target": "chrome",
    "parameters": {
        "websites": [
            "youtube.com",
            "netflix.com"
        ],
        "monitor": 2
    }
}

Preserve explicitly provided domains.

============================================================
VOLUME
============================================================

Increase/louder/turn up:
    volume_up

Decrease/lower/turn down:
    volume_down

Mute:
    mute_volume

Unmute:
    unmute_volume

Set a specific level:
    set_volume

Example:

"make the volume 50 percent"

{
    "action": "set_volume",
    "target": null,
    "parameters": {
        "level": 50
    }
}

============================================================
BRIGHTNESS
============================================================

Increase/brighter:
    brightness_up

Decrease/darker:
    brightness_down

Specific level:
    set_brightness

============================================================
CLIPBOARD
============================================================

Read/show/what is in clipboard:
    get_clipboard

Copy/set/put something in clipboard:
    set_clipboard

Clear clipboard:
    clear_clipboard

Preserve clipboard text as accurately as possible.

Example:

"copy hello world to my clipboard"

{
    "action": "set_clipboard",
    "target": null,
    "parameters": {
        "text": "hello world"
    }
}

============================================================
POWER
============================================================

Sleep:
    sleep_system

Lock:
    lock_system

Restart:
    restart_system

Shutdown/power off:
    shutdown_system

Do NOT ask for confirmation.
The router handles confirmation.

============================================================
ALIASES
============================================================

Create/remember an alias:
    create_alias

Delete/forget an alias:
    delete_alias

Delete all aliases:
    delete_all_aliases

List aliases:
    list_aliases

Use the available aliases in context.

============================================================
HISTORY / PROCESSES
============================================================

Running processes:
    list_running_processes

Show history:
    show_history

Delete history:
    delete_history

============================================================
AVAILABLE ACTIONS
============================================================

Only use actions supplied in the VALID_ACTIONS list.

Never invent an action.

============================================================
IMPORTANT
============================================================

Interpret the meaning of the entire request rather than matching individual
words.

Do not require exact command wording.

Do not invent targets.

Do not invent parameters.

Do not execute commands.

Return ONLY valid JSON.
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

    if action not in VALID_ACTIONS:
        return False, f"Invalid action: {action}"

    if not isinstance(parameters, dict):
        return False, "Parameters must be an object"

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

    # Validate known targets
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

        if not target:
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
            if target not in valid_targets:
                return False, f"Unknown target: {target}"


    if action in {"open", "start_project", "run_script"}:
        if action == "open":
            if target not in apps and target not in files:
                return False, f"{target} cannot be opened"

        elif action == "start_project":
            if target not in projects:
                return False, f"{target} is not a known project"

        elif action == "run_script":
            if target not in scripts:
                return False, f"{target} is not a known script"


    # Numeric validation
    if action in {"set_volume", "set_brightness"}:
        level = parameters.get("level")

        if not isinstance(level, (int, float)):
            return False, f"{action} requires a numeric level"

        if not 0 <= level <= 100:
            return False, f"{action} level must be between 0 and 100"

    if action in {"open", "move_window_to_monitor"}:
        if "monitor" in parameters:
            monitor = parameters["monitor"]

            if not isinstance(monitor, int) or monitor < 1:
                return False, "Monitor must be a positive integer"

    if action == "snap_window":
        if parameters.get("direction") not in {"left", "right"}:
            return False, "Snap direction must be left or right"

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

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json"
        )
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "error": "Gemini returned invalid JSON",
            "raw_response": response.text
        }

    # Normalize single command to a list
    if isinstance(result, dict):
        result = [result]

    if not isinstance(result, list):
        return {
            "error": "Gemini response must be a command or list of commands"
        }

    # Validate every command
    for command in result:
        valid, error = validate_command(command)

        if not valid:
            return {
                "error": error,
                "command": command
            }

    return result