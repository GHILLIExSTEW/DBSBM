import logging
import os
from typing import Dict, List, Optional

import aiohttp
from config.leagues import ENDPOINTS, LEAGUE_IDS, get_current_season
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
logger = logging.getLogger(__name__)

# API-Sports endpoints
ENDPOINTS = {
    "baseball": "https://v1.baseball.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "nba": "https://v1.basketball.api-sports.io",  # Alias for basketball
    "american-football": "https://v1.american-football.api-sports.io",
    "nfl": "https://v1.american-football.api-sports.io",  # Alias for american-football
    "hockey": "https://v1.hockey.api-sports.io",
    "football": "https://v3.football.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "afl": "https://v1.afl.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
    # Note: tennis, golf, and darts APIs may not be available
    # "tennis": "https://v1.tennis.api-sports.io",
    # "golf": "https://v1.golf.api-sports.io",
    # "darts": "https://v1.darts.api-sports.io",
}

# Expanded ENDPOINTS_MAP to include all requested sports
ENDPOINTS_MAP = {
    "afl": {
        "base": "https://v1.afl.api-sports.io",
        "leagues": "/leagues",
        "seasons": "/seasons",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "odds": "/odds",
    },
    "baseball": {
        "base": "https://v1.baseball.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "basketball": {
        "base": "https://v1.basketball.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "nba": {
        "base": "https://v1.basketball.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "football": {
        "base": "https://v3.football.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "fixtures": "/fixtures",
        "standings": "/standings",
        "topscorers": "/players/topscorers",
        "topassists": "/players/topassists",
        "topcards": "/players/topcards",
        "injuries": "/injuries",
        "coachs": "/coachs",
        "venues": "/venues",
        "transfers": "/transfers",
        "odds": "/odds",
        "predictions": "/predictions",
        "sidelined": "/sidelined",
        "trophies": "/trophies",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
        "lineups": "/fixtures/lineups",
        "statistics_fixtures": "/fixtures/statistics",
        "statistics_players": "/players/statistics",
        "players_squads": "/players/squads",
        "fixtures_headtohead": "/fixtures/headtohead",
        "fixtures_players": "/fixtures/players",
        "fixtures_statistics": "/fixtures/statistics",
        "fixtures_events": "/fixtures/events",
        "fixtures_lineups": "/fixtures/lineups",
        "fixtures_odds": "/fixtures/odds",
        "fixtures_predictions": "/fixtures/predictions",
        "fixtures_sidelined": "/fixtures/sidelined",
    },
    "formula-1": {
        "base": "https://v1.formula-1.api-sports.io",
        "leagues": "/leagues",
        "seasons": "/seasons",
        "circuits": "/circuits",
        "races": "/races",
        "drivers": "/drivers",
        "teams": "/teams",
        "standings": "/standings",
        "status": "/status",
        "countries": "/countries",
        "timezone": "/timezone",
        "odds": "/odds",
    },
    "american-football": {
        "base": "https://v1.american-football.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "handball": {
        "base": "https://v1.handball.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "hockey": {
        "base": "https://v1.hockey.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "mma": {
        "base": "https://v1.mma.api-sports.io",
        "leagues": "/leagues",
        "seasons": "/seasons",
        "events": "/events",
        "fights": "/fights",
        "fighters": "/fighters",
        "countries": "/countries",
        "odds": "/odds",
        "status": "/status",
        "timezone": "/timezone",
    },
    "nfl": {
        "base": "https://v1.american-football.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "rugby": {
        "base": "https://v1.rugby.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
    "volleyball": {
        "base": "https://v1.volleyball.api-sports.io",
        "leagues": "/leagues",
        "teams": "/teams",
        "players": "/players",
        "games": "/games",
        "standings": "/standings",
        "odds": "/odds",
        "statistics": "/statistics",
        "venues": "/venues",
        "countries": "/countries",
        "timezone": "/timezone",
        "status": "/status",
        "events": "/events",
    },
}


class APISportsClient:
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the API-Sports API."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {"x-apisports-key": self.api_key}
        try:
            async with self.session.get(
                endpoint, headers=headers, params=params
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(
                        f"API request failed with status {resp.status}: {error_text}"
                    )
                return await resp.json()
        except Exception as e:
            logger.error(f"Error making API request to {endpoint}: {str(e)}")
            raise

    async def get_games(self, league: str, date: str) -> List[Dict]:
        """Get games for a specific league and date."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")

        sport = league_info["sport"]
        league_id = league_info["id"]
        base_endpoint = ENDPOINTS.get(sport)
        if not base_endpoint:
            raise ValueError(f"Unsupported sport: {sport}")

        endpoint = f"{base_endpoint}/{'fixtures' if sport == 'football' else 'games'}"
        params = {
            "league": league_id,
            "date": date,
            "season": get_current_season(league),
        }

        data = await self._make_request(endpoint, params)
        return data.get("response", [])

    async def get_teams(self, league: str) -> List[Dict]:
        """Get teams for a specific league."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")

        sport = league_info["sport"]
        league_id = league_info["id"]
        base_endpoint = ENDPOINTS.get(sport)
        if not base_endpoint:
            raise ValueError(f"Unsupported sport: {sport}")

        endpoint = f"{base_endpoint}/teams"
        params = {"league": league_id, "season": get_current_season(league)}

        data = await self._make_request(endpoint, params)
        return data.get("response", [])

    async def get_standings(self, league: str) -> List[Dict]:
        """Get standings for a specific league."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")

        sport = league_info["sport"]
        league_id = league_info["id"]
        base_endpoint = ENDPOINTS.get(sport)
        if not base_endpoint:
            raise ValueError(f"Unsupported sport: {sport}")

        endpoint = f"{base_endpoint}/standings"
        params = {"league": league_id, "season": get_current_season(league)}

        data = await self._make_request(endpoint, params)
        return data.get("response", [])

    def build_full_url(self, sport: str, operation: str) -> str:
        """Build a full URL for a given sport and operation."""
        if sport not in ENDPOINTS_MAP:
            raise ValueError(f"Unsupported sport: {sport}")
        if operation not in ENDPOINTS_MAP[sport]:
            raise ValueError(f"Unsupported operation: {operation}")
        return f"{ENDPOINTS_MAP[sport]['base']}{ENDPOINTS_MAP[sport][operation]}"

    async def get_games_with_full_url(self, league: str, date: str) -> List[Dict]:
        """Get games for a specific league and date using the full URL."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")
        full_url = self.build_full_url(
            league_info["sport"],
            "fixtures" if league_info["sport"] == "football" else "games",
        )
        params = {
            "league": league_info["id"],
            "date": date,
            "season": get_current_season(league),
        }
        data = await self._make_request(full_url, params)
        return data.get("response", [])

    async def get_teams_with_full_url(self, league: str) -> List[Dict]:
        """Get teams for a specific league using the full URL."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")
        full_url = self.build_full_url(league_info["sport"], "teams")
        params = {"league": league_info["id"], "season": get_current_season(league)}
        data = await self._make_request(full_url, params)
        return data.get("response", [])

    async def get_standings_with_full_url(self, league: str) -> List[Dict]:
        """Get standings for a specific league using the full URL."""
        league_info = LEAGUE_IDS.get(league)
        if not league_info:
            raise ValueError(f"Unsupported league: {league}")
        full_url = self.build_full_url(league_info["sport"], "standings")
        params = {"league": league_info["id"], "season": get_current_season(league)}
        data = await self._make_request(full_url, params)
        return data.get("response", [])
