#!/usr/bin/env python3
"""
Test different NFL seasons to find which ones are available.
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

async def test_nfl_seasons():
    """Test different NFL seasons."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-SeasonTest/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get NFL league info
        league_info = LEAGUE_IDS.get('NFL')
        if not league_info:
            print("❌ NFL league info not found!")
            return
        
        sport = league_info['sport']
        league_id = league_info['id']
        
        print(f"NFL League Info:")
        print(f"  Sport: {sport}")
        print(f"  League ID: {league_id}")
        
        # Get endpoint config
        endpoint_config = ENDPOINTS_MAP.get(sport)
        if not endpoint_config:
            print(f"❌ No endpoint config for sport: {sport}")
            return
        
        base_url = endpoint_config['base']
        teams_endpoint = endpoint_config['teams']
        teams_url = f"{base_url}{teams_endpoint}"
        
        # Test different seasons
        seasons_to_test = [2024, 2023, 2022, 2021, 2020]
        
        for season in seasons_to_test:
            print(f"\nTesting season {season}:")
            
            teams_params = {
                'league': league_id,
                'season': season
            }
            
            try:
                async with session.get(teams_url, params=teams_params, timeout=30) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        teams_data = await response.json()
                        teams = teams_data.get('response', [])
                        
                        print(f"  Teams found: {len(teams)}")
                        
                        if teams:
                            # Test players for first team
                            first_team = teams[0]
                            if 'team' in first_team:
                                team_id = first_team['team']['id']
                                team_name = first_team['team']['name']
                            else:
                                team_id = first_team['id']
                                team_name = first_team['name']
                            
                            players_endpoint = endpoint_config['players']
                            players_url = f"{base_url}{players_endpoint}"
                            
                            players_params = {
                                'league': league_id,
                                'team': team_id,
                                'season': season
                            }
                            
                            async with session.get(players_url, params=players_params, timeout=30) as players_response:
                                if players_response.status == 200:
                                    players_data = await players_response.json()
                                    players = players_data.get('response', [])
                                    
                                    print(f"  Players for {team_name}: {len(players)}")
                                    
                                    if players:
                                        print(f"  ✅ Season {season} works!")
                                        # Show first few player names
                                        print(f"  First 3 players:")
                                        for i, player in enumerate(players[:3]):
                                            if 'player' in player:
                                                name = player['player'].get('name')
                                            else:
                                                name = player.get('name')
                                            print(f"    {i+1}. {name}")
                                        break  # Found working season
                                    else:
                                        print(f"  ❌ No players found")
                                else:
                                    print(f"  ❌ Players endpoint failed: {players_response.status}")
                        else:
                            print(f"  ❌ No teams found")
                    else:
                        print(f"  ❌ Teams endpoint failed: {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Rate limiting
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_nfl_seasons()) 