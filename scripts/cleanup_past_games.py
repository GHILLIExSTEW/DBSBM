#!/usr/bin/env python3
"""
Cleanup script to delete past games from api_games table.
Deletes all records where start_time is before the current time.
"""

import asyncio
import logging
from datetime import datetime, timezone
from bot.data.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_past_games():
    """Delete all games from api_games table that have started."""
    db_manager = DatabaseManager()
    
    try:
        await db_manager.connect()
        logger.info("Connected to database")
        
        # Get current time in UTC
        current_time = datetime.now(timezone.utc)
        logger.info(f"Current time (UTC): {current_time}")
        
        # First, let's see how many past games we have
        count_query = """
            SELECT COUNT(*) as count 
            FROM api_games 
            WHERE start_time < %s
        """
        
        count_result = await db_manager.fetch_one(count_query, (current_time,))
        past_games_count = count_result['count'] if count_result else 0
        
        logger.info(f"Found {past_games_count} games with start time before current time")
        
        if past_games_count == 0:
            logger.info("No past games to delete")
            return
        
        # Show some examples of games that will be deleted
        sample_query = """
            SELECT id, league, home_team_name, away_team_name, start_time, status
            FROM api_games 
            WHERE start_time < %s
            ORDER BY start_time DESC
            LIMIT 10
        """
        
        sample_games = await db_manager.fetch_all(sample_query, (current_time,))
        
        logger.info("Sample games that will be deleted:")
        for game in sample_games:
            logger.info(f"  - {game['league']}: {game['away_team_name']} @ {game['home_team_name']} (Started: {game['start_time']})")
        
        # Confirm deletion
        print(f"\nAbout to delete {past_games_count} past games from api_games table.")
        response = input("Do you want to proceed? (yes/no): ")
        
        if response.lower() != 'yes':
            logger.info("Deletion cancelled by user")
            return
        
        # Delete past games
        delete_query = """
            DELETE FROM api_games 
            WHERE start_time < %s
        """
        
        result = await db_manager.execute(delete_query, (current_time,))
        logger.info(f"Successfully deleted {past_games_count} past games from api_games table")
        
        # Verify deletion
        remaining_count = await db_manager.fetch_one("SELECT COUNT(*) as count FROM api_games")
        logger.info(f"Remaining games in api_games table: {remaining_count['count']}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise
    finally:
        await db_manager.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    asyncio.run(cleanup_past_games()) 