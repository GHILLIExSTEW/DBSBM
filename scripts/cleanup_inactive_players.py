#!/usr/bin/env python3
"""
Clean up inactive players from the database.
Removes retired/inactive players and keeps only current active players.
"""

import os
import sys
import asyncio
import aiohttp
import csv
import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

class InactivePlayerCleaner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        
        # Statistics
        self.stats = {
            'original_players': 0,
            'active_players': 0,
            'removed_players': 0,
            'leagues_processed': 0
        }
        
        # Load current CSV
        self.csv_file = Path(__file__).parent.parent / 'bot' / 'data' / 'players.csv'
        self.backup_file = self.csv_file.parent / f'players_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'x-apisports-key': self.api_key,
            'User-Agent': 'DBSBM-Cleaner/1.0'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def load_current_csv(self) -> List[Dict]:
        """Load current players from CSV."""
        if not self.csv_file.exists():
            print("❌ players.csv not found!")
            return []
        
        players = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    players.append(row)
            
            self.stats['original_players'] = len(players)
            print(f"✅ Loaded {len(players)} players from CSV")
            return players
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def create_backup(self, players: List[Dict]):
        """Create backup of current CSV."""
        try:
            with open(self.backup_file, 'w', encoding='utf-8', newline='') as f:
                if players:
                    writer = csv.DictWriter(f, fieldnames=players[0].keys())
                    writer.writeheader()
                    writer.writerows(players)
            
            print(f"✅ Backup created: {self.backup_file}")
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
    
    async def get_active_players_for_league(self, league_key: str) -> Set[str]:
        """Get set of active player names for a league."""
        league_info = LEAGUE_IDS.get(league_key)
        if not league_info:
            print(f"❌ Unknown league: {league_key}")
            return set()
        
        sport = league_info['sport']
        league_id = league_info['id']
        season = get_current_season(league_key)
        
        print(f"Getting active players for {league_key}...")
        
        active_players = set()
        
        # Get teams for this league
        try:
            endpoint_config = ENDPOINTS_MAP.get(sport)
            if not endpoint_config:
                return set()
            
            base_url = endpoint_config['base']
            teams_endpoint = endpoint_config['teams']
            teams_url = f"{base_url}{teams_endpoint}"
            
            teams_params = {
                'league': league_id,
                'season': season
            }
            
            async with self.session.get(teams_url, params=teams_params, timeout=30) as response:
                if response.status == 200:
                    teams_data = await response.json()
                    teams = teams_data.get('response', [])
                else:
                    print(f"❌ HTTP {response.status} getting teams for {league_key}")
                    return set()
                    
        except Exception as e:
            print(f"❌ Error getting teams for {league_key}: {e}")
            return set()
        
        # Get players for each team
        for team in teams:
            # Handle both nested and flat team structures
            if 'team' in team:
                team_id = team.get('team', {}).get('id')
                team_name = team.get('team', {}).get('name')
            else:
                team_id = team.get('id')
                team_name = team.get('name')
            
            if not team_id or not team_name:
                continue
            
            # Get players for this team
            try:
                players_endpoint = endpoint_config['players']
                players_url = f"{base_url}{players_endpoint}"
                
                players_params = {
                    'league': league_id,
                    'team': team_id,
                    'season': season
                }
                
                async with self.session.get(players_url, params=players_params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        players = data.get('response', [])
                        
                        for player in players:
                            player_info = player.get('player', {})
                            player_name = player_info.get('name')
                            
                            if player_name:
                                active_players.add(player_name.lower())
                        
                        print(f"  {team_name}: {len(players)} active players")
                        
                    else:
                        print(f"  ❌ Error getting players for {team_name}")
                        
            except Exception as e:
                print(f"  ❌ Error getting players for {team_name}: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        print(f"  Total active players in {league_key}: {len(active_players)}")
        return active_players
    
    def filter_active_players(self, all_players: List[Dict], active_players_by_league: Dict[str, Set[str]]) -> List[Dict]:
        """Filter CSV players to keep only active ones."""
        active_players = []
        removed_count = 0
        
        for player in all_players:
            player_name = player.get('strPlayer', '').lower()
            league = player.get('strLeague', '')
            
            # Check if player is active in their league
            if league in active_players_by_league:
                if player_name in active_players_by_league[league]:
                    active_players.append(player)
                else:
                    removed_count += 1
                    print(f"Removing inactive: {player.get('strPlayer')} ({player.get('strTeam')})")
            else:
                # League not in our active list, keep the player
                active_players.append(player)
        
        self.stats['active_players'] = len(active_players)
        self.stats['removed_players'] = removed_count
        
        return active_players
    
    def save_cleaned_csv(self, active_players: List[Dict]):
        """Save cleaned CSV with only active players."""
        try:
            with open(self.csv_file, 'w', encoding='utf-8', newline='') as f:
                if active_players:
                    writer = csv.DictWriter(f, fieldnames=active_players[0].keys())
                    writer.writeheader()
                    writer.writerows(active_players)
            
            print(f"✅ Saved cleaned CSV with {len(active_players)} active players")
            
        except Exception as e:
            print(f"❌ Error saving cleaned CSV: {e}")
    
    async def cleanup_league(self, league_key: str) -> Set[str]:
        """Clean up a specific league."""
        print(f"\n{'='*50}")
        print(f"CLEANING LEAGUE: {league_key}")
        print(f"{'='*50}")
        
        active_players = await self.get_active_players_for_league(league_key)
        self.stats['leagues_processed'] += 1
        
        return active_players
    
    async def run(self, leagues: List[str] = None):
        """Main cleanup process."""
        if not leagues:
            # Use priority leagues
            leagues = ['NBA', 'MLB', 'NFL', 'NHL']
        
        print("=" * 60)
        print("INACTIVE PLAYER CLEANUP")
        print("=" * 60)
        
        # Load current CSV
        print("\n1. Loading current CSV...")
        all_players = self.load_current_csv()
        
        if not all_players:
            print("❌ No players to process!")
            return
        
        # Create backup
        print("\n2. Creating backup...")
        self.create_backup(all_players)
        
        # Get active players for each league
        print("\n3. Getting active players from API...")
        active_players_by_league = {}
        
        for league in leagues:
            active_players = await self.cleanup_league(league)
            active_players_by_league[league] = active_players
        
        # Filter players
        print("\n4. Filtering players...")
        active_players = self.filter_active_players(all_players, active_players_by_league)
        
        # Save cleaned CSV
        print("\n5. Saving cleaned CSV...")
        self.save_cleaned_csv(active_players)
        
        # Print statistics
        print(f"\n{'='*60}")
        print("CLEANUP COMPLETE")
        print(f"{'='*60}")
        print(f"Original players: {self.stats['original_players']}")
        print(f"Active players: {self.stats['active_players']}")
        print(f"Removed players: {self.stats['removed_players']}")
        print(f"Leagues processed: {self.stats['leagues_processed']}")
        print(f"Reduction: {((self.stats['removed_players'] / self.stats['original_players']) * 100):.1f}%")
        
        if self.stats['removed_players'] > 0:
            print(f"\nBackup saved to: {self.backup_file}")
            print("You can restore from backup if needed.")

async def main():
    """Main function."""
    print("=" * 60)
    print("INACTIVE PLAYER CLEANUP")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Priority leagues
    priority_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    print(f"\nWill clean up inactive players for:")
    for league in priority_leagues:
        print(f"  - {league}")
    
    print("\n⚠️  WARNING: This will permanently remove inactive players from your database!")
    print("A backup will be created before any changes.")
    
    confirm = input("\nContinue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    async with InactivePlayerCleaner(api_key) as cleaner:
        await cleaner.run(priority_leagues)

if __name__ == "__main__":
    asyncio.run(main()) 