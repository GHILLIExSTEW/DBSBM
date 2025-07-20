#!/usr/bin/env python3
"""
Debug script to see the actual API response structure.
"""

import os
import sys
import asyncio
import aiohttp
import json

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

async def debug_api_response(api_key: str, league_key: str):
    """Debug the actual API response structure."""
    print(f"\n{'='*60}")
    print(f"DEBUGGING API RESPONSE: {league_key}")
    print(f"{'='*60}")
    
    league_info = LEAGUE_IDS.get(league_key)
    if not league_info:
        print(f"❌ Unknown league: {league_key}")
        return
    
    sport = league_info['sport']
    league_id = league_info['id']
    season = get_current_season(league_key)
    
    print(f"Sport: {sport}")
    print(f"League ID: {league_id}")
    print(f"Season: {season}")
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-Debug/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        endpoint_config = ENDPOINTS_MAP.get(sport)
        if not endpoint_config:
            print(f"❌ No endpoint config for sport: {sport}")
            return
        
        base_url = endpoint_config['base']
        teams_endpoint = endpoint_config['teams']
        teams_url = f"{base_url}{teams_endpoint}"
        
        teams_params = {
            'league': league_id,
            'season': season
        }
        
        try:
            async with session.get(teams_url, params=teams_params, timeout=30) as response:
                print(f"Teams API Status: {response.status}")
                
                if response.status == 200:
                    teams_data = await response.json()
                    
                    print(f"\nRaw API Response Structure:")
                    print(f"Keys in response: {list(teams_data.keys())}")
                    
                    teams = teams_data.get('response', [])
                    print(f"Number of teams: {len(teams)}")
                    
                    if teams:
                        print(f"\nFirst team structure:")
                        first_team = teams[0]
                        print(json.dumps(first_team, indent=2))
                        
                        # Check if team data is nested
                        if 'team' in first_team:
                            team_info = first_team['team']
                            print(f"\nTeam info keys: {list(team_info.keys())}")
                            print(f"Team name: {team_info.get('name')}")
                            print(f"Team ID: {team_info.get('id')}")
                        else:
                            print(f"\nTeam data is not nested:")
                            print(f"Team keys: {list(first_team.keys())}")
                            print(f"Team name: {first_team.get('name')}")
                            print(f"Team ID: {first_team.get('id')}")
                    else:
                        print("No teams found in response")
                        
                else:
                    print(f"❌ Teams API failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main debug function."""
    print("=" * 60)
    print("API RESPONSE DEBUG")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Test with MLB first since it showed teams
    await debug_api_response(api_key, 'MLB')

if __name__ == "__main__":
    asyncio.run(main()) 