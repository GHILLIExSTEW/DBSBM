import requests
import os
import json

API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
if not API_SPORTS_KEY:
    API_SPORTS_KEY = input("Enter your API-Sports key: ").strip()

SPORT = os.getenv("SPORT")
if not SPORT:
    SPORT = input("Enter sport (e.g., football, basketball): ").strip()

LEAGUE_ID = os.getenv("LEAGUE_ID")
if not LEAGUE_ID:
    LEAGUE_ID = input("Enter league ID (e.g., 39 for EPL): ").strip()
LEAGUE_ID = int(LEAGUE_ID)

SEASON = os.getenv("SEASON")
if not SEASON:
    SEASON = input("Enter season (e.g., 2023): ").strip()
SEASON = int(SEASON)

url = f"https://v3.{SPORT}.api-sports.io/teams?league={LEAGUE_ID}&season={SEASON}"
headers = {"x-apisports-key": API_SPORTS_KEY}

response = requests.get(url, headers=headers)
data = response.json()

teams = []
for team in data.get("response", []):
    t = team["team"]
    teams.append({
        "api_sports_id": t["id"],
        "name": t["name"],
        "code": t.get("code"),
        "country": t.get("country"),
        "logo": t.get("logo"),
    })

with open(f"{SPORT}_league_{LEAGUE_ID}_teams.json", "w", encoding="utf-8") as f:
    json.dump(teams, f, indent=2, ensure_ascii=False)

print(f"Saved {len(teams)} teams to {SPORT}_league_{LEAGUE_ID}_teams.json") 