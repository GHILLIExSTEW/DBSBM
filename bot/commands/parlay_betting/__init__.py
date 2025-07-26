"""Parlay betting module for Discord bot.

This module provides comprehensive parlay betting functionality including:
- Multi-leg bet creation
- Interactive UI components
- Bet validation and processing
- Image generation for bet slips
"""

from .commands import ParlayCog, setup
from .constants import (
    ALLOWED_LEAGUES,
    DEFAULT_LEGS_PER_PAGE,
    DEFAULT_ODDS,
    DEFAULT_UNITS,
    LEAGUE_FILE_KEY_MAP,
    LINE_TYPES,
    UNITS_DISPLAY_MODES,
    get_league_file_key,
)
from .utils import (
    calculate_parlay_odds,
    format_odds_with_sign,
    generate_parlay_summary_text,
    get_all_available_leagues,
    get_leagues_for_sport,
    get_sport_categories,
    validate_bet_details,
)
from .workflow import ParlayBetWorkflowView

__all__ = [
    # Commands and setup
    "ParlayCog",
    "setup",
    # Main workflow
    "ParlayBetWorkflowView",
    # Constants
    "ALLOWED_LEAGUES",
    "LEAGUE_FILE_KEY_MAP",
    "LINE_TYPES",
    "UNITS_DISPLAY_MODES",
    "DEFAULT_LEGS_PER_PAGE",
    "DEFAULT_UNITS",
    "DEFAULT_ODDS",
    "get_league_file_key",
    # Utilities
    "get_sport_categories",
    "get_leagues_for_sport",
    "get_all_available_leagues",
    "format_odds_with_sign",
    "calculate_parlay_odds",
    "validate_bet_details",
    "generate_parlay_summary_text",
]
