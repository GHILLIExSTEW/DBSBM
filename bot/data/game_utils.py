# REV 1.0.0 - Enhanced logging for game fetching and normalization
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from config.leagues import LEAGUE_CONFIG, LEAGUE_IDS

# Import all league dictionaries

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
    "UEFA Europa League": "EuropaLeague",
    "FIFA World Cup": "WorldCup",
    "Super Rugby": "SuperRugby",
    "Six Nations Championship": "SixNations",
    "FIVB World League": "FIVB",
    "EHF Champions League": "EHF",
    "Tennis": "Tennis",
    "ATP Tour": "ATP",
    "WTA Tour": "WTA",
    "PGA Tour": "PGA",
    "LPGA Tour": "LPGA",
    "European Tour": "EuropeanTour",
    "LIV Golf": "LIVGolf",
    "Ryder Cup": "RyderCup",
    "Presidents Cup": "PresidentsCup",
    "Bellator MMA": "Bellator",
    "TENNIS_CATEGORY": ["WTP", "ATP", "WTA"],
    "ESPORTS": ["CSGO", "VALORANT", "LOL", "DOTA 2", "PUBG", "COD"],
    "OTHER_SPORTS": ["OTHER_SPORTS"],
}

# Add 'UEFA CL' as an alias for ChampionsLeague
LEAGUE_FILE_KEY_MAP["UEFA CL"] = "ChampionsLeague"

# Map league names to sports
LEAGUE_TO_SPORT_MAP = {
    "EPL": "Football",
    "La Liga": "Football",
    "Bundesliga": "Football",
    "Serie A": "Football",
    "Ligue 1": "Football",
    "MLS": "Football",
    "ChampionsLeague": "Football",
    "EuropaLeague": "Football",
    "WorldCup": "Football",
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
    "Tennis": "Tennis",
    "ATP": "Tennis",
    "WTA": "Tennis",
    "PGA": "Golf",
    "LPGA": "Golf",
    "EuropeanTour": "Golf",
    "LIVGolf": "Golf",
    "RyderCup": "Golf",
    "PresidentsCup": "Golf",
    "MMA": "MMA",
    "Bellator": "MMA",
    "Formula-1": "Formula 1",
    "SuperRugby": "Rugby",
    "SixNations": "Rugby",
    "FIVB": "Volleyball",
    "EHF": "Handball",
    "AFL": "Australian Football",
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
    "ChampionsLeague": "2",
    "EuropaLeague": "3",
    "Brazil_Serie_A": "71",
    "WorldCup": "15",  # FIXED: was "1"
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
    "Tennis": "1",
    "ATP": "2",
    "WTA": "3",
    "PGA": "1",
    "LPGA": "2",
    "EuropeanTour": "3",
    "LIVGolf": "4",
    "RyderCup": "5",
    "PresidentsCup": "6",
    "MMA": "1",
    "Bellator": "2",
    "Formula-1": "1",
    "SuperRugby": "1",
    "SixNations": "2",
    "FIVB": "1",
    "EHF": "1",
    "AFL": "1",
}

# Map short league names to full normalized names
LEAGUE_NAME_NORMALIZATION = {
    "EPL": "English Premier League",
    "La Liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie A": "Serie A",
    "Ligue 1": "Ligue 1",
    "MLS": "Major League Soccer",
    "ChampionsLeague": "UEFA Champions League",
    "EuropaLeague": "UEFA Europa League",
    "WorldCup": "FIFA World Cup",
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
    "Tennis": "Tennis",
    "ATP": "ATP Tour",
    "WTA": "WTA Tour",
    "PGA": "PGA Tour",
    "LPGA": "LPGA Tour",
    "EuropeanTour": "European Tour",
    "LIVGolf": "LIV Golf",
    "RyderCup": "Ryder Cup",
    "PresidentsCup": "Presidents Cup",
    "MMA": "UFC",
    "Bellator": "Bellator MMA",
    "Formula-1": "Formula 1",
    "SuperRugby": "Super Rugby",
    "SixNations": "Six Nations Championship",
    "FIVB": "FIVB World League",
    "EHF": "EHF Champions League",
    "AFL": "Australian Football League",
}

# Add 'UEFA CL' as an alias for ChampionsLeague
LEAGUE_NAME_NORMALIZATION["UEFA CL"] = "UEFA Champions League"


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


