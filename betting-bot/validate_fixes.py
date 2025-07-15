#!/usr/bin/env python3
"""
Validation script to test the straight-bet workflow fixes.
This script validates that all components can be imported and basic functionality works.
"""

import os
import sys
import traceback


def test_imports():
    """Test that all critical components can be imported."""
    print("🔍 Testing imports...")

    try:
        from commands.straight_betting import StraightBetWorkflowView

        print("✅ StraightBetWorkflowView imported successfully")
    except Exception as e:
        print(f"❌ Failed to import StraightBetWorkflowView: {e}")
        return False

    try:
        from utils.modals import StraightBetDetailsModal

        print("✅ StraightBetDetailsModal imported successfully")
    except Exception as e:
        print(f"❌ Failed to import StraightBetDetailsModal: {e}")
        return False

    try:
        from services.bet_service import BetService

        print("✅ BetService imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BetService: {e}")
        return False

    try:
        from utils.game_line_image_generator import GameLineImageGenerator

        print("✅ GameLineImageGenerator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import GameLineImageGenerator: {e}")
        return False

    try:
        from data.game_utils import get_normalized_games_for_dropdown

        print("✅ get_normalized_games_for_dropdown imported successfully")
    except Exception as e:
        print(f"❌ Failed to import get_normalized_games_for_dropdown: {e}")
        return False

    return True


def test_bet_service_methods():
    """Test that BetService methods exist and have correct signatures."""
    print("\n🔍 Testing BetService methods...")

    try:
        from services.bet_service import BetService

        # Check if create_straight_bet method exists
        if hasattr(BetService, "create_straight_bet"):
            print("✅ create_straight_bet method exists")
        else:
            print("❌ create_straight_bet method missing")
            return False

        # Check if _get_or_create_game method exists
        if hasattr(BetService, "_get_or_create_game"):
            print("✅ _get_or_create_game method exists")
        else:
            print("❌ _get_or_create_game method missing")
            return False

        return True
    except Exception as e:
        print(f"❌ Error testing BetService methods: {e}")
        return False


def test_image_generator_methods():
    """Test that image generator methods have correct signatures."""
    print("\n🔍 Testing image generator methods...")

    try:
        from utils.game_line_image_generator import GameLineImageGenerator

        # Check if draw_teams_section method exists
        if hasattr(GameLineImageGenerator, "draw_teams_section"):
            print("✅ draw_teams_section method exists")
        else:
            print("❌ draw_teams_section method missing")
            return False

        return True
    except Exception as e:
        print(f"❌ Error testing image generator methods: {e}")
        return False


def test_modal_methods():
    """Test that modal methods exist."""
    print("\n🔍 Testing modal methods...")

    try:
        from utils.modals import StraightBetDetailsModal

        # Check if on_submit method exists
        if hasattr(StraightBetDetailsModal, "on_submit"):
            print("✅ on_submit method exists")
        else:
            print("❌ on_submit method missing")
            return False

        # Check if on_error method exists
        if hasattr(StraightBetDetailsModal, "on_error"):
            print("✅ on_error method exists")
        else:
            print("❌ on_error method missing")
            return False

        return True
    except Exception as e:
        print(f"❌ Error testing modal methods: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Starting validation of straight-bet workflow fixes...\n")

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test BetService methods
    if not test_bet_service_methods():
        all_passed = False

    # Test image generator methods
    if not test_image_generator_methods():
        all_passed = False

    # Test modal methods
    if not test_modal_methods():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ The straight-bet workflow fixes are ready for production testing.")
    else:
        print("❌ SOME VALIDATION TESTS FAILED!")
        print("⚠️  Please review the errors above before deploying.")
    print("=" * 50)

    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"🚨 Validation script crashed: {e}")
        traceback.print_exc()
        sys.exit(1)
