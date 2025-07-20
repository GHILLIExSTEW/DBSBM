#!/usr/bin/env python3
"""
Test Soccer API with the correct v3 endpoint.
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_soccer_api():
    """Test Soccer API calls."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-SoccerTest/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        base_url = "https://v3.football.api-sports.io"
        
        print("Testing Soccer API:")
        
        # Test leagues endpoint
        print("\n1. Testing /leagues endpoint:")
        leagues_url = f"{base_url}/leagues"
        leagues_params = {'season': 2024}
        try:
            async with session.get(leagues_url, params=leagues_params, headers=headers, timeout=30) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    leagues = data.get('response', [])
                    print(f"  Leagues found: {len(leagues)}")
                    
                    # Show first few leagues
                    for i, league in enumerate(leagues[:5]):
                        league_info = league.get('league', {})
                        print(f"    {i+1}. {league_info.get('name')} (ID: {league_info.get('id')})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test players endpoint for Premier League
        print("\n2. Testing /players endpoint for Premier League:")
        players_url = f"{base_url}/players"
        players_params = {
            'league': 39,  # Premier League
            'season': 2024
        }
        
        try:
            async with session.get(players_url, params=players_params, headers=headers, timeout=30) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    players = data.get('response', [])
                    
                    print(f"  Players found: {len(players)}")
                    
                    if players:
                        print(f"  ✅ Success! First 5 players:")
                        for i, player in enumerate(players[:5]):
                            player_info = player.get('player', {})
                            name = player_info.get('name')
                            team = player_info.get('team', {}).get('name', 'Unknown Team')
                            print(f"    {i+1}. {name} ({team})")
                    else:
                        print(f"  ❌ No players found")
                        print(f"  Response: {data}")
                else:
                    response_text = await response.text()
                    print(f"  ❌ HTTP {response.status}")
                    print(f"  Response: {response_text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_soccer_api()) 