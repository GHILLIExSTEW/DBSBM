# REV 1.0.0 - Enhanced logging for API requests and game data processing
# api/sports_api.py
# Service for fetching sports data from TheSportsDB API

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import aiohttp
from dotenv import load_dotenv

# Import LEAGUE_IDS for league mapping
from config.leagues import LEAGUE_IDS

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API-Sports Base URLs
BASE_URLS = {
    "football": "https://v3.football.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "baseball": "https://v1.baseball.api-sports.io",
    "hockey": "https://v1.hockey.api-sports.io",
    "american-football": "https://v1.american-football.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "tennis": "https://v1.tennis.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
}

# League configurations with proper IDs and endpoints
LEAGUE_CONFIG = {
    # Football (Soccer)
    "football": {
        "EPL": {"id": 39, "name": "Premier League"},
        "LaLiga": {"id": 140, "name": "La Liga"},
        "Bundesliga": {"id": 78, "name": "Bundesliga"},
        "SerieA": {"id": 135, "name": "Serie A"},
        "Ligue1": {"id": 61, "name": "Ligue 1"},
        "MLS": {"id": 253, "name": "Major League Soccer"},
        "ChampionsLeague": {"id": 2, "name": "UEFA Champions League"},
        "EuropaLeague": {"id": 3, "name": "UEFA Europa League"},
        "Brazil_Serie_A": {"id": 71, "name": "Brazil Serie A"},
        "WorldCup": {"id": 15, "name": "FIFA World Cup"},
    },
    # Basketball
    "basketball": {
        "NBA": {"id": 12, "name": "National Basketball Association"},
        "WNBA": {"id": 13, "name": "Women's National Basketball Association"},
        "EuroLeague": {"id": 1, "name": "EuroLeague"},
    },
    # Baseball
    "baseball": {
        "MLB": {"id": 1, "name": "Major League Baseball"},
        "NPB": {"id": 2, "name": "Nippon Professional Baseball"},
        "KBO": {"id": 3, "name": "Korea Baseball Organization"},
    },
    # Hockey
    "hockey": {
        "NHL": {"id": 57, "name": "National Hockey League"},
        "KHL": {"id": 1, "name": "Kontinental Hockey League"},
    },
    # American Football
    "american-football": {
        "NFL": {"id": 1, "name": "National Football League"},
        "NCAA": {"id": 2, "name": "NCAA Football"},
    },
    # Rugby
    "rugby": {
        "SuperRugby": {"id": 1, "name": "Super Rugby"},
        "SixNations": {"id": 2, "name": "Six Nations Championship"},
    },
    # Volleyball
    "volleyball": {"FIVB": {"id": 1, "name": "FIVB World League"}},
    # Handball
    "handball": {"EHF": {"id": 1, "name": "EHF Champions League"}},
    # Tennis
    "tennis": {
        "ATP": {"id": 1, "name": "ATP Tour"},
        "WTA": {"id": 2, "name": "WTA Tour"},
        "GrandSlam": {"id": 3, "name": "Grand Slam"},
    },
    # Formula 1
    "formula-1": {"F1": {"id": 1, "name": "Formula 1"}},
    # MMA
    "mma": {
        "UFC": {"id": 1, "name": "Ultimate Fighting Championship"},
        "Bellator": {"id": 2, "name": "Bellator MMA"},
    },
}


class APISportsRateLimiter:
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [call for call in self.calls if now - call < 60]

            if len(self.calls) >= self.calls_per_minute:
                # Wait until we can make another call
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.calls = self.calls[1:]

            self.calls.append(now)


