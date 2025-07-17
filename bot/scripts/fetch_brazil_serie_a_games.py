#!/usr/bin/env python3
"""
Fetch Brazil Serie A games from API-Sports and save them to api_games table
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
import aiohttp
import aiomysql

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API settings and database manager
from config.api_settings import API_KEY
from data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 71  # Brazil Serie A
LEAGUE_NAME = "Brazil Serie A"
SPORT = "football"
SEASON = 2025


async def fetch_brazil_serie_a_games():
    """Fetch Brazil Serie A games from API-Sports and save to database."""
    logger.info("Starting Brazil Serie A games fetch...")

    # Initialize database manager
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Create session with timeout
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:

            # Fetch games for the next 30 days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)

            logger.info(
                f"Fetching games from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )

            # API endpoint
            url = f"{API_BASE_URL}/fixtures"
            headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": API_KEY,
            }

            params = {
                "league": LEAGUE_ID,
                "season": SEASON,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
            }

            logger.info(f"Making API request to: {url}")
            logger.info(f"Parameters: {params}")

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    logger.info(f"Response status: {response.status}")

                    # Check for API errors
                    if data.get("errors"):
                        logger.error(f"API returned errors: {data['errors']}")
                        return False

                    # Check if we got a successful response
                    if "response" not in data:
                        logger.error(f"No 'response' field in API data: {data}")
                        return False

                    games = data.get("response", [])
                    logger.info(f"Found {len(games)} games in API response")

                    if not games:
                        logger.warning("No games found in the date range")
                        return True

                    # Process and save each game
                    saved_count = 0
                    for game in games:
                        try:
                            # Extract game data
                            fixture = game.get("fixture", {})
                            teams = game.get("teams", {})
                            goals = game.get("goals", {})
                            score = game.get("score", {})

                            # Prepare game data for database
                            game_data = {
                                "api_game_id": str(fixture.get("id")),
                                "sport": SPORT,
                                "league_id": str(LEAGUE_ID),
                                "league_name": LEAGUE_NAME,
                                "home_team_id": teams.get("home", {}).get("id"),
                                "away_team_id": teams.get("away", {}).get("id"),
                                "home_team_name": teams.get("home", {}).get(
                                    "name", "Unknown"
                                ),
                                "away_team_name": teams.get("away", {}).get(
                                    "name", "Unknown"
                                ),
                                "start_time": fixture.get("date"),
                                "end_time": None,  # API doesn't provide end time
                                "status": fixture.get("status", {}).get("short", "NS"),
                                "score": json.dumps(score) if score else None,
                                "venue": fixture.get("venue", {}).get("name"),
                                "referee": fixture.get("referee"),
                                "season": SEASON,
                                "raw_json": json.dumps(game),
                                "fetched_at": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }

                            # Save to database
                            await db_manager.upsert_api_game(game_data)
                            saved_count += 1

                            logger.info(
                                f"Saved game: {game_data['home_team_name']} vs {game_data['away_team_name']} ({game_data['start_time']})"
                            )

                        except Exception as e:
                            logger.error(f"Error processing game: {e}")
                            continue

                    logger.info(
                        f"Successfully saved {saved_count}/{len(games)} games to database"
                    )
                    return True

                else:
                    error_text = await response.text()
                    logger.error(
                        f"API request failed: {response.status} - {error_text}"
                    )
                    return False

    except Exception as e:
        logger.error(f"Error fetching Brazil Serie A games: {e}")
        return False
    finally:
        await db_manager.close()


async def main():
    """Main function to run the Brazil Serie A games fetch."""
    logger.info("Starting Brazil Serie A games fetch process...")

    success = await fetch_brazil_serie_a_games()

    if success:
        logger.info("Brazil Serie A games fetch completed successfully!")
    else:
        logger.error("Brazil Serie A games fetch failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
