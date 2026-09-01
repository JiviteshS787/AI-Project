import requests

HOME_LAT = 43.85
HOME_LON = -79.29  # Markham -> Default

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
        "current": "temperature_2m,apparent_temperature,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability",
        "forecast_days": 1,
        "timezone": "auto",
    })
    data = r.json()
    current = data.get("current", {})
    hourly = data.get("hourly", {})

    temp = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    wind = current.get("wind_speed_10m")

    if temp is None:
        return f"I couldn't get the weather for {label} right now."

    base = f"It's currently {temp}°C in {label}, feels like {feels_like}°C, with winds at {wind} km/h."

    # Build a short-term nudge from the next few hours
    nudge = _build_nudge(hourly, current_temp=temp)

    return f"{base} {nudge}" if nudge else base


def _build_nudge(hourly: dict, current_temp: float) -> str:
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rain_chance = hourly.get("precipitation_probability", [])

    if not times:
        return ""

    # Find the current hour's index, look ~4 hours ahead
    from datetime import datetime
    now = datetime.now()
    current_index = 0
    for i, t in enumerate(times):
        if datetime.fromisoformat(t) >= now:
            current_index = i
            break

    lookahead = min(current_index + 4, len(times) - 1)
    upcoming_rain = max(rain_chance[current_index:lookahead + 1], default=0)
    upcoming_temp = temps[lookahead] if lookahead < len(temps) else current_temp

    messages = []

    if upcoming_rain >= 50:
        messages.append("Rain's likely in the next few hours — head out now if you can, or bring an umbrella if you're going later.")

    temp_drop = current_temp - upcoming_temp
    if temp_drop >= 5:
        messages.append("It's going to get noticeably colder later, so grab a jacket if you're heading out this evening.")
    elif upcoming_temp - current_temp >= 5:
        messages.append("It's warming up later, so you can dress lighter if you're heading out then.")

    return " ".join(messages)