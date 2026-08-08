import pygetwindow as gw
import pyautogui


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