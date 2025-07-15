import json
import os
from pathlib import Path
from time import sleep

import requests

# --- CONFIG ---
API_KEY = os.getenv("API_SPORTS_KEY")
if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
    API_KEY = input("Enter your API-SPORTS key: ").strip()
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Output directories
LEAGUE_LOGO_DIR = Path("static/logos/leagues/SOCCER")
TEAM_LOGO_BASE_DIR = Path("static/logos/teams/SOCCER")
SUMMARY_JSON = Path("data/sweden_leagues_and_teams.json")


# --- HELPERS ---
def safe_filename(name):
    return "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name
    ).replace(" ", "_")


def download_image(url, path):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded: {path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def fetch_json(endpoint, params=None):
    r = requests.get(BASE_URL + endpoint, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


# --- MAIN ---
def main():
    LEAGUE_LOGO_DIR.mkdir(parents=True, exist_ok=True)
    TEAM_LOGO_BASE_DIR.mkdir(parents=True, exist_ok=True)
    all_leagues = []

    # 1. Fetch Sweden leagues
    print("Fetching Sweden leagues...")
    leagues_data = fetch_json("/leagues", {"search": "sweden"})
    leagues = leagues_data.get("response", [])
    print("Raw leagues API response:", json.dumps(leagues_data, indent=2))
    print(f"Number of leagues found: {len(leagues)}")
    if not leagues:
        print("No leagues found for Sweden!")

    for league_info in leagues:
        league = league_info["league"]
        league_info["country"]
        league_id = league["id"]
        league_name = league["name"]
        league_logo = league["logo"]
        print(f"Processing league: {league_name} (ID: {league_id})")

        # Save league logo
        league_dir = LEAGUE_LOGO_DIR / safe_filename(league_name)
        league_dir.mkdir(parents=True, exist_ok=True)
        if league_logo:
            logo_path = league_dir / "logo.png"
            download_image(league_logo, logo_path)

        # 2. Fetch teams for this league (use most recent season)
        seasons = league_info.get("seasons", [])
        if not seasons:
            print(f"No seasons found for {league_name}")
            continue
        latest_season = max(s["year"] for s in seasons if "year" in s)
        print(f"Fetching teams for {league_name}, season {latest_season}")
        try:
            teams_data = fetch_json(
                "/teams", {"league": league_id, "season": latest_season}
            )
            teams = teams_data.get("response", [])
        except Exception as e:
            print(f"Failed to fetch teams for {league_name}: {e}")
            continue

        team_dir = TEAM_LOGO_BASE_DIR / safe_filename(league_name)
        team_dir.mkdir(parents=True, exist_ok=True)
        team_list = []
        for team_info in teams:
            team = team_info["team"]
            team_name = team["name"]
            team_logo = team["logo"]
            team_id = team["id"]
            print(f"  Team: {team_name}")
            if team_logo:
                logo_path = team_dir / f"{safe_filename(team_name)}.png"
                download_image(team_logo, logo_path)
            team_list.append(
                {
                    "id": team_id,
                    "name": team_name,
                    "logo": str(logo_path) if team_logo else None,
                }
            )
            sleep(0.2)  # Be nice to the API

        all_leagues.append(
            {
                "id": league_id,
                "name": league_name,
                "logo": str(league_dir / "logo.png") if league_logo else None,
                "teams": team_list,
                "season": latest_season,
            }
        )
        sleep(0.5)  # Be nice to the API

    # Save summary JSON
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(all_leagues, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
