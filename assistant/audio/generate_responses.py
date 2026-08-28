# generate_acks.py
import os
from groq import Groq

client = Groq(api_key=os.environ("GROQ_API_KEY_2"))  # reuse one of your rotation keys

VOICE = "troy"

MODEL = "canopylabs/orpheus-v1-english"  # pick one you like — see note below on listing voices

ACKS = {
    "generic": [
        "[professionally] Understood",
        "Right away sir",
        "Certainly",
        "Working on it",
    ],
    "restart": [
        "[professionally] Restarting now",
        "See you in a minute"
    ],
    "shutdown": [
        "[professionally] Shutting down goodbye sir",
        "Goodbye Sir"
    ],
    "sleep": [
        "Putting the system to sleep see you later sir.",
        "[calmly] Entering sleep mode"
    ],
    "lock": [
        "[professionally] Alright locking up sir",
        "Locking the system sir.",
    ],
}

BASE_DIR = os.path.join(os.path.dirname(__file__), "acks")

def generate():
    for action, phrases in ACKS.items():
        folder = os.path.join(BASE_DIR, action)
        os.makedirs(folder, exist_ok=True)
        for i, phrase in enumerate(phrases):
            out_path = os.path.join(folder, f"{action}_{i}.wav")
            response = client.audio.speech.create(
                model=MODEL,
                voice=VOICE,
                input=phrase,
                response_format="wav",
            )
            response.write_to_file(out_path)
            print(f"Saved {out_path}")

if __name__ == "__main__":
    generate()