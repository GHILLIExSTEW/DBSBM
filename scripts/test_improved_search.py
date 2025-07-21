#!/usr/bin/env python3
"""
Test script for improved external player search functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the bot directory to the path so we can import modules
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from compile_teams_and_players_improved import ImprovedPlayerSearcher

async def test_search():
    """Test the improved external search functionality."""
    searcher = ImprovedPlayerSearcher()
    
    # Test with a few well-known teams
    test_cases = [
        ("Los Angeles Lakers", "NBA"),
        ("Boston Celtics", "NBA"),
        ("New York Yankees", "MLB"),
    ]
    
    for team, league in test_cases:
        print(f"\nTesting: {team} ({league})")
        players, url = searcher.search_team_roster(team, league)
        
        print(f"Found {len(players)} players")
        print(f"Source URL: {url}")
        
        if players:
            print("Sample players:")
            for player in players[:10]:  # Show first 10 players
                print(f"  - {player}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_search()) 