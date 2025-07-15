# REV 1.0.0 - Enhanced bet service with improved bet creation and management
"""Service for managing bets and handling bet-related reactions."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
from zoneinfo import ZoneInfo

import discord
from aiomysql import IntegrityError

try:
    from ..data.db_manager import DatabaseManager
    from ..utils.errors import BetServiceError
except ImportError:
    from data.db_manager import DatabaseManager

    from utils.errors import BetServiceError

logger = logging.getLogger(__name__)

EDT = ZoneInfo("America/New_York")


class BetService:
    def __init__(self, bot, db_manager: DatabaseManager):
        """Initialize the BetService.

        Args:
            bot: The Discord bot instance.
            db_manager: The database manager instance.
        """
        self.bot = bot
        self.db_manager = db_manager
        self.pending_reactions: Dict[int, Dict[str, Union[str, int, List]]] = {}
        logger.info("BetService initialized")

    async def start(self):
        """Start the BetService and perform any necessary setup."""
        logger.info("Starting BetService")
        try:
            await self.cleanup_expired_bets()
            logger.info("BetService started successfully")
        except Exception as e:
            logger.error(f"Failed to start BetService: {e}", exc_info=True)
            raise BetServiceError(f"Could not start BetService: {str(e)}")

    async def stop(self):
        """Stop the BetService and perform any necessary cleanup."""
        logger.info("Stopping BetService")
        try:
            self.pending_reactions.clear()
            logger.info("BetService stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop BetService: {e}", exc_info=True)
            raise BetServiceError(f"Could not stop BetService: {str(e)}")

    async def cleanup_expired_bets(self):
        """Remove expired pending bets from the database."""
        logger.debug("Checking for expired pending bets")
        try:
            expiration_datetime = datetime.now(EDT) - timedelta(hours=24)
            query = """
                DELETE FROM bets
                WHERE status = 'pending'
                AND COALESCE(expiration_time, created_at) < %s
            """
            result = await self.db_manager.execute(query, (expiration_datetime,))
            rowcount = result[0] if result and result[0] is not None else 0
            if rowcount > 0:
                logger.info(f"Cleaned up {rowcount} expired pending bets.")
            else:
                logger.debug("No expired pending bets found to clean up.")
        except Exception as e:
            logger.error(f"Failed to clean up expired bets: {e}", exc_info=True)

    async def cleanup_unconfirmed_bets(self):
        """Delete unconfirmed bets that are older than 5 minutes."""
        logger.info("Starting cleanup of unconfirmed bets")
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            query_select = """
                SELECT bet_serial, guild_id, user_id
                FROM bets
                WHERE confirmed = 0
                AND created_at < %s
            """
            expired_bets = await self.db_manager.fetch_all(query_select, (cutoff_time,))

            if not expired_bets:
                logger.debug("No unconfirmed bets to clean up")
                return

            logger.info(f"Found {len(expired_bets)} unconfirmed bets to clean up")

            deleted_count = 0
            for bet in expired_bets:
                bet_serial_int = int(bet["bet_serial"])
                logger.debug(
                    f"Attempting to clean up unconfirmed bet: {bet_serial_int}"
                )
                try:
                    delete_query = (
                        "DELETE FROM bets WHERE bet_serial = %s AND confirmed = 0"
                    )
                    rowcount, _ = await self.db_manager.execute(
                        delete_query, (bet_serial_int,)
                    )
                    if rowcount is not None and rowcount > 0:
                        logger.info(
                            f"Successfully cleaned up unconfirmed bet {bet_serial_int} for user {bet['user_id']} "
                            f"in guild {bet['guild_id']}"
                        )
                        deleted_count += 1
                    else:
                        logger.warning(
                            f"Did not delete bet {bet_serial_int}. It might have been confirmed or deleted already."
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to clean up bet {bet_serial_int}: {e}", exc_info=True
                    )
                    continue

            logger.info(f"Finished cleanup. Deleted {deleted_count} unconfirmed bets.")
        except Exception as e:
            logger.error(f"Error in cleanup_unconfirmed_bets: {e}", exc_info=True)

    async def confirm_bet(
        self, bet_serial: int, message_id: int, channel_id: int
    ) -> bool:
        """Mark a bet as confirmed and store message_id."""
        try:
            query = """
                UPDATE bets
                SET confirmed = 1,
                    message_id = %s,
                    channel_id = %s
                WHERE bet_serial = %s AND confirmed = 0
            """
            rowcount, _ = await self.db_manager.execute(
                query, (message_id, channel_id, bet_serial)
            )
            if rowcount is not None and rowcount > 0:
                logger.info(
                    f"Bet {bet_serial} confirmed with message {message_id} in channel {channel_id}."
                )
                return True
            else:
                logger.warning(
                    f"Failed to confirm bet {bet_serial}. Rowcount: {rowcount}. May already be confirmed or deleted."
                )
                existing = await self.db_manager.fetch_one(
                    "SELECT confirmed, message_id, channel_id FROM bets WHERE bet_serial = %s",
                    (bet_serial,),
                )
                if (
                    existing
                    and existing["confirmed"] == 1
                    and existing["message_id"] == message_id
                    and existing["channel_id"] == channel_id
                ):
                    logger.info(
                        f"Bet {bet_serial} was already confirmed with message {message_id} in channel {channel_id}."
                    )
                    return True
                return False
        except Exception as e:
            logger.error(f"Error confirming bet {bet_serial}: {e}", exc_info=True)
            return False

    async def get_game_id_by_api_id(self, api_game_id: str) -> Optional[int]:
        """Get internal game ID from api_game_id as a plain integer."""
        try:
            query = "SELECT id FROM api_games WHERE api_game_id = %s"
            # fetchval returns a single value or None
            game_id = await self.db_manager.fetchval(query, (api_game_id,))
            return game_id
        except Exception as e:
            logger.error(
                f"Error retrieving game_id for api_game_id {api_game_id}: {str(e)}"
            )
            return None

    async def create_straight_bet(
        self,
        guild_id: int,
        user_id: int,
        league: str,
        bet_type: str,
        units: float,
        odds: float,
        team: str,
        opponent: str,
        line: str,
        api_game_id: str,
        channel_id: int,
        confirmed: int = 0,
    ) -> int:
        """Create a straight bet record."""
        logger.info(
            f"[BET INSERT] Starting bet creation with args: guild_id={guild_id}, user_id={user_id}, league={league}, bet_type={bet_type}, units={units}, odds={odds}, team={team}, opponent={opponent}, line={line}, api_game_id={api_game_id}, channel_id={channel_id}, confirmed={confirmed}"
        )
        try:
            internal_game_id = None
            if api_game_id and api_game_id != "manual":
                try:
                    logger.info(
                        f"[BET INSERT] Checking if game exists for api_game_id: {api_game_id}"
                    )
                    game_exists = await self.db_manager.fetch_one(
                        "SELECT id FROM api_games WHERE api_game_id = %s",
                        (api_game_id,),
                    )
                    if not game_exists:
                        logger.warning(
                            f"[BET INSERT] Game with api_game_id {api_game_id} not found in api_games table"
                        )
                        raise BetServiceError(f"Game with ID {api_game_id} not found")
                    logger.info(
                        f"[BET INSERT] Game found, getting/creating internal game record"
                    )
                    internal_game_id = await self._get_or_create_game(api_game_id)
                    logger.info(f"[BET INSERT] Internal game_id: {internal_game_id}")
                except BetServiceError as e:
                    logger.warning(
                        f"[BET INSERT] Could not get/create game for api_game_id {api_game_id}: {e}"
                    )
                    raise
            else:
                logger.info("[BET INSERT] Manual entry bet - setting game_id to NULL")

            internal_bet_details_dict = {
                "api_game_id": api_game_id,
                "provided_bet_type": bet_type,
                "provided_line": line,
                "team_selected": team,
                "opponent_involved": opponent,
                "game_start_iso": None,
                "expiration_time_iso": None,
            }
            bet_details_json = json.dumps(internal_bet_details_dict)
            logger.info(f"[BET INSERT] Prepared bet_details JSON: {bet_details_json}")

            query = """
                INSERT INTO bets (
                    guild_id, user_id, league, bet_type, units, odds,
                    team, opponent, line, player_prop, player_id,
                    game_id, game_start, expiration_time,
                    legs, channel_id, confirmed, status, bet_details
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """
            args = (
                guild_id,
                user_id,
                league,
                bet_type,
                units,
                odds,
                team,
                opponent,
                line,
                None,  # player_prop_details
                None,  # player_id
                internal_game_id,  # game_id
                None,  # game_start
                None,  # expiration_time
                1,
                channel_id,
                confirmed,
                "pending",
                bet_details_json,
            )
            logger.info(f"[BET INSERT] Executing query: {query} with args: {args}")
            rowcount, last_id = await self.db_manager.execute(query, args)
            logger.info(
                f"[BET INSERT] Insert result: rowcount={rowcount}, last_id={last_id}"
            )

            if (
                rowcount is not None
                and rowcount > 0
                and last_id is not None
                and last_id > 0
            ):
                logger.info(
                    f"[BET INSERT] Straight bet created successfully with bet_serial: {last_id}"
                )
                # --- No longer insert into unit_records table here ---
                return last_id
            else:
                logger.error(f"[BET INSERT] Failed to create straight bet record.")
                return None
        except IntegrityError as e:
            logger.error(
                f"[BET INSERT] Database integrity error creating straight bet: {e}",
                exc_info=True,
            )
            raise BetServiceError(
                f"Failed to create bet due to database error: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"[BET INSERT] Exception during straight bet insert: {e}", exc_info=True
            )
            raise BetServiceError(f"Failed to create bet: {str(e)}")

    async def create_parlay_bet(
        self,
        guild_id: int,
        user_id: int,
        league: str,
        legs_data: List[Dict],
        units: float,
        channel_id: Optional[int] = None,
        game_start: Optional[datetime] = None,
        expiration_time: Optional[datetime] = None,
        confirmed: int = 0,
    ) -> Optional[int]:
        """Create a parlay bet, populating all relevant fields based on the new schema."""
        logger.info(
            f"[BET INSERT] Attempting to create parlay bet with args: guild_id={guild_id}, user_id={user_id}, league={league}, legs_data={legs_data}, units={units}, channel_id={channel_id}, game_start={game_start}, expiration_time={expiration_time}, confirmed={confirmed}"
        )
        if not legs_data:
            logger.error("Cannot create parlay bet with no legs.")
            return None
        try:
            for leg in legs_data:
                api_game_id = leg.get("api_game_id")
                if api_game_id and api_game_id != "Other":
                    game_exists = await self.db_manager.fetch_one(
                        "SELECT id FROM api_games WHERE api_game_id = %s",
                        (api_game_id,),
                    )
                    if not game_exists:
                        logger.error(
                            f"API Game ID {api_game_id} not found in api_games table"
                        )
                        raise BetServiceError(
                            f"Game ID {api_game_id} not found in database"
                        )
                    logger.debug(
                        f"Validated API Game ID {api_game_id} exists in database"
                    )
            total_odds = self._calculate_parlay_odds(legs_data)
            if total_odds == 0.0 and len(legs_data) > 0:
                logger.warning(
                    f"Calculated parlay odds are 0.0 for legs: {legs_data}. Proceeding with 0 odds."
                )
            internal_bet_details_dict = {
                "legs_info": legs_data,
                "calculated_total_odds": total_odds,
                "game_start_iso": game_start.isoformat() if game_start else None,
                "expiration_time_iso": (
                    expiration_time.isoformat() if expiration_time else None
                ),
            }
            bet_details_json = json.dumps(internal_bet_details_dict)
            num_legs = len(legs_data)
            query = """
                INSERT INTO bets (
                    guild_id, user_id, league, bet_type, units, odds,
                    legs, game_start, expiration_time,
                    channel_id, confirmed, status, bet_details
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """
            args = (
                guild_id,
                user_id,
                league,
                "parlay",
                units,
                total_odds,
                num_legs,
                game_start,
                expiration_time,
                channel_id,
                confirmed,
                "pending",
                bet_details_json,
            )
            logger.info(f"[BET INSERT] Executing query: {query} with args: {args}")
            rowcount, last_id = await self.db_manager.execute(query, args)
            logger.info(
                f"[BET INSERT] Insert result: rowcount={rowcount}, last_id={last_id}"
            )
            if (
                rowcount is not None
                and rowcount > 0
                and last_id is not None
                and last_id > 0
            ):
                logger.info(
                    f"Parlay bet created successfully with bet_serial: {last_id} and {num_legs} legs."
                )
                return last_id
            else:
                logger.error(
                    f"Failed to create parlay bet or retrieve valid ID. Rowcount: {rowcount}, Last ID: {last_id}, Args: {args}"
                )
                return None
        except Exception as e:
            logger.error(
                f"[BET INSERT] Exception during parlay bet insert: {e}", exc_info=True
            )
            return None

    def _calculate_parlay_odds(self, legs: List[Dict]) -> float:
        """Calculate total American odds for a parlay bet from American odds legs."""
        if not legs:
            return 0.0

        total_decimal_odds = 1.0
        try:
            for leg in legs:
                odds_val = leg.get("odds")
                if odds_val is None:
                    logger.warning(
                        f"Skipping leg in parlay calculation due to missing 'odds': {leg}"
                    )
                    continue
                try:
                    current_odds = float(odds_val)
                except (ValueError, TypeError):
                    logger.error(
                        f"Invalid odds format for leg in parlay calculation: {leg}. Odds: '{odds_val}'"
                    )
                    return 0.0

                if current_odds == 0:
                    continue

                if current_odds > 0:
                    decimal_leg = (current_odds / 100.0) + 1.0
                else:
                    decimal_leg = (100.0 / abs(current_odds)) + 1.0
                total_decimal_odds *= decimal_leg

            if total_decimal_odds <= 1.0:
                logger.warning(
                    f"Total decimal odds for parlay is <= 1.0 ({total_decimal_odds}). Legs: {legs}"
                )
                return 0.0

            if total_decimal_odds >= 2.0:
                american_odds = (total_decimal_odds - 1.0) * 100.0
            else:
                if total_decimal_odds == 1.0:
                    logger.warning(
                        f"Cannot convert parlay decimal odds of 1.0 back to American. Legs: {legs}"
                    )
                    return 100.0
                american_odds = -100.0 / (total_decimal_odds - 1.0)
            return round(american_odds)
        except Exception as e:
            logger.error(f"Error calculating parlay odds: {e}", exc_info=True)
            return 0.0

    async def update_straight_bet_channel(
        self, bet_serial: int, channel_id: int, message_id: int
    ):
        """Update the channel ID and message ID for a straight bet and mark as confirmed."""
        logger.debug(
            f"Updating channel_id to {channel_id} and message_id to {message_id} for bet {bet_serial}"
        )
        try:
            query = """
                UPDATE bets
                SET channel_id = %s, message_id = %s, confirmed = 1
                WHERE bet_serial = %s
            """
            rowcount, _ = await self.db_manager.execute(
                query, (channel_id, message_id, bet_serial)
            )
            if rowcount is not None and rowcount > 0:
                logger.debug(
                    f"Bet {bet_serial} channel and message ID updated and confirmed."
                )
            else:
                logger.warning(
                    f"Did not update channel/message for bet {bet_serial}. Rowcount: {rowcount}"
                )
        except Exception as e:
            logger.error(
                f"Failed to update channel/message for bet {bet_serial}: {e}",
                exc_info=True,
            )

    async def update_bet(self, bet_serial: int, **kwargs):
        """Update a bet's details.

        Args:
            bet_serial: The serial number of the bet to update
            **kwargs: The fields to update and their new values
        """
        logger.info(f"Updating bet {bet_serial} with fields: {kwargs}")
        try:
            if not kwargs:
                logger.warning("No fields provided to update for bet {bet_serial}")
                return False

            # Build the SET clause dynamically
            set_clause = ", ".join(f"{field} = %s" for field in kwargs.keys())
            query = f"""
                UPDATE bets
                SET {set_clause}
                WHERE bet_serial = %s
            """

            # Add bet_serial to the end of the values tuple
            values = tuple(kwargs.values()) + (bet_serial,)

            rowcount, _ = await self.db_manager.execute(query, values)
            if rowcount is not None and rowcount > 0:
                logger.info(f"Successfully updated bet {bet_serial}")
                return True
            else:
                logger.warning(
                    f"No rows updated for bet {bet_serial}. Rowcount: {rowcount}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to update bet {bet_serial}: {e}", exc_info=True)
            raise BetServiceError(f"Could not update bet {bet_serial}: {str(e)}")

    async def update_parlay_bet_channel(
        self, bet_serial: int, channel_id: int, message_id: int
    ):
        """Update the channel ID and message ID for a parlay bet and mark as confirmed."""
        logger.debug(
            f"Updating channel_id to {channel_id} and message_id to {message_id} for parlay bet {bet_serial}"
        )
        try:
            query = """
                UPDATE bets
                SET channel_id = %s, message_id = %s, confirmed = 1
                WHERE bet_serial = %s AND bet_type = 'parlay'
            """
            rowcount, _ = await self.db_manager.execute(
                query, (channel_id, message_id, bet_serial)
            )
            if rowcount is not None and rowcount > 0:
                logger.debug(
                    f"Parlay bet {bet_serial} channel and message ID updated and confirmed."
                )
            else:
                logger.warning(
                    f"Did not update channel/message for parlay bet {bet_serial}. Rowcount: {rowcount}"
                )
        except Exception as e:
            logger.error(
                f"Failed to update channel/message for parlay bet {bet_serial}: {e}",
                exc_info=True,
            )

    async def delete_bet(self, bet_serial: int):
        """Delete a bet and its associated data from the database."""
        logger.info(f"Attempting to delete bet {bet_serial} and associated data.")
        try:
            bet_query = "DELETE FROM bets WHERE bet_serial = %s"
            rowcount, _ = await self.db_manager.execute(bet_query, (bet_serial,))

            if rowcount is not None and rowcount > 0:
                self.pending_reactions = {
                    msg_id: data
                    for msg_id, data in self.pending_reactions.items()
                    if data.get("bet_serial") != bet_serial
                }
                logger.info(f"Bet {bet_serial} deleted successfully.")
            else:
                logger.warning(
                    f"Bet {bet_serial} not found for deletion or delete failed. Rowcount: {rowcount}"
                )
                self.pending_reactions = {
                    msg_id: data
                    for msg_id, data in self.pending_reactions.items()
                    if data.get("bet_serial") != bet_serial
                }
        except Exception as e:
            logger.error(f"Failed to delete bet {bet_serial}: {e}", exc_info=True)
            raise BetServiceError(f"Could not delete bet {bet_serial}: {str(e)}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle a reaction added to a bet slip message."""
        if payload.user_id == self.bot.user.id:
            return

        message_id = payload.message_id
        if not payload.guild_id:
            logger.debug(
                f"Reaction on message {message_id} without guild_id, cannot process."
            )
            return

        logger.debug(
            f"Handling reaction add for message {message_id} by user {payload.user_id} in guild {payload.guild_id}"
        )

        try:
            bet_lookup_query = "SELECT bet_serial, user_id, guild_id, status FROM bets WHERE message_id = %s AND guild_id = %s"
            bet_context = await self.db_manager.fetch_one(
                bet_lookup_query, (message_id, payload.guild_id)
            )

            if not bet_context:
                return

            bet_serial = bet_context["bet_serial"]
            original_user_id = bet_context["user_id"]
            guild_id = bet_context["guild_id"]
            current_bet_status = bet_context["status"]
            emoji_str = str(payload.emoji)

            logger.info(
                f"Reaction '{emoji_str}' added to bet {bet_serial} (message {message_id}) by user {payload.user_id} "
                f"in channel {payload.channel_id} (guild {guild_id})"
            )

            reaction_query = """
                INSERT IGNORE INTO bet_reactions (
                    bet_serial, user_id, emoji, channel_id, message_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            reaction_params = (
                bet_serial,
                payload.user_id,
                emoji_str,
                payload.channel_id,
                message_id,
                datetime.now(timezone.utc),
            )
            await self.db_manager.execute(reaction_query, reaction_params)

            resolve_emoji_map = {"✅": "won", "❌": "lost", "➖": "push"}

            if emoji_str in resolve_emoji_map:
                member = payload.member
                if not (
                    payload.user_id == original_user_id
                    or (member and member.guild_permissions.manage_messages)
                ):
                    logger.warning(
                        f"User {payload.user_id} (not owner or admin) tried to resolve bet {bet_serial}."
                    )
                    return

                new_status = resolve_emoji_map[emoji_str]
                new_result_description = (
                    f"Resolved as {new_status} by user {payload.user_id} via reaction."
                )

                if current_bet_status not in ["pending", "live"]:
                    logger.warning(
                        f"Bet {bet_serial} (message {message_id}) cannot be resolved. Current status: {current_bet_status}"
                    )
                    return

                logger.info(
                    f"Attempting to resolve bet {bet_serial} as '{new_status}' by user {payload.user_id}"
                )

                bet_data_query = """
                    SELECT guild_id, user_id, units, odds, league, bet_type, bet_details, game_start, created_at
                    FROM bets
                    WHERE bet_serial = %s
                """
                bet_data = await self.db_manager.fetch_one(
                    bet_data_query, (bet_serial,)
                )

                if not bet_data:
                    logger.error(
                        f"Cannot resolve bet: Bet {bet_serial} data not found after initial context."
                    )
                    return

                update_time = datetime.now(timezone.utc)
                status_query = """
                    UPDATE bets
                    SET status = %s,
                        result_value = %s,
                        bet_won = CASE WHEN %s = 'won' THEN 1 ELSE 0 END,
                        bet_loss = CASE WHEN %s = 'lost' THEN 1 ELSE 0 END,
                        updated_at = %s
                    WHERE bet_serial = %s
                """

                units_staked = float(bet_data.get("units", 0.0))
                odds_val = float(bet_data.get("odds", 0.0))
                calculated_result_value = 0.0

                if new_status == "won":
                    if odds_val > 0:
                        calculated_result_value = units_staked * (odds_val / 100.0)
                    elif odds_val < 0:
                        calculated_result_value = units_staked * (100.0 / abs(odds_val))
                elif new_status == "lost":
                    calculated_result_value = -units_staked

                rowcount, _ = await self.db_manager.execute(
                    status_query,
                    (
                        new_status,
                        calculated_result_value,
                        new_status,
                        new_status,
                        update_time,
                        bet_serial,
                    ),
                )

                if rowcount is None or rowcount == 0:
                    logger.error(
                        f"Failed to update status/result for bet {bet_serial} to {new_status}."
                    )
                    return
                logger.info(
                    f"Bet {bet_serial} status updated to '{new_status}', result_value to {calculated_result_value:.2f}"
                )

                record_period_date = (
                    bet_data.get("game_start")
                    or bet_data.get("created_at")
                    or update_time
                )
                year = record_period_date.year
                month = record_period_date.month

                unit_query = """
                    INSERT INTO unit_records (
                        bet_serial, guild_id, user_id, year, month, units, odds, monthly_result_value, total_result_value, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        monthly_result_value = VALUES(monthly_result_value),
                        total_result_value = VALUES(total_result_value),
                        created_at = VALUES(created_at)
                """
                unit_params = (
                    bet_serial,
                    bet_data["guild_id"],
                    bet_data["user_id"],
                    year,
                    month,
                    units_staked,
                    odds_val,
                    calculated_result_value,
                    calculated_result_value,
                    update_time,
                )
                await self.db_manager.execute(unit_query, unit_params)
                logger.info(
                    f"Unit record updated for bet {bet_serial}. Result Value: {calculated_result_value:.2f}"
                )

                # Update cappers table with win/loss/push counts
                capper_update_query = """
                    UPDATE cappers
                    SET
                        bet_won = (
                            SELECT COUNT(*)
                            FROM bets b2
                            WHERE b2.user_id = %s
                            AND b2.guild_id = %s
                            AND b2.status = 'won'
                        ),
                        bet_loss = (
                            SELECT COUNT(*)
                            FROM bets b2
                            WHERE b2.user_id = %s
                            AND b2.guild_id = %s
                            AND b2.status = 'lost'
                        ),
                        bet_push = (
                            SELECT COUNT(*)
                            FROM bets b2
                            WHERE b2.user_id = %s
                            AND b2.guild_id = %s
                            AND b2.status = 'push'
                        ),
                        updated_at = UTC_TIMESTAMP()
                    WHERE user_id = %s AND guild_id = %s
                """
                capper_params = (
                    bet_data["user_id"],
                    bet_data["guild_id"],  # For won count
                    bet_data["user_id"],
                    bet_data["guild_id"],  # For lost count
                    bet_data["user_id"],
                    bet_data["guild_id"],  # For push count
                    bet_data["user_id"],
                    bet_data["guild_id"],  # WHERE clause
                )
                await self.db_manager.execute(capper_update_query, capper_params)
                logger.info(
                    f"Cappers table updated for user {bet_data['user_id']} in guild {bet_data['guild_id']}"
                )

                if hasattr(self.bot, "voice_service") and hasattr(
                    self.bot.voice_service, "update_on_bet_resolve"
                ):
                    asyncio.create_task(
                        self.bot.voice_service.update_on_bet_resolve(
                            bet_data["guild_id"]
                        )
                    )
                    logger.debug(
                        f"Triggered voice channel update for guild {bet_data['guild_id']}"
                    )
        except Exception as e:
            logger.error(
                f"Failed to handle reaction add for message {message_id}: {e}",
                exc_info=True,
            )

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle a reaction removed from a bet slip message."""
        if payload.user_id == self.bot.user.id:
            return
        if not payload.guild_id:
            return

        message_id = payload.message_id
        logger.debug(
            f"Handling reaction remove for message {message_id} by user {payload.user_id} in guild {payload.guild_id}"
        )

        try:
            bet_lookup_query = (
                "SELECT bet_serial FROM bets WHERE message_id = %s AND guild_id = %s"
            )
            bet_context = await self.db_manager.fetch_one(
                bet_lookup_query, (message_id, payload.guild_id)
            )

            if not bet_context:
                return

            bet_serial = bet_context["bet_serial"]
            emoji_str = str(payload.emoji)

            logger.info(
                f"Reaction '{emoji_str}' removed from bet {bet_serial} (message {message_id}) by user {payload.user_id} "
                f"in channel {payload.channel_id} (guild {payload.guild_id})"
            )

            query = """
                DELETE FROM bet_reactions
                WHERE bet_serial = %s AND user_id = %s AND emoji = %s AND message_id = %s
            """
            params = (bet_serial, payload.user_id, emoji_str, message_id)
            await self.db_manager.execute(query, params)
        except Exception as e:
            logger.error(
                f"Failed to handle reaction remove for message {message_id}: {e}",
                exc_info=True,
            )

    async def _get_or_create_game(self, api_game_id: str) -> int:
        # 1) look up in games
        row = await self.db_manager.fetch_one(
            "SELECT id FROM games WHERE api_game_id = %s", (api_game_id,)
        )
        if row:
            return row["id"]
        # 2) pull details from api_games
        src = await self.db_manager.fetch_one(
            """
            SELECT sport, league_id, home_team_name, away_team_name, start_time, status
            FROM api_games WHERE api_game_id = %s
            """,
            (api_game_id,),
        )
        if not src:
            raise BetServiceError(f"No api_games row for {api_game_id}")
        # 3) insert into games
        rowcount, last_id = await self.db_manager.execute(
            """
            INSERT INTO games
              (api_game_id, sport, league_id, home_team_name, away_team_name, start_time, status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())
            """,
            (
                api_game_id,
                src["sport"],
                src["league_id"],
                src["home_team_name"],
                src["away_team_name"],
                src["start_time"],
                src["status"],
            ),
        )
        if last_id is None:
            raise BetServiceError(
                f"Failed to create game record for api_game_id {api_game_id}"
            )
        return last_id
