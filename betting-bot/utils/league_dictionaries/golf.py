# Golf League Dictionary
# Player name mappings for golf leagues

"""
Golf league dictionary for the betting bot.
Contains mappings for golf tours and tournaments.
"""

GOLF_LEAGUES = {
    "PGA": {
        "name": "PGA Tour",
        "sport": "golf",
        "type": "men",
        "tournaments": [
            "Masters Tournament",
            "PGA Championship", 
            "U.S. Open",
            "The Open Championship",
            "FedEx Cup",
            "PGA Tour Championship"
        ]
    },
    "LPGA": {
        "name": "LPGA Tour", 
        "sport": "golf",
        "type": "women",
        "tournaments": [
            "ANA Inspiration",
            "KPMG Women's PGA Championship",
            "U.S. Women's Open",
            "AIG Women's Open",
            "CME Group Tour Championship"
        ]
    },
    "EuropeanTour": {
        "name": "European Tour",
        "sport": "golf", 
        "type": "men",
        "tournaments": [
            "BMW PGA Championship",
            "DP World Tour Championship",
            "Scottish Open",
            "Irish Open",
            "French Open"
        ]
    },
    "LIVGolf": {
        "name": "LIV Golf",
        "sport": "golf",
        "type": "men",
        "tournaments": [
            "LIV Golf Invitational Series",
            "LIV Golf Team Championship"
        ]
    }
}

# Golf specific mappings
GOLF_MAPPINGS = {
    "course_types": ["links", "parkland", "desert", "mountain", "coastal"],
    "tournament_formats": ["stroke_play", "match_play", "stableford", "scramble"],
    "major_championships": ["masters", "pga", "us_open", "open_championship"]
}

