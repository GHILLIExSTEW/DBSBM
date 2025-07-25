#!/usr/bin/env python3
"""
Compile Teams and Players CSV Script - External Sources

This script compiles a comprehensive CSV file containing all teams and players
from all supported leagues by searching external sources (Google/Wikipedia)
for active rosters.

Output CSV columns: League, Team, Player, URL
"""

import asyncio
import csv
import logging
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup

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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExternalPlayerSearcher:
    """Searches external sources for team rosters and player names."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.delay = 1  # Delay between requests to be respectful

    def search_google(self, query: str) -> Optional[str]:
        """Search Google for a query and return the first result URL."""
        try:
            # Use a simple Google search approach
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for Wikipedia links first
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "wikipedia.org" in href and "/wiki/" in href:
                    # Extract Wikipedia URL
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    return href

            # Look for any sports-related links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if any(
                    domain in href
                    for domain in [
                        "espn.com",
                        "sports-reference.com",
                        "basketball-reference.com",
                        "baseball-reference.com",
                        "hockey-reference.com",
                        "pro-football-reference.com",
                    ]
                ):
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    return href

            time.sleep(self.delay)
            return None

        except Exception as e:
            logger.warning(f"Error searching Google for '{query}': {e}")
            return None

    def search_wikipedia(self, query: str) -> Optional[str]:
        """Search Wikipedia for a query and return the page URL."""
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=1&namespace=0&format=json"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if len(data) > 1 and len(data[1]) > 0:
                return data[1][0]  # Return the first result URL

            time.sleep(self.delay)
            return None

        except Exception as e:
            logger.warning(f"Error searching Wikipedia for '{query}': {e}")
            return None

    def extract_players_from_wikipedia(
        self, url: str, team_name: str, league: str
    ) -> List[str]:
        """Extract player names from a Wikipedia page."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            players = []

            # Look for roster tables
            tables = soup.find_all("table", class_="wikitable")

            for table in tables:
                # Look for headers that might indicate a roster
                headers = table.find_all("th")
                header_text = " ".join([h.get_text().lower() for h in headers])

                if any(
                    keyword in header_text
                    for keyword in ["player", "name", "roster", "squad"]
                ):
                    rows = table.find_all("tr")[1:]  # Skip header row

                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            # First cell is usually the player name
                            player_cell = cells[0]
                            player_name = player_cell.get_text().strip()

                            # Clean up the player name
                            player_name = re.sub(
                                r"\[.*?\]", "", player_name
                            )  # Remove Wikipedia links
                            player_name = re.sub(
                                r"\(.*?\)", "", player_name
                            )  # Remove parentheses
                            player_name = player_name.strip()

                            # Filter out non-player entries
                            if (
                                len(player_name) > 2
                                and not player_name.isdigit()
                                and not any(
                                    word in player_name.lower()
                                    for word in [
                                        "total",
                                        "coach",
                                        "manager",
                                        "captain",
                                        "goalkeeper",
                                        "defender",
                                        "midfielder",
                                        "forward",
                                    ]
                                )
                            ):
                                players.append(player_name)

            # If no roster table found, look for player lists in the text
            if not players:
                content = soup.find("div", id="mw-content-text")
                if content:
                    # Look for patterns like "Players: John Doe, Jane Smith"
                    text = content.get_text()
                    player_patterns = [
                        r"players?:?\s*([^.]*?)(?:\.|$)",
                        r"roster:?\s*([^.]*?)(?:\.|$)",
                        r"squad:?\s*([^.]*?)(?:\.|$)",
                    ]

                    for pattern in player_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", match)
                            players.extend(names)

            return list(set(players))  # Remove duplicates

        except Exception as e:
            logger.warning(f"Error extracting players from {url}: {e}")
            return []

    def extract_players_from_sports_site(
        self, url: str, team_name: str, league: str
    ) -> List[str]:
        """Extract player names from sports reference sites."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            players = []

            # Look for player name elements
            player_selectors = [
                'td[data-stat="player"] a',
                ".player-name",
                ".roster-player-name",
                "td.player a",
                'a[href*="/players/"]',
            ]

            for selector in player_selectors:
                elements = soup.select(selector)
                for element in elements:
                    player_name = element.get_text().strip()
                    if len(player_name) > 2 and not player_name.isdigit():
                        players.append(player_name)

            return list(set(players))

        except Exception as e:
            logger.warning(f"Error extracting players from sports site {url}: {e}")
            return []

    def search_team_roster(
        self, team_name: str, league: str
    ) -> tuple[List[str], Optional[str]]:
        """Search for a team's roster and return players and source URL."""
        logger.info(f"Searching for roster: {team_name} ({league})")

        # Try different search queries
        search_queries = [
            f"{team_name} {league} roster 2024",
            f"{team_name} {league} players 2024",
            f"{team_name} {league} squad 2024",
            f"{team_name} {league} active roster",
            f"{team_name} {league} current players",
        ]

        for query in search_queries:
            # Try Wikipedia first
            wiki_url = self.search_wikipedia(query)
            if wiki_url:
                players = self.extract_players_from_wikipedia(
                    wiki_url, team_name, league
                )
                if players:
                    logger.info(
                        f"Found {len(players)} players from Wikipedia for {team_name}"
                    )
                    return players, wiki_url

            # Try Google search
            google_url = self.search_google(query)
            if google_url:
                if "wikipedia.org" in google_url:
                    players = self.extract_players_from_wikipedia(
                        google_url, team_name, league
                    )
                else:
                    players = self.extract_players_from_sports_site(
                        google_url, team_name, league
                    )

                if players:
                    logger.info(
                        f"Found {len(players)} players from external source for {team_name}"
                    )
                    return players, google_url

        logger.warning(f"No players found for {team_name} ({league})")
        return [], None


