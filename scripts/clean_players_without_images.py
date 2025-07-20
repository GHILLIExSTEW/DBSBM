#!/usr/bin/env python3
"""
Script to clean the players_without_images.csv file by removing NCAA players.
NCAA players don't need individual images since they use the NCAA logo.
"""

import os
import csv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_players_without_images():
    """Remove NCAA players from the players_without_images.csv file"""
    csv_path = "reports/players_without_images.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Read the CSV file
    players = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        players = list(reader)
    
    logger.info(f"Processing {len(players)} players...")
    
    # Filter out NCAA players
    non_ncaa_players = []
    ncaa_count = 0
    
    for player in players:
        league = player.get('league', '')
        if league and 'NCAA' in league.upper():
            ncaa_count += 1
            logger.debug(f"Removing NCAA player: {player.get('name', '')} ({player.get('team', '')})")
        else:
            non_ncaa_players.append(player)
    
    logger.info(f"Removed {ncaa_count} NCAA players")
    logger.info(f"Remaining players: {len(non_ncaa_players)}")
    
    # Write cleaned CSV
    if non_ncaa_players:
        backup_path = f"{csv_path}.backup"
        os.rename(csv_path, backup_path)
        logger.info(f"Backed up original CSV to: {backup_path}")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=non_ncaa_players[0].keys())
            writer.writeheader()
            writer.writerows(non_ncaa_players)
        
        logger.info(f"Updated CSV file: {csv_path}")
    
    return len(players), len(non_ncaa_players), ncaa_count

def main():
    """Main function"""
    logger.info("Starting cleanup of players without images...")
    
    total, remaining, removed = clean_players_without_images()
    
    logger.info(f"Cleanup completed:")
    logger.info(f"Total players before: {total}")
    logger.info(f"Players after removing NCAA: {remaining}")
    logger.info(f"NCAA players removed: {removed}")

if __name__ == "__main__":
    main() 