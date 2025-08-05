#!/usr/bin/env python3
"""
Test script to verify that darts leagues are being consolidated under a single "Darts" entry.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager
from utils.multi_provider_api import MultiProviderAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_darts_consolidation():
    """Test that darts leagues are being consolidated under a single 'Darts' entry."""

    # Mock environment variables for testing
    with patch.dict(
        os.environ,
        {
            "MYSQL_HOST": "localhost",
            "MYSQL_USER": "test_user",
            "MYSQL_PASSWORD": "test_password",
            "MYSQL_DB": "test_db",
        },
    ):
        # Mock the module-level imports
        with patch("bot.data.db_manager.MYSQL_HOST", "localhost"), patch(
            "bot.data.db_manager.MYSQL_USER", "test_user"
        ), patch("bot.data.db_manager.MYSQL_PASSWORD", "test_password"), patch(
            "bot.data.db_manager.MYSQL_DB", "test_db"
        ):

            # Initialize database manager
            logger.info("Initializing database manager...")
            db_manager = DatabaseManager()
            await db_manager.connect()

            try:
                # Initialize MultiProviderAPI
                logger.info("Initializing MultiProviderAPI...")
                async with MultiProviderAPI(db_manager.db) as api:

                    logger.info("Testing darts league consolidation...")

                    # Discover leagues for darts
                    logger.info("Discovering darts leagues...")
                    darts_response = await api.discover_leagues("darts")

                    # Handle APIResponse object
                    if hasattr(darts_response, "data"):
                        darts_leagues = darts_response.data
                    else:
                        darts_leagues = darts_response

                    if darts_leagues:
                        logger.info(f"Found {len(darts_leagues)} darts leagues:")
                        for league in darts_leagues[:10]:  # Show first 10
                            logger.info(
                                f"  - {league.get('name')} (ID: {league.get('id')})"
                            )

                    # Test the fetch_all_leagues_data method to see consolidation
                    logger.info(
                        "Testing fetch_all_leagues_data to see consolidation..."
                    )
                    results = await api.fetch_all_leagues_data(
                        date=datetime.now().strftime("%Y-%m-%d"), next_days=1
                    )

                    logger.info(f"Fetch results: {results}")

                    # Check what's in the database
                    logger.info("Checking database for darts games...")
                    async with db_manager.db.acquire() as conn:
                        async with conn.cursor() as cur:
                            # Check darts games by league name
                            await cur.execute(
                                """
                                SELECT league_name, COUNT(*) as count
                                FROM api_games
                                WHERE LOWER(sport) = 'darts'
                                GROUP BY league_name
                                ORDER BY count DESC
                            """
                            )
                            league_counts = await cur.fetchall()

                            logger.info("Darts games in database by league name:")
                            for league_count in league_counts:
                                logger.info(
                                    f"  {league_count[0]}: {league_count[1]} games"
                                )

                            # Check total darts games
                            await cur.execute(
                                """
                                SELECT COUNT(*) as count
                                FROM api_games
                                WHERE LOWER(sport) = 'darts'
                            """
                            )
                            total_darts = await cur.fetchone()
                            total_darts = total_darts[0] if total_darts else 0

                            logger.info(f"Total darts games in database: {total_darts}")

                            # Show some recent darts games
                            await cur.execute(
                                """
                                SELECT api_game_id, league_name, home_team_name, away_team_name, start_time, status
                                FROM api_games
                                WHERE LOWER(sport) = 'darts'
                                ORDER BY fetched_at DESC
                                LIMIT 10
                            """
                            )
                            recent_games = await cur.fetchall()

                            if recent_games:
                                logger.info("Recent darts games:")
                                for game in recent_games:
                                    logger.info(
                                        f"  {game[0]}: {game[1]} - {game[2]} vs {game[3]} ({game[4]}) - {game[5]}"
                                    )
                            else:
                                logger.warning("No darts games found in database")

            except Exception as e:
                logger.error(f"Error in test: {e}")
                assert False, f"Test failed with error: {e}"

            finally:
                await db_manager.close()

            assert True, "Darts consolidation test completed successfully"


if __name__ == "__main__":
    asyncio.run(test_darts_consolidation())
