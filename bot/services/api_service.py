# services/api_service.py
# Service module for handling API-Sports API calls

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from bot.api.sports_api import APISportsFetcher
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
logger = logging.getLogger(__name__)


class ApiService:
    """Service for fetching sports data from API-Sports."""

    def __init__(self):
        self.fetcher = APISportsFetcher()

    async def get_upcoming_events(self, league_key: str, date: str) -> List[Dict]:
        """Fetch upcoming events for a league and date."""
        try:
            data = await self.fetcher.fetch_games(league_key, date)
            if not data or "response" not in data:
                logger.warning(f"No response data for league {league_key}")
                return []
            return [
                self.fetcher.map_game(game, league_key) for game in data["response"]
            ]
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {str(e)}")
            return []

    async def get_event_details(
        self, league_key: str, event_id: str, date: str
    ) -> Optional[Dict]:
        """Fetch details for a specific event by ID (searches by date and league)."""
        try:
            data = await self.fetcher.fetch_games(league_key, date)
            if not data or "response" not in data:
                return None
            for game in data["response"]:
                if str(game.get("id", game.get("fixture", {}).get("id", ""))) == str(
                    event_id
                ):
                    return self.fetcher.map_game(game, league_key)
            return None
        except Exception as e:
            logger.error(f"Error fetching event details: {str(e)}")
            return None

    async def get_league_standings(
        self, league_key: str, season: Optional[int] = None
    ) -> List[Dict]:
        """Fetch standings for a league."""
        try:
            # Get sport and league info
            sport, league_id = self._get_sport_and_league_id(league_key)
            if not sport or not league_id:
                logger.warning(f"Could not determine sport/league_id for {league_key}")
                return []

            if season is None:
                season = datetime.now().year

            # Use the fetcher to get standings
            if not self.fetcher:
                self.fetcher = await APISportsFetcher().__aenter__()

            params = {"league": league_id, "season": season}

            data = await self.fetcher.fetch_data(sport, "standings", params)

            if not data or "response" not in data:
                logger.warning(f"No standings data for {league_key}")
                return []

            standings = []
            for standing in data["response"]:
                if "league" in standing and "standings" in standing["league"]:
                    for group in standing["league"]["standings"]:
                        for team in group:
                            standings.append(
                                {
                                    "rank": team.get("rank", 0),
                                    "team": team.get("team", {}).get("name", "Unknown"),
                                    "points": team.get("points", 0),
                                    "played": team.get("all", {}).get("played", 0),
                                    "won": team.get("all", {}).get("win", 0),
                                    "drawn": team.get("all", {}).get("draw", 0),
                                    "lost": team.get("all", {}).get("lose", 0),
                                    "goals_for": team.get("all", {})
                                    .get("goals", {})
                                    .get("for", 0),
                                    "goals_against": team.get("all", {})
                                    .get("goals", {})
                                    .get("against", 0),
                                }
                            )

            logger.info(
                f"Retrieved {len(standings)} standings entries for {league_key}"
            )
            return standings

        except Exception as e:
            logger.error(f"Error fetching league standings for {league_key}: {str(e)}")
            return []

    async def get_teams(self, league_key: str) -> List[str]:
        """Fetch teams for a league."""
        try:
            # Get sport and league info
            sport, league_id = self._get_sport_and_league_id(league_key)
            if not sport or not league_id:
                logger.warning(f"Could not determine sport/league_id for {league_key}")
                return []

            # Use the fetcher to get teams
            if not self.fetcher:
                self.fetcher = await APISportsFetcher().__aenter__()

            params = {"league": league_id, "season": datetime.now().year}

            data = await self.fetcher.fetch_data(sport, "teams", params)

            if not data or "response" not in data:
                logger.warning(f"No teams data for {league_key}")
                return []

            teams = []
            for team in data["response"]:
                team_name = team.get("team", {}).get("name")
                if team_name:
                    teams.append(team_name)

            logger.info(f"Retrieved {len(teams)} teams for {league_key}")
            return teams

        except Exception as e:
            logger.error(f"Error fetching teams for {league_key}: {str(e)}")
            return []

    async def get_team_logo(self, team_name: str, league_key: str) -> Optional[str]:
        """Get the file path for a team's logo."""
        try:
            # Get sport and league info
            sport, league_id = self._get_sport_and_league_id(league_key)
            if not sport or not league_id:
                logger.warning(f"Could not determine sport/league_id for {league_key}")
                return None

            # Use the fetcher to get team details
            if not self.fetcher:
                self.fetcher = await APISportsFetcher().__aenter__()

            params = {"league": league_id, "season": datetime.now().year}

            data = await self.fetcher.fetch_data(sport, "teams", params)

            if not data or "response" not in data:
                logger.warning(f"No teams data for {league_key}")
                return None

            # Find the team by name
            for team in data["response"]:
                if team.get("team", {}).get("name") == team_name:
                    logo_url = team.get("team", {}).get("logo")
                    if logo_url:
                        # Return the URL - the download script will handle saving
                        return logo_url

            logger.warning(f"Team logo not found for {team_name} in {league_key}")
            return None

        except Exception as e:
            logger.error(
                f"Error fetching team logo for {team_name} in {league_key}: {str(e)}"
            )
            return None

    @staticmethod
    async def get_league_logo(league_key: str) -> Optional[str]:
        """Get the file path for a league's logo."""
        # This method is no longer used in the new implementation
        return None

    @staticmethod
    async def get_player_details(player_name: str, league_key: str) -> Optional[Dict]:
        """Fetch details for a player (e.g., Darts, Tennis, UFC/MMA)."""
        # This method is no longer used in the new implementation
        return None

    def _get_sport_and_league_id(
        self, league_key: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Helper method to get sport and league_id from league_key."""
        # Map league keys to sport and league_id
        league_mapping = {
            # Football
            "EPL": ("football", "39"),
            "LaLiga": ("football", "140"),
            "Bundesliga": ("football", "78"),
            "SerieA": ("football", "135"),
            "Ligue1": ("football", "61"),
            "MLS": ("football", "253"),
            "ChampionsLeague": ("football", "2"),
            "EuropaLeague": ("football", "3"),
            "WorldCup": ("football", "15"),
            # Basketball
            "NBA": ("basketball", "12"),
            "WNBA": ("basketball", "13"),
            "EuroLeague": ("basketball", "1"),
            # Baseball
            "MLB": ("baseball", "1"),
            "NPB": ("baseball", "2"),
            "KBO": ("baseball", "3"),
            # Hockey
            "NHL": ("hockey", "57"),
            "KHL": ("hockey", "1"),
            # American Football
            "NFL": ("american-football", "1"),
            "NCAA": ("american-football", "2"),
            # Rugby
            "SuperRugby": ("rugby", "1"),
            "SixNations": ("rugby", "2"),
            # Volleyball
            "FIVB": ("volleyball", "1"),
            # Handball
            "EHF": ("handball", "1"),
            # Tennis
            "ATP": ("tennis", "1"),
            "WTA": ("tennis", "2"),
            "GrandSlam": ("tennis", "3"),
            # Formula 1
            "Formula-1": ("formula-1", "1"),
            # MMA
            "MMA": ("mma", "1"),
            "UFC": ("mma", "1"),
            "Bellator": ("mma", "2"),
        }

        return league_mapping.get(league_key, (None, None))
