"""
LLM interpretation stress tests for the AI Assistant.

This file tests assistant.brain.interpret() using Gemini.

IMPORTANT:
- These tests DO NOT execute commands.
- They only test whether Gemini converts natural language
  into the correct JSON command structure.
- Tests are intentionally broad and include natural,
  conversational, awkward, and unusual wording.
- A delay is used between Gemini requests to reduce the
  chance of hitting the free-tier request-per-minute limit.
"""

import json
import time

from assistant.brain import interpret


# ============================================================
# Configuration
# ============================================================

DELAY_BETWEEN_REQUESTS = 15

# Start from this test number.
# Set to 1 to start from the beginning.
START_TEST = 1

# Stop immediately when Gemini returns a 429.
STOP_ON_RATE_LIMIT = True

# Save progress so interrupted tests can be resumed.
CHECKPOINT_FILE = "tests/brain_llm_checkpoint.json"

# Save every completed result.
RESULTS_FILE = "tests/brain_llm_results.json"

PRINT_RESPONSES = True


# ============================================================
# Test definitions
# ============================================================

TESTS = [

    # ========================================================
    # BASIC OPENING
    # ========================================================

    {
        "name": "Open Chrome",
        "input": "open chrome",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Launch Chrome",
        "input": "launch chrome",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Fire up Chrome",
        "input": "fire up chrome",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Bring up browser",
        "input": "can you bring up my browser?",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Get Chrome running",
        "input": "get chrome up for me",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # SYNONYMS / NATURAL LANGUAGE
    # ========================================================

    {
        "name": "Browser synonym",
        "input": "open my browser",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Google synonym",
        "input": "bring up google",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "VS Code natural language",
        "input": "get my code editor up",
        "expected": [
            {
                "action": "open",
                "target": "visual studio",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Calculator natural language",
        "input": "I need the calculator",
        "expected": [
            {
                "action": "open",
                "target": "calculator",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Notion natural language",
        "input": "could you open my Notion?",
        "expected": [
            {
                "action": "open",
                "target": "notion",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # FILES
    # ========================================================

    {
        "name": "Open downloads",
        "input": "open my downloads",
        "expected": [
            {
                "action": "open",
                "target": "downloads",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Open documents naturally",
        "input": "can you pull up my documents folder?",
        "expected": [
            {
                "action": "open",
                "target": "documents",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Open AI project folder",
        "input": "open my AI assistant project folder",
        "expected": [
            {
                "action": "open",
                "target": "ai-project",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Open hand tracking folder",
        "input": "open the hand tracking folder",
        "expected": [
            {
                "action": "open",
                "target": "hand tracking",
                "parameters": {}
            }
        ]
    },

    {
        "name": "File synonym",
        "input": "show me my downloaded files",
        "expected": [
            {
                "action": "open",
                "target": "downloads",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # PROJECTS
    # ========================================================

    {
        "name": "Start hand tracking",
        "input": "start hand tracking",
        "expected": [
            {
                "action": "start_project",
                "target": "hand-tracking",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Launch hand tracking project",
        "input": "launch my hand tracking project",
        "expected": [
            {
                "action": "start_project",
                "target": "hand-tracking",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Boot hand tracking",
        "input": "boot up the hand tracking project",
        "expected": [
            {
                "action": "start_project",
                "target": "hand-tracking",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Get project running",
        "input": "get my hand tracking project running",
        "expected": [
            {
                "action": "start_project",
                "target": "hand-tracking",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # SCRIPTS
    # ========================================================

    {
        "name": "Run hello",
        "input": "run hello",
        "expected": [
            {
                "action": "run_script",
                "target": "hello",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Execute hello script",
        "input": "execute my hello script",
        "expected": [
            {
                "action": "run_script",
                "target": "hello",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Start hello script naturally",
        "input": "can you run that hello script for me?",
        "expected": [
            {
                "action": "run_script",
                "target": "hello",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # CLOSE
    # ========================================================

    {
        "name": "Close Chrome",
        "input": "close chrome",
        "expected": [
            {
                "action": "close",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Quit Chrome",
        "input": "quit chrome",
        "expected": [
            {
                "action": "close",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Exit browser",
        "input": "get my browser out of here",
        "expected": [
            {
                "action": "close",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # MULTIPLE APPLICATIONS
    # ========================================================

    {
        "name": "Open two apps",
        "input": "open chrome and notepad",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            },
            {
                "action": "open",
                "target": "notepad",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Open three apps",
        "input": "open chrome, notion and outlook",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            },
            {
                "action": "open",
                "target": "notion",
                "parameters": {}
            },
            {
                "action": "open",
                "target": "outlook",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Natural three-app request",
        "input": "I need Chrome, Outlook and OneNote open",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            },
            {
                "action": "open",
                "target": "outlook",
                "parameters": {}
            },
            {
                "action": "open",
                "target": "onenote",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # WEBSITES
    # ========================================================

    {
        "name": "Chrome YouTube",
        "input": "open chrome with youtube",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "websites": ["youtube.com"]
                }
            }
        ]
    },

    {
        "name": "Chrome YouTube Netflix",
        "input": "open chrome with youtube and netflix",
        "expected": [
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
        ]
    },

    {
        "name": "Natural website request",
        "input": "get Chrome going with YouTube and Netflix ready",
        "expected": [
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
        ]
    },

    {
        "name": "Explicit domains",
        "input": "open chrome with youtube.com and github.com",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "websites": [
                        "youtube.com",
                        "github.com"
                    ]
                }
            }
        ]
    },


    # ========================================================
    # MONITORS
    # ========================================================

    {
        "name": "Chrome monitor two",
        "input": "open chrome on my second monitor",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },

    {
        "name": "Chrome screen two",
        "input": "launch chrome on screen 2",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },

    {
        "name": "Chrome websites monitor two",
        "input": "open chrome with youtube and netflix on my second monitor",
        "expected": [
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
        ]
    },

    {
        "name": "Chrome second display",
        "input": "put Chrome on my second display",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },

    {
        "name": "File monitor two",
        "input": "open my downloads on the second monitor",
        "expected": [
            {
                "action": "open",
                "target": "downloads",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },


    # ========================================================
    # WINDOW CONTROL
    # ========================================================

    {
        "name": "Focus Chrome",
        "input": "focus chrome",
        "expected": [
            {
                "action": "focus_window",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Switch to Chrome",
        "input": "switch over to Chrome",
        "expected": [
            {
                "action": "focus_window",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Minimize Chrome",
        "input": "minimize chrome",
        "expected": [
            {
                "action": "minimize_window",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Maximize Chrome",
        "input": "make chrome full screen",
        "expected": [
            {
                "action": "maximize_window",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Snap Chrome left",
        "input": "snap chrome to the left",
        "expected": [
            {
                "action": "snap_window",
                "target": "chrome",
                "parameters": {
                    "direction": "left"
                }
            }
        ]
    },

    {
        "name": "Snap Chrome right",
        "input": "put chrome on the right side",
        "expected": [
            {
                "action": "snap_window",
                "target": "chrome",
                "parameters": {
                    "direction": "right"
                }
            }
        ]
    },

    {
        "name": "Move Chrome monitor two",
        "input": "move chrome to my second monitor",
        "expected": [
            {
                "action": "move_window_to_monitor",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },

    {
        "name": "Move Chrome screen two",
        "input": "can you put Chrome on screen 2?",
        "expected": [
            {
                "action": "move_window_to_monitor",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },


    # ========================================================
    # VOLUME
    # ========================================================

    {
        "name": "Volume up",
        "input": "turn it up",
        "expected": [
            {
                "action": "volume_up",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Volume louder",
        "input": "make the volume louder",
        "expected": [
            {
                "action": "volume_up",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Volume down",
        "input": "turn the volume down",
        "expected": [
            {
                "action": "volume_down",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Mute",
        "input": "mute my computer",
        "expected": [
            {
                "action": "mute_volume",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Unmute",
        "input": "okay, turn the sound back on",
        "expected": [
            {
                "action": "unmute_volume",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Set volume",
        "input": "set the volume to 50",
        "expected": [
            {
                "action": "set_volume",
                "target": None,
                "parameters": {
                    "level": 50
                }
            }
        ]
    },

    {
        "name": "Set volume naturally",
        "input": "it's too loud, put the volume around 30 percent",
        "expected": [
            {
                "action": "set_volume",
                "target": None,
                "parameters": {
                    "level": 30
                }
            }
        ]
    },


    # ========================================================
    # BRIGHTNESS
    # ========================================================

    {
        "name": "Brightness up",
        "input": "make the screen brighter",
        "expected": [
            {
                "action": "brightness_up",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Brightness down",
        "input": "the screen is too bright",
        "expected": [
            {
                "action": "brightness_down",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Set brightness",
        "input": "set my brightness to 60 percent",
        "expected": [
            {
                "action": "set_brightness",
                "target": None,
                "parameters": {
                    "level": 60
                }
            }
        ]
    },


    # ========================================================
    # CLIPBOARD
    # ========================================================

    {
        "name": "Read clipboard",
        "input": "what's in my clipboard?",
        "expected": [
            {
                "action": "get_clipboard",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Clear clipboard",
        "input": "clear my clipboard",
        "expected": [
            {
                "action": "clear_clipboard",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Set clipboard",
        "input": "put hello world in my clipboard",
        "expected": [
            {
                "action": "set_clipboard",
                "target": None,
                "parameters": {
                    "text": "hello world"
                }
            }
        ]
    },

    {
        "name": "Copy longer clipboard text",
        "input": "copy this into my clipboard: Hello, this is a test!",
        "expected": [
            {
                "action": "set_clipboard",
                "target": None,
                "parameters": {
                    "text": "Hello, this is a test!"
                }
            }
        ]
    },


    # ========================================================
    # POWER
    # ========================================================

    {
        "name": "Sleep",
        "input": "put my computer to sleep",
        "expected": [
            {
                "action": "sleep_system",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Lock",
        "input": "lock my computer",
        "expected": [
            {
                "action": "lock_system",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Restart",
        "input": "I want to restart the computer",
        "expected": [
            {
                "action": "restart_system",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Shutdown",
        "input": "turn the computer off",
        "expected": [
            {
                "action": "shutdown_system",
                "target": None,
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # ALIASES — SINGLE TARGET
    # ========================================================

    {
        "name": "Create browser alias",
        "input": "create an alias called browser for Chrome",
        "expected": [
            {
                "action": "create_alias",
                "target": "browser",
                "parameters": {
                    "alias_for": "chrome"
                }
            }
        ]
    },

    {
        "name": "Remember browser alias",
        "input": "remember Chrome as browser",
        "expected": [
            {
                "action": "create_alias",
                "target": "browser",
                "parameters": {
                    "alias_for": "chrome"
                }
            }
        ]
    },


    # ========================================================
    # ALIASES — MULTIPLE TARGETS
    # ========================================================

    {
        "name": "School2 three apps",
        "input": "create alias school2 for Outlook, Chrome and OneNote",
        "expected": [
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },

    {
        "name": "Natural school alias",
        "input": "I want school2 to open Outlook, Chrome, and OneNote",
        "expected": [
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },

    {
        "name": "Conversational school alias",
        "input": "make me an alias named school2 that opens Outlook, Chrome and OneNote whenever I use it",
        "expected": [
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },

    {
        "name": "School alias with and",
        "input": "remember school2 as Outlook and Chrome and OneNote",
        "expected": [
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school2",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },


    # ========================================================
    # ALIASES — NATURAL / WEIRD WORDING
    # ========================================================

    {
        "name": "Alias weird wording",
        "input": "make schoolstuff open my browser, mail and notes",
        "expected": [
            {
                "action": "create_alias",
                "target": "schoolstuff",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "schoolstuff",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "schoolstuff",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },

    {
        "name": "Alias conversational",
        "input": "I'd like a shortcut called school that brings up Chrome, Outlook and OneNote",
        "expected": [
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "chrome"
                }
            },
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "outlook"
                }
            },
            {
                "action": "create_alias",
                "target": "school",
                "parameters": {
                    "alias_for": "onenote"
                }
            }
        ]
    },


    # ========================================================
    # ALIASES — DELETE / LIST
    # ========================================================

    {
        "name": "Delete alias",
        "input": "forget my school2 alias",
        "expected": [
            {
                "action": "delete_alias",
                "target": "school2",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Remove alias",
        "input": "get rid of the school2 alias",
        "expected": [
            {
                "action": "delete_alias",
                "target": "school2",
                "parameters": {}
            }
        ]
    },

    {
        "name": "List aliases",
        "input": "what aliases do I have?",
        "expected": [
            {
                "action": "list_aliases",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Delete all aliases",
        "input": "wipe all my aliases",
        "expected": [
            {
                "action": "delete_all_aliases",
                "target": None,
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # HISTORY
    # ========================================================

    {
        "name": "Show history",
        "input": "what have I done recently?",
        "expected": [
            {
                "action": "show_history",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Delete history",
        "input": "clear my command history",
        "expected": [
            {
                "action": "delete_history",
                "target": None,
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # MONITOR LIST
    # ========================================================

    {
        "name": "List monitors",
        "input": "what monitors do I have?",
        "expected": [
            {
                "action": "list_monitors",
                "target": None,
                "parameters": {}
            }
        ]
    },

    {
        "name": "Show displays",
        "input": "show me my displays",
        "expected": [
            {
                "action": "list_monitors",
                "target": None,
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # FUZZY / IMPERFECT NATURAL LANGUAGE
    # ========================================================

    {
        "name": "Misspelled Chrome",
        "input": "opne chorme",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Awkward Chrome",
        "input": "chrome please",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Casual browser",
        "input": "yo open up my browser",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {}
            }
        ]
    },

    {
        "name": "Natural Notion",
        "input": "I need Notion open",
        "expected": [
            {
                "action": "open",
                "target": "notion",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # MIXED / COMPLEX COMMANDS
    # ========================================================

    {
        "name": "Multiple apps plus monitor",
        "input": "open Chrome and Notion on my second monitor",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "monitor": 2
                }
            },
            {
                "action": "open",
                "target": "notion",
                "parameters": {
                    "monitor": 2
                }
            }
        ]
    },

    {
        "name": "Chrome websites and Notion",
        "input": "open Chrome with YouTube and Netflix, then open Notion",
        "expected": [
            {
                "action": "open",
                "target": "chrome",
                "parameters": {
                    "websites": [
                        "youtube.com",
                        "netflix.com"
                    ]
                }
            },
            {
                "action": "open",
                "target": "notion",
                "parameters": {}
            }
        ]
    },


    # ========================================================
    # AGAIN / CONTEXTUAL
    # ========================================================

    {
        "name": "Again",
        "input": "again",
        "special": True
    },

    {
        "name": "Do that again",
        "input": "do that again",
        "special": True
    },


    # ========================================================
    # INVALID / SHOULD NOT INVENT
    # ========================================================

    {
        "name": "Unknown application",
        "input": "open Spotify",
        "special": True
    },

    {
        "name": "Unknown project",
        "input": "start my Minecraft project",
        "special": True
    },

    {
        "name": "Unknown script",
        "input": "run my weather script",
        "special": True
    },

    {
        "name": "Unknown alias target",
        "input": "create alias gaming for Spotify",
        "special": True
    },

]


# ============================================================
# Comparison helpers
# ============================================================

def normalize_command(command):
    """
    Normalize a command for comparison.

    This makes comparison less sensitive to irrelevant
    differences such as omitted target=None.
    """

    if not isinstance(command, dict):
        return command

    return {
        "action": command.get("action"),
        "target": command.get("target"),
        "parameters": command.get("parameters", {})
    }


def normalize_result(result):
    if isinstance(result, dict):
        result = [result]

    if not isinstance(result, list):
        return result

    return [
        normalize_command(command)
        for command in result
    ]


def commands_match(actual, expected):
    """
    Compare commands.

    For most commands, order matters because multiple commands
    are executed sequentially.

    For create_alias, however, the order of targets does not
    matter. Creating school2 for Chrome, Outlook and OneNote
    is equivalent regardless of target order.
    """

    actual = normalize_result(actual)
    expected = normalize_result(expected)

    if not isinstance(actual, list) or not isinstance(expected, list):
        return actual == expected

    # Alias creation order should not matter.
    if all(
        isinstance(x, dict)
        and x.get("action") == "create_alias"
        for x in actual + expected
    ):
        actual = sorted(
            actual,
            key=lambda x: (
                x.get("target", ""),
                x.get("parameters", {}).get("alias_for", "")
            )
        )

        expected = sorted(
            expected,
            key=lambda x: (
                x.get("target", ""),
                x.get("parameters", {}).get("alias_for", "")
            )
        )

    return actual == expected


# ============================================================
# Checkpoint helpers
# ============================================================

def save_checkpoint(test_number, passed, failed, skipped, failures):
    data = {
        "next_test": test_number,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "failures": failures
    }

    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        return None


def save_results(results):
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)
    


# ============================================================
# Test runner
# ============================================================

def run_tests():

    total = len(TESTS)
    passed = 0
    failed = 0
    skipped = 0

    failures = []

    print("=" * 75)
    print("AI ASSISTANT — GEMINI INTERPRETATION STRESS TEST")
    print("=" * 75)

    print(f"Total tests: {total}")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print()

    for number, test in enumerate(TESTS, 1):

        name = test["name"]
        user_input = test["input"]

        print("-" * 75)
        print(f"TEST {number}/{total}: {name}")
        print(f"Input: {user_input}")

        # ----------------------------------------------------
        # Special contextual tests
        # ----------------------------------------------------

        if test.get("special"):

            print("SKIPPED")
            print("Reason: requires previous assistant state or")
            print("requires testing unknown-target behavior separately.")

            skipped += 1
            continue

        # ----------------------------------------------------
        # Call Gemini
        # ----------------------------------------------------

        try:
            result = interpret(user_input)

        except Exception as e:
            print("FAILED")
            print(f"Exception: {type(e).__name__}: {e}")

            failed += 1

            failures.append({
                "name": name,
                "input": user_input,
                "expected": test.get("expected"),
                "actual": f"EXCEPTION: {e}"
            })

            # ----------------------------------------------------
            # Stop immediately on Gemini quota/rate-limit errors
            # ----------------------------------------------------

            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):

                print()
                print("=" * 75)
                print("GEMINI QUOTA/RATE LIMIT REACHED")
                print("=" * 75)
                print("Stopping test run.")
                print(f"Resume from test {number + 1} later.")

                save_checkpoint(
                    number + 1,
                    passed,
                    failed,
                    skipped,
                    failures
                )

                return False

            time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        # ----------------------------------------------------
        # Print result
        # ----------------------------------------------------

        if PRINT_RESPONSES:

            print("Gemini returned:")

            print(
                json.dumps(
                    result,
                    indent=4,
                    ensure_ascii=False
                )
            )

        # ----------------------------------------------------
        # Compare
        # ----------------------------------------------------

        expected = test.get("expected")

        if commands_match(result, expected):

            print("PASS")
            passed += 1

        else:

            print("FAIL")

            print("\nExpected:")
            print(
                json.dumps(
                    expected,
                    indent=4,
                    ensure_ascii=False
                )
            )

            print("\nActual:")
            print(
                json.dumps(
                    result,
                    indent=4,
                    ensure_ascii=False
                )
            )

            failed += 1

            failures.append({
                "name": name,
                "input": user_input,
                "expected": expected,
                "actual": result
            })

        # ----------------------------------------------------
        # Rate-limit protection
        # ----------------------------------------------------

        if number < total:

            print(
                f"\nWaiting {DELAY_BETWEEN_REQUESTS}s "
                "before next Gemini request..."
            )

            time.sleep(DELAY_BETWEEN_REQUESTS)

    # ========================================================
    # Final report
    # ========================================================

    print()
    print("=" * 75)
    print("FINAL RESULTS")
    print("=" * 75)

    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")

    if failed == 0:

        print()
        print("ALL NON-SKIPPED TESTS PASSED!")

    else:

        print()
        print("=" * 75)
        print("FAILED TESTS")
        print("=" * 75)

        for failure in failures:

            print()
            print(f"TEST: {failure['name']}")
            print(f"INPUT: {failure['input']}")

            print("\nEXPECTED:")
            print(
                json.dumps(
                    failure["expected"],
                    indent=4,
                    ensure_ascii=False
                )
            )

            print("\nACTUAL:")
            print(
                json.dumps(
                    failure["actual"],
                    indent=4,
                    ensure_ascii=False
                )
            )

    return failed == 0


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    success = run_tests()

    if not success:
        raise SystemExit(1)
