"""Configuration for asset paths and directory structure."""

import os
import logging
from .leagues import LEAGUE_CONFIG

logger = logging.getLogger(__name__)

# Base directory structure
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")
# LOGO_DIR = os.path.join(ASSETS_DIR, "logos")
# TEAMS_SUBDIR = os.path.join(LOGO_DIR, "teams")
# LEAGUES_SUBDIR = os.path.join(LOGO_DIR, "leagues")

# Sport categories and their leagues
SPORT_CATEGORIES = {
    "BASKETBALL": [
        "NBA", "NCAAB", "WNBA", "EUROLEAGUE", "CBA",  # Current leagues
        "BRITISH BASKETBALL LEAGUE",
        "G_LEAGUE", "NBL", "BASKETBALL_CHAMPIONS_LEAGUE", "FIBA_AMERICAS",
        "FIBA_ASIA", "FIBA_EUROPE", "FIBA_OCEANIA", "FIBA_AFRICA"
    ],
    "FOOTBALL": [
        "NFL", "NCAAF", "CFL", "XFL", "USFL",  # Current leagues
        "AFL", "ARENA_FOOTBALL", "IFAF", "WORLD_FOOTBALL_LEAGUE"
    ],
    "HOCKEY": [
        "NHL", "AHL", "NCAAH",  # Current leagues
        "KHL", "SHL", "DEL", "LIIGA", "NLA", "EIHL", "CHL", "SPHL", "ECHL",
        "IIHF_WORLD_CHAMPIONSHIP", "IIHF_WORLD_JUNIORS", "OLYMPIC_HOCKEY"
    ],
    "BASEBALL": [
        "MLB", "NPB", "KBO",  # Current leagues
        "NCAAB_BASEBALL", "LIDOM", "ABL", "CPBL", "LMB", "WBSC_PREMIER12",
        "WORLD_BASEBALL_CLASSIC", "CARIBBEAN_SERIES"
    ],
    "SOCCER": [
        "MLS", "EPL", "LA_LIGA", "BUNDESLIGA", "SERIE_A", "LIGUE_1",
        "UEFACL", "EuropaLeague", "WORLDCUP",
        "Allsvenskan", "Superettan", "Damallsvenskan", "Elitettan",
        "Svenska_Cupen", "Svenska_Cupen_-_Women",
        "Ettan_-_Norra", "Ettan_-_Södra", "Ettan_-_Relegation_Round",
        "Division_2_-_Norra_Götaland", "Division_2_-_Norra_Svealand", "Division_2_-_Norrland",
        "Division_2_-_Södra_Svealand", "Division_2_-_Västra_Götaland", "Division_2_-_Östra_Götaland"
    ],
    "TENNIS": [
        "ATP", "WTA",  # Current leagues
        "ITF", "GRAND_SLAM", "DAVIS_CUP", "BILLIE_JEAN_KING_CUP",
        "ATP_FINALS", "WTA_FINALS", "OLYMPIC_TENNIS"
    ],
    "GOLF": [
        "PGA", "LPGA",  # Current leagues
        "EUROPEAN_TOUR", "KORN_FERRY", "CHAMPIONS_TOUR", "LIV_GOLF",
        "RYDER_CUP", "PRESIDENTS_CUP", "SOLHEIM_CUP", "OLYMPIC_GOLF"
    ],
    "RACING": [
        "F1", "NASCAR", "INDYCAR",  # Current leagues
        "MOTOGP", "WRC", "WEC", "IMSA", "SUPER_GT", "DTM", "BTCC",
        "FORMULA_E", "WORLD_RALLYCROSS", "WORLD_TOURING_CARS"
    ],
    "FIGHTING": [
        "UFC", "BOXING",  # Current leagues
        "BELLATOR", "ONE_CHAMPIONSHIP", "PFL", "RIZIN", "K_1",
        "GLORY", "BELLATOR_KICKBOXING", "ONE_KICKBOXING"
    ],
    "ESPORTS": [
        "LOL", "CSGO", "DOTA2", "VALORANT",  # Current leagues
        "OVERWATCH", "RAINBOW_SIX", "ROCKET_LEAGUE", "FIFA", "STARCRAFT",
        "HEARTHSTONE", "STREET_FIGHTER", "TEKKEN", "SMASH", "APEX_LEGENDS"
    ],
    "CRICKET": [
        "IPL", "BBL", "PSL", "CPL", "THE_HUNDRED", "T20_BLAST",
        "TEST_CRICKET", "ODI", "T20I", "WORLD_CUP", "CHAMPIONS_TROPHY"
    ],
    "RUGBY": [
        "SUPER_RUGBY", "SIX_NATIONS", "RUGBY_CHAMPIONSHIP", "PRO14",
        "TOP14", "PREMIERSHIP", "WORLD_CUP", "SEVENS", "OLYMPIC_RUGBY"
    ],
    "AUSTRALIAN_FOOTBALL": [
        "AFL", "AFLW", "VFL", "SANFL", "WAFL", "NEAFL"
    ],
    "VOLLEYBALL": [
        "FIVB", "CEV", "AVC", "NORCECA", "WORLD_LEAGUE", "NATIONS_LEAGUE",
        "WORLD_CUP", "OLYMPIC_VOLLEYBALL"
    ],
    "HANDBALL": [
        "EHF_CL", "EHF_CUP", "WORLD_CHAMPIONSHIP", "EUROPEAN_CHAMPIONSHIP",
        "OLYMPIC_HANDBALL"
    ],
    "LACROSSE": [
        "NLL", "PLL", "MLL", "WORLD_LACROSSE_CHAMPIONSHIP"
    ],
    "FIELD_HOCKEY": [
        "FIH_PRO_LEAGUE", "WORLD_CUP", "OLYMPIC_FIELD_HOCKEY",
        "EUROPEAN_CHAMPIONSHIP", "PAN_AMERICAN_CUP"
    ],
    "BADMINTON": [
        "BWF", "THOMAS_CUP", "UBER_CUP", "SUDIRMAN_CUP",
        "WORLD_CHAMPIONSHIPS", "OLYMPIC_BADMINTON"
    ],
    "TABLE_TENNIS": [
        "ITTF", "WORLD_CHAMPIONSHIPS", "WORLD_CUP", "OLYMPIC_TABLE_TENNIS"
    ],
    "SNOOKER": [
        "WORLD_CHAMPIONSHIP", "UK_CHAMPIONSHIP", "MASTERS",
        "CHAMPION_OF_CHAMPIONS", "TOUR_CHAMPIONSHIP"
    ],
    "DARTS": [
        "PDC", "BDO", "WORLD_CHAMPIONSHIP", "PREMIER_LEAGUE",
        "WORLD_MATCHPLAY", "WORLD_GRAND_PRIX"
    ],
    "CYCLING": [
        "TOUR_DE_FRANCE", "GIRO_D_ITALIA", "VUELTA_A_ESPANA",
        "WORLD_CHAMPIONSHIPS", "OLYMPIC_CYCLING"
    ]
}

