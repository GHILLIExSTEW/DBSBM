#!/usr/bin/env python3
"""
Test Logo System for Golf, Tennis, and F1
Verifies that the logo system is working correctly for all configured sports.
"""

import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot.config.asset_paths import get_sport_category_for_path
from bot.utils.asset_loader import asset_loader


def test_league_logo_loading():
    """Test loading league logos for all configured sports."""
    print("🧪 Testing League Logo System")
    print("=" * 50)

    # Test leagues for each sport
    test_leagues = {
        "tennis": ["ATP", "WTA"],
        "golf": [
            "PGA",
            "LPGA",
            "EUROPEAN_TOUR",
            "LIV_GOLF",
            "KORN_FERRY",
            "CHAMPIONS_TOUR",
            "RYDER_CUP",
            "PRESIDENTS_CUP",
            "SOLHEIM_CUP",
            "OLYMPIC_GOLF",
        ],
        "racing": ["FORMULA-1"],
    }

    total_tests = 0
    passed_tests = 0

    for sport, leagues in test_leagues.items():
        sport_emoji = {"tennis": "🎾", "golf": "⛳", "racing": "🏎️"}
        emoji = sport_emoji.get(sport, "🎾")
        print(f"\n{emoji} Testing {sport.upper()} leagues:")
        print("-" * 30)

        for league in leagues:
            total_tests += 1
            print(f"  Testing {league}...", end=" ")

            try:
                # Test loading the league logo
                logo = asset_loader.load_league_logo(league)

                if logo:
                    print("✅ PASS - Logo loaded successfully")
                    passed_tests += 1
                else:
                    print("❌ FAIL - No logo found")

            except Exception as e:
                print(f"❌ ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Logo system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logo files and directory structure.")

    return passed_tests == total_tests


def test_directory_structure():
    """Test that the directory structure is correct."""
    print("\n📁 Testing Directory Structure")
    print("=" * 50)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logos_dir = os.path.join(base_dir, "static", "logos", "leagues")

    expected_dirs = [
        "TENNIS/ATP",
        "TENNIS/WTA",
        "GOLF/PGA",
        "GOLF/LPGA",
        "GOLF/EUROPEAN_TOUR",
        "GOLF/LIV_GOLF",
        "GOLF/KORN_FERRY",
        "GOLF/CHAMPIONS_TOUR",
        "GOLF/RYDER_CUP",
        "GOLF/PRESIDENTS_CUP",
        "GOLF/SOLHEIM_CUP",
        "GOLF/OLYMPIC_GOLF",
        "RACING/FORMULA1",
    ]

    missing_dirs = []
    existing_dirs = []

    for dir_path in expected_dirs:
        full_path = os.path.join(logos_dir, dir_path)
        if os.path.exists(full_path):
            existing_dirs.append(dir_path)
            # Check for logo files
            files = [f for f in os.listdir(full_path) if f.endswith(".webp")]
            if files:
                print(f"  ✅ {dir_path}/ - {len(files)} logo(s) found")
            else:
                print(f"  ⚠️  {dir_path}/ - Directory exists but no logos found")
        else:
            missing_dirs.append(dir_path)
            print(f"  ❌ {dir_path}/ - Directory missing")

    print(
        f"\n📊 Directory Status: {len(existing_dirs)}/{len(expected_dirs)} directories exist"
    )

    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ All expected directories exist!")
        return True


def test_sport_category_mapping():
    """Test that sport category mapping is working correctly."""
    print("\n🗺️  Testing Sport Category Mapping")
    print("=" * 50)

    test_cases = [
        ("ATP", "TENNIS"),
        ("WTA", "TENNIS"),
        ("PGA", "GOLF"),
        ("LPGA", "GOLF"),
        ("EUROPEAN_TOUR", "GOLF"),
        ("LIV_GOLF", "GOLF"),
        ("FORMULA-1", "RACING"),
    ]

    passed = 0
    total = len(test_cases)

    for league, expected_sport in test_cases:
        actual_sport = get_sport_category_for_path(league)
        if actual_sport == expected_sport:
            print(f"  ✅ {league} -> {actual_sport}")
            passed += 1
        else:
            print(f"  ❌ {league} -> {actual_sport} (expected {expected_sport})")

    print(f"\n📊 Mapping Results: {passed}/{total} correct")
    return passed == total


def main():
    """Run all tests."""
    print("🚀 League Logo System Test Suite")
    print("=" * 60)

    # Run all tests
    structure_ok = test_directory_structure()
    mapping_ok = test_sport_category_mapping()
    logos_ok = test_league_logo_loading()

    print("\n" + "=" * 60)
    print("📋 Final Test Summary:")
    print(f"  Directory Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"  Sport Mapping: {'✅ PASS' if mapping_ok else '❌ FAIL'}")
    print(f"  Logo Loading: {'✅ PASS' if logos_ok else '❌ FAIL'}")

    if all([structure_ok, mapping_ok, logos_ok]):
        print("\n🎉 All systems are working correctly!")
        print("Golf, Tennis, and F1 logos are now working like Darts!")
    else:
        print("\n⚠️  Some issues detected. Check the output above for details.")

    return all([structure_ok, mapping_ok, logos_ok])


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
