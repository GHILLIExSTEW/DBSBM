"""Constants for parlay betting functionality."""

# Allowed leagues for parlay betting
ALLOWED_LEAGUES = [
    "NFL",
    "EPL",
    "NBA",
    "MLB",
    "NHL",
    "La Liga",
    "NCAA",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
    "MLS",
    "ChampionsLeague",
    "EuropaLeague",
    "Brazil Serie A",
    "WorldCup",
    "Formula 1",
    "Tennis",
    "ATP",
    "WTA",
    "MMA",
    "Bellator",
    "WNBA",
    "CFL",
    "AFL",
    "PDC",
    "BDO",
    "WDF",
    "Premier League Darts",
    "World Matchplay",
    "World Grand Prix",
    "UK Open",
    "Grand Slam",
    "Players Championship",
    "European Championship",
    "Masters",
    "EuroLeague",
    "NPB",
    "KBO",
    "KHL",
    "PGA",
    "LPGA",
    "EuropeanTour",
    "LIVGolf",
    "RyderCup",
    "PresidentsCup",
    "SuperRugby",
    "SixNations",
    "FIVB",
    "EHF",
]

# League name normalization mapping
LEAGUE_FILE_KEY_MAP = {
    "La Liga": "LaLiga",
    "Serie A": "SerieA",
    "Ligue 1": "Ligue1",
    "EPL": "EPL",
    "Bundesliga": "Bundesliga",
    "MLS": "MLS",
    "NBA": "NBA",
    "WNBA": "WNBA",
    "MLB": "MLB",
    "NHL": "NHL",
    "NFL": "NFL",
    "NCAA": [
        "NCAAF",
        "NCAAB",
        "NCAABM",
        "NCAABW",
        "NCAAFBS",
        "NCAAVB",
        "NCAAFB",
        "NCAAWBB",
        "NCAAWVB",
        "NCAAWFB",
    ],
    "NPB": "NPB",
    "KBO": "KBO",
    "KHL": "KHL",
    "MMA": "MMA",
    "Bellator": "Bellator",
    "PDC": "PDC",
    "BDO": "BDO",
    "WDF": "WDF",
    "Premier League Darts": "PremierLeagueDarts",
    "World Matchplay": "WorldMatchplay",
    "World Grand Prix": "WorldGrandPrix",
    "UK Open": "UKOpen",
    "Grand Slam": "GrandSlam",
    "Players Championship": "PlayersChampionship",
    "European Championship": "EuropeanChampionship",
    "Masters": "Masters",
    "ChampionsLeague": "ChampionsLeague",
    "EuropaLeague": "EuropaLeague",
    "WorldCup": "WorldCup",
    "SuperRugby": "SuperRugby",
    "SixNations": "SixNations",
    "FIVB": "FIVB",
    "EHF": "EHF",
    "Tennis": "Tennis",
    "ATP": "ATP",
    "WTA": "WTA",
    "PGA": "PGA",
    "LPGA": "LPGA",
    "EuropeanTour": "EuropeanTour",
    "LIVGolf": "LIVGolf",
    "RyderCup": "RyderCup",
    "PresidentsCup": "PresidentsCup",
    "ESPORTS": ["CSGO", "VALORANT", "LOL", "DOTA 2", "PUBG", "COD"],
    "OTHER_SPORTS": ["OTHER_SPORTS"],
    # Add more as needed
    "UEFA CL": "ChampionsLeague",
}

# Line types available for betting
LINE_TYPES = [
    "Moneyline",
    "Spread",
    "Total",
    "Player Props",
    "Team Props",
    "Futures",
    "Live Betting",
]

# Units display modes
UNITS_DISPLAY_MODES = ["auto", "manual", "percentage"]

# Default values
DEFAULT_LEGS_PER_PAGE = 21
DEFAULT_UNITS = 1.0
DEFAULT_ODDS = 100


def get_league_file_key(league_name):
    """Get the file key for a league name."""
    key = LEAGUE_FILE_KEY_MAP.get(league_name, league_name.replace(" ", ""))
    if isinstance(key, list):
        return key[0]
    return key
