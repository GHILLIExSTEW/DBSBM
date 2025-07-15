#!/usr/bin/env python3
"""
Script to fetch players for a single league and save immediately
This allows us to test each league individually and save data incrementally
"""

import asyncio
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List

import aiohttp
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

# Configuration
print("🎯 Single League Player Fetcher")
print("=" * 50)
API_KEY = input("Please enter your API-Sports key: ").strip()
if not API_KEY:
    print("❌ API key is required")
    sys.exit(1)

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "players.csv")

# Available leagues to choose from
AVAILABLE_LEAGUES = {
    "1": {"sport": "basketball", "league": "NBA", "id": 12, "name": "NBA"},
    "2": {"sport": "american-football", "league": "NFL", "id": 1, "name": "NFL"},
    "3": {"sport": "american-football", "league": "NCAA", "id": 2, "name": "NCAA"},
    "4": {
        "sport": "football",
        "league": "EPL",
        "id": 39,
        "name": "English Premier League",
    },
    "5": {"sport": "football", "league": "LaLiga", "id": 140, "name": "La Liga"},
    "6": {"sport": "football", "league": "Bundesliga", "id": 78, "name": "Bundesliga"},
    "7": {"sport": "football", "league": "SerieA", "id": 135, "name": "Serie A"},
    "8": {"sport": "football", "league": "Ligue1", "id": 61, "name": "Ligue 1"},
    "9": {
        "sport": "football",
        "league": "ChampionsLeague",
        "id": 2,
        "name": "UEFA Champions League",
    },
}

# API endpoints
ENDPOINTS = {
    "teams": {
        "basketball": "https://v1.basketball.api-sports.io/teams",
        "baseball": "https://v1.baseball.api-sports.io/teams",
        "american-football": "https://v1.american-football.api-sports.io/teams",
        "hockey": "https://v1.hockey.api-sports.io/teams",
        "football": "https://v3.football.api-sports.io/teams",
    },
    "players": {
        "basketball": "https://v1.basketball.api-sports.io/players",
        "baseball": "https://v1.baseball.api-sports.io/players",
        "american-football": "https://v1.american-football.api-sports.io/players",
        "hockey": "https://v1.hockey.api-sports.io/players",
        "football": "https://v3.football.api-sports.io/players",
    },
}


class SingleLeagueFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"x-apisports-key": self.api_key}
        self.session = None
        self.players_data = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_teams_for_league(self, sport: str, league_info: dict) -> List[Dict]:
        """Fetch teams for a specific league"""
        print(f"🔍 Fetching teams for {league_info['name']} ({sport})...")

        endpoint = ENDPOINTS["teams"].get(sport)
        if not endpoint:
            print(f"❌ No teams endpoint for sport: {sport}")
            return []

        # Try different season formats for problematic sports
        season_formats = []
        if sport == "basketball":
            # NBA might need different season format
            season_formats = [
                {"season": "2023-2024", "description": "2023-2024"},
                {"season": 2023, "description": "2023"},
                {"season": "2024-2025", "description": "2024-2025"},
                {"season": 2024, "description": "2024"},
            ]
        else:
            # Default season format
            season_formats = [
                {"season": 2024, "description": "2024"},
                {"season": "2024", "description": "2024 (string)"},
            ]

        for season_test in season_formats:
            season = season_test["season"]
            description = season_test["description"]

            print(f"📅 Trying season: {description}, league ID: {league_info['id']}")

            params = {"league": league_info["id"], "season": season}

            try:
                async with self.session.get(endpoint, params=params) as response:
                    print(f"🔗 API URL: {response.url}")
                    print(f"📊 Response status: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        # Check for errors in response
                        if data.get("errors"):
                            print(f"❌ API Errors: {data['errors']}")
                            continue  # Try next season format

                        teams = data.get("response", [])
                        print(
                            f"✅ Found {len(teams)} teams for {league_info['name']} with season {description}"
                        )

                        if teams:
                            return teams
                        else:
                            print(
                                f"⚠️ No teams found with season {description}, trying next..."
                            )
                            continue
                    else:
                        error_text = await response.text()
                        print(
                            f"❌ Error fetching teams for {league_info['name']}: {response.status}"
                        )
                        print(f"❌ Error response: {error_text[:200]}...")
                        continue
            except Exception as e:
                print(f"❌ Exception fetching teams for {league_info['name']}: {e}")
                continue

            # Rate limiting between attempts
            await asyncio.sleep(1)

        print(f"❌ No teams found for {league_info['name']} with any season format")
        return []

    async def fetch_players_for_team(
        self, sport: str, team_name: str, team_id: int
    ) -> List[Dict]:
        """Fetch players for a specific team"""
        print(f"  👥 Fetching players for {team_name}...")

        endpoint = ENDPOINTS["players"].get(sport)
        if not endpoint:
            print(f"  ❌ No players endpoint for sport: {sport}")
            return []

        # Skip baseball and hockey as they don't have player endpoints
        if sport == "baseball":
            print(
                "  ⚠️ Baseball (MLB) doesn't have a player endpoint in API-Sports. Skipping..."
            )
            return []
        elif sport == "hockey":
            print(
                "  ⚠️ Hockey (NHL) doesn't have a player endpoint in API-Sports. Skipping..."
            )
            return []

        # Try different season formats for problematic sports
        season_formats = []
        if sport == "basketball":
            # NBA might need different season format
            season_formats = [
                {"season": "2023-2024", "description": "2023-2024"},
                {"season": 2023, "description": "2023"},
                {"season": "2024-2025", "description": "2024-2025"},
                {"season": 2024, "description": "2024"},
            ]
        else:
            # Default season format
            season_formats = [
                {"season": 2024, "description": "2024"},
                {"season": "2024", "description": "2024 (string)"},
            ]

        for season_test in season_formats:
            season = season_test["season"]
            description = season_test["description"]

            params = {"team": team_id, "season": season}

            try:
                async with self.session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check for errors in response
                        if data.get("errors"):
                            print(
                                f"  ❌ API Errors with season {description}: {data['errors']}"
                            )
                            continue  # Try next season format

                        players = data.get("response", [])
                        print(
                            f"  ✅ Found {len(players)} players for {team_name} with season {description}"
                        )

                        if players:
                            return players
                        else:
                            print(
                                f"  ⚠️ No players found with season {description}, trying next..."
                            )
                            continue
                    else:
                        print(
                            f"  ❌ Error fetching players for {team_name}: {response.status}"
                        )
                        continue
            except Exception as e:
                print(f"  ❌ Exception fetching players for {team_name}: {e}")
                continue

            # Rate limiting between attempts
            await asyncio.sleep(0.5)

        print(f"  ❌ No players found for {team_name} with any season format")
        return []

    def process_player_data(
        self, raw_players: List[Dict], team_name: str, league_name: str, sport: str
    ) -> List[Dict]:
        """Process raw player data into CSV format"""
        processed_players = []

        # Debug: Show first player structure if available
        if raw_players and len(raw_players) > 0:
            first_player = raw_players[0]
            print(f"    🔍 Debug: First player keys: {list(first_player.keys())}")
            if "player" in first_player:
                print(
                    f"    🔍 Debug: Player info keys: {list(first_player['player'].keys())}"
                )

        for player in raw_players:
            # Extract player info based on sport
            player_info = player.get("player", {})
            team_info = (
                player.get("statistics", [{}])[0].get("team", {})
                if player.get("statistics")
                else {}
            )

            # Get player name - try different possible fields
            # For basketball, the name is directly in the player object
            player_name = (
                player.get("name")
                or player_info.get("name")  # Direct name field
                or player_info.get("firstname", "")
                + " "
                + player_info.get("lastname", "")
                or ""
            ).strip()

            # Get position - try different possible fields
            position = (
                player.get("position")
                or player_info.get("position")  # Direct position field
                or ""
            )

            # Get country/nationality
            country = (
                player.get("country")
                or player_info.get("country")  # Direct country field
                or player_info.get("nationality")
                or ""
            )

            processed_player = {
                "strPlayer": player_name,
                "strTeam": team_info.get("name", team_name),
                "strSport": sport.title(),
                "strLeague": league_name,
                "strPosition": position,
                "strCutouts": player_info.get("photo", ""),
                "strThumb": player_info.get("photo", ""),
                "strHeight": player_info.get("height", ""),
                "strWeight": player_info.get("weight", ""),
                "strBirthLocation": player_info.get("birth", {}).get("place", ""),
                "strDescriptionEN": player_info.get("height", ""),
                "strNationality": country,
                "strCollege": "",
                "strSide": "",
                "strKit": "",
                "strAgent": "",
                "strBirthDate": player_info.get("birth", {}).get("date", ""),
                "strSigning": "",
                "strWage": "",
                "strOutfitter": "",
                "strLeague2": "",
                "strLeague3": "",
                "strLeague4": "",
                "strLeague5": "",
                "strLeague6": "",
                "strLeague7": "",
                "strDivision": "",
                "strManager": "",
                "strWebsite": "",
                "strFacebook": "",
                "strTwitter": "",
                "strInstagram": "",
                "strYoutube": "",
                "strTiktok": "",
                "strLastname": "",
                "strFirstname": "",
                "strNumber": player.get("number", ""),
                "strSeason": str(datetime.now().year),
                "strDescriptionDE": "",
                "strDescriptionFR": "",
                "strDescriptionCN": "",
                "strDescriptionIT": "",
                "strDescriptionJP": "",
                "strDescriptionRU": "",
                "strDescriptionES": "",
                "strDescriptionPT": "",
                "strDescriptionSE": "",
                "strDescriptionNL": "",
                "strDescriptionHU": "",
                "strDescriptionNO": "",
                "strDescriptionIL": "",
                "strDescriptionPL": "",
                "strGender": "",
                "strCountry": country,
                "strBanner": "",
                "strFanart1": "",
                "strFanart2": "",
                "strFanart3": "",
                "strFanart4": "",
                "strLocked": "unlocked",
            }

            # Only add if player has a name
            if processed_player["strPlayer"]:
                processed_players.append(processed_player)
            else:
                print(f"    ⚠️ Skipping player with no name: {player}")

        print(
            f"    📊 Processed {len(processed_players)} players with names out of {len(raw_players)} total"
        )
        return processed_players

    async def fetch_league_players(self, league_info: dict):
        """Fetch all players for a single league"""
        sport = league_info["sport"]
        league_name = league_info["name"]

        print(f"\n🏈 Processing {sport.title()} - {league_name}")
        print("=" * 60)

        # Step 1: Fetch teams
        teams = await self.fetch_teams_for_league(sport, league_info)

        if not teams:
            print(f"❌ No teams found for {league_name}")
            return

        # Step 2: Fetch players for each team
        print(f"\n👥 Fetching players from {len(teams)} teams...")
        total_players = 0

        for i, team in enumerate(teams, 1):
            # Handle different team data structures
            if "team" in team:
                # Football structure: {"team": {...}, "venue": {...}}
                team_info = team["team"]
            else:
                # Other sports structure: direct team data
                team_info = team

            team_name = team_info.get("name", "Unknown Team")
            team_id = team_info.get("id")

            if not team_id:
                print(f"  ⚠️ No team ID for {team_name}")
                continue

            print(f"  [{i}/{len(teams)}] Processing {team_name} (ID: {team_id})")

            # Fetch players for this team
            players = await self.fetch_players_for_team(sport, team_name, team_id)

            if players:
                # Process the player data
                processed_players = self.process_player_data(
                    players, team_name, league_name, sport
                )
                self.players_data.extend(processed_players)
                total_players += len(processed_players)

                # Rate limiting
                await asyncio.sleep(0.5)
            else:
                print(f"  ⚠️ No players found for {team_name}")

        print(f"\n✅ Total players fetched for {league_name}: {total_players}")

    def save_to_csv(self, append: bool = True):
        """Save player data to CSV file"""
        if not self.players_data:
            print("❌ No player data to save")
            return

        # Define CSV headers (matching the existing format)
        headers = [
            "strPlayer",
            "strTeam",
            "strSport",
            "strLeague",
            "strPosition",
            "strCutouts",
            "strThumb",
            "strHeight",
            "strWeight",
            "strBirthLocation",
            "strDescriptionEN",
            "strNationality",
            "strCollege",
            "strSide",
            "strKit",
            "strAgent",
            "strBirthDate",
            "strSigning",
            "strWage",
            "strOutfitter",
            "strLeague2",
            "strLeague3",
            "strLeague4",
            "strLeague5",
            "strLeague6",
            "strLeague7",
            "strDivision",
            "strManager",
            "strWebsite",
            "strFacebook",
            "strTwitter",
            "strInstagram",
            "strYoutube",
            "strTiktok",
            "strLastname",
            "strFirstname",
            "strNumber",
            "strSeason",
            "strDescriptionDE",
            "strDescriptionFR",
            "strDescriptionCN",
            "strDescriptionIT",
            "strDescriptionJP",
            "strDescriptionRU",
            "strDescriptionES",
            "strDescriptionPT",
            "strDescriptionSE",
            "strDescriptionNL",
            "strDescriptionHU",
            "strDescriptionNO",
            "strDescriptionIL",
            "strDescriptionPL",
            "strGender",
            "strCountry",
            "strBanner",
            "strFanart1",
            "strFanart2",
            "strFanart3",
            "strFanart4",
            "strLocked",
        ]

        # Check if file exists and has headers
        file_exists = os.path.exists(CSV_FILE)

        if append and file_exists:
            # Append to existing file
            mode = "a"
            write_header = False
            print(
                f"📝 Appending {len(self.players_data)} players to existing CSV file..."
            )
        else:
            # Create new file or overwrite
            mode = "w"
            write_header = True
            if file_exists:
                backup_file = (
                    f"{CSV_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                os.rename(CSV_FILE, backup_file)
                print(f"📦 Created backup: {backup_file}")
            print(f"💾 Saving {len(self.players_data)} players to new CSV file...")

        # Write CSV file
        with open(CSV_FILE, mode, newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            if write_header:
                writer.writeheader()
            writer.writerows(self.players_data)

        print(f"✅ Successfully saved players to {CSV_FILE}")


def show_league_menu():
    """Show available leagues menu"""
    print("\n📋 Available Leagues:")
    print("-" * 40)
    for key, league in AVAILABLE_LEAGUES.items():
        print(f"{key}. {league['sport'].title()} - {league['name']}")
    print("0. Exit")


async def main():
    """Main function"""
    while True:
        show_league_menu()
        choice = input("\nSelect a league to fetch (0-9): ").strip()

        if choice == "0":
            print("👋 Goodbye!")
            break

        if choice not in AVAILABLE_LEAGUES:
            print("❌ Invalid choice. Please select 0-9.")
            continue

        league_info = AVAILABLE_LEAGUES[choice]

        # Ask if user wants to append or overwrite
        append_choice = input("Append to existing CSV? (y/n): ").strip().lower()
        append = append_choice in ["y", "yes"]

        print(
            f"\n🎯 Fetching players for {league_info['sport'].title()} - {league_info['name']}"
        )
        print("=" * 60)

        async with SingleLeagueFetcher(API_KEY) as fetcher:
            await fetcher.fetch_league_players(league_info)
            fetcher.save_to_csv(append=append)

        # Ask if user wants to continue
        continue_choice = input("\nFetch another league? (y/n): ").strip().lower()
        if continue_choice not in ["y", "yes"]:
            print("👋 Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
