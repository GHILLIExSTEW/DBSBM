#!/usr/bin/env python3
"""
Script to download missing player images and save them according to the existing logo structure.
This script will:
1. Read the players_without_images.csv file
2. Download images from the API URLs
3. Save them with proper naming according to the existing structure
4. Follow the established folder and naming conventions
"""

import os
import csv
import requests
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlayerImageDownloader:
    def __init__(self, csv_path: str, logos_base_path: str):
        self.csv_path = csv_path
        self.logos_base_path = logos_base_path
        self.sport_mapping = {
            'Football': 'soccer',
            'Basketball': 'basketball', 
            'Baseball': 'baseball',
            'Ice Hockey': 'ice_hockey',
            'American Football': 'american_football',
            'Australian Football': 'australian_football',
            'MMA': 'mma',
            'Darts': 'darts',
            'Golf': 'golf',
            'Tennis': 'tennis',
            'Motorsport': 'motorsport'
        }
        
        # Statistics tracking
        self.stats = {
            'total_players': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def normalize_name(self, name: str) -> str:
        """Normalize player name for file naming"""
        if not name:
            return ""
        
        # Remove special characters and normalize
        name = re.sub(r'[^\w\s]', '', name.lower())
        name = re.sub(r'\s+', '_', name.strip())
        
        # Handle common variations
        name = name.replace('jr', 'junior')
        name = name.replace('sr', 'senior')
        
        return name
    
    def generate_name_variations(self, player_name: str) -> List[str]:
        """Generate multiple variations of a player name for file naming"""
        if not player_name:
            return []
            
        variations = []
        
        # Handle special characters first (like "Lindelöf")
        processed_name = player_name
        
        # Handle names with "ö" (like "Lindelöf")
        if 'ö' in processed_name.lower():
            processed_name = processed_name.lower().replace('ö', 'o')
        
        # Handle names with special characters (like "Reguilón")
        if 'ó' in processed_name.lower():
            processed_name = processed_name.lower().replace('ó', 'o')
        
        # Original name normalization
        original = self.normalize_name(processed_name)
        if original:
            variations.append(original)
        
        # Handle initials (e.g., "C. Eriksen" -> "christian_eriksen")
        if '.' in processed_name:
            # Common initial mappings
            initial_mappings = {
                'c': 'christian',
                'r': 'raphael',
                'v': 'victor',
                'm': 'mason',
                'l': 'luke',
                'h': 'harry',
                'd': 'diogo',
                'b': 'bruno',
                'a': 'alejandro',
                'j': 'joshua',
                'k': 'kobbie',
                'n': 'noussair',
                'm': 'matthijs',
                'm': 'manuel',
                'l': 'leny',
                'j': 'jonny',
                'a': 'amad',
                'a': 'ayden',
                'a': 'andré',
                'a': 'altay',
            }
            
            # Split by dots and spaces
            parts = re.split(r'[.\s]+', processed_name.lower())
            if len(parts) >= 2:
                first_part = parts[0].strip()
                rest_parts = parts[1:]
                
                # Try with expanded initial
                if first_part in initial_mappings:
                    expanded_name = f"{initial_mappings[first_part]}_{'_'.join(rest_parts)}"
                    variations.append(expanded_name)
                
                # Try with just the initial
                initial_name = f"{first_part}_{'_'.join(rest_parts)}"
                variations.append(initial_name)
        
        # Handle special characters and accents
        # Remove accents and special characters
        clean_name = re.sub(r'[^\w\s]', '', processed_name.lower())
        clean_name = re.sub(r'\s+', '_', clean_name.strip())
        if clean_name and clean_name not in variations:
            variations.append(clean_name)
        
        return variations
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for folder naming"""
        if not team_name:
            return ""
            
        # Remove special characters and normalize
        team = re.sub(r'[^\w\s]', '', team_name.lower())
        team = re.sub(r'\s+', '_', team.strip())
        
        # Handle common team name variations
        team_mappings = {
            'manchester_united': 'manchester_united',
            'manchester_city': 'manchester_city',
            'arsenal': 'arsenal',
            'chelsea': 'chelsea',
            'liverpool': 'liverpool',
            'tottenham': 'tottenham',
            'newcastle': 'newcastle',
            'west_ham': 'west_ham',
            'crystal_palace': 'crystal_palace',
            'brighton': 'brighton',
            'aston_villa': 'aston_villa',
            'fulham': 'fulham',
            'brentford': 'brentford',
            'wolves': 'wolves',
            'nottingham_forest': 'nottingham_forest',
            'everton': 'everton',
            'leeds': 'leeds',
            'leicester': 'leicester',
            'southampton': 'southampton',
            'bournemouth': 'bournemouth',
            'burnley': 'burnley',
            'sheffield_united': 'sheffield_united',
            'luton': 'luton',
            'ipswich': 'ipswich',
        }
        
        return team_mappings.get(team, team)
    
    def download_image(self, url: str, file_path: Path) -> bool:
        """Download image from URL and save to file path"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not return an image: {url}")
                return False
            
            # Save the image
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            return False
    
    def process_players(self, max_downloads: int = 100) -> dict:
        """Process players and download missing images"""
        if not os.path.exists(self.csv_path):
            logger.error(f"CSV file not found: {self.csv_path}")
            return self.stats
            
        # Read the CSV file
        players = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        logger.info(f"Processing {len(players)} players (max {max_downloads} downloads)...")
        
        self.stats['total_players'] = len(players)
        
        for i, player in enumerate(players):
            # Check if we've reached the maximum downloads limit
            if max_downloads is not None and i >= max_downloads:
                logger.info(f"Reached maximum downloads limit ({max_downloads})")
                break
                
            # Log progress
            if i % 10 == 0:
                total_to_process = min(len(players), max_downloads) if max_downloads is not None else len(players)
                logger.info(f"Processing player {i+1}/{total_to_process}")
            
            player_name = player.get('name', '')
            team_name = player.get('team', '')
            sport = player.get('sport', '')
            league = player.get('league', '')
            image_url = player.get('current_image', '')
            
            # Skip if no image URL
            if not image_url or not image_url.startswith('http'):
                self.stats['skipped'] += 1
                continue
            
            # Skip NCAA players (they already have the NCAA logo)
            if league and 'NCAA' in league.upper():
                logger.debug(f"Skipping NCAA player: {player_name} ({team_name})")
                self.stats['skipped'] += 1
                continue
            
            # Map sport to folder name
            sport_folder = self.sport_mapping.get(sport, sport.lower())
            if not sport_folder:
                self.stats['skipped'] += 1
                continue
            
            # Normalize team name for folder matching
            team_folder = self.normalize_team_name(team_name)
            if not team_folder:
                self.stats['skipped'] += 1
                continue
            
            # Build the team path
            team_path = Path(self.logos_base_path) / sport_folder / team_folder
            
            # Create directory if it doesn't exist
            team_path.mkdir(parents=True, exist_ok=True)
            
            # Generate name variations for file naming
            name_variations = self.generate_name_variations(player_name)
            
            # Try to save with each name variation
            success = False
            for normalized_name in name_variations:
                if not normalized_name:
                    continue
                
                file_path = team_path / f"{normalized_name}.png"
                
                # Skip if file already exists
                if file_path.exists():
                    logger.debug(f"File already exists: {file_path}")
                    self.stats['skipped'] += 1
                    success = True
                    break
                
                # Download the image
                if self.download_image(image_url, file_path):
                    logger.info(f"Downloaded: {player_name} -> {file_path}")
                    self.stats['downloaded'] += 1
                    success = True
                    break
                else:
                    # Try with .jpg extension
                    file_path_jpg = team_path / f"{normalized_name}.jpg"
                    if self.download_image(image_url, file_path_jpg):
                        logger.info(f"Downloaded: {player_name} -> {file_path_jpg}")
                        self.stats['downloaded'] += 1
                        success = True
                        break
            
            if not success:
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'name': player_name,
                    'team': team_name,
                    'sport': sport,
                    'league': league,
                    'url': image_url
                })
            
            # Add a small delay to be respectful to the server
            time.sleep(0.1)
        
        return self.stats
    
    def generate_report(self, output_dir: str = "reports"):
        """Generate a report of the download process"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report
        summary_path = os.path.join(output_dir, "player_image_download_summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Player Image Download Summary\n\n")
            f.write(f"**Total Players Processed:** {self.stats['total_players']}\n")
            f.write(f"**Images Downloaded:** {self.stats['downloaded']}\n")
            f.write(f"**Downloads Failed:** {self.stats['failed']}\n")
            f.write(f"**Skipped (already exists):** {self.stats['skipped']}\n")
            f.write(f"**Success Rate:** {(self.stats['downloaded']/(self.stats['downloaded']+self.stats['failed'])*100):.1f}%\n\n" if (self.stats['downloaded']+self.stats['failed']) > 0 else "**Success Rate:** N/A (no downloads attempted)\n\n")
            
            if self.stats['errors']:
                f.write("## Failed Downloads (Sample - First 20)\n")
                for i, error in enumerate(self.stats['errors'][:20]):
                    f.write(f"### {i+1}. {error['name']} ({error['team']})\n")
                    f.write(f"- Sport: {error['sport']}\n")
                    f.write(f"- League: {error['league']}\n")
                    f.write(f"- URL: {error['url']}\n\n")
                
                if len(self.stats['errors']) > 20:
                    f.write(f"... and {len(self.stats['errors']) - 20} more failed downloads\n")
        
        # Failed downloads report
        failed_path = os.path.join(output_dir, "failed_downloads.csv")
        with open(failed_path, 'w', newline='', encoding='utf-8') as f:
            if self.stats['errors']:
                writer = csv.DictWriter(f, fieldnames=['name', 'team', 'sport', 'league', 'url'])
                writer.writeheader()
                writer.writerows(self.stats['errors'])
        
        logger.info(f"Reports generated in {output_dir}/")
        logger.info(f"- Summary: {summary_path}")
        logger.info(f"- Failed downloads: {failed_path}")

def main():
    """Main function"""
    # Paths
    csv_path = "reports/players_without_images.csv"
    logos_base_path = "bot/static/logos/players"
    
    # Check if files exist
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
        
    if not os.path.exists(logos_base_path):
        logger.error(f"Logos directory not found: {logos_base_path}")
        return
    
    # Create downloader and process
    downloader = PlayerImageDownloader(csv_path, logos_base_path)
    
    logger.info("Starting player image download...")
    start_time = time.time()
    
    # Process all players
    stats = downloader.process_players(max_downloads=None)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Generate report
    downloader.generate_report()
    
    # Print summary
    logger.info(f"Processing completed in {duration:.2f} seconds")
    logger.info(f"Total players processed: {stats['total_players']}")
    logger.info(f"Images downloaded: {stats['downloaded']}")
    logger.info(f"Downloads failed: {stats['failed']}")
    logger.info(f"Skipped (already exists): {stats['skipped']}")
    logger.info(f"Success rate: {(stats['downloaded']/(stats['downloaded']+stats['failed'])*100):.1f}%" if (stats['downloaded']+stats['failed']) > 0 else "No downloads attempted")

if __name__ == "__main__":
    main() 