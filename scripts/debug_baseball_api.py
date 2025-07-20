#!/usr/bin/env python3
"""
Debug Baseball API to find the correct endpoints and parameters.
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

async def debug_baseball_api():
    """Debug Baseball API structure."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-BaseballDebug/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        base_url = "https://v1.baseball.api-sports.io"
        
        print("Testing Baseball API endpoints:")
        
        # 1. Test leagues endpoint
        print("\n1. Testing /leagues endpoint:")
        leagues_url = f"{base_url}/leagues"
        try:
            async with session.get(leagues_url, headers=headers, timeout=30) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    leagues = data.get('response', [])
                    print(f"  Leagues found: {len(leagues)}")
                    for league in leagues[:5]:  # Show first 5
                        league_info = league.get('league', {})
                        print(f"    - {league_info.get('name')} (ID: {league_info.get('id')})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # 2. Test teams endpoint for MLB
        print("\n2. Testing /teams endpoint for MLB:")
        teams_url = f"{base_url}/teams"
        teams_params = {'league': 1, 'season': 2024}
        try:
            async with session.get(teams_url, params=teams_params, headers=headers, timeout=30) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    teams = data.get('response', [])
                    print(f"  Teams found: {len(teams)}")
                    if teams:
                        first_team = teams[0]
                        print(f"  First team structure: {list(first_team.keys())}")
                        if 'team' in first_team:
                            team_info = first_team['team']
                            print(f"    Team: {team_info.get('name')} (ID: {team_info.get('id')})")
                        else:
                            print(f"    Team: {first_team.get('name')} (ID: {first_team.get('id')})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # 3. Test different player endpoints
        print("\n3. Testing player endpoints:")
        
        # Try different possible endpoints
        player_endpoints = [
            "/players",
            "/players/statistics", 
            "/players/seasons",
            "/players/teams",
            "/players/leagues"
        ]
        
        for endpoint in player_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n  Testing {endpoint}:")
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    print(f"    Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"    Response keys: {list(data.keys())}")
                        if 'errors' in data:
                            print(f"    Errors: {data['errors']}")
                    else:
                        response_text = await response.text()
                        print(f"    Response: {response_text}")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # 4. Test players endpoint with different parameters
        print("\n4. Testing /players endpoint with different parameters:")
        players_url = f"{base_url}/players"
        
        # Try different parameter combinations
        test_cases = [
            {'league': 1, 'season': 2024},
            {'league': 1, 'season': 2024, 'team': 1},
            {'league': 1, 'season': 2024, 'team': 1, 'page': 1},
            {'league': 1, 'season': 2024, 'page': 1},
            {'season': 2024, 'team': 1},  # Without league
            {'team': 1, 'season': 2024},  # Just team and season
        ]
        
        for i, params in enumerate(test_cases, 1):
            print(f"\n  4.{i} Testing with params: {params}")
            try:
                async with session.get(players_url, params=params, headers=headers, timeout=30) as response:
                    print(f"    Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        players = data.get('response', [])
                        print(f"    Players found: {len(players)}")
                        
                        if players:
                            print(f"    ✅ Found players!")
                            first_player = players[0]
                            print(f"    First player structure: {list(first_player.keys())}")
                            if 'player' in first_player:
                                player_info = first_player['player']
                                print(f"      Name: {player_info.get('name')}")
                                print(f"      ID: {player_info.get('id')}")
                            else:
                                print(f"      Name: {first_player.get('name')}")
                                print(f"      ID: {first_player.get('id')}")
                            break
                        else:
                            print(f"    Response: {data}")
                    else:
                        response_text = await response.text()
                        print(f"    Response: {response_text}")
            except Exception as e:
                print(f"    ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_baseball_api()) 