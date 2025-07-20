#!/usr/bin/env python3
"""
Test API connection and show available leagues.
"""

import os
import sys
import asyncio
import aiohttp

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

async def test_api_connection(api_key: str):
    """Test API connection with a simple request."""
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-Test/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Test with NBA teams endpoint
        url = "https://v1.basketball.api-sports.io/teams"
        params = {
            'league': 12,  # NBA league ID
            'season': 2024
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                print(f"API Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    teams = data.get('response', [])
                    print(f"✅ API connection successful!")
                    print(f"Found {len(teams)} NBA teams")
                    
                    # Show first few teams
                    print("\nSample teams:")
                    for team in teams[:5]:
                        team_name = team.get('team', {}).get('name', 'Unknown')
                        print(f"  - {team_name}")
                        
                    return True
                else:
                    print(f"❌ API request failed with status {response.status}")
                    if response.status == 401:
                        print("Invalid API key")
                    elif response.status == 429:
                        print("Rate limit exceeded")
                    return False
                    
        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False

def show_available_leagues():
    """Show all available leagues."""
    print("\n" + "=" * 60)
    print("AVAILABLE LEAGUES")
    print("=" * 60)
    
    # Group by sport
    sports = {}
    for league, info in LEAGUE_IDS.items():
        sport = info['sport']
        if sport not in sports:
            sports[sport] = []
        sports[sport].append(league)
    
    for sport, leagues in sports.items():
        print(f"\n{sport.upper()}:")
        for league in leagues:
            season = get_current_season(league)
            print(f"  - {league} (Season: {season})")

async def main():
    """Main function."""
    print("=" * 60)
    print("API CONNECTION TEST")
    print("=" * 60)
    
    # Get API key
    api_key = input("Enter your API-Sports key: ").strip()
    if not api_key:
        print("API key is required!")
        return
    
    print(f"\nTesting API connection...")
    success = await test_api_connection(api_key)
    
    if success:
        show_available_leagues()
        
        print(f"\n" + "=" * 60)
        print("API TEST COMPLETE")
        print("=" * 60)
        print("✅ API connection working!")
        print("You can now run the download scripts.")
    else:
        print(f"\n" + "=" * 60)
        print("API TEST FAILED")
        print("=" * 60)
        print("❌ Please check your API key and try again.")

if __name__ == "__main__":
    asyncio.run(main()) 