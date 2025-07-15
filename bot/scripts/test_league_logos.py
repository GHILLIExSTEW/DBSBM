#!/usr/bin/env python3
"""
Test script to verify league logo loading with the new naming convention.
"""

import os
import sys

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.leagues import LEAGUE_IDS

from utils.asset_loader import AssetLoader


def test_league_logos():
    """Test loading league logos with the new naming convention."""

    asset_loader = AssetLoader()

    print("🧪 Testing League Logo Loading")
    print("=" * 50)

    # Test a few key leagues
    test_leagues = [
        "EPL",  # English Premier League
        "NBA",  # NBA
        "MLB",  # MLB
        "NHL",  # NHL
        "NFL",  # NFL
        "ChampionsLeague",  # UEFA Champions League
        "EuropaLeague",  # UEFA Europa League
        "LaLiga",  # La Liga
        "Bundesliga",  # Bundesliga
        "SerieA",  # Serie A
        "Ligue1",  # Ligue 1
        "MLS",  # MLS
        "WorldCup",  # FIFA World Cup
        "KHL",  # Kontinental Hockey League
        "CFL",  # CFL
        "NCAA",  # NCAA Football
        "SuperRugby",  # Super Rugby
        "SixNations",  # Six Nations Championship
        "EHF",  # EHF Champions League
        "PDC",  # Professional Darts Corporation
        "ATP",  # ATP Tour
        "WTA",  # WTA Tour
    ]

    success_count = 0
    total_count = len(test_leagues)

    for league_code in test_leagues:
        print(f"\n📋 Testing {league_code}...")

        # Get league info
        league_info = LEAGUE_IDS.get(league_code.upper())
        if not league_info:
            print(f"  ❌ No league info found for {league_code}")
            continue

        league_name = league_info.get("name", league_code)
        sport = league_info.get("sport", "unknown")

        print(f"  📝 League: {league_name}")
        print(f"  🏆 Sport: {sport}")

        # Try to load the logo
        logo = asset_loader.load_league_logo(league_code)

        if logo:
            print(f"  ✅ Logo loaded successfully! Size: {logo.size}")
            success_count += 1
        else:
            print(f"  ❌ Failed to load logo")

    print(f"\n📊 Results:")
    print(f"  Total leagues tested: {total_count}")
    print(f"  Successful loads: {success_count}")
    print(f"  Success rate: {(success_count/total_count)*100:.1f}%")

    if success_count == total_count:
        print(f"\n🎉 All league logos loaded successfully!")
    else:
        print(f"\n⚠️  Some league logos failed to load. Check the file structure.")


if __name__ == "__main__":
    test_league_logos()
