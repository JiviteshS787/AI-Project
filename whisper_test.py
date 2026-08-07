import whisper

model = whisper.load_model("base")

result = model.transcribe("test_audio.m4a")

print(result["text"])