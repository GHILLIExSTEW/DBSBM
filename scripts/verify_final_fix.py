#!/usr/bin/env python3
"""
Final verification script to confirm Brazil Serie A fix is working
"""

import asyncio
import sys
import os

# Add bot directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot.data.db_manager import DatabaseManager


async def verify_final_fix():
    db = DatabaseManager()
    await db.connect()
    try:
        # Check current state of league_id=71 games
        rows = await db.fetch_all(
            'SELECT league_name, COUNT(*) as count FROM api_games WHERE league_id = "71" GROUP BY league_name'
        )
        print("Current state of league_id=71 games:")
        for row in rows:
            print(f"  league_name: '{row['league_name']}' - count: {row['count']}")

        # Show some sample rows
        rows = await db.fetch_all(
            'SELECT api_game_id, home_team_name, away_team_name, league_name FROM api_games WHERE league_id = "71" LIMIT 3'
        )
        print("\nSample Brazil Serie A games:")
        for row in rows:
            print(
                f"  {row['api_game_id']}: {row['home_team_name']} vs {row['away_team_name']} - {row['league_name']}"
            )

        # Check if there are any "Serie A" games with league_id=71 (should be 0)
        rows = await db.fetch_all(
            'SELECT COUNT(*) as count FROM api_games WHERE league_id = "71" AND league_name = "Serie A"'
        )
        wrong_count = rows[0]["count"]
        print(f"\nGames with league_id=71 and league_name='Serie A': {wrong_count}")

        if wrong_count == 0:
            print("✅ SUCCESS: All Brazil Serie A games now have correct league_name!")
        else:
            print("❌ ERROR: Some Brazil Serie A games still have wrong league_name!")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(verify_final_fix())
