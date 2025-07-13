import requests
import os
import json

API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
if not API_SPORTS_KEY:
    API_SPORTS_KEY = input("Enter your API-Sports key: ").strip()

# Remove "API_KEY=" prefix if present
if API_SPORTS_KEY.startswith("API_KEY="):
    API_SPORTS_KEY = API_SPORTS_KEY[8:]

# Define leagues to fetch teams for (league_id, season)
LEAGUES_TO_FETCH = {
    "baseball": [
        {"league_id": 1, "season": 2025, "name": "MLB"},
        {"league_id": 2, "season": 2024, "name": "NPB"},
        {"league_id": 3, "season": 2024, "name": "KBO"}
    ],
    "basketball": [
        {"league_id": 12, "season": 2024, "name": "NBA"},
        {"league_id": 13, "season": 2024, "name": "WNBA"},
        {"league_id": 1, "season": 2024, "name": "EuroLeague"}
    ],
    "american-football": [
        {"league_id": 1, "season": 2024, "name": "NFL"},
        {"league_id": 2, "season": 2024, "name": "NCAA"}
    ],
    "hockey": [
        {"league_id": 57, "season": 2024, "name": "NHL"}
    ],
    "football": [
        {"league_id": 39, "season": 2024, "name": "EPL"},
        {"league_id": 140, "season": 2024, "name": "La Liga"},
        {"league_id": 78, "season": 2024, "name": "Bundesliga"},
        {"league_id": 135, "season": 2024, "name": "Serie A"},
        {"league_id": 61, "season": 2024, "name": "Ligue 1"},
        {"league_id": 253, "season": 2024, "name": "MLS"}
    ]
}

# Define correct API versions for each sport
API_VERSIONS = {
    "afl": "v1",
    "baseball": "v1", 
    "basketball": "v1",
    "football": "v3",  # Only football uses v3
    "formula-1": "v1",
    "handball": "v1",
    "hockey": "v1",
    "mma": "v1",
    "rugby": "v1",
    "volleyball": "v1",
    "american-football": "v1"
}

headers = {"x-apisports-key": API_SPORTS_KEY}

for sport, leagues in LEAGUES_TO_FETCH.items():
    print(f"\nFetching teams for {sport}...")
    version = API_VERSIONS.get(sport, "v1")
    
    for league_info in leagues:
        league_id = league_info["league_id"]
        season = league_info["season"]
        league_name = league_info["name"]
        
        print(f"  Fetching teams for {league_name} (ID: {league_id}, Season: {season})...")
        
        url = f"https://{version}.{sport}.api-sports.io/teams"
        params = {
            "league": league_id,
            "season": season
        }
        
        print(f"  URL: {url}")
        print(f"  Params: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"  Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  Error response: {response.text}")
                continue
                
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
            
            teams = data.get("response", [])
            print(f"  Found {len(teams)} teams")
            
            # Save teams to file
            filename = f"{sport}_{league_name.lower().replace(' ', '_')}_teams.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=2, ensure_ascii=False)
            print(f"  Saved teams to {filename}")
            
        except Exception as e:
            print(f"  Failed to fetch teams for {league_name}: {e}")
            continue 