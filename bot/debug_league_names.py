#!/usr/bin/env python3
"""
Debug script to check league names for league_id=71
"""

import asyncio
import sys
import os

# Add bot directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.db_manager import DatabaseManager

async def debug_league_names():
    db = DatabaseManager()
    await db.connect()
    try:
        # Check all games with league_id=71
        rows = await db.fetch_all('SELECT league_name, COUNT(*) as count FROM api_games WHERE league_id = "71" GROUP BY league_name')
        print("Games with league_id=71:")
        for row in rows:
            print(f"  league_name: '{row['league_name']}' - count: {row['count']}")
        
        # Check all games with league_name containing "Serie"
        rows = await db.fetch_all("SELECT league_name, league_id, COUNT(*) as count FROM api_games WHERE league_name LIKE '%%Serie%%' GROUP BY league_name, league_id")
        print("\nAll games with 'Serie' in league_name:")
        for row in rows:
            print(f"  league_name: '{row['league_name']}' - league_id: {row['league_id']} - count: {row['count']}")
        
        # Try the update again
        print("\nTrying to update league_name to 'Brazil Serie A' where league_id = '71'...")
        result = await db.execute("UPDATE api_games SET league_name = 'Brazil Serie A' WHERE league_id = '71'")
        print(f"Update result: {result}")
        
        # Check again after update
        rows = await db.fetch_all('SELECT league_name, COUNT(*) as count FROM api_games WHERE league_id = "71" GROUP BY league_name')
        print("\nAfter update - Games with league_id=71:")
        for row in rows:
            print(f"  league_name: '{row['league_name']}' - count: {row['count']}")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(debug_league_names()) 