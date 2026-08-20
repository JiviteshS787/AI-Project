import requests

requests.post("http://localhost:8000/event", json={
    "type": "open",
    "app": "chrome"
})