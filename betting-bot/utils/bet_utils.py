# betting-bot/utils/bet_utils.py
# Stub for calculate_parlay_payout used in parlay betting

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def determine_risk_win_display_auto(odds: float, units: float, profit: float) -> bool:
    """
    Determines whether to display "To Risk" or "To Win" in auto mode.
    
    Args:
        odds: The American odds value
        units: The number of units being bet
        profit: The calculated profit if the bet wins
        
    Returns:
        True if should display "To Risk", False if should display "To Win"
    """
    # Default to "To Risk" (industry standard)
    display_as_risk = True
    
    # Switch to "To Win" if:
    # 1. Very low negative odds (-150 or lower) - these are typically "To Win" bets (heavy favorites)
    # 2. Profit is significantly lower than risk (less than 0.5x) - indicates "To Win" intent
    if odds < 0 and (odds <= -150 or (profit > 0 and profit <= units * 0.5)):
        display_as_risk = False
        
    return display_as_risk

def calculate_profit_from_odds(odds: float, units: float) -> float:
    """
    Calculates the profit from American odds and units.
    
    Args:
        odds: The American odds value
        units: The number of units being bet
        
    Returns:
        The calculated profit
    """
    try:
        if odds < 0:
            return units * (100.0 / abs(odds))
        elif odds > 0:
            return units * (odds / 100.0)
        else:
            return 0.0
    except Exception:
        return 0.0

def format_units_display(units: float, display_as_risk: bool, unit_label: str = None) -> str:
    """
    Formats the units display text.
    
    Args:
        units: The number of units
        display_as_risk: Whether to display as "To Risk" or "To Win"
        unit_label: The unit label (Unit/Units), auto-determined if None
        
    Returns:
        Formatted display text
    """
    if unit_label is None:
        unit_label = "Unit" if units <= 1 else "Units"
    
    if display_as_risk:
        return f"To Risk {units:.2f} {unit_label}"
    else:
        return f"To Win {units:.2f} {unit_label}"

def calculate_parlay_payout(legs, units, odds_type="american"):
    """Stub for parlay payout calculation."""
    # Return a dummy payout for now
    return units * 2  # Placeholder logic

async def fetch_next_bet_serial(bot) -> int:
    """Fetch the next bet serial (AUTO_INCREMENT) from the bets table using the bot's db_manager."""
    if hasattr(bot, 'db_manager') and bot.db_manager:
        return await bot.db_manager.get_next_bet_serial()
    return None