class TeamsAndPlayersCompiler:
    """Compiles teams and players from all supported leagues using external sources."""

    def __init__(self):
        self.searcher = ExternalPlayerSearcher()
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
                "ATP",
                "WTA",
                "Tennis",
                "PDC",
                "BDO",
                "WDF",
                "PremierLeagueDarts",
                "WorldMatchplay",
                "WorldGrandPrix",
                "UKOpen",
                "GrandSlam",
                "PlayersChampionship",
                "EuropeanChampionship",
                "Masters",
                "PGA",
                "LPGA",
                "EuropeanTour",
                "LIVGolf",
                "RyderCup",
                "PresidentsCup",
            ]:
                # For individual sports, use league name as team
                teams.append(league)
            else:
                # For team sports, extract unique team names
                team_names = set()
                for key, value in league_mappings.items():
                    if isinstance(value, str):
                        team_names.add(value)
                    elif isinstance(value, dict) and "name" in value:
                        team_names.add(value["name"])
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
                    self.output_data.append(
                        {
                            "League": league,
                            "Team": team,
                            "Player": player,
                            "URL": source_url or "",
                        }
                    )
            else:
                # Add team entry even if no players found
                self.output_data.append(
                    {
                        "League": league,
                        "Team": team,
                        "Player": "",  # Empty if no players
                        "URL": source_url or "",
                    }
                )

    async def compile_all_data(self):
        """Compile data for all supported leagues."""
        leagues = self.get_supported_leagues()
        logger.info(f"Found {len(leagues)} supported leagues: {leagues}")

        for league in leagues:
            await self.compile_league_data(league)

    def save_to_csv(self, output_file: str = "teams_and_players_external.csv"):
        """Save the compiled data to a CSV file."""
        if not self.output_data:
            logger.warning("No data to save!")
            return

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["League", "Team", "Player", "URL"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for row in self.output_data:
                writer.writerow(row)

        logger.info(f"Saved {len(self.output_data)} entries to {output_file}")

        # Print summary statistics
        leagues = set(row["League"] for row in self.output_data)
        teams = set((row["League"], row["Team"]) for row in self.output_data)
        players = set(
            (row["League"], row["Team"], row["Player"])
            for row in self.output_data
            if row["Player"]
        )

        logger.info(f"Summary:")
        logger.info(f"  - Total leagues: {len(leagues)}")
        logger.info(f"  - Total teams: {len(teams)}")
        logger.info(f"  - Total players: {len(players)}")
        logger.info(f"  - Total entries: {len(self.output_data)}")


async def main():
    """Main function to run the compilation."""
    logger.info("Starting teams and players compilation using external sources...")

    compiler = TeamsAndPlayersCompiler()
    await compiler.compile_all_data()
    compiler.save_to_csv()

    logger.info("Compilation completed!")


if __name__ == "__main__":
    asyncio.run(main())
