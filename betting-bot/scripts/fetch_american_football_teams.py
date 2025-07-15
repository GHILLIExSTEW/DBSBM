#!/usr/bin/env python3
"""
Script to fetch American football teams from API-Sports
Uses the v1 API with league and season parameters
"""

import os
import json
import requests
from datetime import datetime


def fetch_american_football_teams():
    """Fetch American football teams from API-Sports"""

    # Get API key from environment variable
    api_key = os.getenv("API_SPORTS_KEY")
    if not api_key:
        print("API_SPORTS_KEY environment variable not set")
        api_key = input("Please enter your API-Sports key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return None

    # API-Sports v1 endpoint for teams
    base_url = "https://v3.football.api-sports.io/teams"

    # Headers required by API-Sports
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key,
    }

    # Parameters for American football leagues
    # NFL - league ID 1, current season
    params = {"league": 1, "season": 2024}  # NFL  # Current season

    try:
        print("Fetching American football teams from API-Sports...")
        print(f"URL: {base_url}")
        print(f"Parameters: {params}")

        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"american_football_nfl_teams_{timestamp}.json"
            filepath = os.path.join("data", filename)

            # Save the response
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(
                f"✅ Successfully saved {len(data.get('response', []))} teams to {filepath}"
            )

            # Print some basic info about the response
            if "response" in data:
                print(f"Total teams found: {len(data['response'])}")
                if data["response"]:
                    print("Sample team:")
                    team = data["response"][0]
                    print(f"  - {team.get('team', {}).get('name', 'Unknown')}")
                    print(f"  - ID: {team.get('team', {}).get('id', 'Unknown')}")

            return filepath

        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response text: {response.text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def main():
    """Main function"""
    print("🏈 American Football Teams Fetcher")
    print("=" * 40)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Fetch teams
    result = fetch_american_football_teams()

    if result:
        print(f"\n✅ Teams data saved to: {result}")
        print("\nYou can now use this data to update your teams JSON files.")
    else:
        print("\n❌ Failed to fetch teams data.")


if __name__ == "__main__":
    main()
