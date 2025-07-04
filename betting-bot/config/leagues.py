import os
import requests
from dotenv import load_dotenv
from datetime import datetime



LEAGUE_CONFIG = {
    # Basketball
    "NBA": {
        "sport": "Basketball",
        "name": "NBA",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Boston Celtics",
        "line_placeholder_game": "e.g., Moneyline, Spread +3.5, Total O/U 215.5",
        "line_placeholder_player": "e.g., Points Over 25.5, Rebounds Under 8.0"
    },
    "WNBA": {
        "sport": "Basketball",
        "name": "WNBA",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Las Vegas Aces",
        "line_placeholder_game": "e.g., Moneyline, Spread +3.5, Total O/U 165.5",
        "line_placeholder_player": "e.g., Points Over 15.5, Rebounds Under 8.0"
    },
    "EuroLeague": {
        "sport": "Basketball",
        "name": "EuroLeague",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Real Madrid",
        "line_placeholder_game": "e.g., Moneyline, Spread +3.5, Total O/U 155.5",
        "line_placeholder_player": "e.g., Points Over 15.5, Rebounds Under 8.0"
    },
    
    # Baseball
    "MLB": {
        "sport": "Baseball",
        "name": "MLB",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., New York Yankees",
        "line_placeholder_game": "e.g., Moneyline, Run Line -1.5, Total O/U 8.5",
        "line_placeholder_player": "e.g., Strikeouts Over 6.5, Hits Over 0.5"
    },
    "NPB": {
        "sport": "Baseball",
        "name": "NPB",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Yomiuri Giants",
        "line_placeholder_game": "e.g., Moneyline, Run Line -1.5, Total O/U 7.5",
        "line_placeholder_player": "e.g., Strikeouts Over 6.5, Hits Over 0.5"
    },
    "KBO": {
        "sport": "Baseball",
        "name": "KBO",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Samsung Lions",
        "line_placeholder_game": "e.g., Moneyline, Run Line -1.5, Total O/U 8.5",
        "line_placeholder_player": "e.g., Strikeouts Over 6.5, Hits Over 0.5"
    },
    
    # Hockey
    "NHL": {
        "sport": "Ice Hockey",
        "name": "NHL",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Edmonton Oilers",
        "line_placeholder_game": "e.g., Moneyline, Puck Line -1.5, Total O/U 6.5",
        "line_placeholder_player": "e.g., Shots on Goal Over 3.5, To Score a Goal"
    },
    "KHL": {
        "sport": "Ice Hockey",
        "name": "KHL",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., SKA St. Petersburg",
        "line_placeholder_game": "e.g., Moneyline, Puck Line -1.5, Total O/U 5.5",
        "line_placeholder_player": "e.g., Shots on Goal Over 3.5, To Score a Goal"
    },
    
    # American Football
    "NFL": {
        "sport": "American Football",
        "name": "NFL",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Kansas City Chiefs",
        "line_placeholder_game": "e.g., Moneyline, Spread -7.5, Total O/U 48.5",
        "line_placeholder_player": "e.g., Passing Yards Over 250.5, First TD Scorer"
    },
    "NCAA": {
        "sport": "American Football",
        "name": "NCAA Football",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Alabama Crimson Tide",
        "line_placeholder_game": "e.g., Moneyline, Spread -7.5, Total O/U 48.5",
        "line_placeholder_player": "e.g., Passing Yards Over 250.5, First TD Scorer"
    },
    
    # Soccer
    "EPL": {
        "sport": "Soccer",
        "name": "English Premier League",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Arsenal",
        "line_placeholder_game": "e.g., Arsenal to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "LaLiga": {
        "sport": "Soccer",
        "name": "La Liga",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Real Madrid",
        "line_placeholder_game": "e.g., Real Madrid to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "Bundesliga": {
        "sport": "Soccer",
        "name": "Bundesliga",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Bayern Munich",
        "line_placeholder_game": "e.g., Bayern Munich to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "SerieA": {
        "sport": "Soccer",
        "name": "Serie A",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Inter Milan",
        "line_placeholder_game": "e.g., Inter Milan to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "Ligue1": {
        "sport": "Soccer",
        "name": "Ligue 1",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Paris Saint-Germain",
        "line_placeholder_game": "e.g., PSG to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "MLS": {
        "sport": "Soccer",
        "name": "MLS",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., LAFC",
        "line_placeholder_game": "e.g., LAFC to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "ChampionsLeague": {
        "sport": "Soccer",
        "name": "UEFA Champions League",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Real Madrid",
        "line_placeholder_game": "e.g., Real Madrid to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "EuropaLeague": {
        "sport": "Soccer",
        "name": "UEFA Europa League",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Liverpool",
        "line_placeholder_game": "e.g., Liverpool to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    "WorldCup": {
        "sport": "Soccer",
        "name": "FIFA World Cup",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Brazil",
        "line_placeholder_game": "e.g., Brazil to Win, Over 2.5 Goals, Both Teams to Score",
        "line_placeholder_player": "e.g., To Score Anytime, xG Over 0.5"
    },
    
    # Rugby
    "SuperRugby": {
        "sport": "Rugby",
        "name": "Super Rugby",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Crusaders",
        "line_placeholder_game": "e.g., Crusaders to Win, Handicap -5.5, Total Over/Under 45.5",
        "line_placeholder_player": "e.g., Try Scorer, Points Over 10.5"
    },
    "SixNations": {
        "sport": "Rugby",
        "name": "Six Nations Championship",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., England",
        "line_placeholder_game": "e.g., England to Win, Handicap -5.5, Total Over/Under 45.5",
        "line_placeholder_player": "e.g., Try Scorer, Points Over 10.5"
    },
    
    # Volleyball
    "FIVB": {
        "sport": "Volleyball",
        "name": "FIVB World League",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Brazil",
        "line_placeholder_game": "e.g., Brazil to Win, Set Handicap -1.5, Total Sets Over/Under 3.5",
        "line_placeholder_player": "e.g., Points Over 15.5, Blocks Over 2.5"
    },
    
    # Handball
    "EHF": {
        "sport": "Handball",
        "name": "EHF Champions League",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Barcelona",
        "line_placeholder_game": "e.g., Barcelona to Win, Handicap -3.5, Total Over/Under 55.5",
        "line_placeholder_player": "e.g., Goals Over 7.5, Assists Over 3.5"
    },
    
    # AFL
    "AFL": {
        "sport": "Australian Football",
        "name": "AFL",
        "sport_type": "Team Sport",
        "participant_label": "Team",
        "team_placeholder": "e.g., Richmond Tigers",
        "line_placeholder_game": "e.g., Richmond to Win, Line -15.5, Total Over/Under 165.5",
        "line_placeholder_player": "e.g., Goals Over 2.5, Disposals Over 25.5"
    },
    
    # Formula 1
    "Formula-1": {
        "sport": "Racing",
        "name": "Formula 1",
        "sport_type": "Individual Player",
        "participant_label": "Driver",
        "team_placeholder": "e.g., Max Verstappen",
        "line_placeholder_game": "e.g., To Win Race, Podium Finish, Fastest Lap",
        "line_placeholder_player": "e.g., Qualifying Position Over/Under 3.5, Points Finish"
    },
    
    # MMA
    "MMA": {
        "sport": "Fighting",
        "name": "UFC",
        "sport_type": "Individual Player",
        "participant_label": "Fighter",
        "team_placeholder": "e.g., Jon Jones",
        "line_placeholder_game": "e.g., To Win Fight, Method of Victory (KO/Sub/Decision)",
        "line_placeholder_player": "e.g., Fight to go the Distance - Yes/No, Round Betting"
    },
    "Bellator": {
        "sport": "Fighting",
        "name": "Bellator MMA",
        "sport_type": "Individual Player",
        "participant_label": "Fighter",
        "team_placeholder": "e.g., Patricio Pitbull",
        "line_placeholder_game": "e.g., To Win Fight, Method of Victory (KO/Sub/Decision)",
        "line_placeholder_player": "e.g., Fight to go the Distance - Yes/No, Round Betting"
    },
    
    # Generic fallback
    "OTHER": {
        "sport": "Unknown",
        "name": "Other League",
        "sport_type": "Unknown",
        "participant_label": "Team/Participant",
        "team_placeholder": "Enter participant name",
        "line_placeholder_game": "Enter game line (e.g., Moneyline)",
        "line_placeholder_player": "Enter player prop details"
    }
}

