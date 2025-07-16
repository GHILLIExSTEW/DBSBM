"""
Multi-Provider API System
Handles different API providers for various sports including API-Sports, SportDevs, RapidAPI, etc.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

import aiohttp
import aiomysql

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API settings and database manager
from config.api_settings import API_KEY
from data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string to MySQL-compatible datetime object."""
    if not datetime_str:
        return None
    
    try:
        logger.debug(f"Parsing datetime string: {datetime_str}")
        
        # Handle ISO 8601 format with timezone
        if 'T' in datetime_str and '+' in datetime_str:
            # Remove timezone info and parse
            dt_part = datetime_str.split('+')[0]
            parsed_dt = datetime.fromisoformat(dt_part)
            logger.debug(f"Parsed datetime result: {parsed_dt}")
            return parsed_dt
        elif 'T' in datetime_str:
            # ISO format without timezone
            parsed_dt = datetime.fromisoformat(datetime_str)
            logger.debug(f"Parsed datetime result: {parsed_dt}")
            return parsed_dt
        else:
            # Try standard format
            parsed_dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            logger.debug(f"Parsed datetime result: {parsed_dt}")
            return parsed_dt
            
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{datetime_str}': {e}")
        return None

# API Providers and their configurations
API_PROVIDERS = {
    # API-Sports (existing)
    "api-sports": {
        "base_urls": {
            "football": "https://v3.football.api-sports.io",
            "basketball": "https://v1.basketball.api-sports.io",
            "baseball": "https://v1.baseball.api-sports.io",
            "hockey": "https://v1.hockey.api-sports.io",
            "american-football": "https://v1.american-football.api-sports.io",
            "rugby": "https://v1.rugby.api-sports.io",
            "volleyball": "https://v1.volleyball.api-sports.io",
            "handball": "https://v1.handball.api-sports.io",
            "afl": "https://v1.afl.api-sports.io",
            "formula-1": "https://v1.formula-1.api-sports.io",
            "mma": "https://v1.mma.api-sports.io",
        },
        "auth_type": "header",
        "auth_key": "x-apisports-key",
        "api_key": os.getenv("API_KEY"),
        "rate_limit": 30,  # calls per minute
    },
    
    # SportDevs (new)
    "sportdevs": {
        "base_urls": {
            "darts": "https://darts.sportdevs.com",
            "esports": "https://esports.sportdevs.com",
            "tennis": "https://tennis.sportdevs.com",
        },
        "auth_type": "none",  # No authentication required
        "rate_limit": 60,  # calls per minute
    },
    
    # RapidAPI Golf (new)
    "rapidapi-golf": {
        "base_urls": {
            "golf": "https://livegolfapi.p.rapidapi.com",
        },
        "auth_type": "rapidapi",
        "api_key": "10151b7417mshe26e052885bed6fp1cae61jsn60fa13b51c05",
        "rate_limit": 30,  # Reduced to be conservative
        "host": "livegolfapi.p.rapidapi.com",
    },
    # RapidAPI Darts (new)
    "rapidapi-darts": {
        "base_urls": {
            "darts": "https://darts-devs.p.rapidapi.com",
        },
        "auth_type": "rapidapi",
        "api_key": os.getenv("RAPIDAPI_KEY"),
        "rate_limit": 30,  # Reduced from 100 to 30 calls per minute
        "host": "darts-devs.p.rapidapi.com",
    },
    # RapidAPI Tennis (new)
    "rapidapi-tennis": {
        "base_urls": {
            "tennis": "https://tennis-devs.p.rapidapi.com",
        },
        "auth_type": "rapidapi",
        "api_key": os.getenv("RAPIDAPI_KEY"),
        "rate_limit": 100,
        "host": "tennis-devs.p.rapidapi.com",
    },
    
    # FlashLive Sports API for player data
    "flashlive-sports": {
        "base_urls": {
            "players": "https://flashlive-sports.p.rapidapi.com",
        },
        "auth_type": "rapidapi",
        "api_key": "10151b7417mshe26e052885bed6fp1cae61jsn60fa13b51c05",
        "rate_limit": 30,
        "host": "flashlive-sports.p.rapidapi.com",
    },
    
    # DataGolf API for golf data
    "datagolf": {
        "base_urls": {
            "golf": "https://feeds.datagolf.com",
        },
        "auth_type": "query_param",
        "api_key": "484918a5bad56c0451f96d2ea305",
        "rate_limit": 60,
    },
}

