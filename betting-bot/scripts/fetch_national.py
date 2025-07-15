import os

import requests

API_KEY = "59d5fa03fb6bd373f9ee6cac5f39c689"  # <-- Replace with your actual API key
SPORT = "BASEBALL"
TEAM_ID = 23
SEASON = 2025
API_URL = f"https://v1.baseball.api-sports.io/games?season={SEASON}&team={TEAM_ID}"
HEADERS = {"x-apisports-key": API_KEY}


def download_image(url, save_path):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"Saved: {save_path}")
        else:
            print(f"Failed to download {url}: {resp.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


def main():
    resp = requests.get(API_URL, headers=HEADERS)
    data = resp.json()
    for game in data.get("response", []):
        # League logo
        league = game.get("league", {})
        league_name = league.get("name", SPORT)
        league_logo = league.get("logo")
        if league_logo:
            league_dir = f"betting-bot/static/logos/leagues/{SPORT}/"
            league_path = os.path.join(league_dir, f"{league_name}.png")
            download_image(league_logo, league_path)
        # Team logos
        for side in ["home", "away"]:
            team = game.get("teams", {}).get(side, {})
            team_name = team.get("name")
            team_logo = team.get("logo")
            if team_logo and team_name:
                team_dir = f"betting-bot/static/logos/teams/{SPORT}/"
                team_path = os.path.join(team_dir, f"{team_name}.png")
                download_image(team_logo, team_path)


if __name__ == "__main__":
    main()
