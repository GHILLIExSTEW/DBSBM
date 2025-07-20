#!/usr/bin/env python3
"""
Test NBA API with the correct v2 endpoint.
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_nba_api():
    """Test NBA API calls."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-NBATest/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        base_url = "https://v2.nba.api-sports.io"
        
        print("Testing NBA API:")
        
        # Test teams endpoint
        print("\n1. Testing /teams endpoint:")
        teams_url = f"{base_url}/teams"
        try:
            async with session.get(teams_url, headers=headers, timeout=30) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    teams = data.get('response', [])
                    print(f"  Teams found: {len(teams)}")
                    
                    if teams:
                        # Test first 3 teams
                        for i, team in enumerate(teams[:3]):
                            team_id = team.get('id')
                            team_name = team.get('name')
                            
                            print(f"\n  Testing team {i+1}: {team_name} (ID: {team_id})")
                            
                            # Test players endpoint
                            players_url = f"{base_url}/players"
                            players_params = {
                                'season': 2024,
                                'team': team_id
                            }
                            
                            print(f"    Players URL: {players_url}")
                            print(f"    Players Params: {players_params}")
                            
                            async with session.get(players_url, params=players_params, headers=headers, timeout=30) as players_response:
                                print(f"    Status: {players_response.status}")
                                
                                if players_response.status == 200:
                                    players_data = await players_response.json()
                                    players = players_data.get('response', [])
                                    
                                    print(f"    Players found: {len(players)}")
                                    
                                    if players:
                                        print(f"    ✅ Success! First 3 players:")
                                        for j, player in enumerate(players[:3]):
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
    asyncio.run(test_nba_api()) 