"""Service for managing game data and interactions with sports APIs."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

# Load environment variables for RUN_API_FETCH_ON_START
RUN_API_FETCH_ON_START = os.getenv("RUN_API_FETCH_ON_START", "false").lower() == "true"

logger = logging.getLogger(__name__)


class GameService:
    def __init__(self, sports_api, db_manager):
        self.sports_api = sports_api
        self.db = db_manager
        # Remove the circular import - DataSyncService will be injected later
        self.data_sync = None
        self.logger = logging.getLogger(__name__)
        self.sync_interval = 300  # 5 minutes
        self._sync_task = None
        self.running = False

        # Verify API key is available
        if not API_KEY:
            raise ValueError("API_KEY not found in .env file")

    def set_data_sync_service(self, data_sync_service):
        """Set the data sync service after initialization to avoid circular imports."""
        self.data_sync = data_sync_service

    async def start(self):
        """Start the game service."""
        try:
            self.running = True
            # No periodic sync task; fetcher.py handles game syncing
            self.logger.info(
                "GameService started successfully, relying on fetcher.py for game syncing"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error starting GameService: {e}")
            return False

    async def stop(self):
        """Stop the game service."""
        try:
            self.running = False
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            self.logger.info("GameService stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping GameService: {e}")
            return False

    async def get_live_fixtures(self, league: str) -> List[Dict]:
        """Get live fixtures for a specific league."""
        try:
            fixtures = await self.sports_api.get_live_fixtures(league)
            return fixtures
        except Exception as e:
            self.logger.error(f"Error getting live fixtures for {league}: {str(e)}")
            return []

    # Removed deprecated fetch_and_save_daily_games method - use fetcher.py instead

    async def get_game_details(self, league: str, game_id: str) -> Optional[Dict]:
        """Get details for a specific game."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            game = await self.sports_api.get_event_details(league, game_id, today)
            return game
        except Exception as e:
            logger.error(f"Error getting game details: {str(e)}")
            return None

    async def get_league_standings(self, league: str) -> List[Dict]:
        """Get standings for a league."""
        try:
            standings = await self.sports_api.get_league_standings(league)
            return standings
        except Exception as e:
            logger.error(f"Error getting league standings: {str(e)}")
            return []

    async def get_upcoming_games_by_league(
        self, sport: str, league_name: str, limit: int = 10
    ) -> List[Dict]:
        """Get upcoming games for a specific sport and league."""
        try:
            # Map sport names to database sport values
            sport_mapping = {
                "football": "Football",
                "soccer": "Football",
                "basketball": "Basketball",
                "baseball": "Baseball",
                "hockey": "Hockey",
                "ice hockey": "Hockey",
                "ufc": "UFC",
                "mma": "UFC",
            }

            db_sport = sport_mapping.get(sport.lower(), sport.title())

            # Query the database for upcoming games
            query = """
                SELECT
                    id, api_game_id, sport, league_id, league_name,
                    home_team_name, away_team_name, start_time, status, venue,
                    home_team_id, away_team_id, score
                FROM api_games
                WHERE sport = %s
                AND UPPER(league_name) = UPPER(%s)
                AND start_time > NOW()
                AND status NOT IN ('Match Finished', 'Finished', 'FT', 'Ended', 'Game Finished', 'Final')
                ORDER BY start_time ASC
                LIMIT %s
            """

            games = await self.db.fetch_all(query, (db_sport, league_name, limit))

            if not games:
                logger.info(f"No upcoming games found for {sport} - {league_name}")
                return []

            logger.info(
                f"Found {len(games)} upcoming games for {sport} - {league_name}"
            )
            return games

        except Exception as e:
            logger.error(
                f"Error getting upcoming games for {sport} - {league_name}: {e}"
            )
            return []

    async def get_teams(self, league: str) -> List[str]:
        """Get teams for a league."""
        try:
            teams = await self.sports_api.get_teams(league)
            return teams
        except Exception as e:
            logger.error(f"Error getting teams: {str(e)}")
            return []

    async def get_team_logo(self, team_name: str, league: str) -> Optional[str]:
        """Get the file path for a team's logo."""
        try:
            logo_path = await self.sports_api.get_team_logo(team_name, league)
            return logo_path
        except Exception as e:
            logger.error(f"Error getting team logo: {str(e)}")
            return None

    async def get_league_schedule(
        self,
        sport: str,
        league_id: str,
        start_date: datetime,
        end_date: datetime,
        season: int = None,
    ) -> List[Dict]:
        """Get schedule for a league between start_date and end_date."""
        try:
            endpoint_map = {
                "football": "https://v3.football.api-sports.io/fixtures",
                "soccer": "https://v3.football.api-sports.io/fixtures",
                "basketball": "https://v1.basketball.api-sports.io/games",
                "nba": "https://v1.basketball.api-sports.io/games",
                "baseball": "https://v1.baseball.api-sports.io/games",
                "mlb": "https://v1.baseball.api-sports.io/games",
                "american-football": "https://v1.american-football.api-sports.io/games",
                "nfl": "https://v1.american-football.api-sports.io/games",
                "hockey": "https://v1.hockey.api-sports.io/games",
                "nhl": "https://v1.hockey.api-sports.io/games",
            }

            endpoint = endpoint_map.get(sport.lower())
            if not endpoint:
                logger.error(f"Unsupported sport: {sport}")
                return []

            headers = {"x-apisports-key": API_KEY}
            params = {
                "league": str(league_id),
                "season": (
                    str(season) if season else str(datetime.now(timezone.utc).year)
                ),
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
            }

            logger.info(f"Querying API: {endpoint} with params: {params}")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint, headers=headers, params=params
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            f"API request failed with status {resp.status}: {error_text}"
                        )
                        return []
                    response_data = await resp.json()

            games = response_data.get("response", [])
            logger.info(
                f"Found {len(games)} games for {sport} league {league_id} season {season}"
            )
            return games

        except Exception as e:
            logger.error(f"Error getting league schedule: {str(e)}")
            return []
