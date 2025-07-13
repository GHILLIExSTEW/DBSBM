import requests
import os
import json

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    ODDS_API_KEY = input("Enter your Odds API key: ").strip()

# Step 1: Get all available sport keys
sports_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_API_KEY}"
sports_resp = requests.get(sports_url)
try:
    sports_data = sports_resp.json()
except Exception as e:
    print("Failed to parse sports JSON:", e)
    print("Raw response:", sports_resp.text)
    exit(1)

if not isinstance(sports_data, list):
    print("API did not return a list of sports. Response was:")
    print(json.dumps(sports_data, indent=2))
    exit(1)

sport_keys = [sport['key'] for sport in sports_data if sport.get('key')]
print(f"Found {len(sport_keys)} sport keys.")

# Step 2: For each sport key, fetch teams
for SPORT_KEY in sport_keys:
    print(f"Fetching teams for {SPORT_KEY}...")
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds?apiKey={ODDS_API_KEY}&regions=us&markets=h2h"
    response = requests.get(url)
    try:
        data = response.json()
    except Exception as e:
        print(f"Failed to parse JSON for {SPORT_KEY}: {e}")
        print("Raw response:", response.text)
        continue
    if not isinstance(data, list):
        print(f"API did not return a list of games for {SPORT_KEY}. Response was:")
        print(json.dumps(data, indent=2))
        continue
    teams = set()
    for game in data:
        teams.add(game.get("home_team"))
        teams.add(game.get("away_team"))
    teams = sorted(t for t in teams if t)
    with open(f"oddsapi_{SPORT_KEY}_teams.json", "w", encoding="utf-8") as f:
        json.dump(teams, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(teams)} teams to oddsapi_{SPORT_KEY}_teams.json") 