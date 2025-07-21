#!/usr/bin/env python3
"""
Compile Teams and Players CSV Script

This script compiles a comprehensive CSV file containing all teams and players
from all supported leagues in the betting bot system.

Output CSV columns: League, Team, Player, URL
"""

import asyncio
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add the bot directory to the path so we can import modules
current_dir = Path(__file__).parent
project_root = current_dir.parent
bot_path = project_root / "bot"

print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")
print(f"Bot path: {bot_path}")
print(f"Bot path exists: {bot_path.exists()}")

sys.path.insert(0, str(project_root))

try:
    from bot.config.leagues import LEAGUE_CONFIG
    from bot.services.player_search_service import PlayerSearchService
    from bot.utils.league_dictionaries.team_mappings import LEAGUE_TEAM_MAPPINGS
    print("Successfully imported bot modules")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Available paths: {sys.path}")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockDBManager:
    """Mock database manager for the player search service."""
    
    async def execute(self, query, params=None):
        return None
    
    async def fetch_all(self, query, params=None):
        return []


class TeamsAndPlayersCompiler:
    """Compiles teams and players from all supported leagues."""
    
    def __init__(self):
        self.player_search_service = PlayerSearchService(MockDBManager())
        self.output_data = []
        
    def get_supported_leagues(self) -> List[str]:
        """Get all supported leagues from the configuration."""
        leagues = []
        for league_key, config in LEAGUE_CONFIG.items():
            if league_key not in ["MANUAL", "OTHER"]:
                leagues.append(league_key)
        return sorted(leagues)
    
    def get_teams_for_league(self, league: str) -> List[str]:
        """Get teams for a specific league."""
        teams = []
        
        # Get teams from LEAGUE_TEAM_MAPPINGS
        if league in LEAGUE_TEAM_MAPPINGS:
            league_mappings = LEAGUE_TEAM_MAPPINGS[league]
            
            # For individual sports, the mappings are player names
            if league in [
                "ATP", "WTA", "Tennis",
                "PDC", "BDO", "WDF", "PremierLeagueDarts", "WorldMatchplay", 
                "WorldGrandPrix", "UKOpen", "GrandSlam", "PlayersChampionship", 
                "EuropeanChampionship", "Masters",
                "PGA", "LPGA", "EuropeanTour", "LIVGolf", "RyderCup", "PresidentsCup"
            ]:
                # For individual sports, use league name as team
                teams.append(league)
            else:
                # For team sports, extract unique team names
                team_names = set()
                for key, value in league_mappings.items():
                    if isinstance(value, str):
                        team_names.add(value)
                    elif isinstance(value, dict) and 'name' in value:
                        team_names.add(value['name'])
                teams.extend(sorted(team_names))
        
        return teams
    
    async def get_players_for_team(self, league: str, team: str) -> List[str]:
        """Get players for a specific team in a league."""
        try:
            # For individual sports, get players from the mappings
            if league in [
                "ATP", "WTA", "Tennis",
                "PDC", "BDO", "WDF", "PremierLeagueDarts", "WorldMatchplay", 
                "WorldGrandPrix", "UKOpen", "GrandSlam", "PlayersChampionship", 
                "EuropeanChampionship", "Masters",
                "PGA", "LPGA", "EuropeanTour", "LIVGolf", "RyderCup", "PresidentsCup"
            ]:
                if league in LEAGUE_TEAM_MAPPINGS:
                    return list(LEAGUE_TEAM_MAPPINGS[league].values())
                return []
            
            # For team sports, try to get players from the player search service
            players_data = await self.player_search_service._get_players_from_team_library(league, team)
            player_names = [player['player_name'] for player in players_data if 'player_name' in player]
            
            # If no players found, try the specific team player methods
            if not player_names:
                if league == "NBA":
                    player_names = await self.player_search_service._get_nba_team_players(team)
                elif league == "NFL":
                    player_names = await self.player_search_service._get_nfl_team_players(team)
                elif league == "MLB":
                    player_names = await self.player_search_service._get_mlb_team_players(team)
                elif league == "NHL":
                    player_names = await self.player_search_service._get_nhl_team_players(team)
                elif league in ["EPL", "LaLiga", "Bundesliga", "SerieA", "Ligue1"]:
                    player_names = await self.player_search_service._get_soccer_team_players(team)
            
            return sorted(list(set(player_names))) if player_names else []
            
        except Exception as e:
            logger.warning(f"Error getting players for {team} in {league}: {e}")
            return []
    
    async def compile_league_data(self, league: str):
        """Compile data for a specific league."""
        logger.info(f"Compiling data for league: {league}")
        
        teams = self.get_teams_for_league(league)
        logger.info(f"Found {len(teams)} teams for {league}")
        
        for team in teams:
            players = await self.get_players_for_team(league, team)
            logger.info(f"Found {len(players)} players for {team} in {league}")
            
            if players:
                for player in players:
                    self.output_data.append({
                        'League': league,
                        'Team': team,
                        'Player': player,
                        'URL': ''  # Empty for now as requested
                    })
            else:
                # Add team entry even if no players found
                self.output_data.append({
                    'League': league,
                    'Team': team,
                    'Player': '',  # Empty if no players
                    'URL': ''
                })
    
    async def compile_all_data(self):
        """Compile data for all supported leagues."""
        leagues = self.get_supported_leagues()
        logger.info(f"Found {len(leagues)} supported leagues: {leagues}")
        
        for league in leagues:
            await self.compile_league_data(league)
    
    def save_to_csv(self, output_file: str = "teams_and_players.csv"):
        """Save the compiled data to a CSV file."""
        if not self.output_data:
            logger.warning("No data to save!")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['League', 'Team', 'Player', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.output_data:
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.output_data)} entries to {output_file}")
        
        # Print summary statistics
        leagues = set(row['League'] for row in self.output_data)
        teams = set((row['League'], row['Team']) for row in self.output_data)
        players = set((row['League'], row['Team'], row['Player']) for row in self.output_data if row['Player'])
        
        logger.info(f"Summary:")
        logger.info(f"  - Total leagues: {len(leagues)}")
        logger.info(f"  - Total teams: {len(teams)}")
        logger.info(f"  - Total players: {len(players)}")
        logger.info(f"  - Total entries: {len(self.output_data)}")


async def main():
    """Main function to run the compilation."""
    logger.info("Starting teams and players compilation...")
    
    compiler = TeamsAndPlayersCompiler()
    await compiler.compile_all_data()
    compiler.save_to_csv()
    
    logger.info("Compilation completed!")


if __name__ == "__main__":
    asyncio.run(main()) 