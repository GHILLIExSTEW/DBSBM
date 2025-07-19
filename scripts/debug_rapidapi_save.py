#!/usr/bin/env python3
"""
Debug script to test RapidAPI database saving.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.utils.multi_provider_api import MultiProviderAPI
import aiomysql

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_db_pool() -> aiomysql.Pool:
    """Set up and return a MySQL connection pool."""
    try:
        logger.info("Creating MySQL connection pool...")
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB"),
            minsize=1,
            maxsize=5,
            autocommit=True,
        )
        logger.info("MySQL connection pool created successfully")
        return pool
    except Exception as e:
        logger.error(f"Failed to create MySQL connection pool: {e}")
        raise


async def test_rapidapi_save():
    """Test if RapidAPI games are being saved to database."""
    logger.info("Testing RapidAPI database saving...")

    pool = None
    try:
        pool = await setup_db_pool()

        async with MultiProviderAPI(pool) as api:
            # Test 1: Check if db_pool is available
            logger.info(
                f"MultiProviderAPI db_pool available: {api.db_pool is not None}"
            )

            # Test 2: Test darts leagues discovery
            logger.info("Testing darts leagues discovery...")
            darts_leagues = await api.discover_leagues("darts")
            logger.info(f"Found {len(darts_leagues)} darts leagues")

            if darts_leagues:
                # Test 3: Test fetching games for first darts league
                test_league = darts_leagues[0]
                logger.info(f"Testing with league: {test_league['name']}")

                today = datetime.now().strftime("%Y-%m-%d")
                games = await api.fetch_games("darts", test_league, today)
                logger.info(f"Fetched {len(games)} games for {test_league['name']}")

                if games:
                    # Test 4: Test saving to database
                    logger.info("Testing database save...")
                    for game in games:
                        logger.info(
                            f"Game data: {game.get('api_game_id')} - {game.get('home_team_name')} vs {game.get('away_team_name')}"
                        )
                        success = await api._save_game_to_db(game)
                        logger.info(f"Save result: {success}")

                        # Verify the game was saved
                        async with pool.acquire() as conn:
                            async with conn.cursor() as cur:
                                await cur.execute(
                                    "SELECT api_game_id FROM api_games WHERE api_game_id = %s",
                                    (game.get("api_game_id"),),
                                )
                                result = await cur.fetchone()
                                logger.info(f"Game in database: {result is not None}")
                else:
                    logger.warning("No games found for testing")
            else:
                logger.warning("No darts leagues found for testing")

    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)
    finally:
        if pool:
            pool.close()
            await pool.wait_closed()


if __name__ == "__main__":
    asyncio.run(test_rapidapi_save())
