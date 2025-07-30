"""
Team Colors Configuration for Schedule Command
Provides team color mappings for background generation in schedule images.
"""

# Team color mappings for NFL teams
NFL_TEAM_COLORS = {
    "Arizona Cardinals": {
        "primary": "#97233F",
        "secondary": "#000000",
        "accent": "#FFB612",
    },
    "Atlanta Falcons": {
        "primary": "#A71930",
        "secondary": "#000000",
        "accent": "#A5ACAF",
    },
    "Baltimore Ravens": {
        "primary": "#241773",
        "secondary": "#000000",
        "accent": "#9E7C0C",
    },
    "Buffalo Bills": {
        "primary": "#00338D",
        "secondary": "#C60C30",
        "accent": "#FFFFFF",
    },
    "Carolina Panthers": {
        "primary": "#0085CA",
        "secondary": "#101820",
        "accent": "#BFC0BF",
    },
    "Chicago Bears": {
        "primary": "#0B162A",
        "secondary": "#C83803",
        "accent": "#FFFFFF",
    },
    "Cincinnati Bengals": {
        "primary": "#FB4F14",
        "secondary": "#000000",
        "accent": "#FFFFFF",
    },
    "Cleveland Browns": {
        "primary": "#311D00",
        "secondary": "#FF3C00",
        "accent": "#FFFFFF",
    },
    "Dallas Cowboys": {
        "primary": "#003594",
        "secondary": "#041E42",
        "accent": "#869397",
    },
    "Denver Broncos": {
        "primary": "#FB4F14",
        "secondary": "#002244",
        "accent": "#FFFFFF",
    },
    "Detroit Lions": {
        "primary": "#0076B6",
        "secondary": "#B0B7BC",
        "accent": "#FFFFFF",
    },
    "Green Bay Packers": {
        "primary": "#203731",
        "secondary": "#FFB612",
        "accent": "#FFFFFF",
    },
    "Houston Texans": {
        "primary": "#03202F",
        "secondary": "#A71930",
        "accent": "#FFFFFF",
    },
    "Indianapolis Colts": {
        "primary": "#002C5F",
        "secondary": "#A2AAAD",
        "accent": "#FFFFFF",
    },
    "Jacksonville Jaguars": {
        "primary": "#006778",
        "secondary": "#9F792C",
        "accent": "#D7A22A",
    },
    "Kansas City Chiefs": {
        "primary": "#E31837",
        "secondary": "#FFB81C",
        "accent": "#FFFFFF",
    },
    "Las Vegas Raiders": {
        "primary": "#000000",
        "secondary": "#A5ACAF",
        "accent": "#FFFFFF",
    },
    "Los Angeles Chargers": {
        "primary": "#0080C6",
        "secondary": "#FFC20E",
        "accent": "#FFFFFF",
    },
    "Los Angeles Rams": {
        "primary": "#003594",
        "secondary": "#FFA300",
        "accent": "#FFFFFF",
    },
    "Miami Dolphins": {
        "primary": "#008E97",
        "secondary": "#FC4C02",
        "accent": "#FFFFFF",
    },
    "Minnesota Vikings": {
        "primary": "#4F2683",
        "secondary": "#FFC62F",
        "accent": "#FFFFFF",
    },
    "New England Patriots": {
        "primary": "#002244",
        "secondary": "#C60C30",
        "accent": "#B0B7BC",
    },
    "New Orleans Saints": {
        "primary": "#D3BC8D",
        "secondary": "#101820",
        "accent": "#FFFFFF",
    },
    "New York Giants": {
        "primary": "#0B2265",
        "secondary": "#A71930",
        "accent": "#A5ACAF",
    },
    "New York Jets": {
        "primary": "#125740",
        "secondary": "#000000",
        "accent": "#FFFFFF",
    },
    "Philadelphia Eagles": {
        "primary": "#004C54",
        "secondary": "#A5ACAF",
        "accent": "#000000",
    },
    "Pittsburgh Steelers": {
        "primary": "#000000",
        "secondary": "#FFB612",
        "accent": "#FFFFFF",
    },
    "San Francisco 49ers": {
        "primary": "#AA0000",
        "secondary": "#B3995D",
        "accent": "#FFFFFF",
    },
    "Seattle Seahawks": {
        "primary": "#002244",
        "secondary": "#69BE28",
        "accent": "#A5ACAF",
    },
    "Tampa Bay Buccaneers": {
        "primary": "#D50A0A",
        "secondary": "#34302B",
        "accent": "#FF7900",
    },
    "Tennessee Titans": {
        "primary": "#0C2340",
        "secondary": "#4B92DB",
        "accent": "#C8102E",
    },
    "Washington Commanders": {
        "primary": "#5A1414",
        "secondary": "#FFB612",
        "accent": "#FFFFFF",
    },
}


def get_team_colors(team_name: str, league: str = "NFL") -> dict:
    """
    Get team colors for a given team name and league.

    Args:
        team_name (str): The name of the team
        league (str): The league (default: "NFL")

    Returns:
        dict: Dictionary containing primary, secondary, and accent colors
    """
    if league.upper() == "NFL":
        return NFL_TEAM_COLORS.get(
            team_name,
            {"primary": "#232733", "secondary": "#4A5568", "accent": "#FFFFFF"},
        )

    # Default colors for unknown teams/leagues
    return {"primary": "#232733", "secondary": "#4A5568", "accent": "#FFFFFF"}


def get_team_primary_color(team_name: str, league: str = "NFL") -> str:
    """
    Get the primary color for a team.

    Args:
        team_name (str): The name of the team
        league (str): The league (default: "NFL")

    Returns:
        str: Primary color hex code
    """
    colors = get_team_colors(team_name, league)
    return colors["primary"]


def get_team_gradient_colors(team_name: str, league: str = "NFL") -> tuple:
    """
    Get gradient colors for a team (primary and secondary).

    Args:
        team_name (str): The name of the team
        league (str): The league (default: "NFL")

    Returns:
        tuple: (primary_color, secondary_color)
    """
    colors = get_team_colors(team_name, league)
    return colors["primary"], colors["secondary"]
