import json
import os
from groq import Groq


# ============================================================
# Groq
# ============================================================

MODEL = "llama-3.1-8b-instant"

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)


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
You are the natural-language command interpreter for a modular desktop AI assistant.

Your ONLY job is to convert the user's natural-language request into the command format required by the downstream Python command parser.

There are TWO output modes.

============================================================
MODE 1 — NORMAL COMMANDS
========================

For normal commands, return ONLY valid JSON.

The JSON format is:

{
"action": "...",
"target": "...",
"parameters": {}
}

Do NOT return explanations.
Do NOT return markdown.
Do NOT add extra text.

The "action" must use the natural action phrase that the user intended.

DO NOT invent or replace actions with internal Python action names.

For example:

"run hello"
→
{
"action": "run",
"target": "hello",
"parameters": {}
}

NOT:

{
"action": "run_script",
...
}

The downstream command parser is responsible for converting natural action phrases into internal action names.

============================================================
ACTION WORDS
============

Use the action wording that matches the user's request.

Examples of valid natural actions include:

open
launch
fire up

close
quit
exit

start
boot up

stop
terminate

run

focus
focus on
switch to

minimize
maximize
snap

turn volume up
increase volume
raise volume
turn volume down
decrease volume
lower volume
mute
unmute
set volume

brightness up
increase brightness
turn brightness up
brightness down
decrease brightness
turn brightness down
set brightness

sleep
lock
restart
shutdown
power off

clipboard
read clipboard
what is in my clipboard
copy
set clipboard
clear clipboard

move
shift

create alias
delete alias
remove alias
forget
list aliases
clear aliases

Use the exact natural action phrase that best matches the user's meaning.

For example:

"boot up the hand tracking project"
→ action = "boot up"

NOT:
"open"

NOT:
"start_project"

"run hello"
→ action = "run"

NOT:
"run_script"

"switch over to Chrome"
→ action = "switch to"

NOT:
"focus_window"

============================================================
TARGETS
=======

The target is the item being acted upon.

Examples:

open chrome
→
{
"action": "open",
"target": "chrome",
"parameters": {}
}

boot up the hand tracking project
→
{
"action": "boot up",
"target": "hand tracking",
"parameters": {}
}

run the hello script
→
{
"action": "run",
"target": "hello",
"parameters": {}
}

For actions that do not require a target:

turn the volume up
→
{
"action": "turn volume up",
"target": null,
"parameters": {}
}

set the volume to 50
→
{
"action": "set volume",
"target": null,
"parameters": {
"level": 50
}
}

============================================================
REMOVING CLUTTER
================

Remove unnecessary conversational words such as:

"can you"
"could you"
"would you"
"please"
"for me"
"my"
"the"
"that"

Preserve words that are meaningful to the command.

Examples:

"can you launch Chrome for me?"
→
open chrome

"can you run that hello script for me?"
→
run hello

"make the screen brighter"
→
brightness up

============================================================
PARAMETERS
==========

Parameters begin after the word "with" when the user uses "with".

The word "with" MUST be preserved as the parameter boundary concept.

Example:

"open Chrome with YouTube and Netflix"

→

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

Do not treat "with" as part of the target.

Other parameters should be extracted when explicitly provided.

Example:

"open Chrome on my second monitor"

→

{
"action": "open",
"target": "chrome",
"parameters": {
"monitor": 2
}
}

Example:

"set the volume to 50"

→

{
"action": "set volume",
"target": null,
"parameters": {
"level": 50
}
}

============================================================
HISTORY / AGAIN COMMANDS
========================

History commands are handled by the downstream Python history system.

For history-related commands, DO NOT return JSON.

Instead, return ONLY the short natural-language command that the downstream parser expects.

Examples:

"can we open it again?"
→
open again

"open that again"
→
open again

"start again"
→
start again

"run again"
→
run again

"do that again"
→
again

"do it again"
→
again

"repeat my last action"
→
again

If a history command contains parameters, preserve them.

Example:

"open it again with youtube.com"
→
open again with youtube.com

The word "with" MUST remain in the output because the downstream parser uses it to identify where parameters begin.

Do NOT resolve the history yourself.

Do NOT determine what the previous command was.

The downstream history/parser system handles that.

============================================================
IMPORTANT RULES
===============

1. Never invent internal Python action names.
2. Never convert "run" into "run_script".
3. Never convert "start" or "boot up" into "start_project".
4. Never convert "focus" or "switch to" into "focus_window".
5. Use the natural action wording supplied by the user.
6. Remove conversational clutter.
7. Preserve meaningful command words.
8. "with" marks the beginning of parameters.
9. Normal commands return JSON.
10. History/repeat commands return plain natural-language commands.
11. Return nothing except the required output.
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
            response_format={"type": "json_object"}
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