def normalize_team_name(team_name: str, sport: str = None, league: str = None) -> str:
    """
    Normalize a team name using the appropriate league dictionary.

    Args:
        team_name (str): The team name to normalize
        sport (str, optional): The sport (e.g., 'baseball', 'football')
        league (str, optional): The league (e.g., 'MLB', 'NFL')

    Returns:
        str: The normalized team name
    """
    if not team_name:
        return team_name

    # Convert to lowercase for matching
    team_name_lower = team_name.lower()

    # Get the appropriate team name dictionary based on sport and league
    team_dict = {}
    if sport and league:
        if sport.lower() == "baseball" and league.upper() == "MLB":
            from utils.league_dictionaries.team_mappings import MLB_TEAM_NAMES

            team_dict = MLB_TEAM_NAMES
        elif sport.lower() == "football" and league.upper() == "NFL":
            from utils.league_dictionaries.team_mappings import NFL_TEAM_NAMES

            team_dict = NFL_TEAM_NAMES
        elif sport.lower() == "basketball" and league.upper() == "NBA":
            from utils.league_dictionaries.team_mappings import NBA_TEAM_NAMES

            team_dict = NBA_TEAM_NAMES
        elif sport.lower() == "hockey" and league.upper() == "NHL":
            from utils.league_dictionaries.team_mappings import NHL_TEAM_NAMES

            team_dict = NHL_TEAM_NAMES
        elif sport.lower() == "soccer" and league.upper() == "EPL":
            from utils.league_dictionaries.team_mappings import EPL_TEAM_NAMES

            team_dict = EPL_TEAM_NAMES

    # If we have a team dictionary, try to find a match
    if team_dict:
        # First try exact match
        if team_name_lower in team_dict:
            return team_dict[team_name_lower]

        # Try fuzzy matching
        import difflib

        matches = difflib.get_close_matches(
            team_name_lower, team_dict.keys(), n=1, cutoff=0.75
        )
        if matches:
            return team_dict[matches[0]]

    # If no match found or no dictionary available, handle special cases
    if team_name_lower.startswith("st "):
        return f"St. {team_name[3:].title()}"

    # Return title case as fallback
    return team_name.title()


def normalize_team_name_any_league(team_name: str) -> str:
    """
    Normalize a team name without requiring sport and league parameters.
    This is a wrapper around normalize_team_name that tries common sports and leagues.

    Args:
        team_name (str): The team name to normalize

    Returns:
        str: The normalized team name
    """
    if not team_name:
        return team_name

    # Try each major sport and league combination
    sports_and_leagues = [
        ("baseball", "MLB"),
        ("football", "NFL"),
        ("basketball", "NBA"),
        ("hockey", "NHL"),
        ("soccer", "EPL"),
    ]

    for sport, league in sports_and_leagues:
        normalized = normalize_team_name(team_name, sport, league)
        if normalized != team_name:
            return normalized

    # If no sport/league combination worked, return the original name
    return team_name


