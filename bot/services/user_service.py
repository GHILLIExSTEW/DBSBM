# betting-bot/services/user_service.py

"""Service for managing user data and balances."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import discord

from bot.utils.enhanced_cache_manager import (
    enhanced_cache_get,
    enhanced_cache_set,
    enhanced_cache_delete,
    get_enhanced_cache_manager,
)
from bot.utils.errors import InsufficientUnitsError, UserServiceError

USER_CACHE_TTL = 3600  # Default TTL (1 hour)

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db = db_manager
        self.cache = get_enhanced_cache_manager()

    async def start(self):
        """Initialize async components if needed."""
        try:
            logger.info("User service started successfully.")
        except Exception as e:
            logger.exception(f"Failed to start user service: {e}")
            raise UserServiceError("Failed to start user service")

    async def stop(self):
        """Clean up resources."""
        logger.info("Stopping UserService...")
        logger.info("User service stopped.")

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data by ID (from cache or DB)."""
        cache_key = f"user:{user_id}"
        try:
            cached_user = await enhanced_cache_get("user_data", str(user_id))
            if cached_user:
                logger.debug(f"Cache hit for user {user_id}")
                if "balance" in cached_user and cached_user["balance"] is not None:
                    cached_user["balance"] = float(cached_user["balance"])
                return cached_user

            logger.debug(f"Cache miss for user {user_id}. Fetching from DB.")
            user_data = await self.db.fetch_one(
                """
                SELECT user_id, username, balance, created_at
                FROM users
                WHERE user_id = $1
                """,
                user_id,
            )

            if user_data:
                if "balance" in user_data and user_data["balance"] is not None:
                    user_data["balance"] = float(user_data["balance"])
                await enhanced_cache_set(
                    "user_data", str(user_id), user_data, ttl=USER_CACHE_TTL
                )
                return user_data
            else:
                return None
        except Exception as e:
            logger.exception(f"Error getting user {user_id}: {e}")
            return None

    async def get_or_create_user(
        self, user_id: int, username: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a user, creating them in the DB if they don't exist."""
        user = await self.get_user(user_id)
        if user:
            if username and user.get("username") != username:
                await self.db.execute(
                    """
                    UPDATE users
                    SET username = $1
                    WHERE user_id = $1
                    """,
                    username,
                    user_id,
                )
                user["username"] = username
                await enhanced_cache_delete("user_data", str(user_id))
            return user
        else:
            logger.info(f"User {user_id} not found, attempting to create.")
            if not username:
                try:
                    discord_user = await self.bot.fetch_user(user_id)
                    username = discord_user.name if discord_user else f"User_{user_id}"
                except (discord.NotFound, Exception) as fetch_err:
                    username = f"User_{user_id}"
                    logger.warning(
                        f"Could not fetch username for new user {user_id}: {fetch_err}"
                    )

            try:
                default_balance = 0.0
                await self.db.execute(
                    """
                    INSERT IGNORE INTO users (user_id, username, balance, created_at)
                    VALUES ($1, $2, $3, NOW())
                    """,
                    user_id,
                    username,
                    default_balance,
                )
                return await self.get_user(user_id)
            except Exception as e:
                logger.exception(f"Error creating user {user_id}: {e}")
                raise UserServiceError("Failed to create user")

    async def update_user_balance(
        self, user_id: int, amount: float, transaction_type: str
    ) -> Optional[Dict[str, Any]]:
        """Update user balance and record transaction using shared db_manager."""
        try:
            user = await self.get_or_create_user(user_id)
            if not user:
                raise UserServiceError(
                    f"User {user_id} could not be fetched or created."
                )

            current_balance = float(user.get("balance", 0.0) or 0.0)
            new_balance = current_balance + amount

            if amount < 0 and new_balance < 0:
                raise InsufficientUnitsError(
                    f"User {user_id} has {current_balance:.2f}, cannot subtract {-amount:.2f}"
                )


            updated_rows = await self.db.execute(
                """
                UPDATE users
                SET balance = $1
                WHERE user_id = $2
                """,
                new_balance,
                user_id,
            )

            if updated_rows is None or updated_rows == 0:
                logger.error(
                    f"Failed to update balance for user {user_id}. "
                    f"User might not exist or balance unchanged. Rows affected: {updated_rows}"
                )
                raise UserServiceError("Failed to update user balance.")

            logger.info(
                f"Updated balance for user {user_id}. "
                f"New balance: {new_balance:.2f}. Amount change: {amount:+.2f} ({transaction_type})"
            )

            # Always fetch the updated user from the database after update
            # Clear cache to ensure fresh fetch
            await enhanced_cache_delete("user_data", str(user_id))
            updated_user = await self.get_user(user_id)
            if updated_user:
                await enhanced_cache_set(
                    "user_data", str(user_id), updated_user, ttl=USER_CACHE_TTL
                )
            return updated_user

        except InsufficientUnitsError as e:
            logger.warning(f"Balance update failed for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Error updating balance for user {user_id}: {e}")
            raise UserServiceError(f"Failed to update balance: {e}")

    async def get_user_stats(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        try:
            # Get user's betting history
            bets = await self.db.fetch_all(
                """
                SELECT
                    bet_id, game_id, selection, odds, units,
                    status, created_at, result, payout
                FROM bets
                WHERE user_id = $1 AND guild_id = $2
                ORDER BY created_at DESC
                LIMIT 100
                """,
                user_id,
                guild_id,
            )

            if not bets:
                return {
                    "total_bets": 0,
                    "win_rate": 0.0,
                    "total_volume": 0.0,
                    "avg_bet_size": 0.0,
                    "total_winnings": 0.0,
                    "roi": 0.0,
                }

            # Calculate statistics
            total_bets = len(bets)
            completed_bets = [bet for bet in bets if bet["status"] in ["won", "lost"]]
            won_bets = [bet for bet in completed_bets if bet["status"] == "won"]

            win_rate = len(won_bets) / len(completed_bets) if completed_bets else 0.0
            total_volume = sum(bet["units"] for bet in bets)
            avg_bet_size = total_volume / total_bets if total_bets > 0 else 0.0
            total_winnings = sum(bet.get("payout", 0) for bet in won_bets)
            roi = (
                (total_winnings - total_volume) / total_volume
                if total_volume > 0
                else 0.0
            )

            return {
                "total_bets": total_bets,
                "win_rate": win_rate,
                "total_volume": total_volume,
                "avg_bet_size": avg_bet_size,
                "total_winnings": total_winnings,
                "roi": roi,
            }

        except Exception as e:
            logger.exception(f"Error getting user stats for {user_id}: {e}")
            return {}

    async def get_user_balance(self, user_id: int) -> float:
        """Get user's current balance."""
        try:
            user = await self.get_user(user_id)
            return float(user.get("balance", 0.0) or 0.0) if user else 0.0
        except Exception as e:
            logger.exception(f"Error getting balance for user {user_id}: {e}")
            return 0.0

    async def add_units(self, user_id: int, amount: float) -> bool:
        """Add units to user's balance."""
        try:
            await self.update_user_balance(user_id, amount, "deposit")
            return True
        except Exception as e:
            logger.exception(f"Error adding units for user {user_id}: {e}")
            return False

    async def subtract_units(self, user_id: int, amount: float) -> bool:
        """Subtract units from user's balance."""
        try:
            await self.update_user_balance(user_id, -amount, "withdrawal")
            return True
        except Exception as e:
            logger.exception(f"Error subtracting units for user {user_id}: {e}")
            return False

    async def get_top_users(
        self, guild_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by balance."""
        try:
            users = await self.db.fetch_all(
                """
                SELECT user_id, username, balance
                FROM users
                WHERE balance > 0
                ORDER BY balance DESC
                LIMIT $1
                """,
                limit,
            )
            return users
        except Exception as e:
            logger.exception(f"Error getting top users: {e}")
            return []

    async def clear_user_cache(self, user_id: int) -> bool:
        """Clear user data from cache."""
        try:
            await enhanced_cache_delete("user_data", str(user_id))
            return True
        except Exception as e:
            logger.exception(f"Error clearing cache for user {user_id}: {e}")
            return False