# PGA Tour Players
PGA_PLAYERS = {
    "scottie scheffler": "Scottie Scheffler",
    "rory mcilroy": "Rory McIlroy",
    "jon rahm": "Jon Rahm",
    "viktor hovland": "Viktor Hovland",
    "patrick cantlay": "Patrick Cantlay",
    "xander schauffele": "Xander Schauffele",
    "max homa": "Max Homa",
    "wyndham clark": "Wyndham Clark",
    "brian harman": "Brian Harman",
    "tommy fleetwood": "Tommy Fleetwood",
    "tyrrell hatton": "Tyrrell Hatton",
    "jordan spieth": "Jordan Spieth",
    "justin thomas": "Justin Thomas",
    "collin morikawa": "Collin Morikawa",
    "sam burns": "Sam Burns",
    "tony finau": "Tony Finau",
    "sungjae im": "Sungjae Im",
    "cameron young": "Cameron Young",
    "keegan bradley": "Keegan Bradley",
    "rickie fowler": "Rickie Fowler",
    "hideki matsuyama": "Hideki Matsuyama",
    "shane lowry": "Shane Lowry",
    "corey conners": "Corey Conners",
    "sahith theegala": "Sahith Theegala",
    "kurt kitayama": "Kurt Kitayama",
    "adrian meronk": "Adrian Meronk",
    "ryan fox": "Ryan Fox",
    "seamus power": "Seamus Power",
    "dennis mccarthy": "Dennis McCarthy",
    "nick taylor": "Nick Taylor",
    "adam hadwin": "Adam Hadwin",
    "corey conners": "Corey Conners",
    "mackenzie hughes": "Mackenzie Hughes",
    "adam svensson": "Adam Svensson",
    "taylor pendrith": "Taylor Pendrith",
    "ben griffin": "Ben Griffin",
    "eric cole": "Eric Cole",
    "justin suh": "Justin Suh",
    "davis riley": "Davis Riley",
    "austin eckroat": "Austin Eckroat",
    "peter malnati": "Peter Malnati",
    "jake knapp": "Jake Knapp",
    "chandler phillips": "Chandler Phillips",
    "michael thorbjornsen": "Michael Thorbjornsen",
    "nick dunlap": "Nick Dunlap",
    "matthieu pavon": "Matthieu Pavon",
    "stephan jaeger": "Stephan Jaeger",
    "christiaan bezuidenhout": "Christiaan Bezuidenhout",
    "thomas detry": "Thomas Detry",
    "alex norén": "Alex Norén",
    "alexander björk": "Alexander Björk",
    "vincent norrman": "Vincent Norrman",
    "ludvig åberg": "Ludvig Åberg",
    "nikolai højgaard": "Nikolai Højgaard",
    "rasmus højgaard": "Rasmus Højgaard",
    "thorbjørn olesen": "Thorbjørn Olesen",
    "adrian otageui": "Adrian Otaegui",
    "jorge campillo": "Jorge Campillo",
    "rafael campos": "Rafael Campos",
    "carlos ortiz": "Carlos Ortiz",
    "abraham ancer": "Abraham Ancer",
    "jason day": "Jason Day",
    "cameron smith": "Cameron Smith",
    "marc leishman": "Marc Leishman",
    "lucas herbert": "Lucas Herbert",
    "min woo lee": "Min Woo Lee",
    "adam scott": "Adam Scott",
    "cameron davis": "Cameron Davis",
    "ryan palmer": "Ryan Palmer",
    "kevin kisner": "Kevin Kisner",
    "harold varner iii": "Harold Varner III",
    "talor gooch": "Talor Gooch",
    "dustin johnson": "Dustin Johnson",
    "bryson dechambeau": "Bryson DeChambeau",
    "brooks koepka": "Brooks Koepka",
    "phil mickelson": "Phil Mickelson",
    "sergio garcia": "Sergio Garcia",
    "lee westwood": "Lee Westwood",
    "ian poulter": "Ian Poulter",
    "henrik stenson": "Henrik Stenson",
    "louis oosthuizen": "Louis Oosthuizen",
    "charl schwartzel": "Charl Schwartzel",
    "branden grace": "Branden Grace",
    "kevin na": "Kevin Na",
    "pat perez": "Pat Perez",
    "jason kokrak": "Jason Kokrak",
    "matt jones": "Matt Jones",
    "hudson swafford": "Hudson Swafford",
    "peter uhlein": "Peter Uihlein",
    "bernd wiesberger": "Bernd Wiesberger",
    "richard bland": "Richard Bland",
    "graeme mcdowell": "Graeme McDowell",
    "martin kaymer": "Martin Kaymer",
    "paul casey": "Paul Casey",
    "danny willett": "Danny Willett",
    "matthew fitzpatrick": "Matthew Fitzpatrick",
    "justin rose": "Justin Rose",
}

# LPGA Tour Players
LPGA_PLAYERS = {
    "nelly korda": "Nelly Korda",
    "lilia vu": "Lilia Vu",
    "ruoning yin": "Ruoning Yin",
    "celine boutier": "Celine Boutier",
    "charley hull": "Charley Hull",
    "georgia hall": "Georgia Hall",
    "leona maguire": "Leona Maguire",
    "minjee lee": "Minjee Lee",
    "hannah green": "Hannah Green",
    "hyo joo kim": "Hyo Joo Kim",
    "jin young ko": "Jin Young Ko",
    "seon woo bae": "Seon Woo Bae",
    "ayaka furue": "Ayaka Furue",
    "yuka saso": "Yuka Saso",
    "atthaya thitikul": "Atthaya Thitikul",
    "patty tavatanakit": "Patty Tavatanakit",
    "brooke henderson": "Brooke Henderson",
    "maude aimee leblanc": "Maude-Aimee Leblanc",
    "alena sharp": "Alena Sharp",
    "maddie szeryk": "Maddie Szeryk",
    "sarah schmelzel": "Sarah Schmelzel",
    "lauren stephenson": "Lauren Stephenson",
    "angel yin": "Angel Yin",
    "alison lee": "Alison Lee",
    "danielle kang": "Danielle Kang",
    "jessica korda": "Jessica Korda",
    "lexi thompson": "Lexi Thompson",
    "lizette salas": "Lizette Salas",
    "marina alex": "Marina Alex",
    "austin ernst": "Austin Ernst",
    "jennifer kupcho": "Jennifer Kupcho",
    "lindsey weaver wright": "Lindsey Weaver-Wright",
    "emma talley": "Emma Talley",
    "kristen gillman": "Kristen Gillman",
    "lauren kim": "Lauren Kim",
    "rose zhang": "Rose Zhang",
    "rachel heck": "Rachel Heck",
    "emma spitz": "Emma Spitz",
    "amari avery": "Amari Avery",
    "megha ganne": "Megha Ganne",
    "lucy li": "Lucy Li",
    "alexa pano": "Alexa Pano",
    "yana wilson": "Yana Wilson",
    "gianna clemente": "Gianna Clemente",
    "anna davis": "Anna Davis",
    "lei ye": "Lei Ye",
    "xiyu lin": "Xiyu Lin",
    "yu liu": "Yu Liu",
    "wei wei zhang": "Wei Wei Zhang",
    "mengxuan zhang": "Mengxuan Zhang",
    "jing yan": "Jing Yan",
    "xinyu wang": "Xinyu Wang",
    "ruixin liu": "Ruixin Liu",
    "yuting shi": "Yuting Shi",
}