# Sport to provider mapping
SPORT_PROVIDER_MAP = {
    "football": "api-sports",
    "basketball": "api-sports",
    "baseball": "api-sports",
    "hockey": "api-sports",
    "american-football": "api-sports",
    "rugby": "api-sports",
    "volleyball": "api-sports",
    "handball": "api-sports",
    "afl": "api-sports",
    "formula-1": "api-sports",
    "mma": "api-sports",
    "darts": "rapidapi-darts",
    "esports": "sportdevs",
    "tennis": "rapidapi-tennis",
    "golf": "rapidapi-golf",
    "golf-players": "datagolf",
    "players": "flashlive-sports",
}

# Endpoint configurations for each sport/provider
ENDPOINT_CONFIGS = {
    # API-Sports endpoints
    "api-sports": {
        "football": {"leagues": "/leagues", "games": "/fixtures"},
        "basketball": {"leagues": "/leagues", "games": "/games"},
        "baseball": {"leagues": "/leagues", "games": "/games"},
        "hockey": {"leagues": "/leagues", "games": "/games"},
        "american-football": {"leagues": "/leagues", "games": "/games"},
        "rugby": {"leagues": "/leagues", "games": "/games"},
        "volleyball": {"leagues": "/leagues", "games": "/games"},
        "handball": {"leagues": "/leagues", "games": "/games"},
        "afl": {"leagues": "/leagues", "games": "/games"},
        "formula-1": {"leagues": "/leagues", "games": "/races"},
        "mma": {"leagues": "/leagues", "games": "/fights"},
    },
    
    # SportDevs endpoints
    "sportdevs": {
        "darts": {"leagues": "/tournaments", "games": "/matches"},
        "esports": {"leagues": "/tournaments", "games": "/matches"},
        "tennis": {"leagues": "/tournaments", "games": "/matches"},
    },
    
    # RapidAPI Golf endpoints
    "rapidapi-golf": {
        "golf": {"leagues": "/v1/events", "games": "/v1/events"},  # Golf uses events for both leagues and games
    },
    "rapidapi-darts": {
        "darts": {"leagues": "/tournaments-by-league", "games": "/matches-by-date", "seasons": "/seasons"},
    },
    "rapidapi-tennis": {
        "tennis": {"leagues": "/tournaments", "games": "/matches-by-date"},
    },
    
    # FlashLive Sports endpoints
    "flashlive-sports": {
        "players": {"player_data": "/v1/players/data"},
    },
    
    # DataGolf endpoints
    "datagolf": {
        "golf-players": {"player_list": "/get-player-list"},
    },
}


