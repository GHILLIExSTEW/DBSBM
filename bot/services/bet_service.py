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

from bot.data.db_manager import DatabaseManager
from bot.utils.errors import BetServiceError

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
                AND COALESCE(expiration_time, created_at) < $1
            """
            rowcount = await self.db_manager.execute(query, (expiration_datetime,))
            if isinstance(rowcount, int) and rowcount > 0:
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
                AND created_at < $1
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
                        "DELETE FROM bets WHERE bet_serial = $1 AND confirmed = 0"
                    )
                    rowcount = await self.db_manager.execute(
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
                    message_id = $1,
                    channel_id = $2
                WHERE bet_serial = $3 AND confirmed = 0
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
                    "SELECT confirmed, message_id, channel_id FROM bets WHERE bet_serial = $1",
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
            query = "SELECT id FROM api_games WHERE api_game_id = $1"
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
        logger.debug(f"[BET INSERT] Full argument dump: {{'guild_id': guild_id, 'user_id': user_id, 'league': league, 'bet_type': bet_type, 'units': units, 'odds': odds, 'team': team, 'opponent': opponent, 'line': line, 'api_game_id': api_game_id, 'channel_id': channel_id, 'confirmed': confirmed}}")
        import time
        start_time = time.time()
        logger.info(f"[METRIC] create_straight_bet started at {start_time}")
        try:
            internal_game_id = None
            if api_game_id and api_game_id != "manual":
                try:
                    logger.info(
                        f"[BET INSERT] Checking if game exists for api_game_id: {api_game_id}"
                    )
                    game_exists = await self.db_manager.fetch_one(
                        "SELECT id FROM api_games WHERE api_game_id = $1",
                        (api_game_id,),
                    )
                    if not game_exists:
                        logger.warning(
                            f"[BET INSERT] Game with api_game_id {api_game_id} not found in api_games table"
                        )
                        raise BetServiceError(f"Game with ID {api_game_id} not found")
                    logger.info(
                        "[BET INSERT] Game found, getting/creating internal game record"
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

            # Use auto-generated bet_serial (identity column)
            query = """
                INSERT INTO bets (
                    guild_id, user_id, league, bet_type, units, odds,
                    team, opponent, line, player_prop, player_id,
                    game_id, game_start, expiration_time,
                    legs, channel_id, confirmed, status, bet_details
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11,
                    $12, $13, $14,
                    $15, $16, $17, $18, $19
                ) RETURNING bet_serial
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
            logger.debug(f"[BET INSERT] Query string: {query}")
            logger.debug(f"[BET INSERT] Query args: {args}")
            try:
                result = await self.db_manager.fetch_one(query, args)
                logger.info(f"[BET INSERT] Insert result: {result}")
                logger.info(f"[METRIC] Insert query completed in {time.time() - start_time:.4f} seconds")
                bet_serial = result["bet_serial"] if result and "bet_serial" in result else None
                if bet_serial:
                    # Post-insert fetch to verify existence
                    verify_query = "SELECT * FROM bets WHERE bet_serial = $1"
                    verify_row = await self.db_manager.fetch_one(verify_query, (bet_serial,))
                    if verify_row:
                        logger.info(f"[METRIC] Verified bet_serial {bet_serial} exists in bets table after insert.")
                    else:
                        logger.error(f"[METRIC] bet_serial {bet_serial} NOT FOUND in bets table after insert!")
                    # If db_manager exposes commit status, log it
                    if hasattr(self.db_manager, 'get_last_commit_status'):
                        commit_status = await self.db_manager.get_last_commit_status()
                        logger.info(f"[METRIC] DB commit status after insert: {commit_status}")
                else:
                    logger.error(f"[METRIC] No bet_serial returned from insert result.")
            except Exception as e:
                logger.error(f"[BET INSERT] Exception during DB insert: {e}", exc_info=True)
                logger.error(f"[BET INSERT] Query: {query}")
                logger.error(f"[BET INSERT] Args: {args}")
                raise

            if result and "bet_serial" in result:
                logger.info(f"[BET INSERT] Straight bet created successfully.")
                return result["bet_serial"]
            else:
                logger.error("[BET INSERT] Failed to create straight bet record.")
                logger.error(f"[BET INSERT] Query: {query}")
                logger.error(f"[BET INSERT] Args: {args}")
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
                        "SELECT id FROM api_games WHERE api_game_id = $1",
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
            # Use auto-generated bet_serial (identity column)
            query = """
                INSERT INTO bets (
                    guild_id, user_id, league, bet_type, units, odds,
                    legs, game_start, expiration_time,
                    channel_id, confirmed, status, bet_details
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8, $9, $10,
                    $11, $12, $13, $14
                ) RETURNING bet_serial
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
            result = await self.db_manager.fetch_one(query, args)
            logger.info(f"[BET INSERT] Insert result: {result}")
            if result and "bet_serial" in result:
                logger.info(f"Parlay bet created successfully with bet_serial: {result['bet_serial']} and {num_legs} legs.")
                return result["bet_serial"]
            else:
                logger.error(f"Failed to create parlay bet or retrieve valid ID. Args: {args}")
                return None
        except Exception as e:
            logger.error(
                f"[BET INSERT] Exception during parlay bet insert: {e}", exc_info=True
            )
            return None

    async def create_player_prop_bet(
        self,
        guild_id: int,
        user_id: int,
        league: str,
        sport: str,
        player_name: str,
        team_name: str,
        prop_type: str,
        line_value: float,
        bet_direction: str,
        odds: str,
        units: float = 0.0,
        api_game_id: Optional[str] = None,
        channel_id: Optional[int] = None,
        confirmed: int = 0,
    ) -> Optional[int]:
        """Create a player prop bet, populating all relevant fields based on the schema."""
        logger.info(
            f"[BET INSERT] Attempting to create player prop bet with args: guild_id={guild_id}, user_id={user_id}, league={league}, sport={sport}, player_name={player_name}, team_name={team_name}, prop_type={prop_type}, line_value={line_value}, bet_direction={bet_direction}, odds={odds}, units={units}, api_game_id={api_game_id}, channel_id={channel_id}, confirmed={confirmed}"
        )
        try:
            # Handle game_id conversion like straight bets
            internal_game_id = None
            if api_game_id and api_game_id != "manual":
                try:
                    logger.info(
                        f"[BET INSERT] Checking if game exists for api_game_id: {api_game_id}"
                    )
                    game_exists = await self.db_manager.fetch_one(
                        "SELECT id FROM api_games WHERE api_game_id = $1",
                        (api_game_id,),
                    )
                    if not game_exists:
                        logger.warning(
                            f"[BET INSERT] Game with api_game_id {api_game_id} not found in api_games table"
                        )
                        raise BetServiceError(f"Game with ID {api_game_id} not found")
                    logger.info(
                        "[BET INSERT] Game found, getting/creating internal game record"
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

            # Convert odds to float for storage
            try:
                odds_float = float(odds)
            except (ValueError, TypeError):
                logger.warning(f"Invalid odds format: {odds}, storing as string")
                odds_float = None

            # Create bet_details JSON
            internal_bet_details_dict = {
                "player_name": player_name,
                "team_name": team_name,
                "prop_type": prop_type,
                "line_value": line_value,
                "bet_direction": bet_direction,
                "odds": odds,
                "api_game_id": api_game_id,
                "sport": sport,
            }
            bet_details_json = json.dumps(internal_bet_details_dict)

            # Use auto-generated bet_serial (identity column)
            query = """
                INSERT INTO bets (
                    guild_id, user_id, league, bet_type, player_prop, player_name,
                    team_name, sport, player_prop_type, player_prop_line,
                    player_prop_direction, odds, game_id, status, units, bet_details,
                    channel_id, confirmed
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                ) RETURNING bet_serial
            """
            args = (
                guild_id,
                user_id,
                league,
                "player_prop",
                "true",  # player_prop flag
                player_name,
                team_name,
                sport,
                prop_type.title(),  # Capitalize prop type
                line_value,
                bet_direction,
                odds_float,
                internal_game_id,  # Use converted internal game_id
                "pending",
                units,
                bet_details_json,
                channel_id,
                confirmed,
            )
            logger.info(f"[BET INSERT] Executing query: {query} with args: {args}")
            result = await self.db_manager.fetch_one(query, args)
            logger.info(f"[BET INSERT] Insert result: {result}")
            if result and "bet_serial" in result:
                logger.info(f"Player prop bet created successfully with bet_serial: {result['bet_serial']}")
                return result["bet_serial"]
            else:
                logger.error(f"Failed to create player prop bet or retrieve valid ID. Args: {args}")
                return None
        except Exception as e:
            logger.error(
                f"[BET INSERT] Exception during player prop bet insert: {e}",
                exc_info=True,
            )
            return None

    async def reserve_bet(self, guild_id: int, user_id: int, league: Optional[str] = None, bet_type: str = "straight", bet_details: Optional[Dict] = None) -> Optional[int]:
        """Reserve a DB bet row for a preview flow and return the reserved bet_serial.

        This inserts a minimal row with status='preview' so the frontend can name the preview
        file using the returned DB serial. The frontend should pass this serial back on final
        submit so the backend can update the reserved row instead of inserting a new one.
        """
        try:
            bd_json = json.dumps(bet_details or {})
            query = (
                "INSERT INTO bets (guild_id, user_id, league, bet_type, status, confirmed, bet_details) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING bet_serial"
            )
            args = (guild_id, user_id, league, bet_type, "preview", 0, bd_json)
            result = await self.db_manager.fetch_one(query, args)
            if result and "bet_serial" in result:
                logger.info(f"[RESERVE] Reserved bet_serial {result['bet_serial']} for user {user_id} guild {guild_id}")
                return result["bet_serial"]
            logger.error("[RESERVE] Failed to reserve bet row (no bet_serial returned)")
            return None
        except Exception as e:
            logger.error(f"[RESERVE] Exception while reserving bet row: {e}", exc_info=True)
            return None

    async def cancel_reserved_bet(self, bet_serial: int, guild_id: int, user_id: int) -> bool:
        """Delete a reserved (unconfirmed) bet row created for preview when user cancels.

        Only deletes rows that are unconfirmed to avoid removing legitimate bets.
        """
        try:
            query = "DELETE FROM bets WHERE bet_serial = $1 AND guild_id = $2 AND user_id = $3 AND confirmed = 0"
            rowcount, _ = await self.db_manager.execute(query, (bet_serial, guild_id, user_id))
            if rowcount and rowcount > 0:
                logger.info(f"[RESERVE] Deleted reserved bet_serial {bet_serial} for user {user_id} guild {guild_id}")
                return True
            logger.warning(f"[RESERVE] No reserved bet deleted for bet_serial {bet_serial} (rowcount={rowcount})")
            return False
        except Exception as e:
            logger.error(f"[RESERVE] Exception while deleting reserved bet {bet_serial}: {e}", exc_info=True)
            return False

    async def submit_bet(self, bet_details: Dict) -> Dict:
        """
        Accept a bet_details dict from UI workflows and create the appropriate bet record.
        Returns a dict: {"success": bool, "bet_serial": Optional[int], "error": Optional[str]}
        """
        logger.debug(f"[SUBMIT BET] Received bet_details: {bet_details}")
        if not isinstance(bet_details, dict):
            logger.error(f"[SUBMIT BET] bet_details is not a dict: {bet_details}")
            return {"success": False, "error": "Invalid bet details provided"}

        try:
            logger.debug(f"[SUBMIT BET] Received bet_details: {bet_details}")
            if not isinstance(bet_details, dict):
                logger.error(f"[SUBMIT BET] bet_details is not a dict: {bet_details}")
                return {"success": False, "error": "Invalid bet details provided"}
            bet_type = bet_details.get("bet_type") or bet_details.get("type")
            logger.debug(f"[SUBMIT BET] Initial bet_type: {bet_type}")
            # Accept 'game_line' as alias for 'straight'
            if bet_type == "game_line":
                bet_type = "straight"
            logger.debug(f"[SUBMIT BET] Normalized bet_type: {bet_type}")
            guild_id = int(bet_details.get("guild_id")) if bet_details.get("guild_id") else None
            user_id = int(bet_details.get("user_id")) if bet_details.get("user_id") else None
            logger.debug(f"[SUBMIT BET] guild_id: {guild_id}, user_id: {user_id}")
            if not guild_id or not user_id:
                logger.error(f"[SUBMIT BET] Missing guild_id or user_id. guild_id: {guild_id}, user_id: {user_id}")
                return {"success": False, "error": "Missing guild_id or user_id"}
            # Straight bet
            if bet_type == "straight":
                league = bet_details.get("league")
                bet_sub_type = bet_details.get("line_type") or bet_details.get("bet_sub_type") or ""
                units = float(bet_details.get("units", 0))
                odds = float(bet_details.get("odds", 0)) if bet_details.get("odds") is not None else 0.0
                team = bet_details.get("team") or bet_details.get("selected_team")
                opponent = bet_details.get("opponent") or bet_details.get("other_team")
                line = bet_details.get("line")
                api_game_id = bet_details.get("api_game_id") or bet_details.get("game_id")
                channel_id = bet_details.get("post_channel_id") or bet_details.get("channel_id")
                logger.debug(f"[SUBMIT BET] Straight bet args: league={league}, bet_sub_type={bet_sub_type}, units={units}, odds={odds}, team={team}, opponent={opponent}, line={line}, api_game_id={api_game_id}, channel_id={channel_id}")

                # If a reserved preview bet_serial was provided by the frontend, try to update that row
                reserved_keys = ["reserved_bet_serial", "reserved_serial", "preview_bet_serial", "preview_serial"]
                reserved_serial = None
                for k in reserved_keys:
                    if k in bet_details and bet_details.get(k):
                        try:
                            reserved_serial = int(bet_details.get(k))
                        except Exception:
                            reserved_serial = None
                        break

                bet_serial = None
                # Prepare internal bet_details json for storage
                internal_bet_details_dict = {
                    "api_game_id": api_game_id,
                    "provided_bet_type": bet_sub_type,
                    "provided_line": line,
                    "team_selected": team,
                    "opponent_involved": opponent,
                    "game_start_iso": bet_details.get("game_start"),
                    "expiration_time_iso": bet_details.get("expiration_time"),
                }
                bet_details_json = json.dumps(internal_bet_details_dict)

                if reserved_serial:
                    try:
                        # Normalize api_game_id to internal game_id (int) or None for manual
                        internal_game_id = None
                        try:
                            if api_game_id and api_game_id != "manual":
                                # If api_game_id is numeric string, use as int; otherwise try to resolve
                                try:
                                    internal_game_id = int(api_game_id)
                                except Exception:
                                    internal_game_id = await self.get_game_id_by_api_id(api_game_id)
                        except Exception:
                            internal_game_id = None

                        update_query = """
                            UPDATE bets
                            SET league = $1, bet_type = $2, units = $3, odds = $4,
                                team = $5, opponent = $6, line = $7, game_id = $8,
                                channel_id = $9, confirmed = $10, status = $11, bet_details = $12, updated_at = NOW()
                            WHERE bet_serial = $13 AND user_id = $14 AND guild_id = $15
                        """
                        update_args = (
                            league, bet_sub_type, units, odds,
                            team, opponent, line, internal_game_id,
                            channel_id, 0, "pending", bet_details_json,
                            reserved_serial, user_id, guild_id,
                        )
                        exec_result = await self.db_manager.execute(update_query, update_args)
                        # db_manager.execute may return an int or a (rowcount, ...) tuple depending on implementation
                        if isinstance(exec_result, (list, tuple)):
                            rowcount = exec_result[0]
                        else:
                            rowcount = exec_result
                        if rowcount and rowcount > 0:
                            bet_serial = reserved_serial
                            logger.info(f"[SUBMIT BET] Updated reserved bet_serial {bet_serial} with final data")
                        else:
                            logger.warning(f"[SUBMIT BET] Failed to update reserved bet {reserved_serial}; will insert new row")
                    except Exception as e:
                        logger.error(f"[SUBMIT BET] Exception while updating reserved bet {reserved_serial}: {e}", exc_info=True)

                # If no reserved row updated, create a new bet normally
                if not bet_serial:
                    try:
                        bet_serial = await self.create_straight_bet(
                            guild_id,
                            user_id,
                            league,
                            bet_sub_type,
                            units,
                            odds,
                            team,
                            opponent,
                            line,
                            api_game_id,
                            channel_id,
                        )
                    except Exception as e:
                        logger.error(f"[SUBMIT BET] Exception in create_straight_bet: {e}", exc_info=True)
                        return {"success": False, "error": f"Exception in create_straight_bet: {e}"}

                if bet_serial:
                    # Always return integer bet_serial for DB, format for display elsewhere
                    # --- Discord message sending metrics ---
                    logger.info(f"[METRIC] Preparing to send Discord message for bet_serial {bet_serial} to channel {channel_id}")
                    channel = self.bot.get_channel(channel_id)
                    if channel is None:
                        logger.error(f"[METRIC] Discord channel {channel_id} not found. Message will not be sent.")
                    else:
                        # 1. Fetch member_role from guild_settings
                        member_role_id = None
                        try:
                            gs_row = await self.db_manager.fetch_one("SELECT member_role FROM guild_settings WHERE guild_id = $1", (guild_id,))
                            member_role_id = gs_row["member_role"] if gs_row and "member_role" in gs_row else None
                            logger.info(f"[METRIC] Fetched member_role_id: {member_role_id}")
                        except Exception as e:
                            logger.error(f"[METRIC] Failed to fetch member_role from guild_settings: {e}", exc_info=True)
                        # 2. Fetch user image and display name from cappers
                        user_avatar_url = None
                        user_display_name = None
                        try:
                            # resilient fetch: schema may differ between environments
                            capper_row = await self.db_manager.fetch_one(
                                "SELECT * FROM cappers WHERE user_id = $1 AND guild_id = $2",
                                (user_id, guild_id),
                            )
                            if capper_row:
                                # Common avatar/display name column candidates
                                avatar_keys = [
                                    "avatar_url",
                                    "avatar",
                                    "avatar_uri",
                                    "avatar_path",
                                    "avatar_file",
                                    "avatar_hash",
                                ]
                                display_keys = [
                                    "display_name",
                                    "displayname",
                                    "display",
                                    "name",
                                    "username",
                                ]
                                for k in avatar_keys:
                                    if k in capper_row and capper_row[k]:
                                        user_avatar_url = capper_row[k]
                                        break
                                for k in display_keys:
                                    if k in capper_row and capper_row[k]:
                                        user_display_name = capper_row[k]
                                        break
                            logger.info(f"[METRIC] Fetched user_avatar_url: {user_avatar_url}, user_display_name: {user_display_name}")
                        except Exception as e:
                            logger.error(f"[METRIC] Failed to fetch avatar/display_name from cappers: {e}", exc_info=True)
                        # 3. Resolve preview or generate image
                        image_path = None
                        try:
                            image_path = await self._resolve_image_path(bet_details, bet_serial, guild_id, team, opponent, line, odds, units)
                            logger.info(f"[METRIC] Resolved image_path: {image_path}")
                        except Exception as e:
                            logger.error(f"[METRIC] Exception while resolving/generating image: {e}", exc_info=True)
                        # 4. Compose message content
                        mention_str = f"<@&{member_role_id}> " if member_role_id else ""
                        message_content = f"{mention_str}Bet #{bet_serial} submitted! {team} vs {opponent}, line: {line}, odds: {odds}, units: {units}"
                        logger.info(f"[METRIC] Sending message: '{message_content}' to channel {channel_id}")
                        # 5. Send message with image, avatar, and display name override
                        try:
                            webhook = None
                            for wh in await channel.webhooks():
                                if wh.name == "Bet Tracking Bot":
                                    webhook = wh
                                    break
                            if webhook is None:
                                webhook = await channel.create_webhook(name="Bet Tracking Bot")
                            logger.info(f"[METRIC] Using webhook ID: {webhook.id}")

                            # Require image produced by generate_bet_image. No fallback allowed.
                            if not image_path:
                                logger.error(f"[METRIC] No generated image available for bet_serial {bet_serial}; aborting webhook send.")
                                return {"success": False, "error": "No generated image to send"}

                            import os
                            import shutil
                            import discord

                            # Ensure a stable location for confirmed bet images per guild
                            static_root = os.path.join(os.getcwd(), "StaticFiles", "Confirmed_Bets", str(guild_id))
                            try:
                                os.makedirs(static_root, exist_ok=True)
                            except Exception as e:
                                logger.error(f"[METRIC] Failed to create static directory {static_root}: {e}", exc_info=True)
                                return {"success": False, "error": "Failed to store generated image"}

                            original_filename = os.path.basename(image_path)
                            dest_filename = f"bet_{bet_serial}_{original_filename}"
                            dest_path = os.path.join(static_root, dest_filename)

                            try:
                                shutil.copy2(image_path, dest_path)
                                generated_image_db_path = dest_path
                                # Persist path to DB
                                try:
                                    await self.db_manager.execute(
                                        "UPDATE bets SET generated_image = $1 WHERE bet_serial = $2",
                                        (generated_image_db_path, bet_serial),
                                    )
                                    logger.info(f"[METRIC] Updated bet {bet_serial} generated_image to {generated_image_db_path}")
                                except Exception as e:
                                    logger.error(f"[METRIC] Failed to update generated_image in DB for bet_serial {bet_serial}: {e}", exc_info=True)
                            except Exception as e:
                                logger.error(f"[METRIC] Failed to copy generated image to static directory: {e}", exc_info=True)
                                return {"success": False, "error": "Failed to store generated image"}

                            # Send the copied file from the static directory so the stored path matches what was posted
                            filename = dest_filename
                            file_to_send = discord.File(dest_path, filename=filename)
                            embed = discord.Embed(title=f"Bet #{bet_serial} submitted!", description=message_content)
                            embed.set_image(url=f"attachment://{filename}")

                            sent_message = await webhook.send(
                                content=None,
                                username=user_display_name or "Bet Tracking Bot",
                                avatar_url=user_avatar_url,
                                file=file_to_send,
                                embed=embed,
                                wait=True,
                            )
                            logger.info(f"[METRIC] Discord webhook message sent successfully. Message ID: {getattr(sent_message, 'id', None)}")
                        except Exception as e:
                            logger.error(f"[METRIC] Exception while sending Discord webhook message for bet_serial {bet_serial}: {e}", exc_info=True)
                    return {"success": True, "bet_serial": bet_serial}
                logger.error(f"[SUBMIT BET] Failed to insert straight bet. Args: league={league}, bet_sub_type={bet_sub_type}, units={units}, odds={odds}, team={team}, opponent={opponent}, line={line}, api_game_id={api_game_id}, channel_id={channel_id}")
                return {"success": False, "error": "Failed to insert straight bet"}
            # Parlay bet
            if bet_type == "parlay":
                league = bet_details.get("league")
                legs = bet_details.get("legs") or bet_details.get("legs_data") or []
                units = float(bet_details.get("units", 0))
                channel_id = bet_details.get("post_channel_id") or bet_details.get("channel_id")
                game_start = bet_details.get("game_start")
                expiration = bet_details.get("expiration_time")
                bet_serial = await self.create_parlay_bet(
                    guild_id, user_id, league, legs, units, channel_id, game_start, expiration
                )
                if bet_serial:
                    return {"success": True, "bet_serial": bet_serial}
                return {"success": False, "error": "Failed to insert parlay bet"}
            # Player prop bet
            if bet_type == "player_prop":
                league = bet_details.get("league")
                sport = bet_details.get("sport") or bet_details.get("sport_type")
                player_name = bet_details.get("player_name")
                team_name = bet_details.get("team_name")
                prop_type = bet_details.get("prop_type")
                line_value = bet_details.get("line_value") or bet_details.get("line")
                bet_direction = bet_details.get("bet_direction") or bet_details.get("direction")
                odds = bet_details.get("odds")
                units = float(bet_details.get("units", 0))
                api_game_id = bet_details.get("api_game_id")
                channel_id = bet_details.get("post_channel_id") or bet_details.get("channel_id")
                bet_serial = await self.create_player_prop_bet(
                    guild_id,
                    user_id,
                    league,
                    sport,
                    player_name,
                    team_name,
                    prop_type,
                    line_value,
                    bet_direction,
                    odds,
                    units,
                    api_game_id,
                    channel_id,
                )
                if bet_serial:
                    # --- Discord message sending metrics ---
                    logger.info(f"[METRIC] Preparing to send Discord message for bet_serial {bet_serial} to channel {channel_id}")
                    channel = self.bot.get_channel(channel_id)
                    if channel is None:
                        logger.error(f"[METRIC] Discord channel {channel_id} not found. Message will not be sent.")
                    else:
                        # 1. Fetch member_role from guild_settings
                        member_role_id = None
                        try:
                            gs_row = await self.db_manager.fetch_one("SELECT member_role FROM guild_settings WHERE guild_id = $1", (guild_id,))
                            member_role_id = gs_row["member_role"] if gs_row and "member_role" in gs_row else None
                            logger.info(f"[METRIC] Fetched member_role_id: {member_role_id}")
                        except Exception as e:
                            logger.error(f"[METRIC] Failed to fetch member_role from guild_settings: {e}", exc_info=True)
                        # 2. Fetch user image and display name from cappers
                        user_avatar_url = None
                        user_display_name = None
                        try:
                            capper_row = await self.db_manager.fetch_one(
                                "SELECT * FROM cappers WHERE user_id = $1 AND guild_id = $2",
                                (user_id, guild_id),
                            )
                            if capper_row:
                                avatar_keys = ["avatar_url", "avatar", "avatar_uri", "avatar_path", "avatar_file", "avatar_hash"]
                                display_keys = ["display_name", "displayname", "display", "name", "username"]
                                for k in avatar_keys:
                                    if k in capper_row and capper_row[k]:
                                        user_avatar_url = capper_row[k]
                                        break
                                for k in display_keys:
                                    if k in capper_row and capper_row[k]:
                                        user_display_name = capper_row[k]
                                        break
                            logger.info(f"[METRIC] Fetched user_avatar_url: {user_avatar_url}, user_display_name: {user_display_name}")
                        except Exception as e:
                            logger.error(f"[METRIC] Failed to fetch avatar/display_name from cappers: {e}", exc_info=True)
                        # 3. Resolve preview or generate image
                        image_path = None
                        try:
                            image_path = await self._resolve_image_path(bet_details, bet_serial, guild_id, team_name, None, line_value, odds, units)
                            logger.info(f"[METRIC] Resolved image_path: {image_path}")
                        except Exception as e:
                            logger.error(f"[METRIC] Exception while resolving/generating image: {e}", exc_info=True)
                        # 4. Compose message content
                        mention_str = f"<@&{member_role_id}> " if member_role_id else ""
                        message_content = f"{mention_str}Bet #{bet_serial} submitted! {player_name} ({team_name}), prop: {prop_type} {line_value} {bet_direction}, odds: {odds}, units: {units}"
                        logger.info(f"[METRIC] Sending message: '{message_content}' to channel {channel_id}")
                        # 5. Send message with image, avatar, and display name override
                        try:
                            webhook = None
                            for wh in await channel.webhooks():
                                if wh.name == "Bet Tracking Bot":
                                    webhook = wh
                                    break
                            if webhook is None:
                                webhook = await channel.create_webhook(name="Bet Tracking Bot")
                            logger.info(f"[METRIC] Using webhook ID: {webhook.id}")

                            # Require image produced by generate_bet_image. No fallback allowed.
                            if not image_path:
                                logger.error(f"[METRIC] No generated image available for bet_serial {bet_serial}; aborting webhook send.")
                                return {"success": False, "error": "No generated image to send"}

                            import os
                            import shutil
                            import discord

                            static_root = os.path.join(os.getcwd(), "StaticFiles", "Confirmed_Bets", str(guild_id))
                            try:
                                os.makedirs(static_root, exist_ok=True)
                            except Exception as e:
                                logger.error(f"[METRIC] Failed to create static directory {static_root}: {e}", exc_info=True)
                                return {"success": False, "error": "Failed to store generated image"}

                            original_filename = os.path.basename(image_path)
                            dest_filename = f"bet_{bet_serial}_{original_filename}"
                            dest_path = os.path.join(static_root, dest_filename)

                            try:
                                shutil.copy2(image_path, dest_path)
                                generated_image_db_path = dest_path
                                try:
                                    await self.db_manager.execute(
                                        "UPDATE bets SET generated_image = $1 WHERE bet_serial = $2",
                                        (generated_image_db_path, bet_serial),
                                    )
                                    logger.info(f"[METRIC] Updated bet {bet_serial} generated_image to {generated_image_db_path}")
                                except Exception as e:
                                    logger.error(f"[METRIC] Failed to update generated_image in DB for bet_serial {bet_serial}: {e}", exc_info=True)
                            except Exception as e:
                                logger.error(f"[METRIC] Failed to copy generated image to static directory: {e}", exc_info=True)
                                return {"success": False, "error": "Failed to store generated image"}

                            filename = dest_filename
                            file_to_send = discord.File(dest_path, filename=filename)
                            embed = discord.Embed(title=f"Bet #{bet_serial} submitted!", description=message_content)
                            embed.set_image(url=f"attachment://{filename}")

                            sent_message = await webhook.send(
                                content=None,
                                username=user_display_name or "Bet Tracking Bot",
                                avatar_url=user_avatar_url,
                                file=file_to_send,
                                embed=embed,
                                wait=True,
                            )
                            logger.info(f"[METRIC] Discord webhook message sent successfully. Message ID: {getattr(sent_message, 'id', None)}")
                        except Exception as e:
                            logger.error(f"[METRIC] Exception while sending Discord webhook message for bet_serial {bet_serial}: {e}", exc_info=True)
                    return {"success": True, "bet_serial": bet_serial}
                return {"success": False, "error": "Failed to insert player prop bet"}
        except Exception as e:
            logger.error(f"[SUBMIT BET] Unexpected exception: {e}", exc_info=True)
            return {"success": False, "error": f"Unexpected exception: {e}"}

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
                SET channel_id = $1, message_id = $2, confirmed = 1
                WHERE bet_serial = $3
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
            set_clause = ", ".join(f"{field} = $1" for field in kwargs.keys())
            query = f"""
                UPDATE bets
                SET {set_clause}
                WHERE bet_serial = $1
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
                SET channel_id = $1, message_id = $2, confirmed = 1
                WHERE bet_serial = $3 AND bet_type = 'parlay'
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
            bet_query = "DELETE FROM bets WHERE bet_serial = $1"
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
            bet_lookup_query = "SELECT bet_serial, user_id, guild_id, status FROM bets WHERE message_id = $1 AND guild_id = $2"
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
                ) VALUES ($1, $2, $3, $4, $5, $6)
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

            # Track reaction for community analytics (DISABLED)
            # try:
            #     if (
            #         hasattr(self.bot, "community_analytics_service")
            #         and self.bot.community_analytics_service
            #     ):
            #         await self.bot.community_analytics_service.track_reaction_activity(
            #             guild_id, payload.user_id, bet_serial, emoji_str
            #         )
            # except Exception as e:
            #     logger.error(f"Failed to track reaction for analytics: {e}")

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
                    WHERE bet_serial = $1
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
                    SET status = $1,
                        result_value = $2,
                        bet_won = CASE WHEN $3 = 'won' THEN 1 ELSE 0 END,
                        bet_loss = CASE WHEN $4 = 'lost' THEN 1 ELSE 0 END,
                        updated_at = $5
                    WHERE bet_serial = $6
                """

                units_staked = float(bet_data.get("units", 0.0))
                odds_val = float(bet_data.get("odds", 0.0))
                calculated_result_value = 0.0

                if new_status == "won":
                    if odds_val > 0:
                        # Positive odds: win $odds for every $100 bet
                        # For units: if 1 unit = $100, then profit in units = (odds/100) * units_staked
                        calculated_result_value = units_staked * (odds_val / 100.0)
                    elif odds_val < 0:
                        # Negative odds: need to bet $abs(odds) to win $100
                        # For units: if 1 unit = $100, then profit in units = (100/abs(odds)) * units_staked
                        calculated_result_value = units_staked * (100.0 / abs(odds_val))
                elif new_status == "lost":
                    # Lose the units staked
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
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
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
                            WHERE b2.user_id = $1
                            AND b2.guild_id = $2
                            AND b2.status = 'won'
                        ),
                        bet_loss = (
                            SELECT COUNT(*)
                            FROM bets b2
                            WHERE b2.user_id = $3
                            AND b2.guild_id = $4
                            AND b2.status = 'lost'
                        ),
                        bet_push = (
                            SELECT COUNT(*)
                            FROM bets b2
                            WHERE b2.user_id = $5
                            AND b2.guild_id = $6
                            AND b2.status = 'push'
                        ),
                        updated_at = NOW()
                    WHERE user_id = $7 AND guild_id = $8
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
                "SELECT bet_serial FROM bets WHERE message_id = $1 AND guild_id = $2"
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
                WHERE bet_serial = $1 AND user_id = $2 AND emoji = $3 AND message_id = $4
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
            "SELECT id FROM games WHERE api_game_id = $1", (api_game_id,)
        )
        if row:
            return row["id"]
        # 2) pull details from api_games
        src = await self.db_manager.fetch_one(
            """
            SELECT sport, league_id, home_team_name, away_team_name, start_time, status
            FROM api_games WHERE api_game_id = $1
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
            VALUES ($1,$2,$3,$4,$5,$6,$7,NOW())
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

    def _get_static_root(self, guild_id: int) -> str:
        """Return the absolute static root path for a guild's confirmed bets."""
        import os

        return os.path.join(os.getcwd(), "StaticFiles", "Confirmed_Bets", str(guild_id))

    async def _save_raw_preview(self, preview_data, dest_dir: str, filename: str) -> Optional[str]:
        """Save raw preview data (bytes or base64/data-uri string) to dest_dir/filename.

        Returns the saved absolute path or None on failure.
        """
        import os
        import base64

        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            # bytes
            if isinstance(preview_data, (bytes, bytearray)):
                with open(dest_path, "wb") as fh:
                    fh.write(preview_data)
                return dest_path
            # data URI or base64 string
            if isinstance(preview_data, str):
                # data URI: data:image/png;base64,AAA...
                if preview_data.startswith("data:image/") and "," in preview_data:
                    _, b64 = preview_data.split(",", 1)
                else:
                    b64 = preview_data
                try:
                    raw = base64.b64decode(b64)
                except Exception:
                    logger.warning("[METRIC] Provided preview string is not valid base64")
                    return None
                with open(dest_path, "wb") as fh:
                    fh.write(raw)
                return dest_path
        except Exception as e:
            logger.error(f"[METRIC] Failed to save raw preview image: {e}", exc_info=True)
        return None

    async def _is_base64_string(self, s: str) -> bool:
        import base64
        try:
            # allow padding errors to raise
            base64.b64decode(s)
            return True
        except Exception:
            return False

    async def _resolve_image_path(self, bet_details: Dict, bet_serial: int, guild_id: int, team: Optional[str] = None, opponent: Optional[str] = None, line: Optional[str] = None, odds: Optional[float] = None, units: Optional[float] = None) -> Optional[str]:
        """Resolve an image path to use for the webhook. Behavior:
        - Prefer preview image path fields from bet_details (normalize relative -> absolute).
        - Accept data-uri/base64 or raw bytes keys and write them into StaticFiles/Confirmed_Bets/<guild>.
        - If none, call self.bot.generate_bet_image(...) when available.
        - As a last resort, search StaticFiles for any file with the bet_serial in its filename (useful when preview step saved the file).
        Returns absolute filesystem path or None.
        """
        import os

        static_root = self._get_static_root(guild_id)
        try:
            os.makedirs(static_root, exist_ok=True)
        except Exception as e:
            logger.error(f"[METRIC] Failed to create static root {static_root}: {e}", exc_info=True)
            return None

        # 1) Try common preview path keys
        preview_candidates = [
            "preview_image_path",
            "preview_path",
            "preview_image",
            "preview",
        ]
        preview_value = None
        for k in preview_candidates:
            if k in bet_details and bet_details.get(k):
                preview_value = bet_details.get(k)
                break

        # If preview_value is present, handle it
        if preview_value:
            # If it's bytes-like put it on disk
            if isinstance(preview_value, (bytes, bytearray)):
                filename = f"bet_{bet_serial}_preview"
                # try to guess extension? default .png
                filename = filename + ".png"
                saved = await self._save_raw_preview(preview_value, static_root, filename)
                if saved:
                    return saved
            # If it's a string it may be a path or a data-uri or base64
            if isinstance(preview_value, str):
                # data URI or raw base64
                if preview_value.startswith("data:image/") or (len(preview_value) > 100 and await self._is_base64_string(preview_value)):
                    fname = f"bet_{bet_serial}_preview.png"
                    saved = await self._save_raw_preview(preview_value, static_root, fname)
                    if saved:
                        return saved
                # Otherwise treat as path
                abs_path = preview_value
                if not os.path.isabs(abs_path):
                    abs_path = os.path.abspath(abs_path)
                if os.path.exists(abs_path):
                    return abs_path
                logger.warning(f"[METRIC] Provided preview path not found: {preview_value} -> {abs_path}")

        # 2) Try specific payload keys carrying raw data
        if "preview_image_b64" in bet_details and bet_details.get("preview_image_b64"):
            fname = f"bet_{bet_serial}_preview.png"
            saved = await self._save_raw_preview(bet_details.get("preview_image_b64"), static_root, fname)
            if saved:
                return saved
        if "preview_image_bytes" in bet_details and bet_details.get("preview_image_bytes"):
            fname = f"bet_{bet_serial}_preview.png"
            saved = await self._save_raw_preview(bet_details.get("preview_image_bytes"), static_root, fname)
            if saved:
                return saved

        # 3) Fall back to regenerate via bot if available
        if hasattr(self.bot, "generate_bet_image"):
            try:
                # call generate_bet_image with best-effort args; function should return a path
                generated = await self.bot.generate_bet_image(bet_serial, team, opponent, line, odds, units)
                logger.info(f"[METRIC] generate_bet_image returned: {generated}")
                if generated:
                    # prefer absolute path
                    if not os.path.isabs(generated):
                        generated = os.path.abspath(generated)
                    if os.path.exists(generated):
                        return generated
                    # if file doesn't exist, still return generated (some implementations return remote paths)
                    return generated
            except Exception as e:
                logger.error(f"[METRIC] Exception while generating image fallback: {e}", exc_info=True)
        else:
            logger.debug("[METRIC] No generate_bet_image available on bot for fallback")

        # 4) Last-resort: search StaticFiles for files matching bet_serial.
        # Accept filenames where a date prefix may be prepended to the serial (e.g. 08202025 + 129 => 08202025129)
        try:
            import re
            search_root = os.path.join(os.getcwd(), "StaticFiles")
            if os.path.exists(search_root):
                matches = []
                serial_str = str(bet_serial)
                for root, _, files in os.walk(search_root):
                    for fn in files:
                        full = os.path.join(root, fn)
                        try:
                            # Prefer to match numeric groups explicitly. This lets us omit
                            # a leading date prefix (e.g. 08202025) before the serial.
                            nums = re.findall(r"\d+", fn)
                            matched = False
                            if nums:
                                for n in nums:
                                    # exact numeric group match (best)
                                    if n == serial_str:
                                        mtime = os.path.getmtime(full)
                                        matches.append((mtime, full))
                                        matched = True
                                        break
                                    # numeric group that ends with the serial (date prefix + serial)
                                    if n.endswith(serial_str) and len(n) > len(serial_str):
                                        # accept common date-like prefix lengths (6-9 digits) but allow others
                                        prefix_len = len(n) - len(serial_str)
                                        if prefix_len in (6, 7, 8, 9) or prefix_len > 0:
                                            mtime = os.path.getmtime(full)
                                            matches.append((mtime, full))
                                            matched = True
                                            break
                                if matched:
                                    continue
                            # Fallback: substring match anywhere in filename (least strict)
                            if serial_str in fn:
                                mtime = os.path.getmtime(full)
                                matches.append((mtime, full))
                                continue
                        except Exception:
                            # ignore individual file errors and continue
                            continue
                if matches:
                    # choose the most recently modified match
                    matches.sort(reverse=True)
                    logger.info(f"[METRIC] Found preview candidates for bet_serial {bet_serial}: {[m[1] for m in matches]}")
                    return matches[0][1]
        except Exception as e:
            logger.error(f"[METRIC] Error searching StaticFiles for preview: {e}", exc_info=True)

        return None
