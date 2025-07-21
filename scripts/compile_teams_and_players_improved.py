#!/usr/bin/env python3
"""
Compile Teams and Players CSV Script - Improved External Sources

This script compiles a comprehensive CSV file containing all teams and players
from all supported leagues using more reliable external sources.
"""

import asyncio
import csv
import logging
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Add the bot directory to the path so we can import modules
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from bot.config.leagues import LEAGUE_CONFIG
    from bot.utils.league_dictionaries.team_mappings import LEAGUE_TEAM_MAPPINGS
    print("Successfully imported bot modules")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImprovedPlayerSearcher:
    """Searches external sources for team rosters using more reliable methods."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.delay = 2  # Increased delay to be more respectful
    
    def get_roster_urls(self, team_name: str, league: str) -> List[str]:
        """Get known roster URLs for teams."""
        # Known roster URL patterns for different leagues
        roster_patterns = {
            'NBA': [
                f"https://www.basketball-reference.com/teams/{self._get_team_abbreviation(team_name, 'NBA')}/2024.html",
                f"https://www.espn.com/nba/team/roster/_/name/{self._get_espn_team_id(team_name, 'NBA')}",
            ],
            'MLB': [
                f"https://www.baseball-reference.com/teams/{self._get_team_abbreviation(team_name, 'MLB')}/2024.shtml",
                f"https://www.espn.com/mlb/team/roster/_/name/{self._get_espn_team_id(team_name, 'MLB')}",
            ],
            'NFL': [
                f"https://www.pro-football-reference.com/teams/{self._get_team_abbreviation(team_name, 'NFL')}/2024.htm",
                f"https://www.espn.com/nfl/team/roster/_/name/{self._get_espn_team_id(team_name, 'NFL')}",
            ],
            'NHL': [
                f"https://www.hockey-reference.com/teams/{self._get_team_abbreviation(team_name, 'NHL')}/2024.html",
                f"https://www.espn.com/nhl/team/roster/_/name/{self._get_espn_team_id(team_name, 'NHL')}",
            ],
            'EPL': [
                f"https://en.wikipedia.org/wiki/{team_name.replace(' ', '_')}_F.C.",
                f"https://www.transfermarkt.com/{team_name.lower().replace(' ', '-')}/kader/verein/",
            ],
        }
        
        return roster_patterns.get(league, [])
    
    def _get_team_abbreviation(self, team_name: str, league: str) -> str:
        """Get team abbreviation for sports reference sites."""
        # Common abbreviations
        abbreviations = {
            'NBA': {
                'Los Angeles Lakers': 'LAL',
                'Boston Celtics': 'BOS',
                'Golden State Warriors': 'GSW',
                'Chicago Bulls': 'CHI',
                'Miami Heat': 'MIA',
                'New York Knicks': 'NYK',
                'Dallas Mavericks': 'DAL',
                'Phoenix Suns': 'PHX',
                'Milwaukee Bucks': 'MIL',
                'Denver Nuggets': 'DEN',
            },
            'MLB': {
                'New York Yankees': 'NYY',
                'Boston Red Sox': 'BOS',
                'Los Angeles Dodgers': 'LAD',
                'Chicago Cubs': 'CHC',
                'San Francisco Giants': 'SFG',
                'St. Louis Cardinals': 'STL',
                'Atlanta Braves': 'ATL',
                'Houston Astros': 'HOU',
                'Philadelphia Phillies': 'PHI',
                'Toronto Blue Jays': 'TOR',
            },
            'NFL': {
                'New England Patriots': 'NWE',
                'Dallas Cowboys': 'DAL',
                'Green Bay Packers': 'GNB',
                'Pittsburgh Steelers': 'PIT',
                'San Francisco 49ers': 'SFO',
                'New York Giants': 'NYG',
                'Chicago Bears': 'CHI',
                'Washington Commanders': 'WAS',
                'Philadelphia Eagles': 'PHI',
                'Kansas City Chiefs': 'KAN',
            },
            'NHL': {
                'Boston Bruins': 'BOS',
                'Chicago Blackhawks': 'CHI',
                'Detroit Red Wings': 'DET',
                'Montreal Canadiens': 'MTL',
                'New York Rangers': 'NYR',
                'Toronto Maple Leafs': 'TOR',
                'Edmonton Oilers': 'EDM',
                'Pittsburgh Penguins': 'PIT',
                'Washington Capitals': 'WSH',
                'Vegas Golden Knights': 'VGK',
            }
        }
        
        return abbreviations.get(league, {}).get(team_name, team_name[:3].upper())
    
    def _get_espn_team_id(self, team_name: str, league: str) -> str:
        """Get ESPN team ID."""
        # This would need to be expanded with actual ESPN team IDs
        # For now, return a placeholder
        return "placeholder"
    
    def extract_players_from_sports_reference(self, url: str) -> List[str]:
        """Extract players from sports-reference.com sites."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            
            # Look for player name cells
            player_cells = soup.find_all('td', {'data-stat': 'player'})
            for cell in player_cells:
                player_link = cell.find('a')
                if player_link:
                    player_name = player_link.get_text().strip()
                    if len(player_name) > 2:
                        players.append(player_name)
            
            return list(set(players))
            
        except Exception as e:
            logger.warning(f"Error extracting from sports reference {url}: {e}")
            return []
    
    def extract_players_from_wikipedia(self, url: str) -> List[str]:
        """Extract players from Wikipedia."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            
            # Look for roster tables
            tables = soup.find_all('table', class_='wikitable')
            
            for table in tables:
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text().lower() for h in headers])
                
                if any(keyword in header_text for keyword in ['player', 'name', 'roster', 'squad']):
                    rows = table.find_all('tr')[1:]
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 1:
                            player_cell = cells[0]
                            player_name = player_cell.get_text().strip()
                            
                            # Clean up the player name
                            player_name = re.sub(r'\[.*?\]', '', player_name)
                            player_name = re.sub(r'\(.*?\)', '', player_name)
                            player_name = player_name.strip()
                            
                            if (len(player_name) > 2 and 
                                not player_name.isdigit() and 
                                not any(word in player_name.lower() for word in ['total', 'coach', 'manager'])):
                                players.append(player_name)
            
            return list(set(players))
            
        except Exception as e:
            logger.warning(f"Error extracting from Wikipedia {url}: {e}")
            return []
    
    def search_team_roster(self, team_name: str, league: str) -> tuple[List[str], Optional[str]]:
        """Search for a team's roster."""
        logger.info(f"Searching for roster: {team_name} ({league})")
        
        # Get known roster URLs
        roster_urls = self.get_roster_urls(team_name, league)
        
        for url in roster_urls:
            try:
                if 'sports-reference.com' in url:
                    players = self.extract_players_from_sports_reference(url)
                elif 'wikipedia.org' in url:
                    players = self.extract_players_from_wikipedia(url)
                else:
                    continue
                
                if players:
                    logger.info(f"Found {len(players)} players from {url}")
                    return players, url
                
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Error processing {url}: {e}")
                continue
        
        # If no players found, try a simple Wikipedia search
        try:
            wiki_url = f"https://en.wikipedia.org/wiki/{team_name.replace(' ', '_')}"
            players = self.extract_players_from_wikipedia(wiki_url)
            if players:
                return players, wiki_url
        except:
            pass
        
        logger.warning(f"No players found for {team_name} ({league})")
        return [], None