# League season start dates
LEAGUE_SEASON_STARTS = {
    # Baseball
    "MLB": {"start": "2025-03-27", "end": "2025-09-28"},
    "NPB": {"start": "2024-03-29", "end": "2024-10-10"},
    "KBO": {"start": "2024-03-23", "end": "2024-10-20"},
    
    # Basketball
    "NBA": {"start": "2023-10-24", "end": "2024-04-14"},
    "WNBA": {"start": "2024-05-14", "end": "2024-09-19"},
    "EuroLeague": {"start": "2023-10-05", "end": "2024-05-26"},
    
    # American Football
    "NFL": {"start": "2024-09-05", "end": "2025-02-09"},
    "NCAA": {"start": "2024-08-24", "end": "2025-01-13"},
    
    # Hockey
    "NHL": {"start": "2023-10-10", "end": "2024-04-18"},
    "KHL": {"start": "2023-09-01", "end": "2024-02-29"},
    
    # Soccer (European leagues typically start in 2024 and end in 2025)
    "EPL": {"start": "2024-08-16", "end": "2025-05-25"},
    "LaLiga": {"start": "2024-08-16", "end": "2025-05-25"},
    "Bundesliga": {"start": "2024-08-16", "end": "2025-05-25"},
    "SerieA": {"start": "2024-08-16", "end": "2025-05-25"},
    "Ligue1": {"start": "2024-08-16", "end": "2025-05-25"},
    "MLS": {"start": "2024-02-24", "end": "2024-12-07"},
    "ChampionsLeague": {"start": "2024-09-17", "end": "2025-06-01"},
    "EuropaLeague": {"start": "2024-09-19", "end": "2025-05-28"},
    "WorldCup": {"start": "2026-06-08", "end": "2026-07-19"},
    
    # Rugby
    "SuperRugby": {"start": "2024-02-23", "end": "2024-06-22"},
    "SixNations": {"start": "2024-02-02", "end": "2024-03-16"},
    
    # Volleyball
    "FIVB": {"start": "2024-05-21", "end": "2024-07-07"},
    
    # Handball
    "EHF": {"start": "2023-09-13", "end": "2024-06-02"},
    
    # AFL
    "AFL": {"start": "2024-03-07", "end": "2024-09-28"},
    
    # Formula 1
    "Formula-1": {"start": "2024-03-02", "end": "2024-12-08"},
    
    # MMA
    "MMA": {"start": "2024-01-20", "end": "2024-12-14"},
    "Bellator": {"start": "2024-02-24", "end": "2024-12-14"}
}