class MultiProviderRateLimiter:
    def __init__(self):
        self.limiters = {}
        for provider, config in API_PROVIDERS.items():
            self.limiters[provider] = {
                "calls": [],
                "limit": config.get("rate_limit", 30),
                "lock": asyncio.Lock()
            }

    async def acquire(self, provider: str):
        if provider not in self.limiters:
            return
        
        limiter = self.limiters[provider]
        async with limiter["lock"]:
            now = datetime.now().timestamp()
            # Remove calls older than 1 minute
            limiter["calls"] = [call for call in limiter["calls"] if now - call < 60]

            if len(limiter["calls"]) >= limiter["limit"]:
                # Wait until we can make another call
                sleep_time = 60 - (now - limiter["calls"][0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                limiter["calls"] = limiter["calls"][1:]

            limiter["calls"].append(now)


class MultiProviderAPI:
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.session = None
        self.rate_limiter = MultiProviderRateLimiter()
        self.discovered_leagues = {}
        
        # Verify API keys are available
        if not os.getenv("API_KEY"):
            logger.warning("API_KEY not found in environment variables - API-Sports features may not work")
        if not os.getenv("RAPIDAPI_KEY"):
            logger.warning("RAPIDAPI_KEY not found in environment variables - Golf features may not work")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_provider_for_sport(self, sport: str) -> str:
        """Get the API provider for a given sport."""
        return SPORT_PROVIDER_MAP.get(sport, "api-sports")

    def get_endpoint_config(self, sport: str) -> Dict:
        """Get endpoint configuration for a sport."""
        provider = self.get_provider_for_sport(sport)
        return ENDPOINT_CONFIGS.get(provider, {}).get(sport, {})

    async def make_request(self, sport: str, endpoint: str, params: Dict = None, provider_override: str = None) -> Dict:
        """Make a request to the appropriate API provider."""
        provider = provider_override if provider_override else self.get_provider_for_sport(sport)
        provider_config = API_PROVIDERS[provider]
        
        # Rate limiting
        await self.rate_limiter.acquire(provider)
        
        # Build URL
        base_url = provider_config["base_urls"].get(sport)
        if not base_url:
            raise ValueError(f"No base URL found for sport: {sport}")
        
        url = f"{base_url}{endpoint}"
        
        # Build headers
        headers = {"Accept": "application/json"}
        
        if provider_config["auth_type"] == "header":
            headers[provider_config["auth_key"]] = provider_config["api_key"]
        elif provider_config["auth_type"] == "rapidapi":
            headers["x-rapidapi-key"] = provider_config["api_key"]
            headers["x-rapidapi-host"] = provider_config.get("host", base_url.replace("https://", ""))
        elif provider_config["auth_type"] == "query_param":
            # Add API key as a query parameter
            if params is None:
                params = {}
            params["key"] = provider_config["api_key"]
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 429:  # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for {sport}, waiting...")
                    await asyncio.sleep(60)
                    return await self.make_request(sport, endpoint, params, provider_override)
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"API request failed for {sport}: {e}")
            raise

    async def discover_leagues(self, sport: str) -> List[Dict]:
        """Discover leagues for a specific sport."""
        endpoint_config = self.get_endpoint_config(sport)
        leagues_endpoint = endpoint_config.get("leagues")
        
        if not leagues_endpoint:
            logger.warning(f"No leagues endpoint configured for {sport}")
            return []
        
        try:
            provider = self.get_provider_for_sport(sport)
            
            if provider == "sportdevs":
                # Use SportDevs query builder for proper query syntax
                query = endpoint(leagues_endpoint).limit(50).build_url()
                data = await self.make_request(sport, query, None)
            elif provider == "rapidapi-darts":
                # For Darts Devs, we need to get tournaments by league
                # First, let's get some sample leagues to work with
                params = {
                    "offset": "0",
                    "limit": "50",
                    "lang": "en"
                }
                data = await self.make_request(sport, leagues_endpoint, params)
            elif provider == "rapidapi-tennis":
                # For Tennis Devs, get tournaments
                params = {
                    "offset": "0",
                    "limit": "50",
                    "lang": "en"
                }
                data = await self.make_request(sport, leagues_endpoint, params)
            elif provider == "rapidapi-golf":
                # Golf doesn't have a leagues endpoint, so we'll use events to get tournaments
                # Use a date range to get current/future events
                params = {
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": "2099-12-31"
                }
                data = await self.make_request(sport, leagues_endpoint, params)
            else:
                # API-Sports and others
                params = {"season": datetime.now().year}
                data = await self.make_request(sport, leagues_endpoint, params)
            
            # Handle different response formats
            if sport in ["esports", "tennis"]:
                # SportDevs format
                return self._parse_sportdevs_leagues(data, sport)
            elif sport == "golf":
                # RapidAPI Golf format
                return self._parse_rapidapi_golf_leagues(data, sport)
            elif sport == "darts":
                # RapidAPI Darts format
                return self._parse_rapidapi_darts_leagues(data, sport)
            elif sport == "tennis":
                # RapidAPI Tennis format
                return self._parse_rapidapi_tennis_leagues(data, sport)
            else:
                # API-Sports format
                return self._parse_apisports_leagues(data, sport)
                
        except Exception as e:
            logger.error(f"Error discovering leagues for {sport}: {e}")
            return []

    def _parse_apisports_leagues(self, data: Dict, sport: str) -> List[Dict]:
        """Parse API-Sports league response."""
        leagues = []
        for league_data in data.get("response", []):
            league = league_data.get("league", {})
            country = league_data.get("country", {})
            
            if league and league.get("id"):
                leagues.append({
                    "id": league["id"],
                    "name": league.get("name", ""),
                    "type": league.get("type", ""),
                    "logo": league.get("logo", ""),
                    "country": country.get("name", ""),
                    "country_code": country.get("code", ""),
                    "flag": country.get("flag", ""),
                    "season": datetime.now().year,
                    "sport": sport,
                    "provider": "api-sports"
                })
        return leagues

    def _parse_sportdevs_leagues(self, data: Dict, sport: str) -> List[Dict]:
        """Parse SportDevs league response (for Tennis, Esports)."""
        leagues = []
        tournaments = data if isinstance(data, list) else data.get("tournaments", [])
        for tournament in tournaments:
            leagues.append({
                "id": tournament.get("id"),
                "name": tournament.get("name", ""),
                "type": "tournament",
                "logo": tournament.get("logo", ""),
                "country": tournament.get("country", ""),
                "country_code": tournament.get("country_code", ""),
                "flag": tournament.get("flag", ""),
                "season": datetime.now().year,
                "sport": sport,
                "provider": "sportdevs"
            })
        return leagues

    def _parse_rapidapi_golf_leagues(self, data: Dict, sport: str) -> List[Dict]:
        """Parse RapidAPI Golf events to extract tournaments as leagues."""
        leagues = []
        
        # Golf API returns events, we'll extract unique tournaments
        events = data if isinstance(data, list) else data.get("events", [])
        
        # Create a set of unique tournaments
        tournaments = {}
        for event in events:
            tournament_id = event.get("tournament_id")
            tournament_name = event.get("tournament_name")
            
            if tournament_id and tournament_name:
                tournaments[tournament_id] = {
                    "id": tournament_id,
                    "name": tournament_name,
                    "type": "tournament",
                    "logo": "",
                    "country": event.get("country", ""),
                    "country_code": event.get("country_code", ""),
                    "flag": "",
                    "season": datetime.now().year,
                    "sport": sport,
                    "provider": "rapidapi-golf"
                }
        
        # Convert to list
        leagues = list(tournaments.values())
        return leagues

    def _parse_rapidapi_darts_leagues(self, data: Dict, sport: str) -> List[Dict]:
        """Parse RapidAPI Darts league response."""
        leagues = []
        tournaments = data if isinstance(data, list) else data.get("tournaments", [])
        for tournament in tournaments:
            leagues.append({
                "id": tournament.get("id"),
                "name": tournament.get("name", ""),
                "type": "tournament",
                "logo": tournament.get("logo", ""),
                "country": tournament.get("country", ""),
                "country_code": tournament.get("country_code", ""),
                "flag": tournament.get("flag", ""),
                "season": datetime.now().year,
                "sport": sport,
                "provider": "rapidapi-darts",
                "league_id": tournament.get("league_id", "")  # Store league_id for later use
            })
        return leagues

    def _parse_rapidapi_tennis_leagues(self, data: Dict, sport: str) -> List[Dict]:
        """Parse RapidAPI Tennis league response."""
        leagues = []
        tournaments = data if isinstance(data, list) else data.get("tournaments", [])
        for tournament in tournaments:
            leagues.append({
                "id": tournament.get("id"),
                "name": tournament.get("name", ""),
                "type": "tournament",
                "logo": tournament.get("logo", ""),
                "country": tournament.get("country", ""),
                "country_code": tournament.get("country_code", ""),
                "flag": tournament.get("flag", ""),
                "season": datetime.now().year,
                "sport": sport,
                "provider": "rapidapi-tennis"
            })
        return leagues

    async def fetch_player_data(self, sport_id: str, player_id: str, locale: str = "en_INT") -> Dict:
        """Fetch player data from FlashLive Sports API."""
        try:
            params = {
                "sport_id": sport_id,
                "player_id": player_id,
                "locale": locale
            }
            
            data = await self.make_request("players", "/v1/players/data", params)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching player data: {e}")
            return {}

    async def fetch_golf_players(self, file_format: str = "json") -> List[Dict]:
        """Fetch golf player list from DataGolf API."""
        try:
            params = {
                "file_format": file_format
            }
            
            data = await self.make_request("golf", "/get-player-list", params, provider_override="datagolf")
            return data if isinstance(data, list) else []
            
        except Exception as e:
            logger.error(f"Error fetching golf players: {e}")
            return {}

    async def fetch_games(self, sport: str, league: Dict, date: str) -> List[Dict]:
        """Fetch games for a specific league on a specific date or in the future."""
        endpoint_config = self.get_endpoint_config(sport)
        games_endpoint = endpoint_config.get("games")
        
        if not games_endpoint:
            logger.warning(f"No games endpoint configured for {sport}")
            return []
        
        try:
            provider = self.get_provider_for_sport(sport)
            today = datetime.now().strftime("%Y-%m-%d")
            
            if provider == "sportdevs":
                # For Tennis/Esports Devs, try to filter by date >= today if supported, else just by tournament_id
                # We'll use the query builder for flexibility
                qb = endpoint(games_endpoint).property("tournament_id").equals(league["id"]).limit(50)
                # Try to filter for today or future if supported
                qb = qb.property("date").greater_than_or_equal(today)
                query = qb.build_url()
                data = await self.make_request(sport, query, None)
            elif provider == "api-sports":
                params = {
                    "league": league["id"],
                    "season": league.get("season", datetime.now().year),
                    "date": date
                }
                data = await self.make_request(sport, games_endpoint, params)
            elif provider == "rapidapi-golf":
                # For Golf, use the events endpoint directly with date range
                params = {
                    "start_date": date,
                    "end_date": date  # Same date for single day
                }
                data = await self.make_request(sport, games_endpoint, params)
            elif provider == "rapidapi-darts":
                # For Darts Devs, use matches-by-date endpoint with proper parameters
                params = {
                    "offset": "0",
                    "limit": "50",
                    "lang": "en",
                    "date": f"eq.{date}"  # Use eq. prefix like other endpoints
                }
                data = await self.make_request(sport, games_endpoint, params)
            elif provider == "rapidapi-tennis":
                # For Tennis Devs, use matches-by-date endpoint with proper parameters
                params = {
                    "offset": "0",
                    "limit": "50",
                    "lang": "en",
                    "date": f"eq.{date}"  # Use eq. prefix like other endpoints
                }
                data = await self.make_request(sport, games_endpoint, params)
            else:
                data = await self.make_request(sport, games_endpoint, {})
            
            # Parse games based on provider
            if provider == "api-sports":
                return self._parse_apisports_games(data, sport, league)
            elif provider == "sportdevs":
                return self._parse_sportdevs_games(data, sport, league)
            elif provider == "rapidapi-golf":
                return self._parse_rapidapi_golf_games(data, sport, league)
            elif provider == "rapidapi-darts":
                return self._parse_rapidapi_darts_games(data, sport, league)
            elif provider == "rapidapi-tennis":
                return self._parse_rapidapi_tennis_games(data, sport, league)
            
        except Exception as e:
            logger.error(f"Error fetching games for {sport}/{league['name']}: {e}")
            return []

    def _parse_apisports_games(self, data: Dict, sport: str, league: Dict) -> List[Dict]:
        """Parse API-Sports games response."""
        games = []
        for game in data.get("response", []):
            mapped_game = self._map_apisports_game(game, sport, league)
            if mapped_game:
                games.append(mapped_game)
        return games

    def _parse_sportdevs_games(self, data: Dict, sport: str, league: Dict) -> List[Dict]:
        """Parse SportDevs games response."""
        games = []
        # This is a placeholder - adjust based on actual SportDevs response structure
        for game in data.get("matches", []):
            mapped_game = self._map_sportdevs_game(game, sport, league)
            if mapped_game:
                games.append(mapped_game)
        return games

    def _parse_rapidapi_golf_games(self, data: Dict, sport: str, league: Dict) -> List[Dict]:
        """Parse RapidAPI Golf events response."""
        games = []
        
        # Golf API returns events directly
        events = data if isinstance(data, list) else data.get("events", [])
        
        for event in events:
            mapped_game = self._map_rapidapi_golf_game(event, sport, league)
            if mapped_game:
                games.append(mapped_game)
        
        return games

    def _parse_rapidapi_darts_games(self, data: Dict, sport: str, league: Dict) -> List[Dict]:
        """Parse RapidAPI Darts games response."""
        games = []
        
        # Handle the nested structure where each item has a 'matches' array
        if isinstance(data, list):
            for date_group in data:
                if isinstance(date_group, dict) and 'matches' in date_group:
                    # This is a date group with matches
                    for game in date_group['matches']:
                        mapped_game = self._map_rapidapi_darts_game(game, sport, league)
                        if mapped_game:
                            games.append(mapped_game)
                else:
                    # This is a direct match
                    mapped_game = self._map_rapidapi_darts_game(date_group, sport, league)
                    if mapped_game:
                        games.append(mapped_game)
        else:
            # Handle dictionary response
            matches = data.get("matches", [])
            for game in matches:
                mapped_game = self._map_rapidapi_darts_game(game, sport, league)
                if mapped_game:
                    games.append(mapped_game)
        
        return games

    def _parse_rapidapi_tennis_games(self, data: Dict, sport: str, league: Dict) -> List[Dict]:
        """Parse RapidAPI Tennis games response."""
        games = []
        
        # Handle the nested structure where each item has a 'matches' array
        if isinstance(data, list):
            for date_group in data:
                if isinstance(date_group, dict) and 'matches' in date_group:
                    # This is a date group with matches
                    for game in date_group['matches']:
                        mapped_game = self._map_rapidapi_tennis_game(game, sport, league)
                        if mapped_game:
                            games.append(mapped_game)
                else:
                    # This is a direct match
                    mapped_game = self._map_rapidapi_tennis_game(date_group, sport, league)
                    if mapped_game:
                        games.append(mapped_game)
        else:
            # Handle dictionary response
            matches = data.get("matches", [])
            for game in matches:
                mapped_game = self._map_rapidapi_tennis_game(game, sport, league)
                if mapped_game:
                    games.append(mapped_game)
        
        return games

    def _map_apisports_game(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map API-Sports game data to standard format."""
        try:
            if sport == "football":
                return {
                    "api_game_id": str(game["fixture"]["id"]),
                    "sport": "Football",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["fixture"]["date"],
                    "status": game["fixture"]["status"]["long"],
                    "score": {
                        "home": game["goals"]["home"] if "goals" in game else None,
                        "away": game["goals"]["away"] if "goals" in game else None
                    } if "goals" in game else None,
                    "venue": game["fixture"]["venue"]["name"] if "venue" in game["fixture"] else None,
                    "provider": "api-sports"
                }
            # Add more sport-specific mappings as needed
            else:
                return {
                    "api_game_id": str(game.get("id", "")),
                    "sport": sport.title(),
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game.get("teams", {}).get("home", {}).get("name", ""),
                    "away_team_name": game.get("teams", {}).get("away", {}).get("name", ""),
                    "start_time": game.get("date", ""),
                    "status": game.get("status", {}).get("long", ""),
                    "score": None,
                    "venue": game.get("venue", {}).get("name", ""),
                    "provider": "api-sports"
                }
        except Exception as e:
            logger.error(f"Error mapping API-Sports game: {e}")
            return None

    def _map_sportdevs_game(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map SportDevs game data to standard format."""
        try:
            # This is a placeholder - adjust based on actual SportDevs response structure
            return {
                "api_game_id": str(game.get("id", "")),
                "sport": sport.title(),
                "league_id": str(league["id"]),
                "league_name": league["name"],
                "home_team_name": game.get("home", {}).get("name", ""),
                "away_team_name": game.get("away", {}).get("name", ""),
                "start_time": game.get("date", ""),
                "status": game.get("status", ""),
                "score": None,
                "venue": game.get("venue", ""),
                "provider": "sportdevs"
            }
        except Exception as e:
            logger.error(f"Error mapping SportDevs game: {e}")
            return None

    def _map_rapidapi_golf_game(self, event: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map RapidAPI Golf event data to standard format."""
        try:
            return {
                "api_game_id": str(event.get("id", "")),
                "sport": sport.title(),
                "league_id": str(event.get("tour", {}).get("id", "")),
                "league_name": event.get("tour", {}).get("name", ""),
                "home_team_name": event.get("name", ""),  # Tournament name
                "away_team_name": "",  # Golf doesn't have away teams
                "start_time": event.get("startDatetime", ""),
                "end_time": event.get("endDatetime", ""),
                "status": event.get("status", "upcoming"),
                "score": None,  # Golf scoring is different
                "venue": event.get("course", ""),
                "location": event.get("location", ""),
                "logo": event.get("logoUrl", ""),
                "provider": "rapidapi-golf"
            }
        except Exception as e:
            logger.error(f"Error mapping RapidAPI Golf event: {e}")
            return None

    def _map_rapidapi_darts_game(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map RapidAPI Darts game data to standard format."""
        try:
            return {
                "api_game_id": str(game.get("id", "")),
                "sport": sport.title(),
                "league_id": str(game.get("league_id", league["id"])),
                "league_name": game.get("league_name", league["name"]),
                "home_team_name": game.get("home_team_name", ""),
                "away_team_name": game.get("away_team_name", ""),
                "start_time": game.get("start_time", ""),
                "status": game.get("status", ""),
                "score": {
                    "home": game.get("home_team_score", ""),
                    "away": game.get("away_team_score", "")
                } if game.get("home_team_score") or game.get("away_team_score") else None,
                "venue": game.get("venue", ""),
                "provider": "rapidapi-darts"
            }
        except Exception as e:
            logger.error(f"Error mapping RapidAPI Darts game: {e}")
            return None

    def _map_rapidapi_tennis_game(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map RapidAPI Tennis game data to standard format."""
        try:
            return {
                "api_game_id": str(game.get("id", "")),
                "sport": sport.title(),
                "league_id": str(game.get("league_id", league["id"])),
                "league_name": game.get("league_name", league["name"]),
                "home_team_name": game.get("home_team_name", ""),
                "away_team_name": game.get("away_team_name", ""),
                "start_time": game.get("start_time", ""),
                "status": game.get("status", ""),
                "score": {
                    "home": game.get("home_team_score", ""),
                    "away": game.get("away_team_score", "")
                } if game.get("home_team_score") or game.get("away_team_score") else None,
                "venue": game.get("venue", ""),
                "provider": "rapidapi-tennis"
            }
        except Exception as e:
            logger.error(f"Error mapping RapidAPI Tennis game: {e}")
            return None

    async def discover_all_leagues(self) -> Dict[str, List[Dict]]:
        """Discover all leagues from all providers."""
        logger.info("Starting multi-provider league discovery...")
        
        all_leagues = {}
        
        for sport in SPORT_PROVIDER_MAP.keys():
            try:
                logger.info(f"Discovering leagues for {sport}...")
                leagues = await self.discover_leagues(sport)
                if leagues:
                    all_leagues[sport] = leagues
                    logger.info(f"Found {len(leagues)} leagues for {sport}")
                else:
                    logger.warning(f"No leagues found for {sport}")
                
                # Rate limiting between sports
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error discovering leagues for {sport}: {e}")
                continue
        
        self.discovered_leagues = all_leagues
        logger.info(f"Multi-provider league discovery completed. Found leagues for {len(all_leagues)} sports")
        return all_leagues

    async def fetch_all_leagues_data(self, date: str = None, next_days: int = 2) -> Dict[str, int]:
        """Fetch data for ALL discovered leagues from all providers."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Starting multi-provider fetch for {date} and next {next_days} days")
        
        # Define the leagues we actually want to fetch (major leagues only)
        TARGET_LEAGUES = {
            "football": [
                "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1", 
                "MLS", "UEFA Champions League", "UEFA Europa League", "Brazil Serie A",
                "FIFA World Cup", "Allsvenskan", "Superettan"
            ],
            "basketball": ["NBA", "WNBA", "EuroLeague"],
            "baseball": ["MLB", "NPB", "KBO"],
            "hockey": ["NHL", "Kontinental Hockey League"],
            "american-football": ["NFL", "NCAA Football", "CFL"],
            "rugby": ["Super Rugby", "Six Nations Championship"],
            "tennis": ["ATP Tour", "WTA Tour"],
            "golf": ["PGA Tour", "LPGA Tour"],
            "mma": ["UFC", "Bellator MMA"],
            "darts": ["Professional Darts Corporation"]
        }
        
        results = {
            "total_leagues": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_games": 0
        }
        
        for sport, leagues in self.discovered_leagues.items():
            logger.info(f"Processing {len(leagues)} leagues for {sport}")
            
            # Filter to only target leagues
            target_league_names = TARGET_LEAGUES.get(sport, [])
            filtered_leagues = []
            
            for league in leagues:
                if any(target_name.lower() in league.get('name', '').lower() for target_name in target_league_names):
                    filtered_leagues.append(league)
                    logger.info(f"Including league: {league.get('name')}")
            
            logger.info(f"Filtered to {len(filtered_leagues)} target leagues for {sport}")
            
            for league in filtered_leagues:
                results["total_leagues"] += 1
                
                try:
                    # Fetch for multiple days
                    for day_offset in range(next_days):
                        fetch_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                        
                        games = await self.fetch_games(sport, league, fetch_date)
                        
                        if games:
                            results["total_games"] += len(games)
                            logger.info(f"Fetched {len(games)} games for {league['name']} on {fetch_date}")
                            
                            # Save games to database if db_pool is available
                            if self.db_pool:
                                logger.info(f"Saving {len(games)} games to database for {league['name']}")
                                for game in games:
                                    success = await self._save_game_to_db(game)
                                    if success:
                                        logger.debug(f"Successfully saved game {game.get('api_game_id')} to database")
                                    else:
                                        logger.error(f"Failed to save game {game.get('api_game_id')} to database")
                            else:
                                logger.warning("No database pool available, skipping database save")
                        
                        # Rate limiting between requests
                        await asyncio.sleep(1.5)
                    
                    results["successful_fetches"] += 1
                    
                except Exception as e:
                    results["failed_fetches"] += 1
                    logger.error(f"Failed to fetch data for {league['name']}: {e}")
                    continue
        
        logger.info(f"Multi-provider fetch completed: {results}")
        return results

    async def _save_game_to_db(self, game_data: Dict) -> bool:
        """Save game data to the database."""
        logger.debug(f"Attempting to save game to database: {game_data.get('api_game_id')}")
        
        if not self.db_pool:
            logger.warning("No database pool available")
            return False
            
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Check if game already exists
                    await cur.execute(
                        "SELECT api_game_id FROM api_games WHERE api_game_id = %s",
                        (game_data["api_game_id"],)
                    )
                    
                    # Prepare raw_json data and fetched_at timestamp
                    raw_json = json.dumps(game_data)
                    fetched_at = datetime.now()
                    
                    # Parse datetime strings
                    start_time = parse_datetime(game_data.get("start_time"))
                    end_time = parse_datetime(game_data.get("end_time"))
                    
                    logger.debug(f"Original start_time: {game_data.get('start_time')}")
                    logger.debug(f"Parsed start_time: {start_time}")
                    logger.debug(f"Original end_time: {game_data.get('end_time')}")
                    logger.debug(f"Parsed end_time: {end_time}")
                    
                    if await cur.fetchone():
                        # Update existing game
                        await cur.execute("""
                            UPDATE api_games SET 
                                sport = %s, league_id = %s, league_name = %s, 
                                home_team_id = %s, away_team_id = %s,
                                home_team_name = %s, away_team_name = %s,
                                start_time = %s, end_time = %s, status = %s, 
                                score = %s, venue = %s, referee = %s, season = %s,
                                raw_json = %s, fetched_at = %s
                            WHERE api_game_id = %s
                        """, (
                            game_data.get("sport"), game_data.get("league_id"), 
                            game_data.get("league_name"), game_data.get("home_team_id"),
                            game_data.get("away_team_id"), game_data.get("home_team_name"),
                            game_data.get("away_team_name"), start_time, end_time,
                            game_data.get("status"), json.dumps(game_data.get("score")) if game_data.get("score") else None,
                            game_data.get("venue"), game_data.get("referee"),
                            game_data.get("season"), raw_json, fetched_at,
                            game_data["api_game_id"]
                        ))
                    else:
                        # Insert new game
                        await cur.execute("""
                            INSERT INTO api_games (
                                api_game_id, sport, league_id, league_name, home_team_id,
                                away_team_id, home_team_name, away_team_name, start_time,
                                end_time, status, score, venue, referee, season,
                                raw_json, fetched_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            game_data["api_game_id"], game_data.get("sport"),
                            game_data.get("league_id"), game_data.get("league_name"),
                            game_data.get("home_team_id"), game_data.get("away_team_id"),
                            game_data.get("home_team_name"), game_data.get("away_team_name"),
                            start_time, end_time, game_data.get("status"),
                            json.dumps(game_data.get("score")) if game_data.get("score") else None,
                            game_data.get("venue"), game_data.get("referee"),
                            game_data.get("season"), raw_json, fetched_at
                        ))
                    
                    await conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving game to database: {e}")
            return False 