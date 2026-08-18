import queue
import numpy as np
import sounddevice as sd
import webrtcvad

from assistant.router import execute
from assistant.confirmation import confirm_command
from assistant.brain.brain_groq_json import interpret

from faster_whisper import WhisperModel

from assistant.command_decipher import openables


# ---------- config ----------
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SILENCE_LIMIT_FRAMES = 20
VAD_AGGRESSIVENESS = 2
WAKE_WORD = "assistant"

model = WhisperModel("base", device="cpu", compute_type="int8")
vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
audio_q = queue.Queue()


# ---------- audio capture ----------

#Runs whenever a new audio chunk is ready -> automatic call
def _callback(indata, frames, time_info, status):
    #indata -> new captured sample
    if status:
        print("Stream status:", status)
    #Put new chunk into the queue
    audio_q.put(indata.copy())


#Convert to type accepted by WebRTC VAD
def _frame_to_pcm16(frame):
    clipped = np.clip(frame, -1.0, 1.0)
    return (clipped * 32767).astype(np.int16).tobytes()


#Returns true/false is sound/speed detected
def is_speech(frame):
    return vad.is_speech(_frame_to_pcm16(frame), SAMPLE_RATE)


#Actual listening function
def listen_for_speech():
    print("🎤 Listening...")
    buffer = []
    silence_counter = 0
    speech_started = False
    #Prepend leftover from last time -> ensures no audio is ever lost.
    leftover = np.empty((0,), dtype=np.float32)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=FRAME_SIZE,callback=_callback,):
        while True:
            block = audio_q.get()
            frame = np.concatenate([leftover, np.squeeze(block)])

            #Important to always send FRAME_SIZE chunks to the VAD
            while len(frame) >= FRAME_SIZE:
                chunk, frame = frame[:FRAME_SIZE], frame[FRAME_SIZE:]
                #Check if is speech
                speech = is_speech(chunk)

                #If speech, add to buffer, reset silence, set speech to true
                if speech:
                    buffer.append(chunk)
                    speech_started = True
                    silence_counter = 0

                #If not speech, increment silence
                elif speech_started:
                    buffer.append(chunk)
                    silence_counter += 1

                #To detect an end of speech, SILENCE_LIMIT_FRAMES is the amount of time to be silent
                #before a command is assumed to be complete.
                if speech_started and silence_counter > SILENCE_LIMIT_FRAMES:
                    return np.concatenate(buffer) if buffer else None
                
            #After slicing to 480 frames, if anything is left it is saved for the next run
            leftover = frame


# ---------- command parsing ----------
def parse_input(input):
    user_input = input.lower().strip()
    if user_input == 'help':
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
        all_commands = None
        valid_commands = []
        interpreted_commands = interpret(user_input)
        if isinstance(interpreted_commands, dict) and "error" in interpreted_commands:
            print(f"Error: {interpreted_commands['error']}")
            if "details" in interpreted_commands:
                print(f"Details: {interpreted_commands['details']}")
        else:
            all_commands = interpreted_commands
            for command in all_commands:
                if validate_command(command):
                    valid_commands.append(command)

        if all_commands:
            if confirm_command(all_commands):
                for cmd in all_commands:
                    execute(cmd)
    return

def validate_command(command):
    action = command.get("action")
    target = command.get("target")
    parameters = command.get("parameters") or {}

    assigned_parameters = parameters.keys()

    accepted_parameters = (openables.get(target, {}).get("accepted_parameters", {}))

    for key in assigned_parameters:
        if accepted_parameters.get(key) is not True:
            return False

    return True

# ---------- main loop ----------
device_info = sd.query_devices(sd.default.device[0])
print("Using mic:", device_info["name"])

while True:
    audio = listen_for_speech()

    if audio is None or len(audio) == 0:
        continue

    segments, _ = model.transcribe(audio, language="en")
    user_input = " ".join(seg.text for seg in segments).strip().lower()

    if not user_input:
        continue

    print("You said:", user_input)

    if WAKE_WORD not in user_input:
        print("⏭ Ignored (no wake word)")
        continue

    command = user_input.replace(WAKE_WORD, "").strip()

    if command:
        parse_input(command)