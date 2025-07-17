#!/usr/bin/env python3
"""
Fetch Brazil Serie A teams from API-Sports and save them
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
import aiohttp
import aiofiles

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API settings
from config.api_settings import API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 71  # Brazil Serie A
SEASON = 2025

# Output directory
OUTPUT_DIR = "data/teams"
OUTPUT_FILE = "brazil_serie_a_teams_2025.json"


async def fetch_brazil_serie_a_teams():
    """Fetch Brazil Serie A teams from API-Sports."""
    logger.info("Starting Brazil Serie A teams fetch...")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # API endpoint
    url = f"{API_BASE_URL}/teams"
    params = {"league": LEAGUE_ID, "season": SEASON}

    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_KEY,
    }

    try:
        # Create session with timeout
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.info(f"Fetching teams from: {url}")
            logger.info(f"Parameters: {params}")

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response headers: {dict(response.headers)}")

                    # Log the raw response for debugging
                    logger.info(f"Raw response: {json.dumps(data, indent=2)}")

                    # Check if we got a successful response
                    if data.get("errors"):
                        logger.error(f"API returned errors: {data['errors']}")
                        return False

                    if data.get("response"):
                        teams = data["response"]
                        logger.info(f"Successfully fetched {len(teams)} teams")

                        # Save the data
                        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

                        # Add metadata
                        output_data = {
                            "metadata": {
                                "league": "Brazil Serie A",
                                "league_id": LEAGUE_ID,
                                "season": SEASON,
                                "fetched_at": datetime.now().isoformat(),
                                "total_teams": len(teams),
                            },
                            "teams": teams,
                        }

                        async with aiofiles.open(
                            output_path, "w", encoding="utf-8"
                        ) as f:
                            await f.write(
                                json.dumps(output_data, indent=2, ensure_ascii=False)
                            )

                        logger.info(f"Saved {len(teams)} teams to {output_path}")

                        # Display team names
                        logger.info("Teams found:")
                        for team in teams:
                            team_info = team.get("team", {})
                            team_name = team_info.get("name", "Unknown")
                            team_id = team_info.get("id", "Unknown")
                            logger.info(f"  - {team_name} (ID: {team_id})")

                        return True
                    else:
                        logger.error("No 'response' field in API response")
                        return False
                else:
                    logger.error(f"API request failed with status {response.status}")
                    logger.error(f"Response text: {await response.text()}")
                    return False

    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(fetch_brazil_serie_a_teams())
    if success:
        logger.info("Brazil Serie A teams fetch completed successfully!")
    else:
        logger.error("Brazil Serie A teams fetch failed!")
        sys.exit(1)
