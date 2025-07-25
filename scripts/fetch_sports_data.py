import csv
import os
from datetime import datetime
from getpass import getpass

import requests

# List of API endpoints to query
API_ENDPOINTS = [
    {"sport": "AFL", "base_url": "https://v1.afl.api-sports.io", "has_teams": True},
    {
        "sport": "Baseball",
        "base_url": "https://v1.baseball.api-sports.io",
        "has_teams": True,
    },
    {
        "sport": "Basketball",
        "base_url": "https://v1.basketball.api-sports.io",
        "has_teams": True,
    },
    {
        "sport": "Formula-1",
        "base_url": "https://v1.formula-1.api-sports.io",
        "has_teams": False,
        "player_endpoint": "drivers",
    },
    {
        "sport": "Handball",
        "base_url": "https://v1.handball.api-sports.io",
        "has_teams": True,
    },
    {
        "sport": "Hockey",
        "base_url": "https://v1.hockey.api-sports.io",
        "has_teams": True,
    },
    {
        "sport": "MMA",
        "base_url": "https://v1.mma.api-sports.io",
        "has_teams": False,
        "player_endpoint": "fighters",
    },
    {"sport": "NBA", "base_url": "https://v2.nba.api-sports.io", "has_teams": True},
    {"sport": "NFL", "base_url": "https://v1.nfl.api-sports.io", "has_teams": True},
    {"sport": "Rugby", "base_url": "https://v1.rugby.api-sports.io", "has_teams": True},
    {
        "sport": "Volleyball",
        "base_url": "https://v1.volleyball.api-sports.io",
        "has_teams": True,
    },
    {
        "sport": "Football",
        "base_url": "https://v3.football.api-sports.io",
        "has_teams": True,
    },
]


def fetch_leagues(api_key, base_url):
    """
    Fetch all leagues from a given API-Sports endpoint.

    Args:
        api_key (str): API key for authentication.
        base_url (str): Base URL of the API (e.g., https://v1.basketball.api-sports.io).

    Returns:
        list: List of league data or None if the request fails.
    """
    url = f"{base_url}/leagues"
    headers = {"x-apisports-key": api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.RequestException as e:
        print(f"Error fetching leagues from {base_url}: {e}")
        return None


def fetch_teams(api_key, base_url, league_id, season):
    """
    Fetch all teams for a given league and season.

    Args:
        api_key (str): API key for authentication.
        base_url (str): Base URL of the API.
        league_id (int): League ID.
        season (int): Season year.

    Returns:
        list: List of team data or None if the request fails.
    """
    url = f"{base_url}/teams"
    headers = {"x-apisports-key": api_key}
    params = {"league": league_id, "season": season}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.RequestException as e:
        print(f"Error fetching teams for league {league_id} from {base_url}: {e}")
        return None


def fetch_players(
    api_key, base_url, team_id=None, season=None, player_endpoint="players"
):
    """
    Fetch all players (or drivers/fighters) for a given team/season or league.

    Args:
        api_key (str): API key for authentication.
        base_url (str): Base URL of the API.
        team_id (int, optional): Team ID (None for non-team sports).
        season (int, optional): Season year (None for non-team sports).
        player_endpoint (str): Endpoint name (e.g., 'players', 'drivers', 'fighters').

    Returns:
        list: List of player data or None if the request fails.
    """
    url = f"{base_url}/{player_endpoint}"
    headers = {"x-apisports-key": api_key}
    params = {}
    if team_id:
        params["team"] = team_id
    if season:
        params["season"] = season
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.RequestException as e:
        print(f"Error fetching {player_endpoint} from {base_url}: {e}")
        return None


def save_to_csv(data, filename="scripts/teams_and_players.csv"):
    """
    Save league, team, player data to a CSV file at the specified location.

    Args:
        data (list): List of tuples containing (league, team, player, url).
        filename (str): Path to the CSV file.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["League", "Team", "Player", "URL"])
            for row in data:
                writer.writerow(row)
        print(f"Data saved to {filename}")
    except OSError as e:
        print(f"Error saving to {filename}: {e}")


def main():
    """Main function to fetch leagues, teams, players from multiple APIs and save to CSV."""
    # Prompt for API key securely
    api_key = getpass("Enter your API-Sports API key: ")

    # Get current year for season
    current_year = datetime.now().year

    # Prepare data for CSV
    csv_data = []

    # Iterate through each API endpoint
    for api in API_ENDPOINTS:
        sport = api["sport"]
        base_url = api["base_url"]
        has_teams = api.get("has_teams", True)
        player_endpoint = api.get("player_endpoint", "players")

        print(f"Processing {sport} API...")

        # Fetch leagues
        leagues = fetch_leagues(api_key, base_url)
        if not leagues:
            print(f"No leagues found for {sport}. Skipping.")
            continue

        # Iterate through leagues
        for league in leagues:
            league_id = league.get("id")
            league_name = league.get("name", f"Unknown {sport} League")
            seasons = league.get("seasons", [])

            # Use the most recent season (or current year if available)
            season = current_year
            for s in seasons:
                if s.get("season") == current_year:
                    season = s.get("season")
                    break

            if has_teams:
                # Fetch teams for the league
                teams = fetch_teams(api_key, base_url, league_id, season)
                if not teams:
                    continue

                # Iterate through teams
                for team in teams:
                    team_id = team.get("id")
                    team_name = team.get("name", "Unknown Team")

                    # Fetch players for the team
                    players = fetch_players(
                        api_key, base_url, team_id, season, player_endpoint
                    )
                    if not players:
                        continue

                    # Add player data to CSV
                    for player in players:
                        player_name = f"{player.get('firstname', '')} {player.get('lastname', '')}".strip()
                        if not player_name:
                            player_name = player.get("name", "Unknown Player")
                        csv_data.append([league_name, team_name, player_name, ""])
            else:
                # For non-team sports (e.g., MMA, Formula-1), fetch players directly
                players = fetch_players(
                    api_key, base_url, player_endpoint=player_endpoint
                )
                if not players:
                    continue

                # Add player data to CSV (no team)
                for player in players:
                    player_name = f"{player.get('firstname', '')} {player.get('lastname', '')}".strip()
                    if not player_name:
                        player_name = player.get("name", "Unknown Player")
                    csv_data.append([league_name, "", player_name, ""])

    # Save data to CSV
    if csv_data:
        save_to_csv(csv_data)
    else:
        print("No data to save.")


if __name__ == "__main__":
    main()
