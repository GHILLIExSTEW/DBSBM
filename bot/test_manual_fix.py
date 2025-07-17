#!/usr/bin/env python3
"""Test script to verify manual entry fix."""

import asyncio
import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.leagues import LEAGUE_CONFIG
from config.asset_paths import get_sport_category_for_path
from data.game_utils import get_normalized_games_for_dropdown
from utils.asset_loader import asset_loader

async def test_manual_entry():
    """Test that manual entry is handled correctly."""
    print("Testing manual entry configuration...")
    
    # Test 1: Check if MANUAL is in LEAGUE_CONFIG
    if "MANUAL" in LEAGUE_CONFIG:
        print("✓ MANUAL found in LEAGUE_CONFIG")
        print(f"  Config: {LEAGUE_CONFIG['MANUAL']}")
    else:
        print("✗ MANUAL not found in LEAGUE_CONFIG")
        return False
    
    # Test 2: Check sport category mapping
    sport_category = get_sport_category_for_path("MANUAL")
    if sport_category:
        print(f"✓ Sport category for MANUAL: {sport_category}")
    else:
        print("✗ No sport category found for MANUAL")
        return False
    
    # Test 3: Test asset loader
    try:
        logo = asset_loader.load_team_logo("Test Team", "MANUAL")
        if logo:
            print("✓ Asset loader returned logo for MANUAL")
        else:
            print("✗ Asset loader returned None for MANUAL")
    except Exception as e:
        print(f"✗ Asset loader error: {e}")
        return False
    
    # Test 4: Test dropdown games
    try:
        games = await get_normalized_games_for_dropdown(None, "MANUAL")
        if games and len(games) > 0:
            print(f"✓ Dropdown games returned: {len(games)} games")
            print(f"  First game: {games[0]}")
        else:
            print("✗ No dropdown games returned")
            return False
    except Exception as e:
        print(f"✗ Dropdown games error: {e}")
        return False
    
    print("\nAll tests passed! Manual entry should now work correctly.")
    return True

if __name__ == "__main__":
    asyncio.run(test_manual_entry()) 