class TeamsAndPlayersCompiler:
    """Compiles teams and players from all supported leagues."""
    
    def __init__(self):
        self.searcher = ImprovedPlayerSearcher()
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
        
        if league in LEAGUE_TEAM_MAPPINGS:
            league_mappings = LEAGUE_TEAM_MAPPINGS[league]
            
            # For individual sports, use league name as team
            if league in [
                "ATP", "WTA", "Tennis",
                "PDC", "BDO", "WDF", "PremierLeagueDarts", "WorldMatchplay", 
                "WorldGrandPrix", "UKOpen", "GrandSlam", "PlayersChampionship", 
                "EuropeanChampionship", "Masters",
                "PGA", "LPGA", "EuropeanTour", "LIVGolf", "RyderCup", "PresidentsCup"
            ]:
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
    
    async def compile_league_data(self, league: str):
        """Compile data for a specific league."""
        logger.info(f"Compiling data for league: {league}")
        
        teams = self.get_teams_for_league(league)
        logger.info(f"Found {len(teams)} teams for {league}")
        
        for team in teams:
            players, source_url = self.searcher.search_team_roster(team, league)
            logger.info(f"Found {len(players)} players for {team} in {league}")
            
            if players:
                for player in players:
                    self.output_data.append({
                        'League': league,
                        'Team': team,
                        'Player': player,
                        'URL': source_url or ''
                    })
            else:
                # Add team entry even if no players found
                self.output_data.append({
                    'League': league,
                    'Team': team,
                    'Player': '',
                    'URL': source_url or ''
                })
    
    async def compile_all_data(self):
        """Compile data for all supported leagues."""
        leagues = self.get_supported_leagues()
        logger.info(f"Found {len(leagues)} supported leagues: {leagues}")
        
        for league in leagues:
            await self.compile_league_data(league)
    
    def save_to_csv(self, output_file: str = "teams_and_players_improved.csv"):
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
    logger.info("Starting teams and players compilation using improved external sources...")
    
    compiler = TeamsAndPlayersCompiler()
    await compiler.compile_all_data()
    compiler.save_to_csv()
    
    logger.info("Compilation completed!")


if __name__ == "__main__":
    asyncio.run(main()) 