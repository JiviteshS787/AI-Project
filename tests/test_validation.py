import pytest

from assistant.brain.brain import validate_command
from assistant.brain.brain import apps, files, projects, scripts, aliases


# ============================================================
# Helpers
# ============================================================

def check(command):
    valid, error = validate_command(command)

    assert valid, (
        f"\nValidation failed:"
        f"\nCommand: {command}"
        f"\nError: {error}"
    )


def check_invalid(command):
    valid, error = validate_command(command)

    assert not valid, (
        f"\nCommand should have been rejected:"
        f"\nCommand: {command}"
    )


# ============================================================
# OPEN
# ============================================================

@pytest.mark.parametrize("target", list(apps.keys()) + list(files.keys()))
def test_open_targets(target):
    check({
        "action": "open",
        "target": target,
        "parameters": {}
    })


@pytest.mark.parametrize("target", list(apps.keys()) + list(files.keys()))
def test_open_on_monitor(target):
    check({
        "action": "open",
        "target": target,
        "parameters": {
            "monitor": 2
        }
    })


@pytest.mark.parametrize("target", list(apps.keys()) + list(files.keys()))
def test_open_with_websites(target):
    # Only apps that accept websites should receive this parameter.
    if target in apps:
        accepted = apps[target].get("accepted_parameters", {})

        if accepted.get("websites", False):
            check({
                "action": "open",
                "target": target,
                "parameters": {
                    "websites": [
                        "youtube.com",
                        "netflix.com"
                    ]
                }
            })


@pytest.mark.parametrize("target", list(apps.keys()) + list(files.keys()))
def test_open_websites_and_monitor(target):
    if target in apps:
        accepted = apps[target].get("accepted_parameters", {})

        if accepted.get("websites", False):
            check({
                "action": "open",
                "target": target,
                "parameters": {
                    "websites": [
                        "youtube.com",
                        "netflix.com"
                    ],
                    "monitor": 2
                }
            })


# ============================================================
# CLOSE
# ============================================================

@pytest.mark.parametrize("target", list(apps.keys()) + list(files.keys()))
def test_close_targets(target):
    check({
        "action": "close",
        "target": target,
        "parameters": {}
    })


# ============================================================
# PROJECTS
# ============================================================

@pytest.mark.parametrize("target", list(projects.keys()))
def test_start_projects(target):
    check({
        "action": "start_project",
        "target": target,
        "parameters": {}
    })


@pytest.mark.parametrize("target", list(projects.keys()))
def test_stop_projects(target):
    check({
        "action": "stop_project",
        "target": target,
        "parameters": {}
    })


# ============================================================
# SCRIPTS
# ============================================================

@pytest.mark.parametrize("target", list(scripts.keys()))
def test_run_scripts(target):
    check({
        "action": "run_script",
        "target": target,
        "parameters": {}
    })


# ============================================================
# ALIASES
# ============================================================

@pytest.mark.parametrize("alias", list(aliases.keys()))
def test_delete_aliases(alias):
    check({
        "action": "delete_alias",
        "target": alias,
        "parameters": {}
    })


def test_create_alias():
    check({
        "action": "create_alias",
        "target": "test_alias",
        "parameters": {
            "alias_for": "chrome"
        }
    })


# ============================================================
# NO-TARGET ACTIONS
# ============================================================

@pytest.mark.parametrize("action", [
    "volume_up",
    "volume_down",
    "mute_volume",
    "unmute_volume",
    "brightness_up",
    "brightness_down",
    "sleep_system",
    "lock_system",
    "restart_system",
    "shutdown_system",
    "get_clipboard",
    "clear_clipboard",
    "list_monitors",
    "list_running_processes",
    "list_aliases",
    "show_history",
    "delete_history",
    "delete_all_aliases"
])
def test_no_target_actions(action):
    check({
        "action": action,
        "target": None,
        "parameters": {}
    })


# ============================================================
# VOLUME
# ============================================================

@pytest.mark.parametrize("level", [0, 1, 25, 50, 75, 99, 100])
def test_valid_volume(level):
    check({
        "action": "set_volume",
        "target": None,
        "parameters": {
            "level": level
        }
    })


@pytest.mark.parametrize("level", [-1, 101, 200])
def test_invalid_volume(level):
    check_invalid({
        "action": "set_volume",
        "target": None,
        "parameters": {
            "level": level
        }
    })


# ============================================================
# BRIGHTNESS
# ============================================================

@pytest.mark.parametrize("level", [0, 1, 25, 50, 75, 99, 100])
def test_valid_brightness(level):
    check({
        "action": "set_brightness",
        "target": None,
        "parameters": {
            "level": level
        }
    })


@pytest.mark.parametrize("level", [-1, 101, 200])
def test_invalid_brightness(level):
    check_invalid({
        "action": "set_brightness",
        "target": None,
        "parameters": {
            "level": level
        }
    })


# ============================================================
# WINDOWS
# ============================================================

@pytest.mark.parametrize("action", [
    "focus_window",
    "minimize_window",
    "maximize_window"
])
def test_window_actions(action):
    check({
        "action": action,
        "target": "chrome",
        "parameters": {}
    })


@pytest.mark.parametrize("direction", ["left", "right"])
def test_snap_window(direction):
    check({
        "action": "snap_window",
        "target": "chrome",
        "parameters": {
            "direction": direction
        }
    })


def test_move_window_monitor():
    check({
        "action": "move_window_to_monitor",
        "target": "chrome",
        "parameters": {
            "monitor": 2
        }
    })


# ============================================================
# CLIPBOARD
# ============================================================

def test_set_clipboard():
    check({
        "action": "set_clipboard",
        "target": None,
        "parameters": {
            "text": "Hello world"
        }
    })


# ============================================================
# INVALID COMMANDS
# ============================================================

def test_invalid_action():
    check_invalid({
        "action": "does_not_exist",
        "target": "chrome",
        "parameters": {}
    })


def test_missing_target():
    check_invalid({
        "action": "open",
        "target": None,
        "parameters": {}
    })


def test_invalid_target():
    check_invalid({
        "action": "open",
        "target": "this_does_not_exist",
        "parameters": {}
    })


def test_invalid_monitor():
    check_invalid({
        "action": "open",
        "target": "chrome",
        "parameters": {
            "monitor": 0
        }
    })


def test_invalid_monitor_negative():
    check_invalid({
        "action": "open",
        "target": "chrome",
        "parameters": {
            "monitor": -1
        }
    })


def test_invalid_snap_direction():
    check_invalid({
        "action": "snap_window",
        "target": "chrome",
        "parameters": {
            "direction": "up"
        }
    })


def test_invalid_clipboard():
    check_invalid({
        "action": "set_clipboard",
        "target": None,
        "parameters": {
            "text": 123
        }
    })