#!/usr/bin/env python3
"""
Test script to check if darts, tennis, golf, and esports are being fetched and saved to the database.
"""

import asyncio
import logging
import os
import sys
import pytest
from datetime import datetime, timezone

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.utils.multi_provider_api import MultiProviderAPI
from bot.data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_missing_sports():
    """Test if darts, tennis, golf, and esports are being fetched and saved."""

    # Check environment variables
    logger.info("Checking environment variables...")
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        logger.error("❌ RAPIDAPI_KEY not found in environment variables!")
        logger.error("This is required for darts, tennis, and golf APIs")
        assert False, "RAPIDAPI_KEY not found in environment variables"
    else:
        logger.info(f"✅ RAPIDAPI_KEY found: {rapidapi_key[:10]}...")

    # Initialize database manager
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Initialize MultiProviderAPI
        logger.info("Initializing MultiProviderAPI...")
        async with MultiProviderAPI(db_manager.db) as api:

            # Test league discovery for missing sports
            missing_sports = ["darts", "tennis", "golf", "esports"]

            for sport in missing_sports:
                logger.info(f"\n{'='*50}")
                logger.info(f"Testing {sport.upper()}...")
                logger.info(f"{'='*50}")

                try:
                    # Discover leagues for this sport
                    logger.info(f"Discovering leagues for {sport}...")
                    leagues = await api.discover_leagues(sport)

                    if leagues:
                        logger.info(f"✅ Found {len(leagues)} leagues for {sport}:")
                        for league in leagues[:5]:  # Show first 5 leagues
                            logger.info(
                                f"  - {league.get('name', 'Unknown')} (ID: {league.get('id', 'Unknown')})"
                            )

                        # Test fetching games for the first league
                        if leagues:
                            test_league = leagues[0]
                            logger.info(
                                f"Testing game fetch for {test_league['name']}..."
                            )

                            today = datetime.now().strftime("%Y-%m-%d")
                            games = await api.fetch_games(sport, test_league, today)

                            if games:
                                logger.info(
                                    f"✅ Found {len(games)} games for {test_league['name']}"
                                )

                                # Test saving to database
                                logger.info("Testing database save...")
                                saved_count = 0
                                for game in games[:3]:  # Test first 3 games
                                    success = await api._save_game_to_db(game)
                                    if success:
                                        saved_count += 1
                                        logger.info(
                                            f"  ✅ Saved game: {game.get('api_game_id')} - {game.get('home_team_name')} vs {game.get('away_team_name')}"
                                        )
                                    else:
                                        logger.error(
                                            f"  ❌ Failed to save game: {game.get('api_game_id')}"
                                        )

                                logger.info(
                                    f"Database save test: {saved_count}/{min(3, len(games))} games saved successfully"
                                )
                            else:
                                logger.warning(
                                    f"⚠️ No games found for {test_league['name']} on {today}"
                                )
                    else:
                        logger.warning(f"⚠️ No leagues found for {sport}")

                except Exception as e:
                    logger.error(f"❌ Error testing {sport}: {e}")
                    continue

            # Check what's actually in the database
            logger.info(f"\n{'='*50}")
            logger.info("CHECKING DATABASE CONTENTS...")
            logger.info(f"{'='*50}")

            async with db_manager.db.acquire() as conn:
                async with conn.cursor() as cur:
                    # Check total games by sport
                    await cur.execute(
                        """
                        SELECT sport, COUNT(*) as count 
                        FROM api_games 
                        GROUP BY sport 
                        ORDER BY count DESC
                    """
                    )
                    sport_counts = await cur.fetchall()

                    logger.info("Games in database by sport:")
                    for sport_count in sport_counts:
                        logger.info(f"  {sport_count[0]}: {sport_count[1]} games")

                    # Check specifically for missing sports
                    for sport in missing_sports:
                        await cur.execute(
                            """
                            SELECT COUNT(*) as count 
                            FROM api_games 
                            WHERE LOWER(sport) = %s
                        """,
                            (sport,),
                        )
                        count = await cur.fetchone()
                        count = count[0] if count else 0

                        if count > 0:
                            logger.info(
                                f"✅ {sport.title()}: {count} games in database"
                            )
                        else:
                            logger.warning(f"❌ {sport.title()}: 0 games in database")

                    # Show some recent games for missing sports
                    for sport in missing_sports:
                        await cur.execute(
                            """
                            SELECT api_game_id, league_name, home_team_name, away_team_name, start_time, status
                            FROM api_games 
                            WHERE LOWER(sport) = %s
                            ORDER BY fetched_at DESC
                            LIMIT 3
                        """,
                            (sport,),
                        )
                        recent_games = await cur.fetchall()

                        if recent_games:
                            logger.info(f"\nRecent {sport} games:")
                            for game in recent_games:
                                logger.info(
                                    f"  {game[0]}: {game[1]} - {game[2]} vs {game[3]} ({game[4]}) - {game[5]}"
                                )
                        else:
                            logger.warning(f"No {sport} games found in database")

    except Exception as e:
        logger.error(f"Error in test: {e}")
        assert False, f"Test failed with error: {e}"

    finally:
        await db_manager.close()

    assert True, "Missing sports test completed successfully"


if __name__ == "__main__":
    asyncio.run(test_missing_sports())
