# List of all available leagues (add more as needed)
ALL_LEAGUES = {
    # Soccer
    "EPL": {"id": 39, "name": "English Premier League", "sport": "Soccer"},
    "LaLiga": {"id": 140, "name": "La Liga", "sport": "Soccer"},
    "Bundesliga": {"id": 78, "name": "Bundesliga", "sport": "Soccer"},
    "SerieA": {"id": 135, "name": "Serie A", "sport": "Soccer"},
    "Ligue1": {"id": 61, "name": "Ligue 1", "sport": "Soccer"},
    "MLS": {"id": 253, "name": "Major League Soccer", "sport": "Soccer"},
    "ChampionsLeague": {"id": 2, "name": "UEFA Champions League", "sport": "Soccer"},
    "EuropaLeague": {"id": 3, "name": "UEFA Europa League", "sport": "Soccer"},
    "WorldCup": {"id": 15, "name": "FIFA World Cup", "sport": "Soccer"},
    # Sweden Leagues
    "Allsvenskan": {"id": 113, "name": "Allsvenskan", "sport": "Soccer"},
    "Superettan": {"id": 114, "name": "Superettan", "sport": "Soccer"},
    "Ettan - Norra": {"id": 563, "name": "Ettan - Norra", "sport": "Soccer"},
    # Basketball
    "NBA": {"id": 12, "name": "NBA", "sport": "Basketball"},
    "WNBA": {"id": 13, "name": "WNBA", "sport": "Basketball"},
    "EuroLeague": {"id": 1, "name": "EuroLeague", "sport": "Basketball"},
    # Baseball
    "MLB": {"id": 1, "name": "MLB", "sport": "Baseball"},
    "NPB": {"id": 2, "name": "NPB", "sport": "Baseball"},
    "KBO": {"id": 3, "name": "KBO", "sport": "Baseball"},
    # Hockey
    "NHL": {"id": 57, "name": "NHL", "sport": "Hockey"},
    "KHL": {"id": 1, "name": "Kontinental Hockey League", "sport": "Hockey"},
    # American Football
    "NFL": {"id": 1, "name": "NFL", "sport": "American Football"},
    "NCAA": {"id": 2, "name": "NCAA Football", "sport": "American Football"},
    "CFL": {"id": 3, "name": "CFL", "sport": "American Football"},
    # Rugby
    "SuperRugby": {"id": 1, "name": "Super Rugby", "sport": "Rugby"},
    "SixNations": {"id": 2, "name": "Six Nations Championship", "sport": "Rugby"},
    # Tennis
    "ATP": {"id": 2, "name": "ATP Tour", "sport": "Tennis"},
    "WTA": {"id": 3, "name": "WTA Tour", "sport": "Tennis"},
    # Golf
    "PGA": {"id": 1, "name": "PGA Tour", "sport": "Golf"},
    "LPGA": {"id": 2, "name": "LPGA Tour", "sport": "Golf"},
    # MMA
    "MMA": {"id": 1, "name": "UFC", "sport": "MMA"},
    "Bellator": {"id": 2, "name": "Bellator MMA", "sport": "MMA"},
    # Darts
    "PDC": {"id": 1, "name": "Professional Darts Corporation", "sport": "Darts"},
    # Add more leagues as needed...
}

def get_all_league_names():
    """Return a list of all league names for dropdowns."""
    return [info["name"] for info in ALL_LEAGUES.values()] 