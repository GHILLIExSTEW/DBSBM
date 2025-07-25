"""
Team Display Name Mappings

This file contains mappings from full team names to display names (usually just the mascot/team name)
for all leagues and teams supported by the bot.

The mappings are organized by sport and league for easy maintenance and lookup.
"""

# MLB (Major League Baseball)
MLB_TEAMS = {
    "Arizona Diamondbacks": "Diamondbacks",
    "Atlanta Braves": "Braves",
    "Baltimore Orioles": "Orioles",
    "Boston Red Sox": "Red Sox",
    "Chicago Cubs": "Cubs",
    "Chicago White Sox": "White Sox",
    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",
    "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",
    "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",
    "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",
    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",
    "Minnesota Twins": "Twins",
    "New York Mets": "Mets",
    "New York Yankees": "Yankees",
    "Oakland Athletics": "Athletics",
    "Philadelphia Phillies": "Phillies",
    "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",
    "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",
    "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",
    "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",
    "Washington Nationals": "Nationals",
}

# NBA (National Basketball Association)
NBA_TEAMS = {
    "Atlanta Hawks": "Hawks",
    "Boston Celtics": "Celtics",
    "Brooklyn Nets": "Nets",
    "Charlotte Hornets": "Hornets",
    "Chicago Bulls": "Bulls",
    "Cleveland Cavaliers": "Cavaliers",
    "Dallas Mavericks": "Mavericks",
    "Denver Nuggets": "Nuggets",
    "Detroit Pistons": "Pistons",
    "Golden State Warriors": "Warriors",
    "Houston Rockets": "Rockets",
    "Indiana Pacers": "Pacers",
    "LA Clippers": "Clippers",
    "Los Angeles Clippers": "Clippers",
    "Los Angeles Lakers": "Lakers",
    "Memphis Grizzlies": "Grizzlies",
    "Miami Heat": "Heat",
    "Milwaukee Bucks": "Bucks",
    "Minnesota Timberwolves": "Timberwolves",
    "New Orleans Pelicans": "Pelicans",
    "New York Knicks": "Knicks",
    "Oklahoma City Thunder": "Thunder",
    "Orlando Magic": "Magic",
    "Philadelphia 76ers": "76ers",
    "Phoenix Suns": "Suns",
    "Portland Trail Blazers": "Trail Blazers",
    "Sacramento Kings": "Kings",
    "San Antonio Spurs": "Spurs",
    "Toronto Raptors": "Raptors",
    "Utah Jazz": "Jazz",
    "Washington Wizards": "Wizards",
}

# NFL (National Football League)
NFL_TEAMS = {
    "Arizona Cardinals": "Cardinals",
    "Atlanta Falcons": "Falcons",
    "Baltimore Ravens": "Ravens",
    "Buffalo Bills": "Bills",
    "Carolina Panthers": "Panthers",
    "Chicago Bears": "Bears",
    "Cincinnati Bengals": "Bengals",
    "Cleveland Browns": "Browns",
    "Dallas Cowboys": "Cowboys",
    "Denver Broncos": "Broncos",
    "Detroit Lions": "Lions",
    "Green Bay Packers": "Packers",
    "Houston Texans": "Texans",
    "Indianapolis Colts": "Colts",
    "Jacksonville Jaguars": "Jaguars",
    "Kansas City Chiefs": "Chiefs",
    "Las Vegas Raiders": "Raiders",
    "Los Angeles Chargers": "Chargers",
    "Los Angeles Rams": "Rams",
    "Miami Dolphins": "Dolphins",
    "Minnesota Vikings": "Vikings",
    "New England Patriots": "Patriots",
    "New Orleans Saints": "Saints",
    "New York Giants": "Giants",
    "New York Jets": "Jets",
    "Philadelphia Eagles": "Eagles",
    "Pittsburgh Steelers": "Steelers",
    "San Francisco 49ers": "49ers",
    "Seattle Seahawks": "Seahawks",
    "Tampa Bay Buccaneers": "Buccaneers",
    "Tennessee Titans": "Titans",
    "Washington Commanders": "Commanders",
}

