import requests
import os

from datetime import date

API_KEY = os.environ["API_SPORTS_KEY"]
SPORT_ENDPOINTS = {
    "football":   "https://v3.football.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "hockey":     "https://v1.hockey.api-sports.io",
    "tennis":     "https://v1.tennis.api-sports.io",
    "baseball":   "https://v1.baseball.api-sports.io",
    "mma":        "https://v1.mma.api-sports.io",
}

def handle_sports(team: str, sport: str, league: str | None) -> str:
    base_url = SPORT_ENDPOINTS.get(sport)
    if not base_url:
        return f"I don't have score data set up for {sport} yet."

    headers = {"x-apisports-key": API_KEY}
    r = requests.get(f"{base_url}/teams", headers=headers, params={"search": team})
    teams = r.json().get("response", [])
    if not teams:
        return f"I couldn't find a team called {team}."
    team_id = teams[0]["team"]["id"]

    r = requests.get(f"{base_url}/fixtures", headers=headers, params={
        "team": team_id,
        "date": date.today().isoformat(),
    })
    fixtures = r.json().get("response", [])

    if not fixtures:
        # fall back to most recent past game, but say so explicitly
        r = requests.get(f"{base_url}/fixtures", headers=headers, params={"team": team_id, "last": 1})
        fixtures = r.json().get("response", [])
        if not fixtures:
            return f"I couldn't find a recent game for {team}."
        match = fixtures[0]
        prefix = "They're not playing today. Their last game: "
    else:
        match = fixtures[0]
        prefix = ""

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    home_goals = match["goals"]["home"]
    away_goals = match["goals"]["away"]
    status = match["fixture"]["status"]["short"]

    result = f"{home} {home_goals} - {away_goals} {away}"
    result += ", currently live." if status in ("1H", "2H", "LIVE", "HT") else ", final."
    return prefix + result