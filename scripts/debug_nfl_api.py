#!/usr/bin/env python3
"""
Debug NFL API calls to see why we're getting 0 active players.
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

async def debug_nfl_api():
    """Debug NFL API calls."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-Debug/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get NFL league info
        league_info = LEAGUE_IDS.get('NFL')
        if not league_info:
            print("❌ NFL league info not found!")
            return
        
        sport = league_info['sport']
        league_id = league_info['id']
        season = get_current_season('NFL')
        
        print(f"NFL League Info:")
        print(f"  Sport: {sport}")
        print(f"  League ID: {league_id}")
        print(f"  Season: {season}")
        
        # Get endpoint config
        endpoint_config = ENDPOINTS_MAP.get(sport)
        if not endpoint_config:
            print(f"❌ No endpoint config for sport: {sport}")
            return
        
        print(f"\nEndpoint Config:")
        print(f"  Base URL: {endpoint_config['base']}")
        print(f"  Teams endpoint: {endpoint_config['teams']}")
        print(f"  Players endpoint: {endpoint_config['players']}")
        
        # Test teams endpoint
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
                        # Show first team structure
                        first_team = teams[0]
                        print(f"  First team structure:")
                        print(f"    Keys: {list(first_team.keys())}")
                        
                        if 'team' in first_team:
                            team_info = first_team['team']
                            print(f"    Team ID: {team_info.get('id')}")
                            print(f"    Team Name: {team_info.get('name')}")
                        else:
                            print(f"    Team ID: {first_team.get('id')}")
                            print(f"    Team Name: {first_team.get('name')}")
                        
                        # Test players endpoint for first team
                        if 'team' in first_team:
                            team_id = first_team['team']['id']
                            team_name = first_team['team']['name']
                        else:
                            team_id = first_team['id']
                            team_name = first_team['name']
                        
                        print(f"\nTesting players endpoint for {team_name}:")
                        
                        players_endpoint = endpoint_config['players']
                        players_url = f"{base_url}{players_endpoint}"
                        
                        players_params = {
                            'league': league_id,
                            'team': team_id,
                            'season': season
                        }
                        
                        print(f"  URL: {players_url}")
                        print(f"  Params: {players_params}")
                        
                        async with session.get(players_url, params=players_params, timeout=30) as players_response:
                            print(f"  Status: {players_response.status}")
                            
                            if players_response.status == 200:
                                players_data = await players_response.json()
                                players = players_data.get('response', [])
                                
                                print(f"  Players found: {len(players)}")
                                
                                if players:
                                    # Show first player structure
                                    first_player = players[0]
                                    print(f"  First player structure:")
                                    print(f"    Keys: {list(first_player.keys())}")
                                    
                                    if 'player' in first_player:
                                        player_info = first_player['player']
                                        print(f"    Player name: {player_info.get('name')}")
                                        print(f"    Player ID: {player_info.get('id')}")
                                    else:
                                        print(f"    Player name: {first_player.get('name')}")
                                        print(f"    Player ID: {first_player.get('id')}")
                                    
                                    # Show first few player names
                                    print(f"  First 5 player names:")
                                    for i, player in enumerate(players[:5]):
                                        if 'player' in player:
                                            name = player['player'].get('name')
                                        else:
                                            name = player.get('name')
                                        print(f"    {i+1}. {name}")
                                else:
                                    print(f"  ❌ No players found!")
                                    print(f"  Response: {players_data}")
                            else:
                                print(f"  ❌ HTTP {players_response.status}")
                                response_text = await players_response.text()
                                print(f"  Response: {response_text}")
                    else:
                        print(f"  ❌ No teams found!")
                        print(f"  Response: {teams_data}")
                else:
                    print(f"  ❌ HTTP {response.status}")
                    response_text = await response.text()
                    print(f"  Response: {response_text}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_nfl_api()) 