# NHL (National Hockey League)
NHL_TEAMS = {
    "Anaheim Ducks": "Ducks",
    "Arizona Coyotes": "Coyotes",
    "Boston Bruins": "Bruins",
    "Buffalo Sabres": "Sabres",
    "Calgary Flames": "Flames",
    "Carolina Hurricanes": "Hurricanes",
    "Chicago Blackhawks": "Blackhawks",
    "Colorado Avalanche": "Avalanche",
    "Columbus Blue Jackets": "Blue Jackets",
    "Dallas Stars": "Stars",
    "Detroit Red Wings": "Red Wings",
    "Edmonton Oilers": "Oilers",
    "Florida Panthers": "Panthers",
    "Los Angeles Kings": "Kings",
    "Minnesota Wild": "Wild",
    "Montreal Canadiens": "Canadiens",
    "Nashville Predators": "Predators",
    "New Jersey Devils": "Devils",
    "New York Islanders": "Islanders",
    "New York Rangers": "Rangers",
    "Ottawa Senators": "Senators",
    "Philadelphia Flyers": "Flyers",
    "Pittsburgh Penguins": "Penguins",
    "San Jose Sharks": "Sharks",
    "Seattle Kraken": "Kraken",
    "St. Louis Blues": "Blues",
    "Tampa Bay Lightning": "Lightning",
    "Toronto Maple Leafs": "Maple Leafs",
    "Vancouver Canucks": "Canucks",
    "Vegas Golden Knights": "Golden Knights",
    "Washington Capitals": "Capitals",
    "Winnipeg Jets": "Jets",
}

# NCAA Football
NCAA_FOOTBALL_TEAMS = {
    # ACC
    "Boston College Eagles": "Eagles",
    "Clemson Tigers": "Tigers",
    "Duke Blue Devils": "Blue Devils",
    "Florida State Seminoles": "Seminoles",
    "Georgia Tech Yellow Jackets": "Yellow Jackets",
    "Louisville Cardinals": "Cardinals",
    "Miami Hurricanes": "Hurricanes",
    "NC State Wolfpack": "Wolfpack",
    "North Carolina Tar Heels": "Tar Heels",
    "Pittsburgh Panthers": "Panthers",
    "Syracuse Orange": "Orange",
    "Virginia Cavaliers": "Cavaliers",
    "Virginia Tech Hokies": "Hokies",
    "Wake Forest Demon Deacons": "Demon Deacons",
    # Big 12
    "Baylor Bears": "Bears",
    "BYU Cougars": "Cougars",
    "Cincinnati Bearcats": "Bearcats",
    "Houston Cougars": "Cougars",
    "Iowa State Cyclones": "Cyclones",
    "Kansas Jayhawks": "Jayhawks",
    "Kansas State Wildcats": "Wildcats",
    "Oklahoma Sooners": "Sooners",
    "Oklahoma State Cowboys": "Cowboys",
    "TCU Horned Frogs": "Horned Frogs",
    "Texas Longhorns": "Longhorns",
    "Texas Tech Red Raiders": "Red Raiders",
    "UCF Knights": "Knights",
    "West Virginia Mountaineers": "Mountaineers",
    # Big Ten
    "Illinois Fighting Illini": "Fighting Illini",
    "Indiana Hoosiers": "Hoosiers",
    "Iowa Hawkeyes": "Hawkeyes",
    "Maryland Terrapins": "Terrapins",
    "Michigan Wolverines": "Wolverines",
    "Michigan State Spartans": "Spartans",
    "Minnesota Golden Gophers": "Golden Gophers",
    "Nebraska Cornhuskers": "Cornhuskers",
    "Northwestern Wildcats": "Wildcats",
    "Ohio State Buckeyes": "Buckeyes",
    "Penn State Nittany Lions": "Nittany Lions",
    "Purdue Boilermakers": "Boilermakers",
    "Rutgers Scarlet Knights": "Scarlet Knights",
    "Wisconsin Badgers": "Badgers",
    # SEC
    "Alabama Crimson Tide": "Crimson Tide",
    "Arkansas Razorbacks": "Razorbacks",
    "Auburn Tigers": "Tigers",
    "Florida Gators": "Gators",
    "Georgia Bulldogs": "Bulldogs",
    "Kentucky Wildcats": "Wildcats",
    "LSU Tigers": "Tigers",
    "Mississippi State Bulldogs": "Bulldogs",
    "Missouri Tigers": "Tigers",
    "Ole Miss Rebels": "Rebels",
    "South Carolina Gamecocks": "Gamecocks",
    "Tennessee Volunteers": "Volunteers",
    "Texas A&M Aggies": "Aggies",
    "Vanderbilt Commodores": "Commodores",
    # Pac-12
    "Arizona Wildcats": "Wildcats",
    "Arizona State Sun Devils": "Sun Devils",
    "California Golden Bears": "Golden Bears",
    "Colorado Buffaloes": "Buffaloes",
    "Oregon Ducks": "Ducks",
    "Oregon State Beavers": "Beavers",
    "Stanford Cardinal": "Cardinal",
    "UCLA Bruins": "Bruins",
    "USC Trojans": "Trojans",
    "Utah Utes": "Utes",
    "Washington Huskies": "Huskies",
    "Washington State Cougars": "Cougars",
}