# European Tour Players
EUROPEAN_TOUR_PLAYERS = {
    "rory mcilroy": "Rory McIlroy",
    "jon rahm": "Jon Rahm",
    "viktor hovland": "Viktor Hovland",
    "tyrrell hatton": "Tyrrell Hatton",
    "tommy fleetwood": "Tommy Fleetwood",
    "justin rose": "Justin Rose",
    "danny willett": "Danny Willett",
    "matthew fitzpatrick": "Matthew Fitzpatrick",
    "ian poulter": "Ian Poulter",
    "lee westwood": "Lee Westwood",
    "sergio garcia": "Sergio Garcia",
    "henrik stenson": "Henrik Stenson",
    "louis oosthuizen": "Louis Oosthuizen",
    "charl schwartzel": "Charl Schwartzel",
    "branden grace": "Branden Grace",
    "bernd wiesberger": "Bernd Wiesberger",
    "richard bland": "Richard Bland",
    "graeme mcdowell": "Graeme McDowell",
    "martin kaymer": "Martin Kaymer",
    "paul casey": "Paul Casey",
    "adrian otageui": "Adrian Otaegui",
    "jorge campillo": "Jorge Campillo",
    "rafael campos": "Rafael Campos",
    "carlos ortiz": "Carlos Ortiz",
    "abraham ancer": "Abraham Ancer",
    "jason day": "Jason Day",
    "cameron smith": "Cameron Smith",
    "marc leishman": "Marc Leishman",
    "lucas herbert": "Lucas Herbert",
    "min woo lee": "Min Woo Lee",
    "adam scott": "Adam Scott",
    "cameron davis": "Cameron Davis",
    "ryan palmer": "Ryan Palmer",
    "kevin kisner": "Kevin Kisner",
    "harold varner iii": "Harold Varner III",
    "talor gooch": "Talor Gooch",
    "dustin johnson": "Dustin Johnson",
    "bryson dechambeau": "Bryson DeChambeau",
    "brooks koepka": "Brooks Koepka",
    "phil mickelson": "Phil Mickelson",
    "sergio garcia": "Sergio Garcia",
    "lee westwood": "Lee Westwood",
    "ian poulter": "Ian Poulter",
    "henrik stenson": "Henrik Stenson",
    "louis oosthuizen": "Louis Oosthuizen",
    "charl schwartzel": "Charl Schwartzel",
    "branden grace": "Branden Grace",
    "kevin na": "Kevin Na",
    "pat perez": "Pat Perez",
    "jason kokrak": "Jason Kokrak",
    "matt jones": "Matt Jones",
    "hudson swafford": "Hudson Swafford",
    "peter uhlein": "Peter Uihlein",
    "bernd wiesberger": "Bernd Wiesberger",
    "richard bland": "Richard Bland",
    "graeme mcdowell": "Graeme McDowell",
    "martin kaymer": "Martin Kaymer",
    "paul casey": "Paul Casey",
    "danny willett": "Danny Willett",
    "matthew fitzpatrick": "Matthew Fitzpatrick",
    "justin rose": "Justin Rose",
}

