#!/usr/bin/env python3
"""
Download missing images for players listed in CSV file.
"""

import os
import sys
import asyncio
import aiohttp
import csv
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

class CSVImageDownloader:
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
        
        # Load CSV data
        self.csv_players = self.load_csv_players()
        self.missing_players = self.find_missing_players()
        
        print(f"Found {len(self.missing_players)} players missing images")
    
    def load_csv_players(self) -> List[Dict]:
        """Load players from CSV."""
        players_file = Path(__file__).parent.parent / 'bot' / 'data' / 'players.csv'
        
        players = []
        try:
            with open(players_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    players.append(row)
            
            print(f"✅ Loaded {len(players)} players from CSV")
            return players
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def check_image_exists(self, image_path: str) -> bool:
        """Check if a local image file exists."""
        if not image_path or image_path == '':
            return False
        
        base_path = Path(__file__).parent.parent / 'bot'
        full_path = base_path / image_path
        
        return full_path.exists()
    
    def find_missing_players(self) -> List[Dict]:
        """Find players missing images."""
        missing = []
        
        for player in self.csv_players:
            image_path = player.get('strCutouts', '')
            if not self.check_image_exists(image_path):
                missing.append(player)
        
        return missing
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'x-apisports-key': self.api_key,
            'User-Agent': 'DBSBM-CSV-Downloader/1.0'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
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
    
    async def search_player_image(self, player_name: str, team_name: str, league: str) -> str:
        """Search for player image URL using API."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            return None
        
        sport = league_info['sport']
        league_id = league_info['id']
        season = get_current_season(league)
        
        # Search for player in API
        endpoint_config = ENDPOINTS_MAP.get(sport)
        if not endpoint_config:
            return None
        
        base_url = endpoint_config['base']
        players_endpoint = endpoint_config['players']
        url = f"{base_url}{players_endpoint}"
        
        params = {
            'league': league_id,
            'season': season,
            'search': player_name.split()[0]  # Search by first name
        }
        
        try:
            async with self.semaphore:
                async with self.session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        players = data.get('response', [])
                        
                        # Find best match
                        for player in players:
                            api_name = player.get('player', {}).get('name', '').lower()
                            csv_name = player_name.lower()
                            
                            # Simple name matching
                            if (player_name.split()[0].lower() in api_name or 
                                api_name.split()[0].lower() in csv_name):
                                photo_url = player.get('player', {}).get('photo')
                                if photo_url:
                                    return photo_url
                        
                        return None
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error searching for {player_name}: {e}")
            return None
    
    async def download_and_save_image(self, player: Dict) -> bool:
        """Download and save image for a player."""
        player_name = player.get('strPlayer', '')
        team_name = player.get('strTeam', '')
        league = player.get('strLeague', '')
        sport = player.get('strSport', '')
        
        if not all([player_name, team_name, league, sport]):
            return False
        
        # Search for image URL
        image_url = await self.search_player_image(player_name, team_name, league)
        if not image_url:
            return False
        
        # Download image
        try:
            async with self.semaphore:
                async with self.session.get(image_url, timeout=30) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        if self.validate_image(image_data):
                            # Save image
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
                        return False
                        
        except Exception as e:
            print(f"❌ Error downloading {player_name}: {e}")
            return False
    
    async def process_league(self, league: str) -> int:
        """Process missing players for a specific league."""
        league_players = [p for p in self.missing_players if p.get('strLeague') == league]
        
        if not league_players:
            return 0
        
        print(f"\nProcessing {league}: {len(league_players)} missing players")
        
        successful = 0
        for i, player in enumerate(league_players):
            self.stats['total_attempted'] += 1
            
            if await self.download_and_save_image(player):
                successful += 1
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(league_players)}")
            
            # Rate limiting
            await asyncio.sleep(0.2)
        
        return successful
    
    async def run(self, leagues: List[str] = None):
        """Main execution method."""
        if not leagues:
            # Get unique leagues from missing players
            leagues = list(set(p.get('strLeague') for p in self.missing_players if p.get('strLeague')))
        
        print(f"Starting download for {len(leagues)} leagues")
        print(f"Total missing players: {len(self.missing_players)}")
        
        start_time = asyncio.get_event_loop().time()
        
        for league in leagues:
            try:
                downloads = await self.process_league(league)
                print(f"Completed {league}: {downloads} downloads")
                
            except Exception as e:
                print(f"Error processing {league}: {e}")
                continue
        
        # Final statistics
        total_time = asyncio.get_event_loop().time() - start_time
        print(f"\n{'='*50}")
        print("DOWNLOAD COMPLETE")
        print(f"{'='*50}")
        print(f"Total attempted: {self.stats['total_attempted']}")
        print(f"Successful downloads: {self.stats['successful_downloads']}")
        print(f"Failed downloads: {self.stats['failed_downloads']}")
        print(f"Total time: {total_time:.1f} seconds")

async def main():
    """Main function."""
    print("=" * 60)
    print("CSV MISSING IMAGES DOWNLOADER")
    print("=" * 60)
    
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Priority leagues
    priority_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    print(f"\nWill download missing images for priority leagues:")
    for league in priority_leagues:
        print(f"  - {league}")
    
    confirm = input("\nContinue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    async with CSVImageDownloader(api_key) as downloader:
        await downloader.run(priority_leagues)

if __name__ == "__main__":
    asyncio.run(main()) 