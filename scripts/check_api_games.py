#!/usr/bin/env python3
"""
Script to check the current state of the api_games table
and understand why no games are being returned for the /gameline command.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bot.data.db_manager import DatabaseManager

async def check_api_games():
    """Check the current state of the api_games table."""
    db_manager = DatabaseManager()
    
    try:
        # Connect to database
        await db_manager.connect()
        
        print("=== API Games Table Status ===")
        
        # Check total count
        total_count = await db_manager.fetchval("SELECT COUNT(*) FROM api_games")
        print(f"Total games in api_games table: {total_count}")
        
        if total_count == 0:
            print("❌ No games found in api_games table!")
            print("This explains why no games are listed in /gameline")
            return
        
        # Check games by sport
        sports = await db_manager.fetch_all("SELECT DISTINCT sport FROM api_games")
        print(f"\nSports found: {[s['sport'] for s in sports]}")
        
        # Check games by league
        leagues = await db_manager.fetch_all("SELECT DISTINCT league_name, sport FROM api_games")
        print(f"\nLeagues found:")
        for league in leagues:
            count = await db_manager.fetchval(
                "SELECT COUNT(*) FROM api_games WHERE league_name = $1 AND sport = $2",
                (league['league_name'], league['sport'])
            )
            print(f"  - {league['sport']}: {league['league_name']} ({count} games)")
        
        # Check recent games
        recent_games = await db_manager.fetch_all(
            "SELECT id, api_game_id, sport, league_name, home_team_name, away_team_name, start_time, status, season FROM api_games ORDER BY start_time DESC LIMIT 10"
        )
        print(f"\nMost recent 10 games:")
        for game in recent_games:
            print(f"  - {game['sport']} | {game['league_name']} | {game['home_team_name']} vs {game['away_team_name']} | {game['start_time']} | {game['status']} | Season: {game['season']}")
        
        # Check for MLB specifically
        mlb_games = await db_manager.fetch_all(
            "SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, season FROM api_games WHERE sport = 'Baseball' AND league_name = 'Major League Baseball' ORDER BY start_time DESC LIMIT 5"
        )
        print(f"\nMLB games found: {len(mlb_games)}")
        for game in mlb_games:
            print(f"  - {game['home_team_name']} vs {game['away_team_name']} | {game['start_time']} | {game['status']} | Season: {game['season']}")
        
        # Check for active games (not finished)
        active_games = await db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM api_games WHERE status NOT IN ('Match Finished', 'Finished', 'FT', 'Game Finished', 'Final', 'Ended')"
        )
        print(f"\nActive games (not finished): {active_games[0]['count']}")
        
        # Check for games starting today or later
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        future_games = await db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM api_games WHERE start_time >= $1",
            (today_start,)
        )
        print(f"Games starting today or later: {future_games[0]['count']}")
        
        # Test the exact query from get_normalized_games_for_dropdown
        print(f"\n=== Testing get_normalized_games_for_dropdown query ===")
        
        # Parameters for MLB
        sport = "Baseball"
        league_id = "1"  # From LEAGUE_ID_MAP
        league_name = "Major League Baseball"
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        finished_statuses = ["Match Finished", "Finished", "FT", "Game Finished", "Final"]
        current_year = datetime.now().year
        
        query = """
            SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, score, league_name
            FROM api_games
            WHERE sport = $1
            AND league_id = %s
            AND UPPER(league_name) = UPPER(%s)
            AND start_time >= %s
            AND status NOT IN (%s, %s, %s, %s, %s)
            AND season = %s
            ORDER BY start_time ASC LIMIT 100
        """
        
        test_results = await db_manager.fetch_all(
            query,
            (sport, league_id, league_name, today_start) + tuple(finished_statuses) + (current_year,)
        )
        
        print(f"Query results for MLB: {len(test_results)} games")
        for game in test_results[:5]:  # Show first 5
            print(f"  - {game['home_team_name']} vs {game['away_team_name']} | {game['start_time']} | {game['status']}")
        
    except Exception as e:
        print(f"Error checking api_games table: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_api_games()) 