# betting-bot/utils/bet_utils.py
# Stub for calculate_parlay_payout used in parlay betting

def calculate_parlay_payout(legs, units, odds_type="american"):
    """Stub for parlay payout calculation."""
    # Return a dummy payout for now
    return units * 2  # Placeholder logic

async def fetch_next_bet_serial(bot) -> int:
    """Fetch the next bet serial (AUTO_INCREMENT) from the bets table using the bot's db_manager."""
    if hasattr(bot, 'db_manager') and bot.db_manager:
        return await bot.db_manager.get_next_bet_serial()
    return None
