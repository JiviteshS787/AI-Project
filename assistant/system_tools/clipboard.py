import pyperclip


def get_clipboard():
    text = pyperclip.paste()
    print(f"Clipboard: {text}")
    return text


def set_clipboard(text):
    pyperclip.copy(text)
    print("Clipboard updated")
    return True


def clear_clipboard():
    pyperclip.copy("")
    print("Clipboard cleared")
    return True