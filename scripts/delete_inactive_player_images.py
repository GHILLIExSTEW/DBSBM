#!/usr/bin/env python3
"""
Delete player image files for inactive players.
Removes image files for retired/inactive players across all leagues.
"""

import os
import sys
import asyncio
import aiohttp
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

class InactiveImageCleaner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        
        # Statistics
        self.stats = {
            'total_images_found': 0,
            'active_images': 0,
            'deleted_images': 0,
            'leagues_processed': 0,
            'errors': 0
        }
        
        # Paths
        self.base_path = Path(__file__).parent.parent / 'bot' / 'static' / 'logos' / 'players'
        self.log_file = Path(__file__).parent / f'image_cleanup_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'x-apisports-key': self.api_key,
            'User-Agent': 'DBSBM-ImageCleaner/1.0'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def log_message(self, message: str):
        """Log message to file and print."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def scan_all_player_images(self) -> Dict[str, List[Path]]:
        """Scan all player image directories and return organized by sport."""
        images_by_sport = {}
        
        if not self.base_path.exists():
            self.log_message(f"❌ Player images directory not found: {self.base_path}")
            return images_by_sport
        
        # Scan each sport directory
        for sport_dir in self.base_path.iterdir():
            if sport_dir.is_dir():
                sport_name = sport_dir.name
                images_by_sport[sport_name] = []
                
                # Scan all image files in this sport
                for image_file in sport_dir.rglob('*.png'):
                    images_by_sport[sport_name].append(image_file)
                
                self.log_message(f"Found {len(images_by_sport[sport_name])} images in {sport_name}")
        
        self.stats['total_images_found'] = sum(len(images) for images in images_by_sport.values())
        return images_by_sport
    
    def extract_player_name_from_path(self, image_path: Path) -> str:
        """Extract player name from image file path."""
        # Remove extension and convert to lowercase
        player_name = image_path.stem.lower()
        
        # Handle different naming patterns
        # Remove common suffixes
        suffixes_to_remove = ['_player', '_headshot', '_photo']
        for suffix in suffixes_to_remove:
            if player_name.endswith(suffix):
                player_name = player_name[:-len(suffix)]
        
        return player_name
    
    async def get_active_players_for_league(self, league_key: str) -> Set[str]:
        """Get set of active player names for a league."""
        league_info = LEAGUE_IDS.get(league_key)
        if not league_info:
            self.log_message(f"❌ Unknown league: {league_key}")
            return set()
        
        sport = league_info['sport']
        league_id = league_info['id']
        
        # American Football API doesn't have 2025 data yet, use 2024
        if sport == 'american-football':
            season = 2024
        else:
            season = get_current_season(league_key)
        
        self.log_message(f"Getting active players for {league_key}...")
        
        active_players = set()
        
        # Handle NBA API separately (uses v2.nba.api-sports.io)
        if league_key == 'NBA':
            return await self.get_nba_players(season)
        
        # Handle Soccer API separately (uses v3.football.api-sports.io)
        if sport == 'football':
            return await self.get_soccer_players(league_key, season)
        
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
                    self.log_message(f"❌ HTTP {response.status} getting teams for {league_key}")
                    return set()
                    
        except Exception as e:
            self.log_message(f"❌ Error getting teams for {league_key}: {e}")
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
                
                # American Football has different API structure - no league parameter for players
                if sport == 'american-football':
                    players_params = {
                        'team': team_id,
                        'season': season
                    }
                else:
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
                        
                        self.log_message(f"  {team_name}: {len(players)} active players")
                        
                    else:
                        self.log_message(f"  ❌ Error getting players for {team_name}")
                        
            except Exception as e:
                self.log_message(f"  ❌ Error getting players for {team_name}: {e}")
                self.stats['errors'] += 1
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        self.log_message(f"  Total active players in {league_key}: {len(active_players)}")
        return active_players
    
    async def get_nba_players(self, season: int) -> Set[str]:
        """Get NBA players using the v2 NBA API."""
        active_players = set()
        
        # NBA API uses different endpoint
        base_url = "https://v2.nba.api-sports.io"
        
        # Get teams first
        teams_url = f"{base_url}/teams"
        try:
            async with self.session.get(teams_url, timeout=30) as response:
                if response.status == 200:
                    teams_data = await response.json()
                    teams = teams_data.get('response', [])
                    
                    self.log_message(f"  Found {len(teams)} NBA teams")
                    
                    # Get players for each team
                    for team in teams:
                        team_id = team.get('id')
                        team_name = team.get('name')
                        
                        if not team_id or not team_name:
                            continue
                        
                        # Get players for this team
                        players_url = f"{base_url}/players"
                        players_params = {
                            'season': season,
                            'team': team_id
                        }
                        
                        try:
                            async with self.session.get(players_url, params=players_params, timeout=30) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    players = data.get('response', [])
                                    
                                    for player in players:
                                        player_name = player.get('name')
                                        if player_name:
                                            active_players.add(player_name.lower())
                                    
                                    self.log_message(f"  {team_name}: {len(players)} active players")
                                    
                                else:
                                    self.log_message(f"  ❌ Error getting players for {team_name}")
                                    
                        except Exception as e:
                            self.log_message(f"  ❌ Error getting players for {team_name}: {e}")
                            self.stats['errors'] += 1
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                else:
                    self.log_message(f"❌ HTTP {response.status} getting NBA teams")
                    
        except Exception as e:
            self.log_message(f"❌ Error getting NBA teams: {e}")
        
        self.log_message(f"  Total active NBA players: {len(active_players)}")
        return active_players
    
    async def get_soccer_players(self, league_key: str, season: int) -> Set[str]:
        """Get Soccer players using the v3 Football API."""
        active_players = set()
        
        # Soccer API uses different endpoint and league IDs
        base_url = "https://v3.football.api-sports.io"
        
        # Map league keys to actual API league IDs
        league_id_mapping = {
            'PremierLeague': 39,  # English Premier League
            'LaLiga': 140,        # La Liga
            'Bundesliga': 78,     # Bundesliga
            'SerieA': 135,        # Serie A
            'Ligue1': 61,         # Ligue 1
            'ChampionsLeague': 2, # UEFA Champions League
            'EuropaLeague': 3,    # UEFA Europa League
        }
        
        league_id = league_id_mapping.get(league_key)
        if not league_id:
            self.log_message(f"❌ Unknown soccer league: {league_key}")
            return active_players
        
        # Get players directly for the league (no need to get teams first)
        players_url = f"{base_url}/players"
        players_params = {
            'league': league_id,
            'season': season
        }
        
        try:
            self.log_message(f"  Getting players for {league_key} (League ID: {league_id})")
            
            async with self.session.get(players_url, params=players_params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    players = data.get('response', [])
                    
                    for player in players:
                        player_info = player.get('player', {})
                        player_name = player_info.get('name')
                        
                        if player_name:
                            active_players.add(player_name.lower())
                    
                    self.log_message(f"  Total active players in {league_key}: {len(active_players)}")
                    
                else:
                    self.log_message(f"❌ HTTP {response.status} getting players for {league_key}")
                    
        except Exception as e:
            self.log_message(f"❌ Error getting players for {league_key}: {e}")
        
        return active_players
    
    def map_sport_to_leagues(self, sport_name: str) -> List[str]:
        """Map sport directory name to league keys."""
        sport_mapping = {
            'american_football': ['NFL', 'NCAA'],
            'australian_football': ['AFL'],
            'baseball': ['MLB', 'NPB', 'KBO', 'CPBL', 'LIDOM'],
            'basketball': ['NBA'],  # Skip WNBA and other basketball leagues
            'darts': ['PDC'],
            'golf': ['CHAMPIONS_TOUR', 'OLYMPIC_GOLF'],
            'ice_hockey': ['NHL', 'KHL'],
            'mma': ['UFC'],
            'motorsport': ['FORMULA1'],
            'rugby': ['SixNations', 'SuperRugby'],
            'soccer': ['PremierLeague', 'LaLiga', 'Bundesliga', 'SerieA', 'Ligue1', 'ChampionsLeague', 'EuropaLeague'],
            'tennis': ['ATP', 'WTA']
        }
        
        return sport_mapping.get(sport_name, [])
    
    def get_sports_without_player_data(self) -> Set[str]:
        """Get sports that don't have player data available in API-Sports."""
        return {
            'baseball',  # MLB players not available
            'ice_hockey', # NHL players not available
            'golf',      # Golf players may not be available
            'tennis',    # Tennis players may not be available
            'darts',     # Darts players may not be available
            'motorsport' # Motorsport drivers may not be available
        }
    
    async def cleanup_sport_images(self, sport_name: str, image_files: List[Path]) -> Dict[str, int]:
        """Clean up images for a specific sport."""
        self.log_message(f"\n{'='*50}")
        self.log_message(f"CLEANING SPORT: {sport_name}")
        self.log_message(f"{'='*50}")
        
        # Check if this sport has player data available
        sports_without_data = self.get_sports_without_player_data()
        if sport_name in sports_without_data:
            self.log_message(f"⚠️  {sport_name.upper()} player data not available in API-Sports")
            self.log_message(f"   Keeping all {len(image_files)} images (cannot verify active status)")
            self.stats['active_images'] += len(image_files)
            return {'active': len(image_files), 'deleted': 0}
        
        # Get leagues for this sport
        leagues = self.map_sport_to_leagues(sport_name)
        if not leagues:
            self.log_message(f"⚠️  No leagues mapped for sport: {sport_name}")
            self.log_message(f"   Keeping all {len(image_files)} images (no league mapping)")
            self.stats['active_images'] += len(image_files)
            return {'active': len(image_files), 'deleted': 0}
        
        # Get all active players for this sport's leagues
        all_active_players = set()
        for league in leagues:
            active_players = await self.get_active_players_for_league(league)
            all_active_players.update(active_players)
            self.stats['leagues_processed'] += 1
        
        self.log_message(f"Total active players across {len(leagues)} leagues: {len(all_active_players)}")
        
        # Process each image file
        active_count = 0
        deleted_count = 0
        
        for image_file in image_files:
            player_name = self.extract_player_name_from_path(image_file)
            
            if player_name in all_active_players:
                active_count += 1
                self.stats['active_images'] += 1
            else:
                # Player is inactive, delete the image
                try:
                    image_file.unlink()
                    deleted_count += 1
                    self.stats['deleted_images'] += 1
                    self.log_message(f"🗑️  Deleted: {image_file.name} ({player_name})")
                except Exception as e:
                    self.log_message(f"❌ Error deleting {image_file.name}: {e}")
                    self.stats['errors'] += 1
        
        self.log_message(f"Sport {sport_name}: {active_count} active, {deleted_count} deleted")
        return {'active': active_count, 'deleted': deleted_count}
    
    async def run(self):
        """Main cleanup process."""
        self.log_message("=" * 60)
        self.log_message("INACTIVE PLAYER IMAGE CLEANUP")
        self.log_message("=" * 60)
        
        # Scan all player images
        self.log_message("\n1. Scanning player images...")
        images_by_sport = self.scan_all_player_images()
        
        if not images_by_sport:
            self.log_message("❌ No player images found!")
            return
        
        # Process each sport
        self.log_message("\n2. Processing each sport...")
        for sport_name, image_files in images_by_sport.items():
            if image_files:  # Only process if there are images
                await self.cleanup_sport_images(sport_name, image_files)
        
        # Print final statistics
        self.log_message(f"\n{'='*60}")
        self.log_message("CLEANUP COMPLETE")
        self.log_message(f"{'='*60}")
        self.log_message(f"Total images found: {self.stats['total_images_found']}")
        self.log_message(f"Active images kept: {self.stats['active_images']}")
        self.log_message(f"Images deleted: {self.stats['deleted_images']}")
        self.log_message(f"Leagues processed: {self.stats['leagues_processed']}")
        self.log_message(f"Errors encountered: {self.stats['errors']}")
        
        if self.stats['total_images_found'] > 0:
            reduction = (self.stats['deleted_images'] / self.stats['total_images_found']) * 100
            self.log_message(f"Reduction: {reduction:.1f}%")
        
        self.log_message(f"\nLog file: {self.log_file}")

async def main():
    """Main function."""
    print("=" * 60)
    print("INACTIVE PLAYER IMAGE CLEANUP")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    print("\nThis will delete image files for inactive players across ALL leagues.")
    print("⚠️  WARNING: This will permanently delete image files!")
    print("A detailed log will be created.")
    
    confirm = input("\nContinue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    async with InactiveImageCleaner(api_key) as cleaner:
        await cleaner.run()

if __name__ == "__main__":
    asyncio.run(main()) 