# NCAA Basketball
NCAA_BASKETBALL_TEAMS = {
    # ACC
    "Boston College Eagles": "Eagles",
    "Clemson Tigers": "Tigers",
    "Duke Blue Devils": "Blue Devils",
    "Florida State Seminoles": "Seminoles",
    "Georgia Tech Yellow Jackets": "Yellow Jackets",
    "Louisville Cardinals": "Cardinals",
    "Miami Hurricanes": "Hurricanes",
    "NC State Wolfpack": "Wolfpack",
    "North Carolina Tar Heels": "Tar Heels",
    "Notre Dame Fighting Irish": "Fighting Irish",
    "Pittsburgh Panthers": "Panthers",
    "Syracuse Orange": "Orange",
    "Virginia Cavaliers": "Cavaliers",
    "Virginia Tech Hokies": "Hokies",
    "Wake Forest Demon Deacons": "Demon Deacons",
    # Big 12
    "Baylor Bears": "Bears",
    "BYU Cougars": "Cougars",
    "Cincinnati Bearcats": "Bearcats",
    "Houston Cougars": "Cougars",
    "Iowa State Cyclones": "Cyclones",
    "Kansas Jayhawks": "Jayhawks",
    "Kansas State Wildcats": "Wildcats",
    "Oklahoma Sooners": "Sooners",
    "Oklahoma State Cowboys": "Cowboys",
    "TCU Horned Frogs": "Horned Frogs",
    "Texas Longhorns": "Longhorns",
    "Texas Tech Red Raiders": "Red Raiders",
    "UCF Knights": "Knights",
    "West Virginia Mountaineers": "Mountaineers",
    # Big Ten
    "Illinois Fighting Illini": "Fighting Illini",
    "Indiana Hoosiers": "Hoosiers",
    "Iowa Hawkeyes": "Hawkeyes",
    "Maryland Terrapins": "Terrapins",
    "Michigan Wolverines": "Wolverines",
    "Michigan State Spartans": "Spartans",
    "Minnesota Golden Gophers": "Golden Gophers",
    "Nebraska Cornhuskers": "Cornhuskers",
    "Northwestern Wildcats": "Wildcats",
    "Ohio State Buckeyes": "Buckeyes",
    "Penn State Nittany Lions": "Nittany Lions",
    "Purdue Boilermakers": "Boilermakers",
    "Rutgers Scarlet Knights": "Scarlet Knights",
    "Wisconsin Badgers": "Badgers",
    # SEC
    "Alabama Crimson Tide": "Crimson Tide",
    "Arkansas Razorbacks": "Razorbacks",
    "Auburn Tigers": "Tigers",
    "Florida Gators": "Gators",
    "Georgia Bulldogs": "Bulldogs",
    "Kentucky Wildcats": "Wildcats",
    "LSU Tigers": "Tigers",
    "Mississippi State Bulldogs": "Bulldogs",
    "Missouri Tigers": "Tigers",
    "Ole Miss Rebels": "Rebels",
    "South Carolina Gamecocks": "Gamecocks",
    "Tennessee Volunteers": "Volunteers",
    "Texas A&M Aggies": "Aggies",
    "Vanderbilt Commodores": "Commodores",
    # Pac-12
    "Arizona Wildcats": "Wildcats",
    "Arizona State Sun Devils": "Sun Devils",
    "California Golden Bears": "Golden Bears",
    "Colorado Buffaloes": "Buffaloes",
    "Oregon Ducks": "Ducks",
    "Oregon State Beavers": "Beavers",
    "Stanford Cardinal": "Cardinal",
    "UCLA Bruins": "Bruins",
    "USC Trojans": "Trojans",
    "Utah Utes": "Utes",
    "Washington Huskies": "Huskies",
    "Washington State Cougars": "Cougars",
}

# UFC (Ultimate Fighting Championship)
UFC_FIGHTERS = {
    # This would be populated with fighter names, but typically we show full names for fighters
    # as they don't have "mascot" names like teams do
}

# Formula 1
F1_TEAMS = {
    "Red Bull Racing": "Red Bull",
    "Mercedes": "Mercedes",
    "Ferrari": "Ferrari",
    "McLaren": "McLaren",
    "Aston Martin": "Aston Martin",
    "Alpine": "Alpine",
    "Williams": "Williams",
    "AlphaTauri": "AlphaTauri",
    "Alfa Romeo": "Alfa Romeo",
    "Haas F1 Team": "Haas",
}

