import re
import psutil
import win32process
import pyautogui
import time
import pygetwindow as gw
from difflib import SequenceMatcher

from screeninfo import get_monitors


APP_PROCESS_MAP = {
    "notion": ["notion.exe"],
    "documents": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe"],
    "chrome": ["chrome.exe"],
    "outlook": ["olk.exe", "outlook.exe"],
}


def move_window_to_monitor(name, monitor_number):
    monitors = get_monitors()

    if monitor_number < 1 or monitor_number > len(monitors):
        print(
            f"Monitor {monitor_number} not found. "
            f"Only {len(monitors)} display(s) available."
        )
        return False

    monitor = monitors[monitor_number - 1]

    # Wait for the application window to appear
    win = None

    for _ in range(20):
        win = find_window(name)
        if win:
            break
        time.sleep(0.25)

    if not win:
        print(f"Window not found: {name}")
        return False

    try:
        win.moveTo(monitor.x, monitor.y)
        print(f"{name} moved to monitor {monitor_number}")
        return True
    except Exception as e:
        print(f"Failed to move window: {e}")
        return False


def get_monitors_info():
    monitors = get_monitors()

    for i, monitor in enumerate(monitors, start=1):
        print(
            f"Monitor {i}: "
            f"{monitor.width}x{monitor.height} "
            f"at ({monitor.x}, {monitor.y})"
        )

    return monitors


'''def find_window(name):
    windows = gw.getWindowsWithTitle(name)
    return windows[0] if windows else None'''

########################################################################
#New find window replacement

def _clean_title(title: str) -> str:
    # Remove emoji/symbols, collapse whitespace, lowercase
    title = re.sub(r'[^\w\s\-]', ' ', title, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', title).strip().lower()

def _get_process_name(hwnd) -> str | None:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return None

def _title_score(name: str, title: str) -> float:
    cleaned = _clean_title(title)
    if name in cleaned:
        return 1.0
    return SequenceMatcher(None, name, cleaned).ratio()

def find_window(name: str, min_score: float = 0.55):
    """
    Best-match window lookup:
      1. Match by owning process name (reliable, title-independent)
      2. Fall back to cleaned/fuzzy title matching
    """
    name_lower = name.lower().strip()
    expected_procs = APP_PROCESS_MAP.get(name_lower)
    candidates = []

    for win in gw.getAllWindows():
        if not win.title.strip():
            continue

        if expected_procs:
            proc_name = _get_process_name(win._hWnd)
            if proc_name in expected_procs:
                candidates.append((1.0, win))
                continue

        score = _title_score(name_lower, win.title)
        if score >= min_score:
            candidates.append((score, win))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

########################################################################

def focus_window(name):
    win = find_window(name)
    if win:
        win.activate()
        #print(f"Focused {name}")
        return True
    print(f"Window not found: {name}")
    return False


def minimize_window(name):
    win = find_window(name)
    if win:
        win.minimize()
        #print(f"Minimized {name}")
        return True
    print(f"Window not found: {name}")
    return False


def maximize_window(name):
    win = find_window(name)
    if win:
        win.maximize()
        #print(f"Maximized {name}")
        return True
    print(f"Window not found: {name}")
    return False


def snap_window(name, direction):
    win = find_window(name)

    if not win:
        print(f"Window not found: {name}")
        return False

    try:
        win.activate()
    except:
        pass

    if direction == "left":
        pyautogui.hotkey("win", "left")
    elif direction == "right":
        pyautogui.hotkey("win", "right")
    else:
        print(f"Invalid snap direction: {direction}")
        return False

    #print(f"Snapped {name} {direction}")
    return True