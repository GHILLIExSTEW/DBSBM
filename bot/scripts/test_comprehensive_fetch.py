#!/usr/bin/env python3
"""
Test Comprehensive Fetcher
Tests the comprehensive fetcher with a subset of leagues to verify functionality.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent.parent
sys.path.insert(0, str(bot_dir))

import aiomysql
from utils.comprehensive_fetcher import ComprehensiveFetcher
from utils.league_discovery import LeagueDiscovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("comprehensive_fetch_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def test_comprehensive_fetch():
    """Test the comprehensive fetcher with a subset of leagues."""
    logger.info("Starting comprehensive fetcher test...")

    # Set up database pool
    db_pool = await aiomysql.create_pool(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        minsize=1,
        maxsize=5,
        autocommit=True,
    )

    try:
        async with ComprehensiveFetcher(db_pool) as fetcher:
            # Discover all leagues
            logger.info("Discovering all leagues...")
            discovered_leagues = await fetcher.discover_all_leagues()

            if not discovered_leagues:
                logger.error("No leagues discovered!")
                return False

            # Test with a subset of leagues (first 5 from each sport)
            test_leagues = {}
            for sport, leagues in discovered_leagues.items():
                test_leagues[sport] = leagues[
                    :5
                ]  # Take first 5 leagues from each sport

            # Temporarily replace discovered_leagues with test subset
            original_leagues = fetcher.discovered_leagues
            fetcher.discovered_leagues = test_leagues

            logger.info("Testing comprehensive fetch with subset of leagues...")

            # Fetch data for test leagues
            results = await fetcher.fetch_all_leagues_data(
                next_days=1
            )  # Only fetch for today

            # Get statistics
            stats = await fetcher.get_fetch_statistics()

            logger.info("Test Results:")
            logger.info(f"  - Total leagues tested: {results['total_leagues']}")
            logger.info(f"  - Successful fetches: {results['successful_fetches']}")
            logger.info(f"  - Failed fetches: {results['failed_fetches']}")
            logger.info(f"  - Total games fetched: {results['total_games']}")
            logger.info(f"  - Games in database: {stats.get('total_games', 0)}")
            logger.info(
                f"  - Unique leagues in database: {stats.get('unique_leagues', 0)}"
            )
            logger.info(
                f"  - Unique sports in database: {stats.get('unique_sports', 0)}"
            )

            if results["failed_fetches"] > 0:
                logger.warning(f"Failed leagues: {list(fetcher.failed_leagues)}")

            # Restore original leagues
            fetcher.discovered_leagues = original_leagues

            return results["successful_fetches"] > 0

    except Exception as e:
        logger.error(f"Error during comprehensive fetcher test: {e}")
        return False
    finally:
        db_pool.close()
        await db_pool.wait_closed()


async def test_league_discovery():
    """Test the league discovery functionality."""
    logger.info("Testing league discovery...")

    try:
        async with LeagueDiscovery() as discoverer:
            discovered_leagues = await discoverer.discover_all_leagues()

            if not discovered_leagues:
                logger.error("No leagues discovered!")
                return False

            total_leagues = sum(len(leagues) for leagues in discovered_leagues.values())
            logger.info(
                f"League discovery test successful: {total_leagues} leagues across {len(discovered_leagues)} sports"
            )

            # Print breakdown
            for sport, leagues in discovered_leagues.items():
                logger.info(f"  {sport.title()}: {len(leagues)} leagues")

            return True

    except Exception as e:
        logger.error(f"Error during league discovery test: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting comprehensive fetcher tests...")

    # Test 1: League Discovery
    logger.info("=" * 50)
    logger.info("TEST 1: League Discovery")
    logger.info("=" * 50)
    discovery_success = await test_league_discovery()

    if not discovery_success:
        logger.error("League discovery test failed!")
        return False

    # Test 2: Comprehensive Fetcher
    logger.info("=" * 50)
    logger.info("TEST 2: Comprehensive Fetcher")
    logger.info("=" * 50)
    fetcher_success = await test_comprehensive_fetch()

    if not fetcher_success:
        logger.error("Comprehensive fetcher test failed!")
        return False

    logger.info("=" * 50)
    logger.info("ALL TESTS PASSED!")
    logger.info("=" * 50)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)
