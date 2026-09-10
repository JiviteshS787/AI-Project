import sounddevice as sd
from assistant.audio.TTS import out_path
from elevenlabs.play import play as elevenlabs_play
import time

PREFERRED_OUTPUT_NAMES = ["WH-1000XM5"]


def find_output_device():
    devices = sd.query_devices()
    for name_fragment in PREFERRED_OUTPUT_NAMES:
        for i, dev in enumerate(devices):
            if dev["max_output_channels"] > 0 and name_fragment.lower() in dev["name"].lower():
                return i
    return None


def get_preferred_output_device():
    idx = find_output_device()
    if idx is not None:
        try:
            sd.check_output_settings(device=idx)
            return idx
        except Exception as e:
            print(f"Preferred output device failed verification: {e}")
    return None


def play_audio(path=None):
    path = path or out_path

    with open(path, "rb") as f:
        audio_bytes = f.read()
    elevenlabs_play(audio_bytes)
    time.sleep(0.3)