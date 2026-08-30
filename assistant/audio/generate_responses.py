import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VOICE = "diana"

MODEL = "canopylabs/orpheus-v1-english"

ACKS = {
    "generic": [
        "[professionally] Understood.",
        "Right away, sir.",
        "Certainly.",
        "Working on it.",
    ],
    "restart": [
        "[professionally] Restarting now.",
        "See you in a minute.",
    ],
    "shutdown": [
        "[professionally] Shutting down. Goodbye, sir.",
        "Goodbye, sir.",
    ],
    "sleep": [
        "Putting the system to sleep. See you later, sir.",
        "[calmly] Entering sleep mode.",
    ],
    "lock": [
        "[professionally] Alright, locking up, sir.",
        "Locking the system, sir.",
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