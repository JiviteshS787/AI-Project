import threading, os
from assistant.audio.TTS import _speak, out_path

from assistant.brain.web_search_handler import classify_query

from assistant.audio.play_audio import play_audio

from assistant.external_connectors.news_handler import handle_news
from assistant.external_connectors.weather_handler import handle_weather
from assistant.external_connectors.web_search import search


def trigger_speech_pipeline(command):
    thread = threading.Thread(target=_speech_pipeline_worker, args=(command,), daemon=True)
    thread.start()
    return thread

def _speech_pipeline_worker(command):
    parameters = command.get("parameters") or {}
    routed = classify_query(parameters.get("query")) 
    sub_action = routed["action"]
    sub_params = routed["parameters"]

    try:
        if sub_action == "weather":
            text = handle_weather(sub_params.get("location"))
        elif sub_action == "news":
            text = handle_news(sub_params.get("topic"))
        else:
            text = search(command)

        if not text:
            print("No text generated for speech pipeline")
            return

        _speak(text)
        play_audio()

    except Exception as e:
        print(f"Speech pipeline failed: {e}")