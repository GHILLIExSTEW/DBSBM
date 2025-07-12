import aiomysql
from typing import Dict, Optional, List, Union
from log import logger
import json
from datetime import datetime, timezone, timedelta
import aiohttp
import os

from config.leagues import LEAGUE_CONFIG, get_league_id, is_league_in_season
from utils.league_utils import get_league_info, get_active_leagues

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")

async def save_game_to_db(pool: aiomysql.Pool, game_data: Dict) -> bool:
    """Save a single game to the api_games table."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO api_games 
                    (id, api_game_id, sport, league_id, league_name, home_team_id, away_team_id, 
                     home_team_name, away_team_name, start_time, end_time, status, score, 
                     venue, referee, raw_json, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        api_game_id=VALUES(api_game_id),
                        sport=VALUES(sport),
                        league_name=VALUES(league_name),
                        home_team_id=VALUES(home_team_id),
                        away_team_id=VALUES(away_team_id),
                        home_team_name=VALUES(home_team_name),
                        away_team_name=VALUES(away_team_name),
                        start_time=VALUES(start_time),
                        end_time=VALUES(end_time),
                        status=VALUES(status),
                        score=VALUES(score),
                        venue=VALUES(venue),
                        referee=VALUES(referee),
                        raw_json=VALUES(raw_json),
                        fetched_at=VALUES(fetched_at),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        game_data["id"],
                        game_data.get("api_game_id", game_data["id"]),  # Use api_game_id if available, fallback to id
                        game_data["sport"],
                        game_data["league_id"],
                        game_data["league_name"],
                        game_data["home_team_id"],
                        game_data["away_team_id"],
                        game_data["home_team_name"],
                        game_data["away_team_name"],
                        game_data["start_time"],
                        game_data.get("end_time"),  # Optional field
                        game_data["status"],
                        game_data["score"],
                        game_data["venue"],
                        game_data["referee"],
                        game_data["raw_json"],
                        game_data["fetched_at"],
                    ),
                )
        logger.info(f"Saved game {game_data['id']} to api_games")
        return True
    except Exception as e:
        logger.error(f"Error saving game {game_data['id']} to database: {e}")
        return False 

def map_game_data(game: Dict, sport: str, league: str, league_id: str) -> Optional[Dict]:
    """Normalize game data based on sport and league."""
    try:
        # Common fields for all sports
        teams = safe_get(game, "teams", default={})
        home_team = safe_get(teams, "home", default={})
        away_team = safe_get(teams, "away", default={})
        fixture = safe_get(game, "fixture", default={})
        
        # Get game ID from either game or fixture
        game_id = str(safe_get(game, "id", default=safe_get(fixture, "id", default="")))
        if not game_id:
            logger.error(f"Missing game ID for {sport}/{league}")
            return None
            
        # Get start time from either game or fixture
        start_time = iso_to_mysql_datetime(
            safe_get(game, "date", default=safe_get(fixture, "date"))
        )
        if not start_time:
            logger.error(f"Missing start time for game {game_id}")
            return None

        # Get status from either game or fixture
        status = safe_get(
            game,
            "status",
            "long",
            default=safe_get(fixture, "status", "long", default="Scheduled"),
        )

        # Get score based on sport
        score = {}
        if sport.lower() in ["baseball", "mlb"]:
            score = {
                "home": safe_get(game, "scores", "home", "total", default=0),
                "away": safe_get(game, "scores", "away", "total", default=0),
            }
        elif sport.lower() == "afl":
            score = {
                "home": safe_get(game, "scores", "home", "score", default=0),
                "away": safe_get(game, "scores", "away", "score", default=0),
            }
        else:
            score = {
                "home": safe_get(
                    game,
                    "scores",
                    "home",
                    "total",
                    default=safe_get(game, "goals", "home", default=0),
                ),
                "away": safe_get(
                    game,
                    "scores",
                    "away",
                    "total",
                    default=safe_get(game, "goals", "away", default=0),
                ),
            }

        # Build the game data dictionary
        game_data = {
            "id": game_id,
            "api_game_id": safe_get(game, "api_game_id", default=game_id),  # Use api_game_id if available, fallback to game_id
            "sport": sport.title(),
            "league_id": league_id,
            "league_name": LEAGUE_CONFIG.get(sport, {}).get(league, {}).get("name", league),
            "home_team_id": str(safe_get(home_team, "id")),
            "away_team_id": str(safe_get(away_team, "id")),
            "home_team_name": safe_get(home_team, "name", default="Unknown"),
            "away_team_name": safe_get(away_team, "name", default="Unknown"),
            "start_time": start_time,
            "end_time": None,  # Will be updated when game ends
            "status": status,
            "score": json.dumps(score),
            "venue": safe_get(game, "venue", "name", default=None),
            "referee": safe_get(game, "referee", default=None),
            "raw_json": json.dumps(game),
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }

        return game_data
    except Exception as e:
        logger.error(f"Error mapping game data for {sport}/{league}: {e}")
        return None 

async def fetch_games(
    pool: aiomysql.Pool, session: aiohttp.ClientSession, sport: str, league_name: str, league_id: str, date: str, season: int
):
    """Fetch game data for a specific league and date, saving to database and cache."""
    if not API_KEY:
        logger.error("API_KEY not found in environment variables")
        return
        
    headers = {"x-apisports-key": API_KEY}
    base_endpoint = ENDPOINTS.get(sport)
    if not base_endpoint or not league_id:
        logger.warning(f"Skipping {league_name}: missing endpoint or league_id")
        return
        
    endpoint = (
        f"{base_endpoint}/fixtures"
        if sport == "football"
        else f"{base_endpoint}/games"
    )
    params = {"league": league_id, "date": date, "season": season}
    logger.info(f"Requesting {endpoint} with params: {params}")
    
    try:
        async with session.get(endpoint, headers=headers, params=params) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logger.error(f"API request failed for {league_name}: {resp.status}: {error_text}")
                return
                
            data = await resp.json()
            if not data or "response" not in data:
                logger.error(f"Invalid API response for {league_name}: {data}")
                return
                
            # Save raw data
            raw_file = os.path.join(CACHE_DIR, f"league_{league_name}.json")
            with open(raw_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Fetched and cached raw data for {league_name} ({sport})")
            
            # Normalize and save to database
            games = data.get("response", [])
            if not games:
                logger.info(f"No games found for {league_name} on {date}")
                return
                
            logger.info(f"Found {len(games)} games in API response for {league_name}")
            normalized = []
            for game in games:
                game_data = map_game_data(game, sport, league_name, league_id)
                if game_data:
                    normalized.append(game_data)
                    
            logger.info(f"Successfully normalized {len(normalized)} games for {league_name}")
            
            # Save to database
            for game_data in normalized:
                success = await save_game_to_db(pool, game_data)
                if not success:
                    logger.error(f"Failed to save game to database: {game_data.get('id', 'unknown')}")
                    
            # Save normalized data
            normalized_file = os.path.join(CACHE_DIR, f"league_{league_name}_normalized.json")
            with open(normalized_file, "w") as f:
                json.dump(normalized, f, indent=2)
            logger.info(f"Saved {len(normalized)} normalized games for {league_name} ({sport})")
            
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching {league_name}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for {league_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {league_name}: {e}")
        logger.exception("Full traceback:") 

def get_cache_path(league_key: str, date: str) -> str:
    """Get the cache file path for a league and date."""
    return os.path.join(CACHE_DIR, f"{league_key}_{date}.json")

def get_current_season() -> int:
    """Get the current season year based on the current date."""
    current_date = datetime.now()
    # For most sports, the season year is the year when the season ends
    # For example, 2023-24 season is considered 2024
    if current_date.month >= 7:  # July or later
        return current_date.year + 1
    return current_date.year

def clear_cache(league_key: Optional[str] = None, date: Optional[str] = None):
    """
    Clear the cache for a specific league and/or date.
    
    Args:
        league_key: Optional league identifier. If None, clears all leagues.
        date: Optional date string. If None, clears all dates.
    """
    if league_key and date:
        # Clear specific league and date
        cache_path = get_cache_path(league_key, date)
        if os.path.exists(cache_path):
            os.remove(cache_path)
    elif league_key:
        # Clear all dates for a specific league
        for file in os.listdir(CACHE_DIR):
            if file.startswith(f"{league_key}_"):
                os.remove(os.path.join(CACHE_DIR, file))
    elif date:
        # Clear all leagues for a specific date
        for file in os.listdir(CACHE_DIR):
            if file.endswith(f"_{date}.json"):
                os.remove(os.path.join(CACHE_DIR, file))
    else:
        # Clear entire cache
        for file in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, file)) 