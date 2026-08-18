import json
import sounddevice as sd
import numpy as np

from assistant.router import execute
from assistant.confirmation import confirm_command

from assistant.brain.brain_groq_json import interpret

from faster_whisper import WhisperModel

# Load model (choose size: tiny / base / small / medium)
model = WhisperModel("base", device="cpu", compute_type="int8")

SAMPLE_RATE = 16000
DURATION = 3  # faster response than 3s


with open("data/apps.json", "r") as file:
    apps = json.load(file)

with open("data/files.json", "r") as file:
    files = json.load(file)

openables = {**apps, **files}


def record_audio():
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return np.squeeze(audio)


def parse_input(input):
    user_input = input.lower().strip()
    if user_input == 'help':
        # What commands are there to call?
        print("Available commands:")
        print("- open <app/file>")
        print("- close <app/file>")
        print("- start <project>")
        print("- stop <project>")
        print("- run <script>")
        print("- create alias <alias name> means <app/file>")
        print("- delete alias <alias name>")
        print("- snap <app/file> to the <left/right>")
        print("- move <app/file> to monitor <number>")
        print("- increase/decrease volume")
        print("- set volume to <number>")
        print("- increase/decrease brightness")
        print("- set brightness to <number>")
        print("- history")
        print("- end")
        print("\n")
        return

    elif user_input == 'end':
        return

    else:
        interpreted_commands = interpret(user_input)
        if isinstance(interpreted_commands, dict) and "error" in interpreted_commands:
            print(f"Error: {interpreted_commands['error']}")
            if "details" in interpreted_commands:
                print(f"Details: {interpreted_commands['details']}")
        else:
            all_commands = interpreted_commands

        #Confirm together
        if all_commands:
            if confirm_command(all_commands):
                for cmd in all_commands:
                    execute(cmd)
    return


device_info = sd.query_devices(sd.default.device[0])
print("Using mic:", device_info["name"])

while True:


    print("🎤 Listening...")

    audio = record_audio()

    # Faster-Whisper expects file OR numpy audio (we pass numpy)
    segments, info = model.transcribe(audio, language="en")

    user_input = " ".join(seg.text for seg in segments).strip()

    if user_input:
        print("You said:", user_input)
        if len(user_input) > 1:
            parse_input(user_input)



