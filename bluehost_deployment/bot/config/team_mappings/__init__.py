"""Team name mappings for logo file naming.

This module provides comprehensive team name mappings for various sports leagues
and organizations. The mappings are organized by sport and league for better
maintainability and performance.
"""

from .baseball_teams import MLB_TEAM_MAPPINGS
from .basketball_teams import NBA_TEAM_MAPPINGS
from .football_teams import NFL_TEAM_MAPPINGS
from .hockey_teams import NHL_TEAM_MAPPINGS
from .ncaa_teams import (
    AAC_TEAM_MAPPINGS,
    ACC_TEAM_MAPPINGS,
    BIG_12_TEAM_MAPPINGS,
    BIG_TEN_TEAM_MAPPINGS,
    CUSA_TEAM_MAPPINGS,
    MAC_TEAM_MAPPINGS,
    MWC_TEAM_MAPPINGS,
    SEC_TEAM_MAPPINGS,
    SUN_BELT_TEAM_MAPPINGS,
)
from .other_sports_teams import (
    AFL_TEAM_MAPPINGS,
    CFL_TEAM_MAPPINGS,
    EUROLEAGUE_TEAM_MAPPINGS,
    F1_TEAM_MAPPINGS,
    KBO_TEAM_MAPPINGS,
    KHL_TEAM_MAPPINGS,
    NPB_TEAM_MAPPINGS,
    WNBA_TEAM_MAPPINGS,
)
from .soccer_teams import (
    BUNDESLIGA_TEAM_MAPPINGS,
    EPL_TEAM_MAPPINGS,
    LA_LIGA_TEAM_MAPPINGS,
    LIGUE_1_TEAM_MAPPINGS,
    MLS_TEAM_MAPPINGS,
    SERIE_A_TEAM_MAPPINGS,
)

# Combine all team mappings into a single dictionary
TEAM_MAPPINGS = {}
TEAM_MAPPINGS.update(NFL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(NBA_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(MLB_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(NHL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(MLS_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(EPL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(LA_LIGA_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(SERIE_A_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(BUNDESLIGA_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(LIGUE_1_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(CFL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(WNBA_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(EUROLEAGUE_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(NPB_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(KBO_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(AFL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(F1_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(KHL_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(SEC_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(BIG_TEN_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(ACC_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(BIG_12_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(AAC_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(CUSA_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(MWC_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(SUN_BELT_TEAM_MAPPINGS)
TEAM_MAPPINGS.update(MAC_TEAM_MAPPINGS)


def normalize_team_name(team_name: str) -> str:
    """Normalize team name to match logo file naming convention."""
    # First check if we have a direct mapping (case-sensitive for keys)
    if team_name in TEAM_MAPPINGS:
        return TEAM_MAPPINGS[team_name]

    # Try a case-insensitive check for common shorter names if not found directly
    # For example, if data gives "Mercedes" but mapping has "Mercedes-AMG Petronas" as the preferred long key.
    # This part can be expanded.
    for key, value in TEAM_MAPPINGS.items():
        if key.lower() == team_name.lower():
            return value
        # Check if team_name is a substring of a key (e.g. data "Ferrari", key "Scuderia Ferrari")
        # or if a key is a substring of team_name (e.g. data "Haas F1 Team", key "Haas")
        # This needs careful thought to avoid wrong matches.
        # For simplicity, direct match or simple normalization is safer unless you have very specific partial match rules.

    # If no direct mapping, try to normalize the name
    normalized = (
        team_name.lower().replace(" ", "_").replace(".", "").replace("&", "and")
    )
    # Further specific replacements can be added here if needed for common patterns
    # e.g. normalized = normalized.replace("fc", "").replace("cf", "") if these are often omitted in filenames
    return normalized


# Export the combined mappings
__all__ = [
    "TEAM_MAPPINGS",
    "normalize_team_name",
    "NFL_TEAM_MAPPINGS",
    "NBA_TEAM_MAPPINGS",
    "MLB_TEAM_MAPPINGS",
    "NHL_TEAM_MAPPINGS",
    "MLS_TEAM_MAPPINGS",
    "EPL_TEAM_MAPPINGS",
    "LA_LIGA_TEAM_MAPPINGS",
    "SERIE_A_TEAM_MAPPINGS",
    "BUNDESLIGA_TEAM_MAPPINGS",
    "LIGUE_1_TEAM_MAPPINGS",
    "CFL_TEAM_MAPPINGS",
    "WNBA_TEAM_MAPPINGS",
    "EUROLEAGUE_TEAM_MAPPINGS",
    "NPB_TEAM_MAPPINGS",
    "KBO_TEAM_MAPPINGS",
    "AFL_TEAM_MAPPINGS",
    "F1_TEAM_MAPPINGS",
    "KHL_TEAM_MAPPINGS",
    "SEC_TEAM_MAPPINGS",
    "BIG_TEN_TEAM_MAPPINGS",
    "ACC_TEAM_MAPPINGS",
    "BIG_12_TEAM_MAPPINGS",
    "AAC_TEAM_MAPPINGS",
    "CUSA_TEAM_MAPPINGS",
    "MWC_TEAM_MAPPINGS",
    "SUN_BELT_TEAM_MAPPINGS",
    "MAC_TEAM_MAPPINGS",
]