# League mappings with API-Sports IDs
LEAGUE_IDS = {
    # Football (Soccer)
    "EPL": {"id": 39, "sport": "football", "name": "English Premier League"},
    "LaLiga": {"id": 140, "sport": "football", "name": "La Liga"},
    "Bundesliga": {"id": 78, "sport": "football", "name": "Bundesliga"},
    "SerieA": {"id": 135, "sport": "football", "name": "Serie A"},
    "Ligue1": {"id": 61, "sport": "football", "name": "Ligue 1"},
    "MLS": {"id": 253, "sport": "football", "name": "MLS"},
    "ChampionsLeague": {"id": 2, "sport": "football", "name": "UEFA Champions League"},
    "EuropaLeague": {"id": 3, "sport": "football", "name": "UEFA Europa League"},
    "WorldCup": {"id": 1, "sport": "football", "name": "FIFA World Cup"},
    
    # Basketball
    "NBA": {"id": 12, "sport": "basketball", "name": "NBA"},
    "WNBA": {"id": 13, "sport": "basketball", "name": "WNBA"},
    "EuroLeague": {"id": 1, "sport": "basketball", "name": "EuroLeague"},
    
    # Baseball
    "MLB": {"id": 1, "sport": "baseball", "name": "MLB"},
    "NPB": {"id": 2, "sport": "baseball", "name": "NPB"},
    "KBO": {"id": 3, "sport": "baseball", "name": "KBO"},
    
    # Hockey
    "NHL": {"id": 57, "sport": "hockey", "name": "NHL"},
    "KHL": {"id": 1, "sport": "hockey", "name": "Kontinental Hockey League"},
    
    # American Football
    "NFL": {"id": 1, "sport": "american-football", "name": "NFL"},
    "NCAA": {"id": 2, "sport": "american-football", "name": "NCAA Football"},
    
    # Rugby
    "SuperRugby": {"id": 1, "sport": "rugby", "name": "Super Rugby"},
    "SixNations": {"id": 2, "sport": "rugby", "name": "Six Nations Championship"},
    
    # Volleyball
    "FIVB": {"id": 1, "sport": "volleyball", "name": "FIVB World League"},
    
    # Handball
    "EHF": {"id": 1, "sport": "handball", "name": "EHF Champions League"},
    
    # AFL
    "AFL": {"id": 1, "sport": "afl", "name": "AFL"},
    
    # Formula 1
    "Formula-1": {"id": 1, "sport": "formula-1", "name": "Formula 1"},
    
    # MMA
    "MMA": {"id": 1, "sport": "mma", "name": "UFC"},
    "Bellator": {"id": 2, "sport": "mma", "name": "Bellator MMA"}
}

