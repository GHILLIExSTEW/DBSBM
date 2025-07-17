#!/usr/bin/env python3
"""
Test Multi-Provider API System
Tests the new multi-provider API system with different API providers.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent.parent
sys.path.insert(0, str(bot_dir))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("multi_provider_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def test_sportdevs_apis():
    """Test SportDevs APIs (Darts, Esports, Tennis)."""
    logger.info("=" * 50)
    logger.info("TESTING SPORTDEVS APIS")
    logger.info("=" * 50)

    async with MultiProviderAPI() as api:
        # Test Darts
        logger.info("Testing Darts API...")
        try:
            darts_data = await api.make_request("darts", "/matches-by-date")
            logger.info(f"Darts API response: {len(str(darts_data))} characters")
            logger.info(
                f"Darts data keys: {list(darts_data.keys()) if isinstance(darts_data, dict) else 'Not a dict'}"
            )
        except Exception as e:
            logger.error(f"Darts API failed: {e}")

        await asyncio.sleep(2)

        # Test Esports
        logger.info("Testing Esports API...")
        try:
            esports_data = await api.make_request("esports", "/matches")
            logger.info(f"Esports API response: {len(str(esports_data))} characters")
            logger.info(
                f"Esports data keys: {list(esports_data.keys()) if isinstance(esports_data, dict) else 'Not a dict'}"
            )
        except Exception as e:
            logger.error(f"Esports API failed: {e}")

        await asyncio.sleep(2)

        # Test Tennis
        logger.info("Testing Tennis API...")
        try:
            tennis_data = await api.make_request("tennis", "/matches-by-date")
            logger.info(f"Tennis API response: {len(str(tennis_data))} characters")
            logger.info(
                f"Tennis data keys: {list(tennis_data.keys()) if isinstance(tennis_data, dict) else 'Not a dict'}"
            )
        except Exception as e:
            logger.error(f"Tennis API failed: {e}")


async def test_rapidapi_golf():
    """Test RapidAPI Golf."""
    logger.info("=" * 50)
    logger.info("TESTING RAPIDAPI GOLF")
    logger.info("=" * 50)

    async with MultiProviderAPI() as api:
        logger.info("Testing Golf API...")
        try:
            # Test with date parameters
            params = {"start_date": "2024-10-01", "end_date": "2024-10-30"}
            golf_data = await api.make_request("golf", "/v1/events", params)
            logger.info(f"Golf API response: {len(str(golf_data))} characters")
            logger.info(
                f"Golf data keys: {list(golf_data.keys()) if isinstance(golf_data, dict) else 'Not a dict'}"
            )
        except Exception as e:
            logger.error(f"Golf API failed: {e}")


async def test_apisports():
    """Test API-Sports (existing functionality)."""
    logger.info("=" * 50)
    logger.info("TESTING API-SPORTS")
    logger.info("=" * 50)

    async with MultiProviderAPI() as api:
        # Test Football
        logger.info("Testing Football API...")
        try:
            params = {"season": 2025}
            football_data = await api.make_request("football", "/leagues", params)
            logger.info(
                f"Football API response: {len(football_data.get('response', []))} leagues"
            )
        except Exception as e:
            logger.error(f"Football API failed: {e}")

        await asyncio.sleep(2)

        # Test Basketball
        logger.info("Testing Basketball API...")
        try:
            params = {"season": 2025}
            basketball_data = await api.make_request("basketball", "/leagues", params)
            logger.info(
                f"Basketball API response: {len(basketball_data.get('response', []))} leagues"
            )
        except Exception as e:
            logger.error(f"Basketball API failed: {e}")


async def test_league_discovery():
    """Test league discovery across all providers."""
    logger.info("=" * 50)
    logger.info("TESTING LEAGUE DISCOVERY")
    logger.info("=" * 50)

    async with MultiProviderAPI() as api:
        try:
            discovered_leagues = await api.discover_all_leagues()

            logger.info(
                f"League discovery completed. Found leagues for {len(discovered_leagues)} sports"
            )

            for sport, leagues in discovered_leagues.items():
                logger.info(f"  {sport.title()}: {len(leagues)} leagues")

                # Show first few leagues for each sport
                for i, league in enumerate(leagues[:3]):
                    logger.info(
                        f"    - {league.get('name', 'Unknown')} (ID: {league.get('id', 'Unknown')})"
                    )
                if len(leagues) > 3:
                    logger.info(f"    ... and {len(leagues) - 3} more")

            return discovered_leagues

        except Exception as e:
            logger.error(f"League discovery failed: {e}")
            return {}


async def test_game_fetching():
    """Test game fetching for a few leagues."""
    logger.info("=" * 50)
    logger.info("TESTING GAME FETCHING")
    logger.info("=" * 50)

    async with MultiProviderAPI() as api:
        # First discover leagues
        discovered_leagues = await api.discover_all_leagues()

        if not discovered_leagues:
            logger.error("No leagues discovered, cannot test game fetching")
            return

        # Test fetching games for a few leagues
        test_count = 0
        for sport, leagues in discovered_leagues.items():
            if test_count >= 3:  # Limit to 3 sports for testing
                break

            if leagues:
                league = leagues[0]  # Test first league
                logger.info(f"Testing game fetching for {sport}/{league['name']}...")

                try:
                    games = await api.fetch_games(sport, league, "2024-10-15")
                    logger.info(f"  Fetched {len(games)} games")

                    if games:
                        # Show first game details
                        game = games[0]
                        logger.info(
                            f"  Sample game: {game.get('home_team_name', 'Unknown')} vs {game.get('away_team_name', 'Unknown')}"
                        )
                        logger.info(f"    Time: {game.get('start_time', 'Unknown')}")
                        logger.info(f"    Status: {game.get('status', 'Unknown')}")

                except Exception as e:
                    logger.error(f"  Game fetching failed: {e}")

                test_count += 1
                await asyncio.sleep(2)


async def main():
    """Main test function."""
    logger.info("Starting multi-provider API tests...")

    # Test 1: SportDevs APIs
    await test_sportdevs_apis()

    # Test 2: RapidAPI Golf
    await test_rapidapi_golf()

    # Test 3: API-Sports
    await test_apisports()

    # Test 4: League Discovery
    await test_league_discovery()

    # Test 5: Game Fetching
    await test_game_fetching()

    logger.info("=" * 50)
    logger.info("ALL TESTS COMPLETED!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
