import requests

HOME_LAT = 43.86
HOME_LON = -79.34  #Markham -> Default

def geocode(location: str):
    r = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={
        "name": location,
        "count": 1,
    })
    results = r.json().get("results")
    if not results:
        return None
    return results[0]["latitude"], results[0]["longitude"]

def handle_weather(location: str | None) -> str:
    if location:
        coords = geocode(location)
        if not coords:
            return f"I couldn't find a location called {location}."
        lat, lon = coords
        label = location
    else:
        lat, lon = HOME_LAT, HOME_LON
        label = "your area"

    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,wind_speed_10m",
    })
    data = r.json().get("current", {})
    temp = data.get("temperature_2m")
    wind = data.get("wind_speed_10m")

    if temp is None:
        return f"I couldn't get the weather for {label} right now."

    return f"It's currently {temp}°C in {label}, with winds at {wind} km/h."