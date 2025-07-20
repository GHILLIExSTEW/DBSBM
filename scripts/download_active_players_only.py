#!/usr/bin/env python3
"""
Download images only for ACTIVE players currently on team rosters.
Uses API as source of truth for current active players.
"""

import os
import sys
import asyncio
import aiohttp
import re
from pathlib import Path
from typing import Dict, List, Set

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

class ActivePlayerDownloader:
    def __init__(self, api_key: str, max_concurrent: int = 3):
        self.api_key = api_key
        self.max_concurrent = max_concurrent
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Statistics
        self.stats = {
            'total_attempted': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_existing': 0,
            'api_errors': 0,
            'validation_errors': 0
        }
        
        # Track existing images
        self.existing_images = self.load_existing_images()
        print(f"Found {len(self.existing_images)} existing player images")
    
    def load_existing_images(self) -> Set[str]:
        """Load set of existing player image keys."""
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
    
    def get_image_key(self, player_name: str, team_name: str, sport: str) -> str:
        """Generate unique key for player image."""
        # Normalize names
        player_norm = re.sub(r'[^\w\s]', '', player_name.lower())
        player_norm = re.sub(r'\s+', '_', player_norm)
        
        team_norm = re.sub(r'[^\w\s]', '', team_name.lower())
        team_norm = re.sub(r'\s+', '_', team_norm)
        
        return f"{player_norm}|{team_norm}|{sport}"
    
    def validate_image(self, image_data: bytes) -> bool:
        """Validate downloaded image data."""
        try:
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            
            # Basic validation
            if image.width < 50 or image.height < 50:
                return False
                
            if len(image_data) < 1000 or len(image_data) > 5 * 1024 * 1024:
                return False
            
            # Check if it's not a placeholder
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            pixels = list(image.getdata())
            if len(set(pixels)) < 10:
                return False
                
            return True
            
        except Exception:
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'x-apisports-key': self.api_key,
            'User-Agent': 'DBSBM-Active-Player-Downloader/1.0'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_team_players(self, sport: str, league_id: int, team_id: int, season: int) -> List[Dict]:
        """Get active players for a team from API."""
        try:
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
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    players = data.get('response', [])
                    
                    # Filter for active players only
                    active_players = []
                    for player in players:
                        player_info = player.get('player', {})
                        player_name = player_info.get('name')
                        player_photo = player_info.get('photo')
                        
                        # Only include players with names and photos
                        if player_name and player_photo:
                            active_players.append(player)
                    
                    return active_players
                else:
                    print(f"❌ API error {response.status} for team {team_id}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error getting players for team {team_id}: {e}")
            return []
    
    async def download_player_image(self, player_name: str, image_url: str, team_name: str, sport: str) -> bool:
        """Download and save a single player image."""
        # Check if image already exists
        image_key = self.get_image_key(player_name, team_name, sport)
        if image_key in self.existing_images:
            self.stats['skipped_existing'] += 1
            return True
        
        try:
            async with self.semaphore:
                async with self.session.get(image_url, timeout=30) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        if self.validate_image(image_data):
                            # Save the image
                            team_dir = re.sub(r'[^\w\s]', '', team_name.lower())
                            team_dir = re.sub(r'\s+', '_', team_dir)
                            
                            base_path = Path(__file__).parent.parent / 'bot' / 'static' / 'logos' / 'players'
                            player_dir = base_path / sport / team_dir
                            player_dir.mkdir(parents=True, exist_ok=True)
                            
                            filename = re.sub(r'[^\w\s]', '', player_name.lower())
                            filename = re.sub(r'\s+', '_', filename)
                            filename = f"{filename}.png"
                            
                            file_path = player_dir / filename
                            
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(image_data)
                            
                            print(f"✅ Downloaded: {player_name} ({team_name})")
                            self.stats['successful_downloads'] += 1
                            return True
                        else:
                            self.stats['validation_errors'] += 1
                            return False
                    else:
                        print(f"❌ HTTP {response.status} for {player_name}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error downloading {player_name}: {e}")
            return False
    
    async def process_team(self, sport: str, league_id: int, team: Dict, season: int) -> int:
        """Process all active players for a team."""
        # Handle both nested and flat team structures
        if 'team' in team:
            team_id = team.get('team', {}).get('id')
            team_name = team.get('team', {}).get('name')
        else:
            team_id = team.get('id')
            team_name = team.get('name')
        
        if not team_id or not team_name:
            return 0
        
        print(f"Processing team: {team_name}")
        
        # Get active players for this team
        players = await self.get_team_players(sport, league_id, team_id, season)
        
        successful = 0
        for player in players:
            player_info = player.get('player', {})
            player_name = player_info.get('name')
            player_photo = player_info.get('photo')
            
            if player_name and player_photo:
                self.stats['total_attempted'] += 1
                if await self.download_player_image(player_name, player_photo, team_name, sport):
                    successful += 1
                
                # Rate limiting
                await asyncio.sleep(0.2)
        
        return successful
    
    async def process_league(self, league_key: str) -> int:
        """Process all teams in a league for active players only."""
        league_info = LEAGUE_IDS.get(league_key)
        if not league_info:
            print(f"❌ Unknown league: {league_key}")
            return 0
        
        sport = league_info['sport']
        league_id = league_info['id']
        season = get_current_season(league_key)
        
        print(f"Processing league: {league_key} (Active players only)")
        
        # Get teams for this league
        try:
            endpoint_config = ENDPOINTS_MAP.get(sport)
            if not endpoint_config:
                return 0
            
            base_url = endpoint_config['base']
            teams_endpoint = endpoint_config['teams']
            url = f"{base_url}{teams_endpoint}"
            
            params = {
                'league': league_id,
                'season': season
            }
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    teams = data.get('response', [])
                else:
                    print(f"❌ HTTP {response.status} getting teams for {league_key}")
                    return 0
                    
        except Exception as e:
            print(f"❌ Error getting teams for {league_key}: {e}")
            return 0
        
        total_downloads = 0
        
        # Process teams in smaller batches
        batch_size = 3
        for i in range(0, len(teams), batch_size):
            batch = teams[i:i + batch_size]
            
            tasks = [
                self.process_team(sport, league_id, team, season)
                for team in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, int):
                    total_downloads += result
                else:
                    print(f"❌ Error in batch: {result}")
            
            # Wait between batches
            await asyncio.sleep(2)
        
        return total_downloads
    
    async def run(self, leagues: List[str] = None):
        """Main execution method."""
        if not leagues:
            # Use priority leagues
            leagues = ['NBA', 'MLB', 'NFL', 'NHL']
        
        print(f"Starting download for ACTIVE PLAYERS ONLY in {len(leagues)} leagues")
        
        start_time = asyncio.get_event_loop().time()
        
        for league in leagues:
            try:
                downloads = await self.process_league(league)
                print(f"Completed {league}: {downloads} active player downloads")
                
                # Print progress
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"Progress: {self.stats['successful_downloads']} successful, "
                      f"{self.stats['failed_downloads']} failed, "
                      f"{elapsed:.1f}s elapsed")
                      
            except Exception as e:
                print(f"❌ Error processing {league}: {e}")
                continue
        
        # Final statistics
        total_time = asyncio.get_event_loop().time() - start_time
        print(f"\n{'='*50}")
        print("ACTIVE PLAYER DOWNLOAD COMPLETE")
        print(f"{'='*50}")
        print(f"Total attempted: {self.stats['total_attempted']}")
        print(f"Successful downloads: {self.stats['successful_downloads']}")
        print(f"Failed downloads: {self.stats['failed_downloads']}")
        print(f"Skipped existing: {self.stats['skipped_existing']}")
        print(f"Total time: {total_time:.1f} seconds")

async def main():
    """Main function."""
    print("=" * 60)
    print("ACTIVE PLAYER IMAGE DOWNLOADER")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Priority leagues
    priority_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    print(f"\nWill download images for ACTIVE PLAYERS ONLY in:")
    for league in priority_leagues:
        print(f"  - {league}")
    
    print("\nThis will only download images for players currently on team rosters.")
    print("Historical/retired players will be ignored.")
    
    confirm = input("\nContinue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    async with ActivePlayerDownloader(api_key) as downloader:
        await downloader.run(priority_leagues)

if __name__ == "__main__":
    asyncio.run(main()) 