# betting-bot/utils/bet_utils.py
# Stub for calculate_parlay_payout used in parlay betting

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def determine_risk_win_display_auto(odds: float, units: float, profit: float) -> bool:
    """
    Determines whether to display "To Risk" or "To Win" in auto mode.
    
    Based on capper industry standards:
    - "To Win" range: +100 to -200 (this is the "value range")
    - "To Risk" range: Everything else (odds outside +100 to -200)
    
    Args:
        odds: The American odds value
        units: The number of units being bet
        profit: The calculated profit if the bet wins
        
    Returns:
        True if should display "To Risk", False if should display "To Win"
    """
    # Capper industry standard: +100 to -200 is "To Win" (value range)
    if -200 <= odds <= 100:
        # This is the "value range" - display as "To Win"
        return False
    else:
        # Outside the value range - display as "To Risk"
        return True

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
    """
    Calculate parlay payout based on multiple legs with American odds.
    
    Args:
        legs: List of leg dictionaries with 'odds' field (American odds)
        units: The number of units being bet
        odds_type: Type of odds (currently only supports "american")
        
    Returns:
        Dictionary with 'total_odds', 'payout', 'profit', and 'risk' values
    """
    if not legs or not units:
        return {
            'total_odds': 0,
            'payout': 0,
            'profit': 0,
            'risk': units
        }
    
    try:
        # Convert American odds to decimal odds for calculation
        decimal_odds_list = []
        for leg in legs:
            odds = leg.get('odds')
            if odds is None:
                logger.warning(f"Missing odds in leg: {leg}")
                continue
                
            try:
                odds_val = float(odds)
                if odds_val > 0:
                    # Positive odds: +150 = 2.50 decimal
                    decimal_odds = 1 + (odds_val / 100.0)
                elif odds_val < 0:
                    # Negative odds: -150 = 1.67 decimal
                    decimal_odds = 1 + (100.0 / abs(odds_val))
                else:
                    # Even odds (0) = 2.00 decimal
                    decimal_odds = 2.0
                    
                decimal_odds_list.append(decimal_odds)
                logger.debug(f"Converted American odds {odds_val} to decimal {decimal_odds}")
                
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid odds value in leg: {odds}, error: {e}")
                continue
        
        if not decimal_odds_list:
            logger.error("No valid odds found in legs")
            return {
                'total_odds': 0,
                'payout': 0,
                'profit': 0,
                'risk': units
            }
        
        # Calculate total decimal odds (multiply all legs)
        total_decimal_odds = 1.0
        for decimal_odds in decimal_odds_list:
            total_decimal_odds *= decimal_odds
        
        # Calculate payout and profit
        payout = units * total_decimal_odds
        profit = payout - units
        
        # Convert back to American odds for display
        if total_decimal_odds > 2.0:
            # Decimal > 2.0 = positive American odds
            total_american_odds = (total_decimal_odds - 1) * 100
        else:
            # Decimal < 2.0 = negative American odds
            total_american_odds = -100 / (total_decimal_odds - 1)
        
        result = {
            'total_odds': round(total_american_odds),
            'payout': round(payout, 2),
            'profit': round(profit, 2),
            'risk': units
        }
        
        logger.info(f"Parlay calculation: {len(legs)} legs, {units} units, "
                   f"total odds: {result['total_odds']}, payout: {result['payout']}, "
                   f"profit: {result['profit']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating parlay payout: {e}", exc_info=True)
        return {
            'total_odds': 0,
            'payout': 0,
            'profit': 0,
            'risk': units
        }

async def fetch_next_bet_serial(bot) -> int:
    """Fetch the next bet serial (AUTO_INCREMENT) from the bets table using the bot's db_manager."""
    if hasattr(bot, 'db_manager') and bot.db_manager:
        return await bot.db_manager.get_next_bet_serial()
    return None
