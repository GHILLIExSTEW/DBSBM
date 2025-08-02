#!/usr/bin/env python3
"""
Script to manually trigger sync_games_from_api to populate the api_games table.
This will fetch games from the API and store them in the database.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bot.data.db_manager import DatabaseManager

async def sync_games():
    """Manually trigger the sync_games_from_api function."""
    db_manager = DatabaseManager()
    
    try:
        print("=== Starting Manual Game Sync ===")
        print(f"Current time: {datetime.now()}")
        
        # Connect to database
        await db_manager.connect()
        print("✅ Connected to database")
        
        # Check current state
        total_count_before = await db_manager.fetchval("SELECT COUNT(*) FROM api_games")
        print(f"Games in api_games table before sync: {total_count_before}")
        
        # Trigger the sync
        print("\n🔄 Starting sync_games_from_api...")
        await db_manager.sync_games_from_api()
        print("✅ Sync completed")
        
        # Check results
        total_count_after = await db_manager.fetchval("SELECT COUNT(*) FROM api_games")
        print(f"Games in api_games table after sync: {total_count_after}")
        
        if total_count_after > total_count_before:
            print(f"✅ Successfully added {total_count_after - total_count_before} games")
            
            # Show some sample games
            recent_games = await db_manager.fetch_all(
                "SELECT id, api_game_id, sport, league_name, home_team_name, away_team_name, start_time, status, season FROM api_games ORDER BY created_at DESC LIMIT 5"
            )
            print(f"\n📊 Sample of newly added games:")
            for game in recent_games:
                print(f"  - {game['sport']} | {game['league_name']} | {game['home_team_name']} vs {game['away_team_name']} | {game['start_time']} | {game['status']}")
        else:
            print("⚠️  No new games were added. This could mean:")
            print("   - API is not returning games")
            print("   - All games are already in the database")
            print("   - There's an issue with the API connection")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    asyncio.run(sync_games()) 