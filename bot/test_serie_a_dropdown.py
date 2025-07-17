#!/usr/bin/env python3
"""
Test script to verify Serie A dropdown functionality
"""

import asyncio
import sys
import os

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.game_utils import get_normalized_games_for_dropdown
from data.db_manager import DatabaseManager


async def test_serie_a_dropdown():
    """Test that the dropdown system can distinguish between Italian and Brazilian Serie A."""
    print("Testing Serie A dropdown functionality...")

    # Initialize database manager
    db = DatabaseManager()
    await db.connect()

    try:
        # Test Brazil Serie A
        print("\n1. Testing Brazil Serie A dropdown...")
        print("   Looking for league key: 'Brazil_Serie_A'")
        brazil_games = await get_normalized_games_for_dropdown(db, "Brazil_Serie_A")
        print(
            f"   Brazil Serie A games found: {len(brazil_games) - 1}"
        )  # Subtract 1 for manual entry

        # Test Italian Serie A
        print("\n2. Testing Italian Serie A dropdown...")
        italian_games = await get_normalized_games_for_dropdown(db, "SerieA")
        print(
            f"   Italian Serie A games found: {len(italian_games) - 1}"
        )  # Subtract 1 for manual entry

        # Show some game details
        if len(brazil_games) > 1:
            print("\n   Brazil Serie A sample games:")
            for game in brazil_games[1:4]:  # Skip manual entry, show first 3
                print(f"     {game['home_team']} vs {game['away_team']}")

        if len(italian_games) > 1:
            print("\n   Italian Serie A sample games:")
            for game in italian_games[1:4]:  # Skip manual entry, show first 3
                print(f"     {game['home_team']} vs {game['away_team']}")

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_serie_a_dropdown())