async def insert_games(
    db_manager,
    league_id: str,
    games: List[Dict[str, Any]],
    sport: str,
    league_name: str,
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
            logger.error(
                f"Error inserting game with api_game_id={game.get('api_game_id')}: {e}",
                exc_info=True,
            )
    logger.info(f"Completed inserting/updating games for league_id={league_id}")


async def get_normalized_games_for_dropdown(
    db_manager, league_name: str, season: int = None
) -> List[Dict[str, Any]]:
    """Fetch and normalize games for a league from the api_games table for use in a bet dropdown."""
    logger.info(
        f"[get_normalized_games_for_dropdown] Starting fetch for league_name={league_name}, season={season}"
    )

    dropdown_games = [
        {
            "id": "manual",
            "api_game_id": "manual",
            "home_team": "Manual Entry",
            "away_team": "Manual Entry",
            "start_time": datetime.now(timezone.utc),
            "status": "Manual",
            "home_team_name": "Manual Entry",
            "away_team_name": "Manual Entry",
        }
    ]

    sport = None
    league_key = None
    league_name_db = None

    # First, try to find the league by key (e.g., "ChampionsLeague")
    for key, league_info in LEAGUE_IDS.items():
        if key == league_name:
            sport = league_info.get("sport", "").capitalize()
            league_key = key
            league_name_db = (
                LEAGUE_CONFIG.get(league_info.get("sport", ""), {})
                .get(key, {})
                .get("name", key)
            )
            if league_name_db == "MLB":
                league_name_db = "Major League Baseball"
            logger.info(
                f"[get_normalized_games_for_dropdown] Found league by key: sport={sport}, league_key={league_key}, league_name={league_name_db}"
            )
            break

    # If not found by key, try to find by display name (e.g., "UEFA Champions League")
    if not sport:
        for key, league_info in LEAGUE_IDS.items():
            display_name = (
                LEAGUE_CONFIG.get(league_info.get("sport", ""), {})
                .get(key, {})
                .get("name", key)
            )
            if display_name == league_name:
                sport = league_info.get("sport", "").capitalize()
                league_key = key
                league_name_db = display_name
                if league_name_db == "MLB":
                    league_name_db = "Major League Baseball"
                logger.info(
                    f"[get_normalized_games_for_dropdown] Found league by display name: sport={sport}, league_key={league_key}, league_name={league_name_db}"
                )
                break

    # If still not found, try the reverse mapping from LEAGUE_NAME_NORMALIZATION
    if not sport:
        for key, normalized_name in LEAGUE_NAME_NORMALIZATION.items():
            if normalized_name == league_name:
                # Find the corresponding league info
                for league_key_inner, league_info in LEAGUE_IDS.items():
                    if league_key_inner == key:
                        sport = league_info.get("sport", "").capitalize()
                        league_key = key
                        league_name_db = normalized_name
                        logger.info(
                            f"[get_normalized_games_for_dropdown] Found league by normalization: sport={sport}, league_key={league_key}, league_name={league_name_db}"
                        )
                        break
                if sport:
                    break

    if not sport or not league_key:
        logger.warning(
            f"[get_normalized_games_for_dropdown] Could not find sport and league name for league_name={league_name}"
        )
        return dropdown_games

    # Build possible league names (abbreviation, full name, and common aliases)
    league_names = set()
    league_abbr = get_league_abbreviation(league_key)
    league_names.add(league_name_db)  # Use the display name from database
    league_names.add(league_key)  # Add the league key
    league_names.add(league_abbr)
    normalized_full = normalize_league_name(league_abbr)
    league_names.add(normalized_full)
    # Add all known aliases for WorldCup
    if league_key == "WorldCup":
        league_names.update(["WorldCup", "FIFA World Cup", "FIFA Club World Cup"])
    # Add more common aliases for major leagues
    aliases = {
        "NBA": ["NBA", "National Basketball Association"],
        "NHL": ["NHL", "National Hockey League"],
        "NFL": ["NFL", "National Football League"],
        "MLB": ["MLB", "Major League Baseball"],
        "WNBA": ["WNBA", "Women's National Basketball Association"],
        "EPL": ["EPL", "English Premier League"],
        "MLS": ["MLS", "Major League Soccer"],
        "NCAAF": ["NCAA Football", "NCAAF"],
        "NCAAB": ["NCAA Basketball", "NCAAB"],
    }
    for key, names in aliases.items():
        if league_abbr == key or league_name == key or normalized_full == key:
            league_names.update(names)
    league_names = list(league_names)

    # Define finished statuses based on sport
    if sport.lower() == "baseball":
        finished_statuses = [
            "Match Finished",
            "Finished",
            "FT",
            "Game Finished",
            "Final",
        ]
    else:
        finished_statuses = [
            "Match Finished",
            "Finished",
            "FT",
            "Ended",
            "Game Finished",
            "Final",
        ]
    logger.info(
        f"[get_normalized_games_for_dropdown] Using finished_statuses={finished_statuses}"
    )

    # Dynamically build the correct number of %s for the NOT IN and IN clauses
    status_placeholders = ", ".join(["%s"] * len(finished_statuses))
    league_name_placeholders = ", ".join(["%s"] * len(league_names))
    query = f"""
        SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, score, odds, league_name
        FROM api_games
        WHERE sport = %s
        AND league_id = %s
        AND (UPPER(league_name) IN ({league_name_placeholders}))
        AND status NOT IN ({status_placeholders})
        ORDER BY start_time ASC LIMIT 100
    """

    league_id = LEAGUE_ID_MAP.get(
        league_key, "1"
    )  # Use league_key instead of league_name
    logger.info(f"[get_normalized_games_for_dropdown] Using league_id={league_id}")
    logger.info(
        f"[get_normalized_games_for_dropdown] Fetching all non-finished games for {sport}/{league_key} (league_names={league_names})"
    )
    params = (
        (sport, league_id)
        + tuple([name.upper() for name in league_names])
        + tuple(finished_statuses)
    )
    rows = await db_manager.fetch_all(query, params)
    logger.info(
        f"[get_normalized_games_for_dropdown] Found {len(rows) if rows else 0} games"
    )

    if not rows:
        logger.warning(
            f"[get_normalized_games_for_dropdown] No active games found for sport={sport}, league_id={league_id}, league_key={league_key}"
        )
        return dropdown_games  # Return just manual entry option

    for row in rows:
        try:
            # Always use league-specific normalization for all leagues
            home_team = normalize_team_name(row["home_team_name"], sport, league_key)
            away_team = normalize_team_name(row["away_team_name"], sport, league_key)
            logger.info(
                f"[get_normalized_games_for_dropdown] Normalized teams {row['home_team_name']} -> {home_team}, {row['away_team_name']} -> {away_team}"
            )
            game_data = {
                "id": row["id"],
                "api_game_id": str(row["api_game_id"]),
                "home_team": home_team,
                "away_team": away_team,
                "start_time": row["start_time"],
                "status": row["status"],
                "home_team_name": home_team,
                "away_team_name": away_team,
            }
            dropdown_games.append(game_data)
            logger.info(
                f"[get_normalized_games_for_dropdown] Added game to dropdown: {game_data}"
            )
        except Exception as e:
            logger.error(
                f"[get_normalized_games_for_dropdown] Error processing game data for league_id={league_id}, sport={sport}, league_key={league_key}: {e}",
                exc_info=True,
            )
            continue

    logger.info(
        f"[get_normalized_games_for_dropdown] Returning {len(dropdown_games)} normalized games for dropdown (including manual entry)"
    )
    return dropdown_games
