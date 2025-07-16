#!/usr/bin/env python3
"""
Fix Brazil Serie A league_name in api_games table
"""

import asyncio
import sys
import os

# Add bot directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.db_manager import DatabaseManager

async def fix_brazil_serie_a_league_names():
    db = DatabaseManager()
    await db.connect()
    try:
        print("Updating league_name to 'Brazil Serie A' where league_id = 71...")
        await db.execute("UPDATE api_games SET league_name = 'Brazil Serie A' WHERE league_id = '71'")
        print("Update complete!")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(fix_brazil_serie_a_league_names()) 