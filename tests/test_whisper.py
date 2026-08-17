import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

# Load model (choose size: tiny / base / small / medium)
model = WhisperModel("base", device="cpu", compute_type="int8")

SAMPLE_RATE = 16000
DURATION = 2  # faster response than 3s

INPUT_DEVICE = 1  # change if needed (your Realtek mic worked earlier)

def record_audio():
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32", device=INPUT_DEVICE)
    sd.wait()
    return np.squeeze(audio)

while True:
    print("🎤 Listening...")

    audio = record_audio()

    # Faster-Whisper expects file OR numpy audio (we pass numpy)
    segments, info = model.transcribe(audio, language="en")

    text = " ".join(seg.text for seg in segments).strip()

    if text:
        print("You said:", text)

        # 🔥 Hook into your assistant here
        # execute_command(text)