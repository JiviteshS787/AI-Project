# ============================================================
# Ollama
# ============================================================

import ollama
import json

MODEL = "qwen3:8b"

# ============================================================
# Prompt (NEW — command format, NOT JSON)
# ============================================================

SYSTEM_PROMPT = """
OUTPUT FORMAT

Return ONLY one command in this format:

[action], [target]

If parameters are required:

[action], [target], [parameter] = [value]

Do not return JSON.
Do not use internal action names.
Do not explain anything.
Do not use code blocks.

ACTION EXTRACTION — CRITICAL

Your job is to EXTRACT the user's action, NOT determine the
assistant's internal action.

The action must come from the valid action phrases provided
below.

If a valid action phrase appears in the user's request,
PRESERVE THAT ACTION.

Do NOT replace it with another action that you think has
the same meaning.

For example:

"boot up the hand-tracking project"
→ boot up, hand tracking
→ start, hand tracking 

NOT:
→ open, hand tracking

"run hello"
→ run, hello

Examples:

User: open chrome
Output:
open, chrome

User: get chrome up for me
Output:
open, chrome

User: start hand tracking
Output:
start, hand tracking

User: run hello
Output:
run, hello

User: switch over to Chrome
Output:
switch to, chrome

User: open chrome with youtube and netflix
Output:
open, chrome, websites = "youtube.com, netflix.com"

User: open chrome on my second monitor
Output:
open, chrome, monitor = 2

User: set the volume to 50
Output:
set volume, None, level = 50

User: make the screen brighter
Output:
brightness up, None

User: what's in my clipboard
Output:
what is in my clipboard, None

User: create alias school for Outlook, Chrome and OneNote
Output:
create alias, school, alias_for = "outlook, chrome, onenote"

"""


# ============================================================
# Context builder (reuse yours)
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
# COMMAND PARSER (string → JSON)
# ============================================================

def parse_command(command_str):
    parts = command_str.strip().split()

    if not parts:
        return []

    action = parts[0]
    target = None
    parameters = {}

    # --------------------------------------------------------
    # Simple actions (no target)
    # --------------------------------------------------------

    no_target = {
        "volume_up",
        "volume_down",
        "brightness_up",
        "brightness_down",
        "get_clipboard",
        "mute_volume",
        "unmute_volume"
    }

    if action in no_target:
        return [{
            "action": action,
            "target": None,
            "parameters": {}
        }]

    # --------------------------------------------------------
    # Extract target
    # --------------------------------------------------------

    if len(parts) > 1:
        target = parts[1]

    # --------------------------------------------------------
    # Parse remaining tokens
    # --------------------------------------------------------

    remaining = parts[2:]

    websites = []
    alias_items = []

    for token in remaining:

        if "=" in token:
            key, value = token.split("=")

            if key == "monitor":
                parameters["monitor"] = int(value)

        elif token.endswith(".com"):
            websites.append(token)

        else:
            alias_items.append(token)

    if websites:
        parameters["websites"] = websites

    # --------------------------------------------------------
    # Special cases
    # --------------------------------------------------------

    # set_volume 50
    if action == "set_volume":
        parameters["level"] = int(parts[1])
        target = None

    # set_brightness 70
    if action == "set_brightness":
        parameters["level"] = int(parts[1])
        target = None

    # create_alias school outlook chrome
    if action == "create_alias":
        alias_name = target
        commands = []

        for item in alias_items:
            commands.append({
                "action": "create_alias",
                "target": alias_name,
                "parameters": {
                    "alias_for": item
                }
            })

        return commands

    return [{
        "action": action,
        "target": target,
        "parameters": parameters
    }]


# ============================================================
# INTERPRET (NEW FLOW)
# ============================================================

def interpret(user_input):

    context = build_context()

    prompt = f"""
        {SYSTEM_PROMPT}

        {json.dumps(context, indent=2)}

        USER REQUEST:
        {user_input}

        OUTPUT ONLY THE CLEAN COMMAND:
"""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0
            },
            think=False
        )

    except Exception as e:
        return f"ERROR: Ollama request failed: {e}"

    command = response["message"]["content"].strip()

    return command