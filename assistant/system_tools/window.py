import pygetwindow as gw, pyautogui

from screeninfo import get_monitors


def move_window_to_monitor(name, monitor_number):
    win = find_window(name)

    if not win:
        print(f"Window not found: {name}")
        return False

    monitors = get_monitors()

    if monitor_number < 1 or monitor_number > len(monitors):
        print(f"Monitor {monitor_number} not found")
        return False

    monitor = monitors[monitor_number - 1]

    try:
        win.moveTo(monitor.x, monitor.y)
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


def find_window(name):
    windows = gw.getWindowsWithTitle(name)
    return windows[0] if windows else None


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