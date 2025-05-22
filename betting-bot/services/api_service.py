# services/api_service.py
# Service module for handling API-Sports API calls

from typing import List, Dict, Optional
from api.sports_api import APISportsFetcher
import os
from dotenv import load_dotenv
import logging

load_dotenv()
API_KEY = os.getenv('API_KEY')
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
            return [self.fetcher.map_game(game, league_key) for game in data["response"]]
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {str(e)}")
            return []

    async def get_event_details(self, league_key: str, event_id: str, date: str) -> Optional[Dict]:
        """Fetch details for a specific event by ID (searches by date and league)."""
        try:
            data = await self.fetcher.fetch_games(league_key, date)
            if not data or "response" not in data:
                return None
            for game in data["response"]:
                if str(game.get("id", game.get("fixture", {}).get("id", ""))) == str(event_id):
                    return self.fetcher.map_game(game, league_key)
            return None
        except Exception as e:
            logger.error(f"Error fetching event details: {str(e)}")
            return None

    async def get_league_standings(self, league_key: str, season: Optional[int] = None) -> List[Dict]:
        """Fetch standings for a league."""
        try:
            # This would need to be implemented with API-Sports standings endpoint
            # For now, return empty list as this feature is not yet implemented
            logger.info(f"Standings feature not yet implemented for {league_key}")
            return []
        except Exception as e:
            logger.error(f"Error fetching league standings: {str(e)}")
            return []

    async def get_teams(self, league_key: str) -> List[str]:
        """Fetch teams for a league."""
        try:
            # This would need to be implemented with API-Sports teams endpoint
            # For now, return empty list as this feature is not yet implemented
            logger.info(f"Teams feature not yet implemented for {league_key}")
            return []
        except Exception as e:
            logger.error(f"Error fetching teams: {str(e)}")
            return []

    async def get_team_logo(self, team_name: str, league_key: str) -> Optional[str]:
        """Get the file path for a team's logo."""
        try:
            # This would need to be implemented with API-Sports teams endpoint
            # For now, return None as this feature is not yet implemented
            logger.info(f"Team logo feature not yet implemented for {team_name} in {league_key}")
            return None
        except Exception as e:
            logger.error(f"Error fetching team logo: {str(e)}")
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