class APISportsFetcher:
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")

        self.rate_limiter = APISportsRateLimiter()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_data(
        self, sport: str, endpoint: str, params: Dict[str, Any]
    ) -> Dict:
        """Generic method to fetch data from API-Sports."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use async with context manager."
            )

        base_url = BASE_URLS.get(sport)
        if not base_url:
            raise ValueError(f"Unsupported sport: {sport}")

        url = f"{base_url}/{endpoint}"
        headers = {"x-apisports-key": self.api_key}

        await self.rate_limiter.acquire()

        try:
            async with self.session.get(
                url, headers=headers, params=params
            ) as response:
                if response.status == 429:  # Rate limit exceeded
                    logger.warning("Rate limit exceeded. Waiting before retry...")
                    await asyncio.sleep(60)  # Wait a minute before retry
                    return await self.fetch_data(sport, endpoint, params)

                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def map_game_data(self, game: Dict, sport: str, league: str) -> Dict:
        """Map API-Sports game data to our standard format."""
        try:
            if sport == "football":
                # Get league_id from LEAGUE_IDS to check for Brazil Serie A
                league_id = LEAGUE_IDS.get(league, {}).get("id", "")

                # Force league_name for Brazil Serie A and Italian Serie A
                if str(league_id) == "71":
                    league_name_final = "Brazil Serie A"
                elif str(league_id) == "135":
                    league_name_final = "Serie A"
                else:
                    league_name_final = LEAGUE_CONFIG["football"][league]["name"]

                return {
                    "id": str(game["fixture"]["id"]),
                    "sport": "Football",
                    "league": league_name_final,
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["fixture"]["date"],
                    "status": game["fixture"]["status"]["long"],
                    "score": (
                        {"home": game["goals"]["home"], "away": game["goals"]["away"]}
                        if "goals" in game
                        else None
                    ),
                    "venue": (
                        game["fixture"]["venue"]["name"]
                        if "venue" in game["fixture"]
                        else None
                    ),
                }
            elif sport == "basketball":
                return {
                    "id": str(game["id"]),
                    "sport": "Basketball",
                    "league": LEAGUE_CONFIG["basketball"][league]["name"],
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["date"],
                    "status": game["status"]["long"],
                    "score": (
                        {
                            "home": game["scores"]["home"]["total"],
                            "away": game["scores"]["away"]["total"],
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                }
            elif sport in ["baseball", "mlb"]:
                return {
                    "id": str(game["id"]),
                    "sport": "Baseball",
                    "league": LEAGUE_CONFIG["baseball"][league]["name"],
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["date"],
                    "status": game["status"]["long"],
                    "score": (
                        {
                            "home": game["scores"]["home"]["total"],
                            "away": game["scores"]["away"]["total"],
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                }
            elif sport in ["hockey", "nhl"]:
                return {
                    "id": str(game["id"]),
                    "sport": "Hockey",
                    "league": LEAGUE_CONFIG["hockey"][league]["name"],
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["date"],
                    "status": game["status"]["long"],
                    "score": (
                        {
                            "home": game["scores"]["home"]["total"],
                            "away": game["scores"]["away"]["total"],
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                }
            elif sport in ["mma", "ufc", "bellator"]:
                return {
                    "id": str(game["id"]),
                    "sport": "MMA",
                    "league": LEAGUE_CONFIG["mma"][league]["name"],
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["date"],
                    "status": game["status"]["long"],
                    "score": (
                        {
                            "home": game["scores"]["home"]["total"],
                            "away": game["scores"]["away"]["total"],
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                    "referee": game.get("referee"),
                }
            elif sport in ["formula-1", "f1"]:
                return {
                    "id": str(game["id"]),
                    "sport": "Formula 1",
                    "league": LEAGUE_CONFIG["formula-1"][league]["name"],
                    "home_team": game["teams"]["home"]["name"],
                    "away_team": game["teams"]["away"]["name"],
                    "start_time": game["date"],
                    "status": game["status"]["long"],
                    "score": (
                        {
                            "home": game["scores"]["home"]["total"],
                            "away": game["scores"]["away"]["total"],
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                }
            else:
                # Generic mapping for other sports
                return {
                    "id": str(game.get("id", game.get("fixture", {}).get("id", ""))),
                    "sport": sport.title(),
                    "league": LEAGUE_CONFIG.get(sport, {})
                    .get(league, {})
                    .get("name", league),
                    "home_team": game.get("teams", {})
                    .get("home", {})
                    .get("name", "Unknown"),
                    "away_team": game.get("teams", {})
                    .get("away", {})
                    .get("name", "Unknown"),
                    "start_time": game.get(
                        "date", game.get("fixture", {}).get("date", "")
                    ),
                    "status": game.get("status", {}).get(
                        "long",
                        game.get("fixture", {})
                        .get("status", {})
                        .get("long", "Unknown"),
                    ),
                    "score": (
                        {
                            "home": game.get("scores", {})
                            .get("home", {})
                            .get("total", game.get("goals", {}).get("home", 0)),
                            "away": game.get("scores", {})
                            .get("away", {})
                            .get("total", game.get("goals", {}).get("away", 0)),
                        }
                        if any(key in game for key in ["scores", "goals"])
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name"),
                }
        except Exception as e:
            logger.error(f"Error mapping game data: {str(e)}")
            return None


class SportsAPI:
    def __init__(self, db_manager=None):
        self.fetcher = None
        self.current_year = datetime.now().year
        self.split_season = (
            self.current_year - 1 if datetime.now().month < 7 else self.current_year
        )
        self.db_manager = db_manager
        self.live_updates_enabled = False  # Default to disabled
        self._update_task = None
        logger.debug(
            "SportsAPI initialized with API-Sports integration"
        )  # Changed from info to debug

    async def __aenter__(self):
        self.fetcher = await APISportsFetcher().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.fetcher:
            await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    def toggle_live_updates(self, enabled: bool = None) -> bool:
        """
        Toggle live updates on/off. If no value is provided, it will toggle the current state.
        Returns the new state of live updates.
        """
        if enabled is None:
            self.live_updates_enabled = not self.live_updates_enabled
        else:
            self.live_updates_enabled = enabled

        if self.live_updates_enabled:
            logger.info("Live updates enabled")
            if not self._update_task or self._update_task.done():
                self._update_task = asyncio.create_task(self._run_live_updates())
        else:
            logger.info("Live updates disabled")
            if self._update_task and not self._update_task.done():
                self._update_task.cancel()

        return self.live_updates_enabled

    async def _run_live_updates(self):
        """Background task to fetch live updates periodically."""
        try:
            while self.live_updates_enabled:
                try:
                    await self.fetch_and_save_daily_games()
                    logger.info("Completed live update cycle")
                except Exception as e:
                    logger.error(f"Error in live update cycle: {str(e)}")

                # Wait for 5 minutes before next update
                await asyncio.sleep(300)  # 5 minutes
        except asyncio.CancelledError:
            logger.info("Live updates task cancelled")
        except Exception as e:
            logger.error(f"Live updates task failed: {str(e)}")
            self.live_updates_enabled = False

    async def fetch_games(
        self,
        sport: str,
        league: str,
        date: str = None,
        season: int = None,
        next_games: int = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Fetch games for a specific sport and league."""
        logger.info(
            f"[fetch_games] Starting fetch for sport={sport}, league={league}, date={date}, season={season}"
        )

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"[fetch_games] No date provided, using current date: {date}")

        league_config = LEAGUE_CONFIG.get(sport.lower(), {}).get(league)
        if not league_config:
            logger.error(
                f"[fetch_games] Unsupported sport/league combination: {sport}/{league}"
            )
            raise ValueError(f"Unsupported sport/league combination: {sport}/{league}")

        # If season is provided, use it directly
        if season is None:
            # For MLB, use the current year as the season
            if sport.lower() == "baseball" and league == "MLB":
                season = datetime.now().year
                # If we're in the offseason (October to February), use next year
                if datetime.now().month >= 10 or datetime.now().month <= 2:
                    season += 1
                logger.info(
                    f"[fetch_games] MLB: Using season {season} (calculated based on current date)"
                )
            else:
                season = datetime.now().year
                logger.info(
                    f"[fetch_games] Non-MLB: Using current year as season: {season}"
                )

        # Restrict season to current year or next year
        current_year = datetime.now().year
        next_year = current_year + 1
        if season not in [current_year, next_year]:
            logger.error(
                f"[fetch_games] Invalid season: {season}. Allowed seasons are {current_year} and {next_year}."
            )
            raise ValueError(
                f"Invalid season: {season}. Allowed seasons are {current_year} and {next_year}."
            )

        params = {"league": league_config["id"], "season": season, "date": date}

        if next_games:
            params["next"] = next_games
        if end_date:
            params["to"] = end_date

        # Debug logging for all sports requests
        logger.info(f"[fetch_games] {sport.title()} request parameters: {params}")
        logger.info(
            f"[fetch_games] Request URL: {BASE_URLS[sport.lower()]}/{'fixtures' if sport.lower() == 'football' else 'games'}"
        )
        logger.info(f"[fetch_games] League config: {league_config}")

        try:
            endpoint = "fixtures" if sport.lower() == "football" else "games"

            # Create fetcher if not exists
            if not self.fetcher:
                logger.info("[fetch_games] Creating new APISportsFetcher")
                self.fetcher = await APISportsFetcher().__aenter__()

            logger.info(f"[fetch_games] Making API request to endpoint: {endpoint}")
            data = await self.fetcher.fetch_data(sport.lower(), endpoint, params)

            if not data:
                logger.warning(
                    f"[fetch_games] No data returned from API for {sport}/{league}"
                )
                return []

            if "response" not in data:
                logger.warning(
                    f"[fetch_games] No 'response' field in API data for {sport}/{league}"
                )
                return []

            # Check for API errors
            if "errors" in data and data["errors"]:
                error_msg = ", ".join(f"{k}: {v}" for k, v in data["errors"].items())
                logger.error(
                    f"[fetch_games] API returned errors for {sport}/{league}: {error_msg}"
                )
                return []

            logger.info(
                f"[fetch_games] Successfully received {len(data['response'])} games from API"
            )

            mapped_games = []
            for game in data["response"]:
                logger.info(
                    f"[fetch_games] Processing game: {game.get('id', 'unknown id')}"
                )
                mapped_game = self.fetcher.map_game_data(game, sport.lower(), league)
                if mapped_game:
                    mapped_games.append(mapped_game)
                    logger.info(
                        f"[fetch_games] Successfully mapped game: {mapped_game.get('id')}"
                    )
                    # If we have a database manager, save the mapped game (not the raw API game!)
                    if self.db_manager:
                        try:
                            logger.info(
                                f"[fetch_games] Saving game {mapped_game.get('id')} to database"
                            )
                            await self.db_manager.upsert_api_game(mapped_game)
                            logger.info(
                                f"[fetch_games] Successfully saved game {mapped_game.get('id')} to database"
                            )
                        except Exception as e:
                            logger.error(
                                f"[fetch_games] Error saving game {mapped_game.get('id')} to database: {str(e)}"
                            )
                else:
                    logger.warning(
                        f"[fetch_games] Failed to map game data: {game.get('id', 'unknown id')}"
                    )

            logger.info(
                f"[fetch_games] Successfully processed {len(mapped_games)} games for {sport}/{league}"
            )
            return mapped_games

        except Exception as e:
            logger.error(
                f"[fetch_games] Error fetching games for {sport}/{league}: {str(e)}",
                exc_info=True,
            )
            return []

    async def fetch_and_save_daily_games(self):
        """Fetch and save games for all leagues for today and tomorrow."""
        raw_data_dir = "data/raw_games"
        os.makedirs(raw_data_dir, exist_ok=True)

        current_date = datetime.now(timezone.utc)
        tomorrow_date = current_date + timedelta(days=1)
        current_date_str = current_date.strftime("%Y-%m-%d")
        tomorrow_date_str = tomorrow_date.strftime("%Y-%m-%d")
        saved_files = []

        async with self as api:
            for sport, leagues in LEAGUE_CONFIG.items():
                for league in leagues:
                    try:
                        # Fetch games for today and tomorrow
                        games = await api.fetch_games(
                            sport,
                            league,
                            date=current_date_str,
                            end_date=tomorrow_date_str,
                        )

                        if games:
                            # Save raw JSON
                            safe_league = league.replace("/", "_")
                            file_path = os.path.join(
                                raw_data_dir,
                                f"{current_date_str}_{sport}_{safe_league}.json",
                            )

                            if os.path.exists(file_path):
                                os.remove(file_path)

                            with open(file_path, "w") as f:
                                json.dump({"response": games}, f, indent=2)
                            saved_files.append(file_path)
                            logger.info(
                                f"Saved {len(games)} games for {sport}/{league} to {file_path}"
                            )
                        else:
                            logger.warning(f"No games found for {sport}/{league}")

                    except Exception as e:
                        logger.error(f"Error processing {sport}/{league}: {str(e)}")
                        continue

        return saved_files


async def main():
    """Example usage."""
    async with SportsAPI() as api:
        # Live updates are disabled by default
        api.toggle_live_updates(False)

        # Test fetching some games
        nfl_games = await api.fetch_games("american-football", "NFL")
        print(f"Found {len(nfl_games)} NFL games")

        # Fetch and save all games
        saved_files = await api.fetch_and_save_daily_games()
        print(f"Saved {len(saved_files)} files")

        # Keep the script running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")


if __name__ == "__main__":
    asyncio.run(main())
