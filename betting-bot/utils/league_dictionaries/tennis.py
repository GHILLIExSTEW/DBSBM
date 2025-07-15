"""
Tennis league dictionary for the betting bot.
Contains mappings for tennis tournaments and leagues.
"""

TENNIS_LEAGUES = {
    "ATP": {
        "name": "ATP Tour",
        "sport": "tennis",
        "type": "men",
        "tournaments": [
            "Australian Open",
            "French Open",
            "Wimbledon",
            "US Open",
            "ATP Finals",
            "Masters 1000",
            "ATP 500",
            "ATP 250",
        ],
    },
    "WTA": {
        "name": "WTA Tour",
        "sport": "tennis",
        "type": "women",
        "tournaments": [
            "Australian Open",
            "French Open",
            "Wimbledon",
            "US Open",
            "WTA Finals",
            "WTA 1000",
            "WTA 500",
            "WTA 250",
        ],
    },
    "ITF": {
        "name": "ITF Circuit",
        "sport": "tennis",
        "type": "mixed",
        "tournaments": [
            "ITF Men's World Tennis Tour",
            "ITF Women's World Tennis Tour",
            "ITF Junior Circuit",
        ],
    },
}

# Tennis specific mappings
TENNIS_MAPPINGS = {
    "surface_types": ["hard", "clay", "grass", "carpet"],
    "match_formats": ["best_of_3", "best_of_5"],
    "scoring": ["standard", "tiebreak", "advantage"],
}