# LIV Golf Players
LIV_GOLF_PLAYERS = {
    "dustin johnson": "Dustin Johnson",
    "bryson dechambeau": "Bryson DeChambeau",
    "brooks koepka": "Brooks Koepka",
    "phil mickelson": "Phil Mickelson",
    "sergio garcia": "Sergio Garcia",
    "lee westwood": "Lee Westwood",
    "ian poulter": "Ian Poulter",
    "henrik stenson": "Henrik Stenson",
    "louis oosthuizen": "Louis Oosthuizen",
    "charl schwartzel": "Charl Schwartzel",
    "branden grace": "Branden Grace",
    "kevin na": "Kevin Na",
    "pat perez": "Pat Perez",
    "jason kokrak": "Jason Kokrak",
    "matt jones": "Matt Jones",
    "hudson swafford": "Hudson Swafford",
    "peter uhlein": "Peter Uihlein",
    "bernd wiesberger": "Bernd Wiesberger",
    "richard bland": "Richard Bland",
    "graeme mcdowell": "Graeme McDowell",
    "martin kaymer": "Martin Kaymer",
    "paul casey": "Paul Casey",
    "danny willett": "Danny Willett",
    "matthew fitzpatrick": "Matthew Fitzpatrick",
    "justin rose": "Justin Rose",
    "tyrrell hatton": "Tyrrell Hatton",
    "adrian otageui": "Adrian Otaegui",
    "jorge campillo": "Jorge Campillo",
    "rafael campos": "Rafael Campos",
    "carlos ortiz": "Carlos Ortiz",
    "abraham ancer": "Abraham Ancer",
    "jason day": "Jason Day",
    "cameron smith": "Cameron Smith",
    "marc leishman": "Marc Leishman",
    "lucas herbert": "Lucas Herbert",
    "min woo lee": "Min Woo Lee",
    "adam scott": "Adam Scott",
    "cameron davis": "Cameron Davis",
    "ryan palmer": "Ryan Palmer",
    "kevin kisner": "Kevin Kisner",
    "harold varner iii": "Harold Varner III",
    "talor gooch": "Talor Gooch",
}

# Ryder Cup Teams
RYDER_CUP_TEAMS = {
    "team usa": "Team USA",
    "team europe": "Team Europe",
    "usa": "Team USA",
    "europe": "Team Europe",
    "united states": "Team USA",
    "european team": "Team Europe",
}

# Presidents Cup Teams
PRESIDENTS_CUP_TEAMS = {
    "team usa": "Team USA",
    "team international": "Team International",
    "usa": "Team USA",
    "international": "Team International",
    "united states": "Team USA",
    "international team": "Team International",
}

# Golf Team/Player mappings by league
GOLF_TEAM_MAPPINGS = {
    "PGA": PGA_PLAYERS,
    "LPGA": LPGA_PLAYERS,
    "EuropeanTour": EUROPEAN_TOUR_PLAYERS,
    "LIVGolf": LIV_GOLF_PLAYERS,
    "RyderCup": RYDER_CUP_TEAMS,
    "PresidentsCup": PRESIDENTS_CUP_TEAMS,
}

# Export the main mapping function
def get_golf_player_name(player_name: str, league: str = "PGA") -> str:
    """Get normalized golf player name for a given league."""
    if not player_name:
        return player_name
    
    player_name_lower = player_name.lower().strip()
    league_mappings = GOLF_TEAM_MAPPINGS.get(league, PGA_PLAYERS)
    
    # Try exact match first
    if player_name_lower in league_mappings:
        return league_mappings[player_name_lower]
    
    # Try fuzzy matching
    import difflib
    matches = difflib.get_close_matches(player_name_lower, league_mappings.keys(), n=1, cutoff=0.75)
    if matches:
        return league_mappings[matches[0]]
    
    # Return title case as fallback
    return player_name.title() 