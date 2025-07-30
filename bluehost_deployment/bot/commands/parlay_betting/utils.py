"""Utility functions for parlay betting functionality."""

import logging
from typing import Dict, List, Optional, Union

from bot.config.leagues import LEAGUE_CONFIG
from bot.utils.league_loader import (
    get_all_league_names,
    get_all_sport_categories,
    get_leagues_by_sport,
)

from .constants import LEAGUE_FILE_KEY_MAP

logger = logging.getLogger(__name__)


def get_league_file_key(league_name: str) -> str:
    """Get the file key for a league name."""
    return LEAGUE_FILE_KEY_MAP.get(league_name, league_name)


def format_odds_with_sign(odds: Optional[Union[float, int]]) -> str:
    """Format odds with appropriate sign."""
    if odds is None:
        return "N/A"

    if odds > 0:
        return f"+{odds}"
    else:
        return str(odds)


def calculate_parlay_odds(legs: List[Dict[str, any]]) -> float:
    """Calculate parlay odds from individual leg odds."""
    # Since odds are now provided by TotalOddsModal, return stored total odds
    # This function is kept for backward compatibility
    if not legs:
        return 0.0

    # For now, return the first leg's odds as placeholder
    # In practice, this should calculate the combined odds
    return legs[0].get("odds", 0.0) if legs else 0.0


def validate_bet_details(leg_details: Dict[str, any]) -> bool:
    """Validate bet details for a leg."""
    required_fields = ["sport", "league", "line_type", "selection", "odds"]

    for field in required_fields:
        if field not in leg_details or not leg_details[field]:
            logger.warning(f"Missing required field: {field}")
            return False

    # Validate odds
    try:
        odds = float(leg_details["odds"])
        if odds < -1000 or odds > 10000:  # Reasonable odds range
            logger.warning(f"Odds out of reasonable range: {odds}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Invalid odds format: {leg_details['odds']}")
        return False

    return True


def generate_parlay_summary_text(
    legs: List[Dict[str, any]], total_odds: float, units: float
) -> str:
    """Generate summary text for a parlay bet."""
    if not legs:
        return "No legs added to parlay."

    summary_lines = []
    summary_lines.append(f"**Parlay Bet Summary** ({len(legs)} legs)")
    summary_lines.append("")

    for i, leg in enumerate(legs, 1):
        sport = leg.get("sport", "Unknown")
        league = leg.get("league", "Unknown")
        selection = leg.get("selection", "Unknown")
        odds = leg.get("odds", 0)

        summary_lines.append(f"**Leg {i}:** {sport} - {league}")
        summary_lines.append(f"Selection: {selection}")
        summary_lines.append(f"Odds: {format_odds_with_sign(odds)}")
        summary_lines.append("")

    summary_lines.append(f"**Total Odds:** {format_odds_with_sign(total_odds)}")
    summary_lines.append(f"**Units:** {units}")

    return "\n".join(summary_lines)


def get_sport_categories() -> List[str]:
    """Get available sport categories."""
    return get_all_sport_categories()


def get_leagues_for_sport(sport: str) -> List[str]:
    """Get leagues available for a specific sport."""
    return get_leagues_by_sport(sport)


def get_all_available_leagues() -> List[str]:
    """Get all available leagues."""
    return get_all_league_names()
