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
    "Brazil_Serie_A": {"id": 71, "name": "Brazil Serie A", "sport": "Soccer"},
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
    "EuropeanTour": {"id": 3, "name": "European Tour", "sport": "Golf"},
    "LIVGolf": {"id": 4, "name": "LIV Golf", "sport": "Golf"},
    "RyderCup": {"id": 5, "name": "Ryder Cup", "sport": "Golf"},
    "PresidentsCup": {"id": 6, "name": "Presidents Cup", "sport": "Golf"},
    "KornFerry": {"id": 7, "name": "Korn Ferry Tour", "sport": "Golf"},
    "ChampionsTour": {"id": 8, "name": "Champions Tour", "sport": "Golf"},
    "SolheimCup": {"id": 9, "name": "Solheim Cup", "sport": "Golf"},
    "OlympicGolf": {"id": 10, "name": "Olympic Golf", "sport": "Golf"},
    # MMA
    "MMA": {"id": 1, "name": "UFC", "sport": "MMA"},
    "Bellator": {"id": 2, "name": "Bellator MMA", "sport": "MMA"},
    # Darts
    "PDC": {"id": 1, "name": "Professional Darts Corporation", "sport": "Darts"},
    "BDO": {"id": 2, "name": "British Darts Organisation", "sport": "Darts"},
    "WDF": {"id": 3, "name": "World Darts Federation", "sport": "Darts"},
    "PremierLeagueDarts": {"id": 4, "name": "Premier League Darts", "sport": "Darts"},
    "WorldMatchplay": {"id": 5, "name": "World Matchplay", "sport": "Darts"},
    "WorldGrandPrix": {"id": 6, "name": "World Grand Prix", "sport": "Darts"},
    "UKOpen": {"id": 7, "name": "UK Open", "sport": "Darts"},
    "GrandSlam": {"id": 8, "name": "Grand Slam", "sport": "Darts"},
    "PlayersChampionship": {"id": 9, "name": "Players Championship", "sport": "Darts"},
    "EuropeanChampionship": {
        "id": 10,
        "name": "European Championship",
        "sport": "Darts",
    },
    "Masters": {"id": 11, "name": "Masters", "sport": "Darts"},
    # Racing
    "Formula1": {"id": 1, "name": "Formula 1", "sport": "Racing"},
    "NASCAR": {"id": 2, "name": "NASCAR", "sport": "Racing"},
    "IndyCar": {"id": 3, "name": "IndyCar", "sport": "Racing"},
    # Australian Football
    "AFL": {
        "id": 1,
        "name": "Australian Football League",
        "sport": "Australian Football",
    },
    # Volleyball
    "FIVB": {"id": 1, "name": "FIVB World League", "sport": "Volleyball"},
    # Handball
    "EHF": {"id": 1, "name": "EHF Champions League", "sport": "Handball"},
    # Add more leagues as needed...
}


def get_all_league_names():
    """Return a list of all league names for dropdowns."""
    return [info["name"] for info in ALL_LEAGUES.values()]


def get_all_sport_categories():
    """Return a sorted list of all unique sport categories from ALL_LEAGUES."""
    categories = set()
    for league in ALL_LEAGUES.values():
        categories.add(league["sport"])
    return sorted(categories)


def get_leagues_by_sport(sport: str):
    """Return a list of league names for a given sport category."""
    return [
        info["name"]
        for info in ALL_LEAGUES.values()
        if info["sport"].lower() == sport.lower()
    ]
