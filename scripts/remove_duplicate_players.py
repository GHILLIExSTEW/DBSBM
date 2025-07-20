#!/usr/bin/env python3
"""
Script to remove duplicate players from the CSV file.
This script will:
1. Read the players.csv file
2. Identify duplicate players (same name and team)
3. Keep only one record per unique player
4. Update the CSV file with deduplicated data
"""

import os
import csv
import time
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlayerDeduplicator:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        
        # Statistics tracking
        self.stats = {
            'total_players': 0,
            'unique_players': 0,
            'duplicates_removed': 0,
            'duplicate_groups': 0,
            'duplicate_details': []
        }
    
    def process_csv(self) -> dict:
        """Process the CSV file and remove duplicates"""
        if not os.path.exists(self.csv_path):
            logger.error(f"CSV file not found: {self.csv_path}")
            return self.stats
            
        # Read the CSV file
        players = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            players = list(reader)
        
        logger.info(f"Processing {len(players)} players...")
        
        self.stats['total_players'] = len(players)
        
        # Group players by name and team
        player_groups = defaultdict(list)
        for i, player in enumerate(players):
            player_name = player.get('strPlayer', '').strip()
            team_name = player.get('strTeam', '').strip()
            
            # Create a unique key for each player-team combination
            key = f"{player_name}_{team_name}"
            player_groups[key].append((i, player))
        
        # Process each group and keep only one player per group
        unique_players = []
        duplicate_count = 0
        
        for key, group in player_groups.items():
            if len(group) == 1:
                # No duplicates, keep the player
                unique_players.append(group[0][1])
            else:
                # Duplicates found, keep only the first one
                self.stats['duplicate_groups'] += 1
                self.stats['duplicates_removed'] += len(group) - 1
                
                # Keep the first player in the group
                unique_players.append(group[0][1])
                
                # Log details about the duplicates
                duplicate_info = {
                    'name': group[0][1].get('strPlayer', ''),
                    'team': group[0][1].get('strTeam', ''),
                    'sport': group[0][1].get('strSport', ''),
                    'league': group[0][1].get('strLeague', ''),
                    'duplicate_count': len(group),
                    'kept_index': group[0][0],
                    'removed_indices': [item[0] for item in group[1:]]
                }
                self.stats['duplicate_details'].append(duplicate_info)
                
                logger.debug(f"Removed {len(group) - 1} duplicates for {group[0][1].get('strPlayer', '')} ({group[0][1].get('strTeam', '')})")
        
        self.stats['unique_players'] = len(unique_players)
        
        # Write deduplicated CSV
        if unique_players:
            backup_path = f"{self.csv_path}.backup.{int(time.time())}"
            os.rename(self.csv_path, backup_path)
            logger.info(f"Backed up original CSV to: {backup_path}")
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=unique_players[0].keys())
                writer.writeheader()
                writer.writerows(unique_players)
            
            logger.info(f"Updated CSV file: {self.csv_path}")
        
        return self.stats
    
    def generate_report(self, output_dir: str = "reports"):
        """Generate a report of duplicate removal"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report
        summary_path = os.path.join(output_dir, "duplicate_removal_summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Player Duplicate Removal Summary\n\n")
            f.write(f"**Total Players Before:** {self.stats['total_players']}\n")
            f.write(f"**Unique Players After:** {self.stats['unique_players']}\n")
            f.write(f"**Duplicates Removed:** {self.stats['duplicates_removed']}\n")
            f.write(f"**Duplicate Groups:** {self.stats['duplicate_groups']}\n")
            f.write(f"**Reduction:** {((self.stats['duplicates_removed'] / self.stats['total_players']) * 100):.1f}%\n\n")
            
            f.write("## Duplicate Groups (Sample - First 20)\n")
            for i, dup in enumerate(self.stats['duplicate_details'][:20]):
                f.write(f"### {i+1}. {dup['name']} ({dup['team']})\n")
                f.write(f"- Sport: {dup['sport']}\n")
                f.write(f"- League: {dup['league']}\n")
                f.write(f"- Duplicates: {dup['duplicate_count']}\n")
                f.write(f"- Kept: Row {dup['kept_index'] + 1}\n")
                f.write(f"- Removed: Rows {[idx + 1 for idx in dup['removed_indices']]}\n\n")
            
            if len(self.stats['duplicate_details']) > 20:
                f.write(f"... and {len(self.stats['duplicate_details']) - 20} more duplicate groups\n")
        
        # Detailed duplicates report
        duplicates_path = os.path.join(output_dir, "duplicate_details.csv")
        with open(duplicates_path, 'w', newline='', encoding='utf-8') as f:
            if self.stats['duplicate_details']:
                writer = csv.DictWriter(f, fieldnames=['name', 'team', 'sport', 'league', 'duplicate_count', 'kept_index', 'removed_indices'])
                writer.writeheader()
                for dup in self.stats['duplicate_details']:
                    dup['removed_indices'] = str(dup['removed_indices'])  # Convert list to string for CSV
                    writer.writerow(dup)
        
        logger.info(f"Reports generated in {output_dir}/")
        logger.info(f"- Summary: {summary_path}")
        logger.info(f"- Duplicate details: {duplicates_path}")

def main():
    """Main function"""
    # Paths
    csv_path = "bot/data/players.csv"
    
    # Check if files exist
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Create deduplicator and process
    deduplicator = PlayerDeduplicator(csv_path)
    
    logger.info("Starting player deduplication...")
    start_time = time.time()
    
    stats = deduplicator.process_csv()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Generate report
    deduplicator.generate_report()
    
    # Print summary
    logger.info(f"Processing completed in {duration:.2f} seconds")
    logger.info(f"Total players before: {stats['total_players']}")
    logger.info(f"Unique players after: {stats['unique_players']}")
    logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
    logger.info(f"Duplicate groups: {stats['duplicate_groups']}")
    logger.info(f"Reduction: {((stats['duplicates_removed'] / stats['total_players']) * 100):.1f}%")

if __name__ == "__main__":
    main() 