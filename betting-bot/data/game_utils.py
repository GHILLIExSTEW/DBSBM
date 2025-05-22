from typing import List, Dict, Any
from datetime import datetime, timezone
import json
import logging
from utils.league_dictionaries.mlb import TEAM_FULL_NAMES as MLB_TEAM_NAMES

from config.leagues import LEAGUE_CONFIG, LEAGUE_IDS

logger = logging.getLogger(__name__)

# League name normalization mapping (used for display and verification)
LEAGUE_FILE_KEY_MAP = {
    "La Liga": "LaLiga",
    "Serie A": "SerieA",
    "Ligue 1": "Ligue1",
    "English Premier League": "EPL",
    "Bundesliga": "Bundesliga",
    "Major League Soccer": "MLS",
    "National Basketball Association": "NBA",
    "Women's National Basketball Association": "WNBA",
    "Major League Baseball": "MLB",
    "National Hockey League": "NHL",
    "National Football League": "NFL",
    "NCAA Football": "NCAAF",
    "NCAA Basketball": "NCAAB",
    "NCAA Men's Basketball": "NCAABM",
    "NCAA Women's Basketball": "NCAABW",
    "NCAA Football Bowl Subdivision": "NCAAFBS",
    "NCAA Volleyball": "NCAAVB",
    "NCAA Football Championship": "NCAAFB",
    "NCAA Women's Basketball": "NCAAWBB",
    "NCAA Women's Volleyball": "NCAAWVB",
    "NCAA Women's Football": "NCAAWFB",
    "Nippon Professional Baseball": "NPB",
    "Korea Baseball Organization": "KBO",
    "Kontinental Hockey League": "KHL",
    "Professional Darts Corporation": "PDC",
    "British Darts Organisation": "BDO",
    "World Darts Federation": "WDF",
    "Premier League Darts": "PremierLeagueDarts",
    "World Matchplay": "WorldMatchplay",
    "World Grand Prix": "WorldGrandPrix",
    "UK Open": "UKOpen",
    "Grand Slam": "GrandSlam",
    "Players Championship": "PlayersChampionship",
    "European Championship": "EuropeanChampionship",
    "Masters": "Masters",
    "UEFA Champions League": "ChampionsLeague",
    "TENNIS": ["WTP", "ATP", "WTA"],
    "ESPORTS": ["CSGO", "VALORANT", "LOL", "DOTA 2", "PUBG", "COD"],
    "OTHER_SPORTS": ["OTHER_SPORTS"],
}

# Map league names to sports
LEAGUE_TO_SPORT_MAP = {
    "EPL": "Football",
    "La Liga": "Football",
    "Bundesliga": "Football",
    "Serie A": "Football",
    "Ligue 1": "Football",
    "MLS": "Football",
    "Champions League": "Football",
    "NBA": "Basketball",
    "WNBA": "Basketball",
    "MLB": "Baseball",
    "NHL": "Hockey",
    "NFL": "American Football",
    "NCAA": "American Football",
    "NPB": "Baseball",
    "KBO": "Baseball",
    "KHL": "Hockey",
    "PDC": "Darts",
    "BDO": "Darts",
    "WDF": "Darts",
    "Premier League Darts": "Darts",
    "World Matchplay": "Darts",
    "World Grand Prix": "Darts",
    "UK Open": "Darts",
    "Grand Slam": "Darts",
    "Players Championship": "Darts",
    "European Championship": "Darts",
    "Masters": "Darts",
    "TENNIS": "Tennis",
    "ESPORTS": "Esports",
    "OTHER_SPORTS": "Other",
}

