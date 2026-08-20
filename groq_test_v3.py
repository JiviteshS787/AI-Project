import queue
import numpy as np
import sounddevice as sd
import json
import webrtcvad

from assistant.history import load_history
from assistant.alias_manager import load_aliases

from assistant.router import execute
from assistant.confirmation import confirm_command, format_command
from assistant.brain.brain_groq_json import interpret


from faster_whisper import WhisperModel

from assistant.brain.brain_groq_json import apps, files, projects, scripts, aliases

from assistant.state import state


def get_all_files():
    aliases = load_aliases()
    return {**apps, **files, **projects, **scripts, **aliases}

def get_open_and_close():
    aliases = load_aliases()
    return {**apps, **files, **aliases}

def get_window_control():
    aliases = load_aliases()
    return {**apps, **files, **projects, **aliases}

def get_openables():
    return {**apps, **files, **projects, **scripts}

def get_target_actions():
    open_and_close = get_open_and_close()
    window_control = get_window_control()
    return {
        "open": open_and_close,
        "close": open_and_close,
        "start_project": projects,
        "stop_project": projects,
        "run_script": scripts,
        "delete_aliases": load_aliases(),
        "focus_window": window_control,
        "maximize_window": window_control,
        "minimize_window": window_control,
        "snap_window": window_control,
        "move_window_to_monitor": window_control,
    }

NO_TARGET_ACTIONS = { 
    "list_running_processes": [],
    "show_history": [],
    "delete_history": [],
    "list_aliases": [],
    "delete_all_aliases": [],
    "volume_up": [], 
    "volume_down": [], 
    "mute_volume": [],
    "unmute_volume": [],
    "set_volume": ["level"],
    "brightness_up": [],
    "brightness_down": [],
    "set_brightness": ["level"],
    "sleep_system": [],
    "lock_system": [],
    "shutdown_system": [],
    "restart_system": [],
    "get_clipboard": [],
    "set_clipboard": ["text"],
    "clear_clipboard": [],
    "list_monitors": []
}

#handle -> again, create_alias, none

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
                parameters = command.get("parameters") or {}
                if parameters.get("history") is True:
                    resolved = history_check(command)
                    if resolved:
                        valid_commands.append(resolved)

                elif validate_command(command):
                    valid_commands.append(command)

        if all_commands:
            formatted_commands = []
            for command in all_commands:
                formatted_commands.append(format_command(command))
            state["last_interpretation"] = formatted_commands
            if confirm_command(all_commands):
                for cmd in all_commands:
                    execute(cmd)
    return


def get_accepted_parameters(action, target):
    TARGET_ACTIONS = get_target_actions()

    if action in NO_TARGET_ACTIONS:
        return NO_TARGET_ACTIONS[action]
    if action in TARGET_ACTIONS:
        entry = TARGET_ACTIONS[action].get(target, {})
        return list(entry.get("accepted_parameters", {}).keys())
    return []


def history_check(command):
    history = load_history()

    action = command.get("action")
    parameters = command.get("parameters") or {}

    if action == "again":
        last = history.get("last_action")
        if not last:
            return None
        resolved_action = last.get("action")
        resolved_target = last.get("target")
        old_parameters = last.get("parameters", {})
    else:
        resolved_action = None
        resolved_target = None
        old_parameters = {}
        for entry in reversed(history.get("history", [])):
            entry_action = entry.get("action")
            if action.lower().strip() == entry_action.lower().strip():
                resolved_action = action
                resolved_target = entry.get("target")
                old_parameters = entry.get("parameters", {})
                break
        if resolved_action is None:
            return None

    accepted = get_accepted_parameters(resolved_action, resolved_target)
    for key in parameters:
        if key == "history":
            continue
        if key not in accepted:
            return None

    new_parameters = {k: v for k, v in parameters.items() if k != "history"}

    resolved = {
        "action": resolved_action,
        "target": resolved_target,
        "parameters": {**old_parameters, **new_parameters}
    }

    if validate_command(resolved):
        return resolved
    
    return None


PARAM_TYPE_CHECKS = {
    "level": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 100,
}


def validate_command(command):
    action = command.get("action")
    target = command.get("target")
    parameters = command.get("parameters") or {}
    TARGET_ACTIONS = get_target_actions()

    if action == "create_alias":
        for entry in parameters:
            if entry.lower().strip() not in get_all_files():
                return False
        return True

    elif action == "none":
        if target is not None:
            return False
        return parameters == {}

    elif action in NO_TARGET_ACTIONS:
        if target is not None:
            return False

        accepted_parameters = NO_TARGET_ACTIONS[action]
        for key, value in parameters.items():
            if key not in accepted_parameters:
                return False
            check = PARAM_TYPE_CHECKS.get(key)
            if check and not check(value):
                return False
        return True

    elif action in TARGET_ACTIONS:
        file_to_check = TARGET_ACTIONS[action]

        if target not in file_to_check:
            return False

        accepted_parameters = file_to_check[target].get("accepted_parameters", {})
        for key in parameters:
            if accepted_parameters.get(key) is not True:
                return False
        return True

    else:
        return False


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

    state["last_input"] = user_input

    if command:
        parse_input(command)