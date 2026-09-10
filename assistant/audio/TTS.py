from elevenlabs.client import ElevenLabs
import os

client = ElevenLabs(api_key=os.environ["VOICE_API_KEY"])

BASE_DIR = os.path.join(os.path.dirname(__file__), "TTS_response")
os.makedirs(BASE_DIR, exist_ok = True)

out_path = os.path.join(BASE_DIR, "response.mp3")


def _speak(text, voice_id="KLON7Nwan8mJxpF2R8Yw", model_id="eleven_v3"):
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=text,
        output_format = "mp3_44100_128"
    )

    chunks = []
    for i, chunk in enumerate(audio):
        if chunk:
            chunks.append(chunk)

    audio_data = b"".join(chunks)

    with open(out_path, "wb") as f:
        f.write(audio_data)

