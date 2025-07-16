#!/usr/bin/env python3
"""
Verify the Brazil Serie A fix is working
"""

import asyncio
import sys
import os

# Add bot directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.db_manager import DatabaseManager

async def verify_fix():
    db = DatabaseManager()
    await db.connect()
    try:
        # Check current state
        rows = await db.fetch_all('SELECT league_name, COUNT(*) as count FROM api_games WHERE league_id = "71" GROUP BY league_name')
        print("Current state of league_id=71 games:")
        for row in rows:
            print(f"  league_name: '{row['league_name']}' - count: {row['count']}")
        
        # Show some sample rows
        rows = await db.fetch_all('SELECT api_game_id, home_team_name, away_team_name, league_name FROM api_games WHERE league_id = "71" LIMIT 3')
        print("\nSample rows:")
        for row in rows:
            print(f"  {row['api_game_id']}: {row['home_team_name']} vs {row['away_team_name']} - league_name: '{row['league_name']}'")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(verify_fix()) 