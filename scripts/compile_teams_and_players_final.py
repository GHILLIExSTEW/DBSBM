#!/usr/bin/env python3
"""
Compile Teams and Players CSV Script - Final Comprehensive Version

This script compiles a comprehensive CSV file containing all teams and players
from all supported leagues using a combination of external sources and manual data.
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


class ComprehensivePlayerSearcher:
    """Comprehensive player searcher with manual data and external sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.delay = 1
    
    def get_manual_players(self, team_name: str, league: str) -> List[str]:
        """Get players from manual data for major teams."""
        # Manual player data for major teams
        manual_data = {
            'NBA': {
                'Los Angeles Lakers': [
                    'LeBron James', 'Anthony Davis', 'Austin Reaves', 'D\'Angelo Russell',
                    'Rui Hachimura', 'Taurean Prince', 'Jarred Vanderbilt', 'Gabe Vincent',
                    'Christian Wood', 'Jaxson Hayes', 'Cam Reddish', 'Max Christie'
                ],
                'Boston Celtics': [
                    'Jayson Tatum', 'Jaylen Brown', 'Kristaps Porziņģis', 'Derrick White',
                    'Jrue Holiday', 'Al Horford', 'Payton Pritchard', 'Sam Hauser',
                    'Luke Kornet', 'Oshae Brissett', 'Dalano Banton', 'Svi Mykhailiuk'
                ],
                'Golden State Warriors': [
                    'Stephen Curry', 'Klay Thompson', 'Draymond Green', 'Andrew Wiggins',
                    'Chris Paul', 'Kevon Looney', 'Gary Payton II', 'Jonathan Kuminga',
                    'Moses Moody', 'Brandin Podziemski', 'Trayce Jackson-Davis', 'Cory Joseph'
                ],
                'Miami Heat': [
                    'Jimmy Butler', 'Bam Adebayo', 'Tyler Herro', 'Kyle Lowry',
                    'Duncan Robinson', 'Caleb Martin', 'Haywood Highsmith', 'Jaime Jaquez Jr.',
                    'Nikola Jović', 'Orlando Robinson', 'R.J. Hampton', 'Cole Swider'
                ],
                'Dallas Mavericks': [
                    'Luka Dončić', 'Kyrie Irving', 'Tim Hardaway Jr.', 'Grant Williams',
                    'Dereck Lively II', 'Josh Green', 'Seth Curry', 'Maxi Kleber',
                    'Dwight Powell', 'Jaden Hardy', 'Olivier-Maxence Prosper', 'Markieff Morris'
                ]
            },
            'MLB': {
                'New York Yankees': [
                    'Aaron Judge', 'Giancarlo Stanton', 'Anthony Rizzo', 'DJ LeMahieu',
                    'Gleyber Torres', 'Harrison Bader', 'Isiah Kiner-Falefa', 'Jose Trevino',
                    'Kyle Higashioka', 'Oswaldo Cabrera', 'Oswald Peraza', 'Estevan Florial'
                ],
                'Los Angeles Dodgers': [
                    'Mookie Betts', 'Freddie Freeman', 'Will Smith', 'Max Muncy',
                    'Jason Heyward', 'James Outman', 'Miguel Rojas', 'Austin Barnes',
                    'Chris Taylor', 'Enrique Hernández', 'Miguel Vargas', 'Andy Pages'
                ],
                'Boston Red Sox': [
                    'Rafael Devers', 'Masataka Yoshida', 'Alex Verdugo', 'Justin Turner',
                    'Triston Casas', 'Connor Wong', 'Reese McGuire', 'Pablo Reyes',
                    'Rob Refsnyder', 'Jarren Duran', 'Ceddanne Rafaela', 'Wilyer Abreu'
                ],
                'Houston Astros': [
                    'Yordan Alvarez', 'Kyle Tucker', 'Jose Altuve', 'Alex Bregman',
                    'Jeremy Peña', 'Chas McCormick', 'Martín Maldonado', 'Yainer Diaz',
                    'Mauricio Dubón', 'Jake Meyers', 'Corey Julks', 'Grae Kessinger'
                ]
            },
            'NFL': {
                'Kansas City Chiefs': [
                    'Patrick Mahomes', 'Travis Kelce', 'Isiah Pacheco', 'Rashee Rice',
                    'Marquez Valdes-Scantling', 'Skyy Moore', 'Clyde Edwards-Helaire',
                    'Noah Gray', 'Blake Bell', 'Justin Watson', 'Kadarius Toney', 'Richie James'
                ],
                'San Francisco 49ers': [
                    'Brock Purdy', 'Christian McCaffrey', 'Deebo Samuel', 'Brandon Aiyuk',
                    'George Kittle', 'Elijah Mitchell', 'Jordan Mason', 'Kyle Juszczyk',
                    'Ray-Ray McCloud', 'Danny Gray', 'Jauan Jennings', 'Chris Conley'
                ],
                'Philadelphia Eagles': [
                    'Jalen Hurts', 'A.J. Brown', 'DeVonta Smith', 'Dallas Goedert',
                    'D\'Andre Swift', 'Kenneth Gainwell', 'Boston Scott', 'Olamide Zaccheaus',
                    'Quez Watkins', 'Grant Calcaterra', 'Jack Stoll', 'Britain Covey'
                ],
                'Dallas Cowboys': [
                    'Dak Prescott', 'CeeDee Lamb', 'Brandin Cooks', 'Michael Gallup',
                    'Tony Pollard', 'Jake Ferguson', 'Rico Dowdle', 'Luke Schoonmaker',
                    'KaVontae Turpin', 'Jalen Tolbert', 'Peyton Hendershot', 'Deuce Vaughn'
                ]
            },
            'NHL': {
                'Edmonton Oilers': [
                    'Connor McDavid', 'Leon Draisaitl', 'Ryan Nugent-Hopkins', 'Zach Hyman',
                    'Evander Kane', 'Warren Foegele', 'Derek Ryan', 'Mattias Janmark',
                    'Ryan McLeod', 'Dylan Holloway', 'James Hamblin', 'Raphaël Lavoie'
                ],
                'Boston Bruins': [
                    'David Pastrňák', 'Brad Marchand', 'Charlie Coyle', 'Jake DeBrusk',
                    'Pavel Zacha', 'Morgan Geekie', 'James van Riemsdyk', 'Trent Frederic',
                    'Danton Heinen', 'Jesper Boqvist', 'Oskar Steen', 'John Beecher'
                ],
                'Toronto Maple Leafs': [
                    'Auston Matthews', 'Mitch Marner', 'William Nylander', 'John Tavares',
                    'Tyler Bertuzzi', 'Max Domi', 'Calle Järnkrok', 'Noah Gregor',
                    'David Kämpf', 'Ryan Reaves', 'Pontus Holmberg', 'Fraser Minten'
                ]
            }
        }
        
        return manual_data.get(league, {}).get(team_name, [])
    
    def search_wikipedia_roster(self, team_name: str, league: str) -> tuple[List[str], Optional[str]]:
        """Search Wikipedia for team roster."""
        try:
            # Try different Wikipedia page formats
            wiki_urls = [
                f"https://en.wikipedia.org/wiki/{team_name.replace(' ', '_')}",
                f"https://en.wikipedia.org/wiki/{team_name.replace(' ', '_')}_F.C.",
                f"https://en.wikipedia.org/wiki/{team_name.replace(' ', '_')}_FC",
            ]
            
            for wiki_url in wiki_urls:
                try:
                    response = self.session.get(wiki_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        players = self._extract_players_from_wikipedia_page(soup)
                        if players:
                            return players, wiki_url
                except:
                    continue
            
            return [], None
            
        except Exception as e:
            logger.warning(f"Error searching Wikipedia for {team_name}: {e}")
            return [], None
    
    def _extract_players_from_wikipedia_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract players from a Wikipedia page."""
        players = []
        
        # Look for roster tables
        tables = soup.find_all('table', class_='wikitable')
        
        for table in tables:
            headers = table.find_all('th')
            header_text = ' '.join([h.get_text().lower() for h in headers])
            
            if any(keyword in header_text for keyword in ['player', 'name', 'roster', 'squad', 'current']):
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        player_cell = cells[0]
                        player_name = player_cell.get_text().strip()
                        
                        # Clean up player name
                        player_name = re.sub(r'\[.*?\]', '', player_name)
                        player_name = re.sub(r'\(.*?\)', '', player_name)
                        player_name = player_name.strip()
                        
                        # Filter valid player names
                        if (len(player_name) > 2 and 
                            not player_name.isdigit() and 
                            not any(word in player_name.lower() for word in ['total', 'coach', 'manager', 'captain', 'goalkeeper', 'defender', 'midfielder', 'forward', 'players', 'name', 'no.']) and
                            ' ' in player_name):  # Must have at least first and last name
                            players.append(player_name)
        
        return list(set(players))  # Remove duplicates
    
    def search_team_roster(self, team_name: str, league: str) -> tuple[List[str], Optional[str]]:
        """Search for a team's roster using multiple methods."""
        logger.info(f"Searching for roster: {team_name} ({league})")
        
        # First try manual data
        manual_players = self.get_manual_players(team_name, league)
        if manual_players:
            logger.info(f"Found {len(manual_players)} players from manual data for {team_name}")
            return manual_players, "Manual Data"
        
        # Then try Wikipedia
        wiki_players, wiki_url = self.search_wikipedia_roster(team_name, league)
        if wiki_players:
            logger.info(f"Found {len(wiki_players)} players from Wikipedia for {team_name}")
            return wiki_players, wiki_url
        
        logger.warning(f"No players found for {team_name} ({league})")
        return [], None


class TeamsAndPlayersCompiler:
    """Compiles teams and players from all supported leagues."""
    
    def __init__(self):
        self.searcher = ComprehensivePlayerSearcher()
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
    
    def save_to_csv(self, output_file: str = "teams_and_players_final.csv"):
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
    logger.info("Starting comprehensive teams and players compilation...")
    
    compiler = TeamsAndPlayersCompiler()
    await compiler.compile_all_data()
    compiler.save_to_csv()
    
    logger.info("Compilation completed!")


if __name__ == "__main__":
    asyncio.run(main()) 