# Map league names to league IDs
LEAGUE_ID_MAP = {
    "EPL": "39",
    "La Liga": "140",
    "Bundesliga": "78",
    "Serie A": "135",
    "Ligue 1": "61",
    "MLS": "253",
    "Champions League": "2",
    "NBA": "12",
    "WNBA": "13",
    "MLB": "1",
    "NHL": "57",
    "NFL": "1",
    "NCAA": "2",
    "NPB": "2",
    "KBO": "3",
    "KHL": "1",
    "PDC": "1",
    "BDO": "2",
    "WDF": "3",
    "Premier League Darts": "4",
    "World Matchplay": "5",
    "World Grand Prix": "6",
    "UK Open": "7",
    "Grand Slam": "8",
    "Players Championship": "9",
    "European Championship": "10",
    "Masters": "11",
}

# Map short league names to full normalized names
LEAGUE_NAME_NORMALIZATION = {
    "EPL": "English Premier League",
    "La Liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie A": "Serie A",
    "Ligue 1": "Ligue 1",
    "MLS": "Major League Soccer",
    "Champions League": "UEFA Champions League",
    "NBA": "National Basketball Association",
    "WNBA": "Women's National Basketball Association",
    "MLB": "Major League Baseball",
    "NHL": "National Hockey League",
    "NFL": "National Football League",
    "NCAA": "NCAA Football",
    "NPB": "Nippon Professional Baseball",
    "KBO": "Korea Baseball Organization",
    "KHL": "Kontinental Hockey League",
    "PDC": "Professional Darts Corporation",
    "BDO": "British Darts Organisation",
    "WDF": "World Darts Federation",
    "Premier League Darts": "Premier League Darts",
    "World Matchplay": "World Matchplay",
    "World Grand Prix": "World Grand Prix",
    "UK Open": "UK Open",
    "Grand Slam": "Grand Slam",
    "Players Championship": "Players Championship",
    "European Championship": "European Championship",
    "Masters": "Masters",
}


def get_league_abbreviation(league_name: str) -> str:
    """Convert a league name to its abbreviation for display purposes."""
    if league_name in LEAGUE_FILE_KEY_MAP:
        value = LEAGUE_FILE_KEY_MAP[league_name]
        return value if isinstance(value, str) else value[0]

    for key, value in LEAGUE_FILE_KEY_MAP.items():
        if isinstance(value, list) and league_name in value:
            return league_name

    return league_name


def normalize_league_name(league_name: str) -> str:
    """Normalize a league name to its full form for verification."""
    return LEAGUE_NAME_NORMALIZATION.get(league_name, league_name)


def sanitize_team_name(name: str, max_length: int = 30) -> str:
    """Sanitize a team name to ensure it's a reasonable length and format."""
    if not name:
        return "Unknown Team"
    name = "".join(c for c in name if c.isprintable())
    if len(name) > max_length:
        name = name[: max_length - 3] + "..."
    return name


def normalize_mlb_team_name(team_name: str) -> str:
    """
    Convert any MLB team name format (abbreviation, nickname, or full name) to the standardized full name.
    Example: 'NYY' or 'Yankees' -> 'New York Yankees'
    """
    if not team_name:
        return team_name
        
    # Convert to lowercase for case-insensitive matching
    search_name = team_name.lower().strip()
    
    # Check if it's already in the normalized format
    for full_name in MLB_TEAM_NAMES.values():
        if search_name == full_name.lower():
            return full_name
            
    # Try to find a match in our mappings
    if search_name in MLB_TEAM_NAMES:
        return MLB_TEAM_NAMES[search_name]
        
    return team_name


async def insert_games(
    db_manager, league_id: str, games: List[Dict[str, Any]], sport: str, league_name: str
) -> None:
    """Insert or update games into the api_games table."""
    logger.info(f"Inserting/updating {len(games)} games for league_id={league_id}")
    for game in games:
        try:
            query = """
                INSERT INTO api_games (
                    api_game_id, sport, league_id, league_name,
                    home_team_name, away_team_name, start_time,
                    status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                ) ON DUPLICATE KEY UPDATE
                    home_team_name = VALUES(home_team_name),
                    away_team_name = VALUES(away_team_name),
                    start_time = VALUES(start_time),
                    status = VALUES(status),
                    updated_at = NOW()
            """
            args = (
                game.get("api_game_id"),
                sport,
                league_id,
                league_name,
                sanitize_team_name(game.get("home_team_name", "Unknown Team")),
                sanitize_team_name(game.get("away_team_name", "Unknown Team")),
                game.get("start_time"),
                game.get("status", "scheduled"),
            )
            await db_manager.execute(query, args)
        except Exception as e:
            logger.error(f"Error inserting game with api_game_id={game.get('api_game_id')}: {e}", exc_info=True)
    logger.info(f"Completed inserting/updating games for league_id={league_id}")


