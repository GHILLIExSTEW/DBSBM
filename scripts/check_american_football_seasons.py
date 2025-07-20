#!/usr/bin/env python3
"""
Check what seasons are available for American Football API.
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

async def check_american_football_seasons():
    """Check available seasons for American Football."""
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-SeasonCheck/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        base_url = "https://v1.american-football.api-sports.io"
        
        print("Checking American Football seasons:")
        
        # Test a wide range of seasons
        seasons_to_test = list(range(2010, 2026))  # 2010 to 2025
        
        working_seasons = []
        
        for season in seasons_to_test:
            print(f"Testing season {season}...", end=" ")
            
            # Test teams endpoint first
            teams_url = f"{base_url}/teams"
            teams_params = {'league': 1, 'season': season}
            
            try:
                async with session.get(teams_url, params=teams_params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        teams = data.get('response', [])
                        
                        if teams and len(teams) > 0:
                            # Now test players endpoint
                            players_url = f"{base_url}/players"
                            players_params = {'league': 1, 'season': season, 'team': teams[0]['id']}
                            
                            async with session.get(players_url, params=players_params, headers=headers, timeout=30) as players_response:
                                if players_response.status == 200:
                                    players_data = await players_response.json()
                                    players = players_data.get('response', [])
                                    
                                    if players and len(players) > 0:
                                        print(f"✅ Works! ({len(teams)} teams, {len(players)} players for first team)")
                                        working_seasons.append(season)
                                    else:
                                        print(f"❌ No players")
                                else:
                                    print(f"❌ Players endpoint failed")
                        else:
                            print(f"❌ No teams")
                    else:
                        print(f"❌ Teams endpoint failed")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        print(f"\n{'='*50}")
        print("SUMMARY")
        print(f"{'='*50}")
        if working_seasons:
            print(f"Working seasons: {working_seasons}")
            print(f"Latest working season: {max(working_seasons)}")
        else:
            print("❌ No working seasons found!")
            print("This suggests the American Football API might:")
            print("1. Have different season structure")
            print("2. Require different parameters")
            print("3. Not have player data available")
            print("4. Use a different endpoint for players")

if __name__ == "__main__":
    asyncio.run(check_american_football_seasons()) 