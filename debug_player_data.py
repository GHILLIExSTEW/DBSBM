#!/usr/bin/env python3
"""
Debug script to check player data in the database.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def check_player_data():
    """Check player data in the database."""
    print("Checking player data in database...")
    
    try:
        from data.db_manager import DatabaseManager
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize_db()
        
        print("✅ Database connection successful")
        
        # Try to check if player_search_cache table exists by querying it
        try:
            result = await db_manager.fetch_one("SELECT COUNT(*) as count FROM player_search_cache")
            total_players = result['count'] if result else 0
            print(f"Total players in cache: {total_players}")
            
            # Check MLB players specifically
            mlb_players = await db_manager.fetch_all("SELECT COUNT(*) as count FROM player_search_cache WHERE league = 'MLB'")
            mlb_count = mlb_players[0]['count'] if mlb_players else 0
            print(f"MLB players in cache: {mlb_count}")
            
            # Show some sample MLB players
            if mlb_count > 0:
                sample_players = await db_manager.fetch_all("SELECT player_name, team_name FROM player_search_cache WHERE league = 'MLB' LIMIT 5")
                print("Sample MLB players:")
                for player in sample_players:
                    print(f"  - {player['player_name']} ({player['team_name']})")
            else:
                print("No MLB players found in cache")
                
        except Exception as e:
            print(f"player_search_cache table doesn't exist or has issues: {e}")
        
        # Check bets table for player props
        try:
            bets_result = await db_manager.fetch_one("SELECT COUNT(*) as count FROM bets WHERE bet_type = 'player_prop' AND league = 'MLB'")
            mlb_bets = bets_result['count'] if bets_result else 0
            print(f"MLB player prop bets in bets table: {mlb_bets}")
        except Exception as e:
            print(f"Error checking bets table: {e}")
        
        await db_manager.close()
        
    except Exception as e:
        print(f"❌ Error checking player data: {e}")
        import traceback
        traceback.print_exc()

async def check_static_mlb_players():
    """Check the static MLB players in the code."""
    print("\nChecking static MLB players in code...")
    
    try:
        from services.player_search_service import PlayerSearchService
        
        # Create a mock db_manager to test static players
        class MockDBManager:
            async def fetch_all(self, query, params=None):
                return []
        
        service = PlayerSearchService(MockDBManager())
        
        # Test some MLB teams
        mlb_teams = ["yankees", "dodgers", "astros", "braves", "phillies"]
        
        for team in mlb_teams:
            players = await service._get_mlb_team_players(team)
            print(f"{team}: {len(players)} players - {players}")
        
    except Exception as e:
        print(f"❌ Error checking static players: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_player_data())
    asyncio.run(check_static_mlb_players()) 