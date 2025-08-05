"""Validation utilities for betting commands."""

from typing import Union

from utils.errors import ValidationError


def validate_units(units: Union[int, float, str]) -> float:
    """
    Validates the units value for a bet.

    Args:
        units: The units value to validate (can be int, float or string)

    Returns:
        float: The validated units value

    Raises:
        ValidationError: If the units value is invalid
    """
    try:
        if isinstance(units, str):
            units = float(units.strip())
        else:
            units = float(units)

        if units <= 0:
            raise ValidationError("Units must be greater than 0")

        if units > 100:  # Arbitrary max limit
            raise ValidationError("Units cannot exceed 100")

        # Round to 1 decimal place
        return round(units, 1)

    except (ValueError, TypeError):
        raise ValidationError("Invalid units value - must be a valid number")


def validate_odds(odds: Union[int, float, str]) -> float:
    """
    Validates betting odds in American format.

    Args:
        odds: The odds value to validate (can be int, float or string)

    Returns:
        float: The validated odds value

    Raises:
        ValidationError: If the odds value is invalid
    """
    try:
        if isinstance(odds, str):
            odds = float(odds.replace("+", "").strip())
        else:
            odds = float(odds)

        if -100 < odds < 100 and odds != 0:
            raise ValidationError("Invalid odds range")

        return odds

    except (ValueError, TypeError):
        raise ValidationError("Invalid odds value - must be a valid number")


def validate_bet_type(bet_type: str) -> str:
    """
    Validates the bet type.

    Args:
        bet_type: The bet type to validate

    Returns:
        str: The validated bet type

    Raises:
        ValidationError: If the bet type is invalid
    """
    valid_types = ["straight", "parlay", "teaser", "prop"]
    bet_type = bet_type.lower().strip()

    if bet_type not in valid_types:
        raise ValidationError(
            f"Invalid bet type. Must be one of: {', '.join(valid_types)}"
        )

    return bet_type


def validate_league(league: str) -> str:
    """
    Validates the league name.

    Args:
        league: The league name to validate

    Returns:
        str: The validated league name

    Raises:
        ValidationError: If the league name is invalid
    """
    if not league or not isinstance(league, str):
        raise ValidationError("League name must be a non-empty string")

    league = league.strip().upper()
    if not league:
        raise ValidationError("League name cannot be empty")

    return league
