import json
import os

import requests

API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
if not API_SPORTS_KEY:
    API_SPORTS_KEY = input("Enter your API-Sports key: ").strip()

SEASON = 2025  # Change as needed

# Map user categories to correct subdomains
category_to_subdomain = {
    "AFL": "afl",
    "Baseball": "baseball",
    "Basketball": "basketball",
    "Football": "football",
    "Formula-1": "formula-1",
    "Handball": "handball",
    "Hockey": "hockey",
    "MMA": "mma",
    "NBA": "basketball",  # NBA is a league under basketball
    "NFL": "american-football",  # NFL is a league under american-football
    "Rugby": "rugby",
    "Volleyball": "volleyball",
}

categories = [
    "AFL",
    "Baseball",
    "Basketball",
    "Football",
    "Formula-1",
    "Handball",
    "Hockey",
    "MMA",
    "NBA",
    "NFL",
    "Rugby",
    "Volleyball",
]

headers = {"x-apisports-key": API_SPORTS_KEY}

for category in categories:
    subdomain = category_to_subdomain[category]
    print(f"Fetching leagues for {category} (season {SEASON})...")
    url = f"https://v3.{subdomain}.api-sports.io/leagues?season={SEASON}"
    print(f"Requesting: {url}")
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch or parse leagues for {category}: {e}")
        continue
    # Print the raw response for inspection
    print(json.dumps(data, indent=2))
    leagues = []
    for league_info in data.get("response", []):
        league = league_info.get("league", {})
        country = league_info.get("country", {})
        leagues.append(
            {
                "league_id": league.get("id"),
                "name": league.get("name"),
                "type": league.get("type"),
                "country": country.get("name"),
                "country_code": country.get("code"),
                "season": SEASON,
            }
        )
    with open(f"{category.lower()}_leagues_{SEASON}.json", "w", encoding="utf-8") as f:
        json.dump(leagues, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(leagues)} leagues to {category.lower()}_leagues_{SEASON}.json")
