import pyperclip, time
from pathlib import Path

REQUEST_FILE = Path(r"C:\Users\jivit\AI_Project\AI-Project\data\clipboard_request.txt")
DONE_FILE = Path(r"C:\Users\jivit\AI_Project\AI-Project\data\clipboard_done.flag")

def get_clipboard():
    text = pyperclip.paste()
    print(f"Clipboard: {text}")
    return text

def set_clipboard(text, timeout=2.0):
    REQUEST_FILE.write_text(text, encoding="utf-8")
    expected_mtime = str(REQUEST_FILE.stat().st_mtime)

    deadline = time.time() + timeout
    while time.time() < deadline:
        if DONE_FILE.exists() and DONE_FILE.read_text() == expected_mtime:
            print("Clipboard updated")
            return True
        time.sleep(0.05)

    print("Clipboard update timed out")
    return False


def clear_clipboard():
    pyperclip.copy("")
    print("Clipboard cleared")
    return True