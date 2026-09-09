from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os

client = ElevenLabs(api_key=os.environ["VOICE_API_KEY"])

def speak(text, voice_id="KLON7Nwan8mJxpF2R8Yw", model_id="eleven_v3"):
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=text,
    )
    return audio

def play_audio(command):
    audio = speak(command)
    play(audio)
    return