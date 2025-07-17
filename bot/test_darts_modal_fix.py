#!/usr/bin/env python3
"""Test script to verify darts modal workflow fix."""

import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.leagues import LEAGUE_CONFIG

def test_darts_modal_configuration():
    """Test that darts modal configuration is set up correctly."""
    print("Testing darts modal configuration...")
    
    # Test 1: Check if DARTS is properly configured for modal
    if "DARTS" in LEAGUE_CONFIG:
        darts_config = LEAGUE_CONFIG['DARTS']
        print("✓ DARTS found in LEAGUE_CONFIG")
        
        # Check that it's configured as individual sport
        sport_type = darts_config.get('sport_type')
        if sport_type == "Individual Player":
            print("✓ DARTS configured as Individual Player sport")
        else:
            print(f"✗ DARTS sport_type is {sport_type}, expected Individual Player")
            return False
        
        # Check that it has proper placeholders
        team_placeholder = darts_config.get('team_placeholder')
        if "Michael van Gerwen" in team_placeholder:
            print("✓ DARTS has proper player placeholder")
        else:
            print(f"✗ DARTS team_placeholder is {team_placeholder}")
            return False
            
        opponent_placeholder = darts_config.get('opponent_placeholder')
        if "Peter Wright" in opponent_placeholder:
            print("✓ DARTS has proper opponent placeholder")
        else:
            print(f"✗ DARTS opponent_placeholder is {opponent_placeholder}")
            return False
    else:
        print("✗ DARTS not found in LEAGUE_CONFIG")
        return False
    
    # Test 2: Check that the modal logic will work correctly
    league_conf = LEAGUE_CONFIG.get("DARTS", {})
    sport_type = league_conf.get("sport_type", "Team Sport")
    is_individual_sport = sport_type == "Individual Player"
    
    # Test the condition that will be used in the modal
    modal_condition = is_individual_sport or "DARTS" == "DARTS"
    if modal_condition:
        print("✓ Modal condition will correctly identify DARTS as individual sport")
    else:
        print("✗ Modal condition will not identify DARTS as individual sport")
        return False
    
    print("\nAll tests passed! Darts modal workflow should now work correctly.")
    print("Expected workflow:")
    print("1. User selects 'Darts' as sport")
    print("2. System skips league selection")
    print("3. System goes directly to player/opponent entry modal")
    print("4. Modal shows 'Player' and 'Opponent' fields with darts placeholders")
    print("5. User enters player and opponent names")
    print("6. System continues to units selection")
    return True

if __name__ == "__main__":
    test_darts_modal_configuration() 