# Soccer (Major Leagues)
SOCCER_TEAMS = {
    # Premier League
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton & Hove Albion": "Brighton",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Liverpool": "Liverpool",
    "Luton Town": "Luton",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nottingham Forest",
    "Sheffield United": "Sheffield United",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    # La Liga
    "Real Madrid": "Real Madrid",
    "Barcelona": "Barcelona",
    "Atletico Madrid": "Atletico Madrid",
    "Sevilla": "Sevilla",
    "Real Sociedad": "Real Sociedad",
    "Villarreal": "Villarreal",
    "Athletic Bilbao": "Athletic Bilbao",
    "Real Betis": "Real Betis",
    "Valencia": "Valencia",
    "Girona": "Girona",
    "Las Palmas": "Las Palmas",
    "Rayo Vallecano": "Rayo Vallecano",
    "Osasuna": "Osasuna",
    "Getafe": "Getafe",
    "Mallorca": "Mallorca",
    "Celta Vigo": "Celta Vigo",
    "Alaves": "Alaves",
    "Granada": "Granada",
    "Cadiz": "Cadiz",
    "Almeria": "Almeria",
    # Bundesliga
    "Bayern Munich": "Bayern Munich",
    "Bayer Leverkusen": "Leverkusen",
    "Stuttgart": "Stuttgart",
    "RB Leipzig": "RB Leipzig",
    "Borussia Dortmund": "Dortmund",
    "Hoffenheim": "Hoffenheim",
    "Eintracht Frankfurt": "Frankfurt",
    "Heidenheim": "Heidenheim",
    "SC Freiburg": "Freiburg",
    "VfL Wolfsburg": "Wolfsburg",
    "1. FC Heidenheim": "Heidenheim",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "1. FC Union Berlin": "Union Berlin",
    "Borussia Monchengladbach": "Monchengladbach",
    "Werder Bremen": "Bremen",
    "1. FC Koln": "Koln",
    "FSV Mainz 05": "Mainz",
    "VfB Stuttgart": "Stuttgart",
    "SV Darmstadt 98": "Darmstadt",
    "FC Augsburg": "Augsburg",
    # Serie A
    "Inter Milan": "Inter",
    "Juventus": "Juventus",
    "AC Milan": "AC Milan",
    "Atalanta": "Atalanta",
    "Bologna": "Bologna",
    "Fiorentina": "Fiorentina",
    "Roma": "Roma",
    "Lazio": "Lazio",
    "Napoli": "Napoli",
    "Torino": "Torino",
    "Genoa": "Genoa",
    "Monza": "Monza",
    "Lecce": "Lecce",
    "Sassuolo": "Sassuolo",
    "Frosinone": "Frosinone",
    "Cagliari": "Cagliari",
    "Udinese": "Udinese",
    "Empoli": "Empoli",
    "Verona": "Verona",
    "Salernitana": "Salernitana",
    # Ligue 1
    "Paris Saint-Germain": "PSG",
    "Nice": "Nice",
    "Monaco": "Monaco",
    "Brest": "Brest",
    "Lille": "Lille",
    "Lens": "Lens",
    "Reims": "Reims",
    "Le Havre": "Le Havre",
    "Strasbourg": "Strasbourg",
    "Nantes": "Nantes",
    "Marseille": "Marseille",
    "Lyon": "Lyon",
    "Toulouse": "Toulouse",
    "Rennes": "Rennes",
    "Clermont Foot": "Clermont",
    "Metz": "Metz",
    "Montpellier": "Montpellier",
    "Lorient": "Lorient",
    "Troyes": "Troyes",
    "Angers": "Angers",
}

# Combine all team mappings
ALL_TEAM_MAPPINGS = {
    **MLB_TEAMS,
    **NBA_TEAMS,
    **NFL_TEAMS,
    **NHL_TEAMS,
    **NCAA_FOOTBALL_TEAMS,
    **NCAA_BASKETBALL_TEAMS,
    **F1_TEAMS,
    **SOCCER_TEAMS,
}


def get_team_display_name(team_name: str) -> str:
    """
    Get the display name for a team.

    Args:
        team_name (str): The full team name

    Returns:
        str: The display name (usually just the mascot/team name)
    """
    return ALL_TEAM_MAPPINGS.get(team_name, team_name)


def get_team_display_name_by_league(team_name: str, league: str) -> str:
    """
    Get the display name for a team by specific league.

    Args:
        team_name (str): The full team name
        league (str): The league name

    Returns:
        str: The display name (usually just the mascot/team name)
    """
    league_mappings = {
        "MLB": MLB_TEAMS,
        "NBA": NBA_TEAMS,
        "NFL": NFL_TEAMS,
        "NHL": NHL_TEAMS,
        "NCAA": {**NCAA_FOOTBALL_TEAMS, **NCAA_BASKETBALL_TEAMS},
        "F1": F1_TEAMS,
        "SOCCER": SOCCER_TEAMS,
    }

    league_teams = league_mappings.get(league, {})
    return league_teams.get(team_name, team_name)
