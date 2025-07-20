#!/usr/bin/env python3
"""
Script to assign NCAA league logo to all NCAA players in the CSV file.
This script will:
1. Read the players.csv file
2. Find all players with NCAA in their league field
3. Assign the NCAA league logo to their strCutouts field
4. Update the CSV file
"""

import os
import csv
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NCAALogoAssigner:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.ncaa_logo_path = "static/logos/leagues/NCAA/ncaa.png"  # Relative to bot directory
        
        # Statistics tracking
        self.stats = {
            'total_players': 0,
            'ncaa_players_found': 0,
            'ncaa_players_updated': 0,
            'ncaa_teams': set(),
            'ncaa_sports': set()
        }
    
    def process_csv(self) -> dict:
        """Process the CSV file and assign NCAA logos"""
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
        
        # Process each player
        for i, player in enumerate(players):
            if i % 1000 == 0:
                logger.info(f"Processing player {i+1}/{len(players)}")
                
            player_name = player.get('strPlayer', '')
            team_name = player.get('strTeam', '')
            sport = player.get('strSport', '')
            league = player.get('strLeague', '')
            current_image = player.get('strCutouts', '')
            
            # Check if this is an NCAA player
            if league and 'NCAA' in league.upper():
                self.stats['ncaa_players_found'] += 1
                self.stats['ncaa_teams'].add(team_name)
                self.stats['ncaa_sports'].add(sport)
                
                # Assign NCAA logo
                player['strCutouts'] = self.ncaa_logo_path
                self.stats['ncaa_players_updated'] += 1
                
                logger.debug(f"Assigned NCAA logo to {player_name} ({team_name}, {sport}, {league})")
        
        # Write updated CSV
        if players:
            backup_path = f"{self.csv_path}.backup.{int(time.time())}"
            os.rename(self.csv_path, backup_path)
            logger.info(f"Backed up original CSV to: {backup_path}")
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=players[0].keys())
                writer.writeheader()
                writer.writerows(players)
            
            logger.info(f"Updated CSV file: {self.csv_path}")
        
        return self.stats
    
    def generate_report(self, output_dir: str = "reports"):
        """Generate a report of NCAA logo assignments"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report
        summary_path = os.path.join(output_dir, "ncaa_logo_assignment_summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# NCAA Logo Assignment Summary\n\n")
            f.write(f"**Total Players Processed:** {self.stats['total_players']}\n")
            f.write(f"**NCAA Players Found:** {self.stats['ncaa_players_found']}\n")
            f.write(f"**NCAA Players Updated:** {self.stats['ncaa_players_updated']}\n")
            f.write(f"**NCAA Teams Found:** {len(self.stats['ncaa_teams'])}\n")
            f.write(f"**NCAA Sports Found:** {len(self.stats['ncaa_sports'])}\n\n")
            
            f.write("## NCAA Sports\n")
            for sport in sorted(self.stats['ncaa_sports']):
                f.write(f"- {sport}\n")
            
            f.write("\n## NCAA Teams (Sample - First 50)\n")
            for team in sorted(list(self.stats['ncaa_teams'])[:50]):
                f.write(f"- {team}\n")
            
            if len(self.stats['ncaa_teams']) > 50:
                f.write(f"\n... and {len(self.stats['ncaa_teams']) - 50} more teams\n")
        
        logger.info(f"Report generated: {summary_path}")

def main():
    """Main function"""
    # Paths
    csv_path = "bot/data/players.csv"
    
    # Check if files exist
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Check if NCAA logo exists
    ncaa_logo_path = "bot/static/logos/leagues/NCAA/ncaa.png"
    if not os.path.exists(ncaa_logo_path):
        logger.error(f"NCAA logo not found: {ncaa_logo_path}")
        return
    
    # Create assigner and process
    assigner = NCAALogoAssigner(csv_path)
    
    logger.info("Starting NCAA logo assignment...")
    start_time = time.time()
    
    stats = assigner.process_csv()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Generate report
    assigner.generate_report()
    
    # Print summary
    logger.info(f"Processing completed in {duration:.2f} seconds")
    logger.info(f"Total players: {stats['total_players']}")
    logger.info(f"NCAA players found: {stats['ncaa_players_found']}")
    logger.info(f"NCAA players updated: {stats['ncaa_players_updated']}")
    logger.info(f"NCAA teams: {len(stats['ncaa_teams'])}")
    logger.info(f"NCAA sports: {len(stats['ncaa_sports'])}")

if __name__ == "__main__":
    main() 