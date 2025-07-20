#!/usr/bin/env python3
"""
Diagnostic script to check player data availability from API.
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

async def diagnose_league(api_key: str, league_key: str):
    """Diagnose a specific league."""
    print(f"\n{'='*60}")
    print(f"DIAGNOSING LEAGUE: {league_key}")
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
        'User-Agent': 'DBSBM-Diagnostic/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Check teams endpoint
        print(f"\n1. Checking teams endpoint...")
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
                    teams = teams_data.get('response', [])
                    print(f"✅ Found {len(teams)} teams")
                    
                    # Show first few teams
                    print("\nSample teams:")
                    for i, team in enumerate(teams[:5]):
                        team_info = team.get('team', {})
                        team_name = team_info.get('name', 'Unknown')
                        team_id = team_info.get('id', 'Unknown')
                        print(f"  {i+1}. {team_name} (ID: {team_id})")
                    
                    # 2. Check players for first team
                    if teams:
                        first_team = teams[0]
                        team_id = first_team.get('team', {}).get('id')
                        team_name = first_team.get('team', {}).get('name')
                        
                        print(f"\n2. Checking players for first team: {team_name}")
                        
                        players_endpoint = endpoint_config['players']
                        players_url = f"{base_url}{players_endpoint}"
                        
                        players_params = {
                            'league': league_id,
                            'team': team_id,
                            'season': season
                        }
                        
                        async with session.get(players_url, params=players_params, timeout=30) as response:
                            print(f"Players API Status: {response.status}")
                            
                            if response.status == 200:
                                players_data = await response.json()
                                players = players_data.get('response', [])
                                print(f"✅ Found {len(players)} players")
                                
                                # Check how many have photos
                                players_with_photos = 0
                                sample_players = []
                                
                                for player in players:
                                    player_info = player.get('player', {})
                                    player_name = player_info.get('name')
                                    player_photo = player_info.get('photo')
                                    
                                    if player_name and player_photo:
                                        players_with_photos += 1
                                        if len(sample_players) < 3:
                                            sample_players.append({
                                                'name': player_name,
                                                'photo': player_photo
                                            })
                                
                                print(f"Players with photos: {players_with_photos}/{len(players)}")
                                
                                if sample_players:
                                    print("\nSample players with photos:")
                                    for i, player in enumerate(sample_players):
                                        print(f"  {i+1}. {player['name']}")
                                        print(f"     Photo: {player['photo'][:50]}...")
                                else:
                                    print("❌ No players with photos found!")
                                    
                            else:
                                print(f"❌ Players API failed: {response.status}")
                                if response.status == 401:
                                    print("Invalid API key")
                                elif response.status == 429:
                                    print("Rate limit exceeded")
                                else:
                                    try:
                                        error_data = await response.json()
                                        print(f"Error: {error_data}")
                                    except:
                                        print("Unknown error")
                else:
                    print(f"❌ Teams API failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main diagnostic function."""
    print("=" * 60)
    print("PLAYER DOWNLOAD DIAGNOSTIC")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Test priority leagues
    test_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    for league in test_leagues:
        await diagnose_league(api_key, league)
        await asyncio.sleep(1)  # Rate limiting
    
    print(f"\n{'='*60}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main()) 