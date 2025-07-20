#!/usr/bin/env python3
"""
Compare players.csv data vs API team rosters to identify discrepancies.
"""

import os
import sys
import asyncio
import aiohttp
import csv
import json
from typing import Dict, List, Set
from pathlib import Path
import re

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

def load_players_csv() -> Dict[str, List[Dict]]:
    """Load players from CSV and group by team."""
    players_file = Path(__file__).parent.parent / 'bot' / 'data' / 'players.csv'
    
    if not players_file.exists():
        print("❌ players.csv not found!")
        return {}
    
    teams_players = {}
    
    try:
        with open(players_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = row.get('strTeam', '')
                if team:
                    if team not in teams_players:
                        teams_players[team] = []
                    teams_players[team].append(row)
        
        print(f"✅ Loaded {sum(len(players) for players in teams_players.values())} players from CSV")
        return teams_players
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return {}

def get_existing_images() -> Set[str]:
    """Get set of existing player image keys."""
    
    base_path = Path(__file__).parent.parent / 'bot' / 'static' / 'logos' / 'players'
    existing_images = set()
    
    for sport_dir in base_path.iterdir():
        if not sport_dir.is_dir():
            continue
            
        for team_dir in sport_dir.iterdir():
            if not team_dir.is_dir():
                continue
                
            for image_file in team_dir.glob("*.png"):
                player_name = image_file.stem
                team_name = team_dir.name
                sport_name = sport_dir.name
                
                # Create unique key
                key = f"{player_name}|{team_name}|{sport_name}"
                existing_images.add(key)
    
    return existing_images

async def get_api_team_players(api_key: str, sport: str, league_id: int, team_id: int, season: int) -> List[Dict]:
    """Get players for a team from API."""
    headers = {
        'x-apisports-key': api_key,
        'User-Agent': 'DBSBM-Compare/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        endpoint_config = ENDPOINTS_MAP.get(sport)
        if not endpoint_config:
            return []
        
        base_url = endpoint_config['base']
        players_endpoint = endpoint_config['players']
        url = f"{base_url}{players_endpoint}"
        
        params = {
            'league': league_id,
            'team': team_id,
            'season': season
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('response', [])
                else:
                    print(f"❌ API error {response.status} for team {team_id}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error getting players for team {team_id}: {e}")
            return []

async def compare_team(api_key: str, team_name: str, csv_players: List[Dict], league_key: str) -> Dict:
    """Compare CSV players vs API players for a team."""
    league_info = LEAGUE_IDS.get(league_key)
    if not league_info:
        return {'error': f'Unknown league: {league_key}'}
    
    sport = league_info['sport']
    league_id = league_info['id']
    season = get_current_season(league_key)
    
    # Get team ID from CSV players
    team_id = None
    for player in csv_players:
        if player.get('strTeam') == team_name:
            team_id = player.get('idTeam')
            break
    
    if not team_id:
        return {'error': f'No team ID found for {team_name}'}
    
    # Get API players
    api_players = await get_api_team_players(api_key, sport, league_id, int(team_id), season)
    
    # Compare
    csv_player_names = {p.get('strPlayer', '').lower() for p in csv_players}
    api_player_names = {p.get('player', {}).get('name', '').lower() for p in api_players}
    
    # Check which CSV players are missing from API
    missing_from_api = csv_player_names - api_player_names
    extra_in_api = api_player_names - csv_player_names
    
    return {
        'team_name': team_name,
        'csv_players': len(csv_players),
        'api_players': len(api_players),
        'missing_from_api': len(missing_from_api),
        'extra_in_api': len(extra_in_api),
        'csv_names': list(csv_player_names)[:5],  # First 5 for sample
        'api_names': list(api_player_names)[:5],  # First 5 for sample
        'missing_names': list(missing_from_api)[:5]  # First 5 missing
    }

async def main():
    """Main comparison function."""
    print("=" * 60)
    print("CSV vs API PLAYER COMPARISON")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Load data
    print("\n1. Loading players.csv...")
    teams_players = load_players_csv()
    
    print("\n2. Loading existing images...")
    existing_images = get_existing_images()
    print(f"Found {len(existing_images)} existing player images")
    
    # Focus on priority leagues
    priority_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    print(f"\n3. Comparing CSV vs API for priority leagues...")
    
    for league in priority_leagues:
        print(f"\n{'='*40}")
        print(f"LEAGUE: {league}")
        print(f"{'='*40}")
        
        # Find teams for this league in CSV
        league_teams = {}
        for team_name, players in teams_players.items():
            for player in players:
                if player.get('strLeague') == league:
                    if team_name not in league_teams:
                        league_teams[team_name] = []
                    league_teams[team_name].append(player)
        
        print(f"Teams in CSV for {league}: {len(league_teams)}")
        
        # Compare each team
        for team_name, players in list(league_teams.items())[:3]:  # Test first 3 teams
            print(f"\nTeam: {team_name}")
            result = await compare_team(api_key, team_name, players, league)
            
            if 'error' in result:
                print(f"  ❌ {result['error']}")
            else:
                print(f"  CSV players: {result['csv_players']}")
                print(f"  API players: {result['api_players']}")
                print(f"  Missing from API: {result['missing_from_api']}")
                print(f"  Extra in API: {result['extra_in_api']}")
                
                if result['missing_names']:
                    print(f"  Sample missing: {result['missing_names']}")
                
                # Check if CSV players have images
                csv_with_images = 0
                for player in players:
                    player_name = player.get('strPlayer', '').lower()
                    team_norm = team_name.lower().replace(' ', '_')
                    sport = LEAGUE_IDS[league]['sport']
                    image_key = f"{player_name}|{team_norm}|{sport}"
                    if image_key in existing_images:
                        csv_with_images += 1
                
                print(f"  CSV players with images: {csv_with_images}/{result['csv_players']}")
            
            await asyncio.sleep(0.5)  # Rate limiting

if __name__ == "__main__":
    asyncio.run(main()) 