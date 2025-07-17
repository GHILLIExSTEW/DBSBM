#!/usr/bin/env python3
"""
Test script for the fixed RapidAPI Darts integration.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rapidapi_darts():
    """Test the fixed RapidAPI Darts integration."""
    logger.info("Testing RapidAPI Darts integration...")

    async with MultiProviderAPI() as api:
        try:
            # Test league discovery
            logger.info("Discovering darts leagues...")
            leagues = await api.discover_leagues("darts")
            logger.info(f"Found {len(leagues)} darts leagues")

            if leagues:
                # Show first few leagues
                for i, league in enumerate(leagues[:5]):
                    logger.info(f"  {i+1}. {league['name']} (ID: {league['id']})")

                # Test fetching games for the first league
                if leagues:
                    first_league = leagues[0]
                    today = datetime.now().strftime("%Y-%m-%d")
                    logger.info(
                        f"Fetching games for {first_league['name']} on {today}..."
                    )

                    games = await api.fetch_games("darts", first_league, today)
                    logger.info(f"Found {len(games)} games")

                    if games:
                        for i, game in enumerate(games[:3]):
                            logger.info(
                                f"  {i+1}. {game.get('home_team_name', 'Unknown')} vs {game.get('away_team_name', 'Unknown')}"
                            )
                            logger.info(f"     Status: {game.get('status', 'Unknown')}")
                            if game.get("score"):
                                logger.info(
                                    f"     Score: {game['score']['home']} - {game['score']['away']}"
                                )
            else:
                logger.warning("No darts leagues found")

        except Exception as e:
            logger.error(f"Error testing darts: {e}")
            import traceback

            traceback.print_exc()


async def test_direct_rapidapi_darts():
    """Test direct RapidAPI Darts API call to compare."""
    logger.info("\nTesting direct RapidAPI Darts API call...")

    import aiohttp
    from dotenv import load_dotenv

    load_dotenv()
    rapidapi_key = os.getenv("RAPIDAPI_KEY")

    async with aiohttp.ClientSession() as session:
        # Test tournaments endpoint
        url = "https://darts-devs.p.rapidapi.com/tournaments"
        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "darts-devs.p.rapidapi.com",
        }

        try:
            async with session.get(url, headers=headers) as response:
                logger.info(f"Direct API Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"Direct API Success! Found {len(data.get('tournaments', []))} tournaments"
                    )

                    # Show first few tournaments
                    tournaments = data.get("tournaments", [])
                    for i, tournament in enumerate(tournaments[:3]):
                        logger.info(
                            f"  {i+1}. {tournament.get('name', 'Unknown')} (ID: {tournament.get('id', 'Unknown')})"
                        )
                else:
                    logger.error(f"Direct API failed: {response.status}")

        except Exception as e:
            logger.error(f"Direct API error: {e}")


async def main():
    """Run all tests."""
    logger.info("Starting RapidAPI Darts tests...")

    await test_direct_rapidapi_darts()
    await test_rapidapi_darts()

    logger.info("RapidAPI Darts tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
