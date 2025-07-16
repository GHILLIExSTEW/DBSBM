#!/usr/bin/env python3
"""
Check Brazil Serie A games in database
"""

import asyncio
from data.db_manager import DatabaseManager

async def check_brazil_games():
    """Check if there are Brazil Serie A games in the database."""
    db = DatabaseManager()
    await db.connect()
    
    try:
        # Check Brazil Serie A games
        rows = await db.fetch_all('SELECT COUNT(*) as count FROM api_games WHERE league_name = "Brazil Serie A"')
        brazil_count = rows[0]["count"]
        print(f"Brazil Serie A games: {brazil_count}")
        
        # Check Italian Serie A games
        rows = await db.fetch_all('SELECT COUNT(*) as count FROM api_games WHERE league_name = "Serie A"')
        italian_count = rows[0]["count"]
        print(f"Italian Serie A games: {italian_count}")
        
        # Show some sample Brazil games
        if brazil_count > 0:
            rows = await db.fetch_all('SELECT home_team_name, away_team_name, start_time, status FROM api_games WHERE league_name = "Brazil Serie A" LIMIT 5')
            print("\nSample Brazil Serie A games:")
            for row in rows:
                print(f"  {row['home_team_name']} vs {row['away_team_name']} - {row['start_time']} ({row['status']})")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_brazil_games()) 