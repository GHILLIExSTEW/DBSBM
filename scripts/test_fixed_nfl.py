#!/usr/bin/env python3
"""
Test the fixed NFL API calls.
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

async def test_fixed_nfl():
    """Test the fixed NFL API calls."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-FixedTest/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get NFL league info
        league_info = LEAGUE_IDS.get('NFL')
        if not league_info:
            print("❌ NFL league info not found!")
            return
        
        sport = league_info['sport']
        league_id = league_info['id']
        season = 2024  # Use 2024 for American Football
        
        print(f"NFL League Info:")
        print(f"  Sport: {sport}")
        print(f"  League ID: {league_id}")
        print(f"  Season: {season}")
        
        # Get endpoint config
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
        
        print(f"\nTesting teams endpoint:")
        print(f"  URL: {teams_url}")
        print(f"  Params: {teams_params}")
        
        try:
            async with session.get(teams_url, params=teams_params, timeout=30) as response:
                print(f"  Status: {response.status}")
                
                if response.status == 200:
                    teams_data = await response.json()
                    teams = teams_data.get('response', [])
                    
                    print(f"  Teams found: {len(teams)}")
                    
                    if teams:
                        # Test first 3 teams
                        for i, team in enumerate(teams[:3]):
                            team_id = team['id']
                            team_name = team['name']
                            
                            print(f"\n  Testing team {i+1}: {team_name} (ID: {team_id})")
                            
                            # Test players endpoint with correct parameters
                            players_endpoint = endpoint_config['players']
                            players_url = f"{base_url}{players_endpoint}"
                            
                            # American Football: no league parameter for players
                            players_params = {
                                'team': team_id,
                                'season': season
                            }
                            
                            print(f"    Players URL: {players_url}")
                            print(f"    Players Params: {players_params}")
                            
                            async with session.get(players_url, params=players_params, timeout=30) as players_response:
                                print(f"    Status: {players_response.status}")
                                
                                if players_response.status == 200:
                                    players_data = await players_response.json()
                                    players = players_data.get('response', [])
                                    
                                    print(f"    Players found: {len(players)}")
                                    
                                    if players:
                                        print(f"    ✅ Success! First 3 players:")
                                        for j, player in enumerate(players[:3]):
                                            if 'player' in player:
                                                name = player['player'].get('name')
                                            else:
                                                name = player.get('name')
                                            print(f"      {j+1}. {name}")
                                    else:
                                        print(f"    ❌ No players found")
                                        print(f"    Response: {players_data}")
                                else:
                                    response_text = await players_response.text()
                                    print(f"    ❌ HTTP {players_response.status}")
                                    print(f"    Response: {response_text}")
                            
                            # Rate limiting
                            await asyncio.sleep(0.5)
                    else:
                        print(f"  ❌ No teams found!")
                else:
                    print(f"  ❌ HTTP {response.status}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_nfl()) 