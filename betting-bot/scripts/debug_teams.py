#!/usr/bin/env python3
"""
Debug script to check what teams are returned by FIFA World Cup API
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

# Add the parent directory to sys.path for imports
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from config.leagues import ENDPOINTS


async def debug_teams():
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("API_KEY not found in environment variables")
        return

    base_url = ENDPOINTS["football"]

    async with aiohttp.ClientSession(headers={"x-apisports-key": api_key}) as session:
        # Test both 2022 and 2025 seasons
        for season in [2022, 2025]:
            print(f"\n=== Testing season {season} ===")

            url = f"{base_url}/teams"
            params = {"league": "15", "season": season}  # FIFA World Cup

            try:
                async with session.get(url, params=params) as response:
                    print(f"Status: {response.status}")
                    data = await response.json()

                    if "response" in data and data["response"]:
                        teams = data["response"]
                        print(f"Found {len(teams)} teams:")
                        for team in teams:
                            team_info = team.get("team", {})
                            print(
                                f"  - {team_info.get('name', 'Unknown')} (ID: {team_info.get('id', 'Unknown')})"
                            )
                            if "logo" in team_info:
                                print(f"    Logo URL: {team_info['logo']}")
                    else:
                        print("No teams found or error in response")
                        print(f"Response: {json.dumps(data, indent=2)}")

            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_teams())
