import time
import pyperclip
from pathlib import Path

REQUEST_FILE = Path(r"C:\Users\jivit\AI_Project\AI-Project\data\clipboard_request.txt")
DONE_FILE = Path(r"C:\Users\jivit\AI_Project\AI-Project\data\clipboard_done.flag")

def main():
    last_mtime = None
    while True:
        if REQUEST_FILE.exists():
            mtime = REQUEST_FILE.stat().st_mtime
            if mtime != last_mtime:
                text = REQUEST_FILE.read_text(encoding="utf-8")
                pyperclip.copy(text)
                DONE_FILE.write_text(str(mtime))
                last_mtime = mtime
                print(f"Clipboard updated: {text[:50]!r}")
        time.sleep(0.3)

if __name__ == "__main__":
    main()