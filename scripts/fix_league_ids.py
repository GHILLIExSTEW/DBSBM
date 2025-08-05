#!/usr/bin/env python3
"""
Script to fix league_id values in the api_games table
to match the LEAGUE_ID_MAP values.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bot.data.db_manager import DatabaseManager
from bot.data.game_utils import LEAGUE_ID_MAP

async def fix_league_ids():
    """Fix league_id values in the api_games table."""
    db_manager = DatabaseManager()
    
    try:
        print("=== Fixing League IDs ===")
        print(f"Current time: {datetime.now()}")
        
        # Connect to database
        await db_manager.connect()
        print("✅ Connected to database")
        
        # Get current games with their league names
        query = """
            SELECT id, api_game_id, sport, league_name, league_id, home_team_name, away_team_name
            FROM api_games
            ORDER BY sport, league_name
        """
        
        games = await db_manager.fetch_all(query)
        print(f"Found {len(games)} games in database")
        
        # Group games by sport and league
        updates_needed = []
        for game in games:
            sport = game['sport']
            league_name = game['league_name']
            current_league_id = game['league_id']
            
            # Find the correct league_id from LEAGUE_ID_MAP
            correct_league_id = None
            
            # Try to find the league in LEAGUE_ID_MAP
            for league_key, league_id in LEAGUE_ID_MAP.items():
                if league_key.lower() == league_name.lower():
                    correct_league_id = league_id
                    break
            
            # If not found, try some common mappings
            if not correct_league_id:
                if league_name == "Major League Baseball":
                    correct_league_id = "1"
                elif league_name == "Brazil Serie A":
                    correct_league_id = "71"
                else:
                    print(f"⚠️  No mapping found for: {sport} - {league_name}")
                    continue
            
            if current_league_id != correct_league_id:
                updates_needed.append({
                    'id': game['id'],
                    'sport': sport,
                    'league_name': league_name,
                    'old_league_id': current_league_id,
                    'new_league_id': correct_league_id
                })
        
        print(f"Found {len(updates_needed)} games that need league_id updates")
        
        # Update the league_ids
        for update in updates_needed:
            update_query = """
                UPDATE api_games 
                SET league_id = $1 
                WHERE id = $1
            """
            await db_manager.execute(update_query, (update['new_league_id'], update['id']))
            print(f"✅ Updated {update['sport']} - {update['league_name']}: {update['old_league_id']} -> {update['new_league_id']}")
        
        print(f"✅ Successfully updated {len(updates_needed)} games")
        
        # Verify the updates
        print("\n=== Verification ===")
        verification_query = """
            SELECT sport, league_name, league_id, COUNT(*) as count
            FROM api_games
            GROUP BY sport, league_name, league_id
            ORDER BY sport, league_name
        """
        
        verification_results = await db_manager.fetch_all(verification_query)
        for result in verification_results:
            print(f"  {result['sport']} | {result['league_name']} | league_id={result['league_id']} | {result['count']} games")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()
        print("✅ Database connection closed")

if __name__ == "__main__":
    asyncio.run(fix_league_ids()) 