# API endpoints
ENDPOINTS = {
    "baseball": "https://v1.baseball.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "american-football": "https://v1.american-football.api-sports.io",
    "hockey": "https://v1.hockey.api-sports.io",
    "football": "https://v3.football.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "afl": "https://v1.afl.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
}

def get_current_season(league: str) -> int:
    """
    Determine the current season for a league based on its start and end dates.
    
    Args:
        league (str): The league identifier (e.g., "NBA", "MLB", etc.)
        
    Returns:
        int: The current season year
    """
    if league not in LEAGUE_SEASON_STARTS:
        return datetime.now().year
        
    season_info = LEAGUE_SEASON_STARTS[league]
    current_date = datetime.now()
    start_date = datetime.strptime(season_info["start"], "%Y-%m-%d")
    end_date = datetime.strptime(season_info["end"], "%Y-%m-%d")
    
    # If we're in the current season
    if start_date <= current_date <= end_date:
        return start_date.year
        
    # If we're before the season starts
    if current_date < start_date:
        return start_date.year - 1
        
    # If we're after the season ends
    return end_date.year

def get_auto_season_year(league: str) -> int:
    """
    Automatically determine the correct season year for a league based on the current date
    and the league's standard start/end dates (including playoffs).
    Returns the year that should be sent to the API for the current date.
    """
    from datetime import datetime
    current_date = datetime.now()
    season_info = LEAGUE_SEASON_STARTS.get(league)
    if not season_info:
        return current_date.year
    start = datetime.strptime(season_info["start"], "%Y-%m-%d")
    end = datetime.strptime(season_info["end"], "%Y-%m-%d")
    # If the current date is within the season (including playoffs), use the start year
    if start <= current_date <= end:
        return start.year
    # If before the season starts, use the previous season's start year
    if current_date < start:
        return start.year - 1
    # If after the season ends, use the end year (for leagues that roll over)
    return end.year

load_dotenv()
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

# Map league config keys to API host and country_id
LEAGUE_API_INFO = {
    'MLB': {'host': 'v1.baseball.api-sports.io', 'country_id': 1},
    'NBA': {'host': 'v1.basketball.api-sports.io', 'country_id': 1},
    'NHL': {'host': 'v1.hockey.api-sports.io', 'country_id': 1},
    # Add more as needed
}

def fetch_league_id(league_name, country_id, season, host, api_key):
    url = f"https://{host}/leagues"
    params = {
        "name": league_name,
        "country_id": country_id,
        "season": season
    }
    headers = {"x-apisports-key": api_key}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        for entry in data.get("response", []):
            league = entry.get("league", {})
            return league.get("id")
    except Exception as e:
        print(f"Error fetching league ID for {league_name}: {e}")
    return None

if __name__ == "__main__":
    # Example: update LEAGUE_IDS for all leagues in LEAGUE_API_INFO
    season = 2025  # or dynamically set
    for league_key, info in LEAGUE_API_INFO.items():
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        league_name = league_conf.get('name', league_key)
        country_id = info['country_id']
        host = info['host']
        league_id = fetch_league_id(league_name, country_id, season, host, API_KEY)
        if league_id:
            LEAGUE_IDS[league_key] = {
                'id': league_id,
                'sport': league_conf.get('sport', ''),
                'name': league_name
            }
            print(f"Updated {league_key}: id={league_id}")
        else:
            print(f"Could not find ID for {league_key}")
    print("\nFinal LEAGUE_IDS:")
    for k, v in LEAGUE_IDS.items():
        print(f"{k}: {v}")