# Default fallback category
DEFAULT_FALLBACK_CATEGORY = "OTHER_SPORTS"

# --- AUTO-GENERATED: Add all leagues from LEAGUE_CONFIG to SPORT_CATEGORIES ---
# Build a reverse map from sport name to SPORT_CATEGORIES key
SPORT_NAME_TO_CATEGORY = {
    'Basketball': 'BASKETBALL',
    'Baseball': 'BASEBALL',
    'Ice Hockey': 'HOCKEY',
    'American Football': 'FOOTBALL',
    'Soccer': 'SOCCER',
    'Rugby': 'RUGBY',
    'Volleyball': 'VOLLEYBALL',
    'Handball': 'HANDBALL',
    'Australian Football': 'AUSTRALIAN_FOOTBALL',
    'Tennis': 'TENNIS',
    'Golf': 'GOLF',
    'Racing': 'RACING',
    'Fighting': 'FIGHTING',
    'Darts': 'DARTS',
    'Esports': 'ESPORTS',
    'Cricket': 'CRICKET',
    'Lacrosse': 'LACROSSE',
    'Field Hockey': 'FIELD_HOCKEY',
    'Badminton': 'BADMINTON',
    'Table Tennis': 'TABLE_TENNIS',
    'Snooker': 'SNOOKER',
    'Cycling': 'CYCLING',
}

for league_key, conf in LEAGUE_CONFIG.items():
    sport = conf.get('sport')
    cat = SPORT_NAME_TO_CATEGORY.get(sport)
    if cat:
        if league_key.upper() not in SPORT_CATEGORIES[cat]:
            SPORT_CATEGORIES[cat].append(league_key.upper())
# --- END AUTO-GENERATED ---

def get_sport_category_for_path(league_name):
    league_name_norm = league_name.replace(" ", "_").replace("-", "_").upper()
    for sport, leagues in SPORT_CATEGORIES.items():
        for l in leagues:
            l_norm = l.replace(" ", "_").replace("-", "_").upper()
            if league_name_norm == l_norm:
                print(f"[DEBUG] Matched league '{league_name}' to sport '{sport}'")
                return sport
    print(f"[DEBUG] No sport category found for league: {league_name}")
    return None

def determine_asset_paths():
    """Dynamically determine asset paths based on directory structure."""
    # Create base directories if they don't exist
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(FONT_DIR, exist_ok=True)
    # os.makedirs(LOGO_DIR, exist_ok=True)
    # os.makedirs(TEAMS_SUBDIR, exist_ok=True)
    # os.makedirs(LEAGUES_SUBDIR, exist_ok=True)
    
    # Create sport category directories
    # for category in SPORT_CATEGORIES.keys():
    #     os.makedirs(os.path.join(TEAMS_SUBDIR, category), exist_ok=True)
    #     os.makedirs(os.path.join(LEAGUES_SUBDIR, category), exist_ok=True)
    #     
    #     # Create league subdirectories
    #     for league in SPORT_CATEGORIES[category]:
    #         os.makedirs(os.path.join(TEAMS_SUBDIR, category, league), exist_ok=True)
    #         os.makedirs(os.path.join(LEAGUES_SUBDIR, category, league), exist_ok=True)

# Initialize paths
determine_asset_paths() 