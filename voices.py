import os
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=os.environ["VOICE_API_KEY"])

response = client.voices.get_all()
for voice in response.voices:
    print(voice.voice_id, "-", voice.name)