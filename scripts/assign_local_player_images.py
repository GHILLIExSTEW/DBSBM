#!/usr/bin/env python3
"""
Script to assign local player images to players in the CSV file.
This script will:
1. Read the players.csv file
2. For each player, check if there's a corresponding local image
3. Update the CSV to point to local image paths instead of remote URLs
4. Handle different naming conventions and variations
"""

import os
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlayerImageAssigner:
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
        
    def normalize_name(self, name: str) -> str:
        """Normalize player name for file matching"""
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
        """Generate multiple variations of a player name for matching"""
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
            # Common initial mappings - be more specific
            initial_mappings = {
                'c': 'christian',  # Fixed: was incorrectly 'casemiro'
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
    
    def find_player_image(self, player_name: str, team_name: str, sport: str, league: str) -> Optional[str]:
        """Find local player image file"""
        if not player_name or not team_name or not sport:
            return None
            
        # Map sport to folder name
        sport_folder = self.sport_mapping.get(sport, sport.lower())
        if not sport_folder:
            return None
            
        # Normalize team name for folder matching
        team_folder = self.normalize_team_name(team_name)
        if not team_folder:
            return None
            
        # Build the team path
        team_path = Path(self.logos_base_path) / sport_folder / team_folder
        if not team_path.exists():
            logger.debug(f"Team path does not exist: {team_path}")
            return None
            
        # Try multiple name normalization strategies
        name_variations = self.generate_name_variations(player_name)
        
        # First, try exact matches
        for normalized_player in name_variations:
            if not normalized_player:
                continue
                
            # Direct match
            direct_file = team_path / f"{normalized_player}.png"
            if direct_file.exists():
                return str(direct_file)
            
            # Try variations
            variations = [
                f"{normalized_player}.jpg",
                f"{normalized_player}.jpeg",
                f"{normalized_player}_1.png",
                f"{normalized_player}_2.png",
            ]
            
            for variation in variations:
                var_file = team_path / variation
                if var_file.exists():
                    return str(var_file)
        
        # If no exact match, try partial matches but be more strict
        for file_path in team_path.glob("*.png"):
            file_name = file_path.stem.lower()
            
            # Try matching with each name variation
            for normalized_player in name_variations:
                if normalized_player:
                    # More strict matching - check if the normalized player name is contained in the file name
                    # or if the file name is contained in the normalized player name
                    if (normalized_player in file_name or file_name in normalized_player):
                        # Additional check: make sure it's not a false match
                        # For example, "c_eriksen" should match "christian_eriksen" but not "casemiro"
                        if self.is_valid_match(normalized_player, file_name):
                            return str(file_path)
        
        return None
    
    def is_valid_match(self, normalized_player: str, file_name: str) -> bool:
        """Check if a match is valid (not a false positive)"""
        # Split both names into parts
        player_parts = normalized_player.split('_')
        file_parts = file_name.split('_')
        
        # Check if there's significant overlap
        common_parts = set(player_parts) & set(file_parts)
        
        # For a valid match, we need at least one common part and the parts should be substantial
        if len(common_parts) == 0:
            return False
            
        # Check if the common parts are substantial (not just single letters)
        substantial_common_parts = [part for part in common_parts if len(part) > 1]
        
        # If we have substantial common parts, it's likely a valid match
        if substantial_common_parts:
            return True
            
        # If no substantial common parts, check if one name is contained in the other
        # but only if the contained part is substantial
        if len(normalized_player) > 3 and normalized_player in file_name:
            return True
        if len(file_name) > 3 and file_name in normalized_player:
            return True
            
        return False
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for folder matching"""
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
    
    def process_csv(self) -> Tuple[int, int, int]:
        """Process the CSV file and assign local images"""
        if not os.path.exists(self.csv_path):
            logger.error(f"CSV file not found: {self.csv_path}")
            return 0, 0, 0
            
        # Read the CSV file
        players = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        logger.info(f"Processing {len(players)} players...")
        
        total_players = len(players)
        found_images = 0
        updated_players = 0
        
        for i, player in enumerate(players):
            if i % 100 == 0:
                logger.info(f"Processing player {i+1}/{total_players}")
                
            player_name = player.get('strPlayer', '')
            team_name = player.get('strTeam', '')
            sport = player.get('strSport', '')
            league = player.get('strLeague', '')
            current_image = player.get('strCutouts', '')
            
            # Skip if already a local path
            if current_image and not current_image.startswith('http'):
                continue
                
            # Find local image
            local_image = self.find_player_image(player_name, team_name, sport, league)
            
            if local_image:
                # Convert to relative path for the bot
                relative_path = os.path.relpath(local_image, 'bot')
                player['strCutouts'] = relative_path
                found_images += 1
                logger.debug(f"Found image for {player_name}: {relative_path}")
            else:
                # Keep the original remote URL if no local image found
                logger.debug(f"No local image found for {player_name} ({team_name}, {sport})")
        
        # Write updated CSV
        if players:
            backup_path = f"{self.csv_path}.backup.{int(time.time())}"
            os.rename(self.csv_path, backup_path)
            logger.info(f"Backed up original CSV to: {backup_path}")
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=players[0].keys())
                writer.writeheader()
                writer.writerows(players)
            
            updated_players = len(players)
            logger.info(f"Updated CSV file: {self.csv_path}")
        
        return total_players, found_images, updated_players

def main():
    """Main function"""
    import time
    
    # Paths
    csv_path = "bot/data/players.csv"
    logos_base_path = "bot/static/logos/players"
    
    # Check if files exist
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
        
    if not os.path.exists(logos_base_path):
        logger.error(f"Logos directory not found: {logos_base_path}")
        return
    
    # Create assigner and process
    assigner = PlayerImageAssigner(csv_path, logos_base_path)
    
    logger.info("Starting player image assignment...")
    start_time = time.time()
    
    total, found, updated = assigner.process_csv()
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Processing completed in {duration:.2f} seconds")
    logger.info(f"Total players: {total}")
    logger.info(f"Local images found: {found}")
    logger.info(f"Players updated: {updated}")
    logger.info(f"Success rate: {(found/total*100):.1f}%" if total > 0 else "No players processed")

if __name__ == "__main__":
    main() 