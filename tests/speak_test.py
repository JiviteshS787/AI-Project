from elevenlabs.play import play as elevenlabs_play

path = r"C:\Users\jivit\AI_Project\AI-Project\assistant\audio\TTS_response\response.mp3"

with open(path, "rb") as f:
    audio_bytes = f.read()

elevenlabs_play(audio_bytes)
print("Done")