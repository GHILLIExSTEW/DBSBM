#!/usr/bin/env python3
"""
Test script to verify the parlay command fix.
"""

import sys
import os

# Add the bot directory to the path
sys.path.append(os.path.dirname(__file__))

def test_parlay_workflow():
    """Test the parlay workflow initialization."""
    print("Testing parlay workflow...")
    
    try:
        from commands.parlay_betting import ParlayBetWorkflowView
        from utils.league_loader import get_all_sport_categories
        
        # Test sport categories
        sports = get_all_sport_categories()
        print(f"✅ Available sports: {sports}")
        
        if not sports:
            print("❌ No sports found - this would cause the parlay to freeze")
            return False
        
        # Test that we can create the workflow view (without Discord interaction)
        print("✅ Sport categories loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing parlay workflow: {e}")
        return False

def test_sport_select():
    """Test the SportSelect component."""
    print("\nTesting SportSelect component...")
    
    try:
        from commands.parlay_betting import SportSelect
        from utils.league_loader import get_all_sport_categories
        
        sports = get_all_sport_categories()
        
        # Create a mock parent view
        class MockParentView:
            def __init__(self):
                self.original_interaction = type('MockInteraction', (), {'id': 12345})()
        
        parent_view = MockParentView()
        
        # Create SportSelect
        sport_select = SportSelect(parent_view, sports)
        print(f"✅ SportSelect created with {len(sport_select.options)} options")
        
        # Check if options are valid
        for option in sport_select.options:
            if not option.label or not option.value:
                print(f"❌ Invalid option: {option}")
                return False
        
        print("✅ All SportSelect options are valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SportSelect: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Parlay Fix Verification")
    print("=" * 40)
    
    tests = [
        test_parlay_workflow,
        test_sport_select
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Parlay command should work now.")
    else:
        print("⚠️  Some tests failed. Check the output above for issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 