async def get_normalized_games_for_dropdown(
    db_manager, league_name: str, season: int = None
) -> List[Dict[str, Any]]:
    """Fetch and normalize games for a league from the api_games table for use in a bet dropdown."""
    logger.info(f"Fetching games for league_name={league_name}")

    # Step 1: Map league to sport
    sport = LEAGUE_TO_SPORT_MAP.get(league_name, "Unknown")
    if sport == "Unknown":
        logger.warning(f"No sport mapping found for league_name={league_name}")
        return []

    # Step 2: Map league to league_id
    league_id = LEAGUE_ID_MAP.get(league_name)
    if not league_id:
        logger.warning(f"No league_id mapping found for league_name={league_name}")
        return []

    # Step 3: Normalize league name for verification
    normalized_league_name = normalize_league_name(league_name)
    logger.debug(f"Normalized league_name={normalized_league_name} for league_name={league_name}")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    seasons_to_check = [datetime.now().year, datetime.now().year - 1] if season is None else [season]
    all_games = []

    # Define finished statuses
    finished_statuses = ["Match Finished", "Finished", "FT", "Ended", "Game Finished", "Final"]

    for current_season in seasons_to_check:
        logger.debug(f"Querying games for sport={sport}, league_id={league_id}, season={current_season}")

        # Query games matching sport, league_id, and season, excluding finished games
        query = """
            SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, score, league_name
            FROM api_games
            WHERE sport = %s
            AND league_id = %s
            AND start_time >= %s
            AND season = %s
            AND status NOT IN (%s, %s, %s, %s, %s, %s)
            ORDER BY start_time ASC LIMIT 100
        """
        rows = await db_manager.fetch_all(query, (sport, league_id, today_start, current_season) + tuple(finished_statuses))

        if not rows:
            logger.warning(
                f"No active games found for sport={sport}, league_id={league_id}, season={current_season}"
            )
            continue

        # Verify league_name matches normalized name
        for row in rows:
            db_league_name = row["league_name"]
            if db_league_name.lower() != normalized_league_name.lower():
                logger.debug(
                    f"Skipping game id={row['id']} due to league_name mismatch: "
                    f"db={db_league_name}, expected={normalized_league_name}"
                )
                continue

            try:
                # For MLB games, normalize team names
                if sport.lower() == "baseball" and league_name in ["MLB", "Major League Baseball"]:
                    home_team = normalize_mlb_team_name(row["home_team_name"])
                    away_team = normalize_mlb_team_name(row["away_team_name"])
                else:
                    home_team = sanitize_team_name(row["home_team_name"])
                    away_team = sanitize_team_name(row["away_team_name"])
                    
                all_games.append(
                    {
                        "id": row["id"],
                        "api_game_id": row["api_game_id"] or row["id"],
                        "home_team": home_team,
                        "away_team": away_team,
                        "start_time": row["start_time"],
                        "status": row["status"],
                        "home_team_name": home_team,
                        "away_team_name": away_team,
                        "sport": sport,
                        "league_name": db_league_name,
                        "label": f"{home_team} vs {away_team} ({row['start_time']})",
                    }
                )
            except Exception as e:
                logger.error(
                    f"Error processing game data for league_id={league_id}, sport={sport}, "
                    f"league_name={db_league_name}: {e}",
                    exc_info=True,
                )
                continue

    logger.info(f"Returning {len(all_games)} normalized games for dropdown")
    return all_games