import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

import discord
import pytz

logger = logging.getLogger(__name__)


class LiveGameChannelService:
    def __init__(self, bot: discord.Client, db_manager):
        self.bot = bot
        self.db = db_manager
        self.running = False
        self._update_task: Optional[asyncio.Task] = None
        self.guild_game_channels: Dict[int, Dict[str, int]] = (
            {}
        )  # guild_id -> {api_game_id: channel_id}
        self.cleanup_tasks: Set[asyncio.Task] = set()

    async def start(self):
        """Start the live game channel service."""
        self.running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("LiveGameChannelService started.")

    async def stop(self):
        """Stop the live game channel service."""
        self.running = False
        if self._update_task:
            self._update_task.cancel()
        for task in self.cleanup_tasks.copy():
            task.cancel()
        self.cleanup_tasks.clear()
        logger.info("LiveGameChannelService stopped.")

    async def _update_loop(self):
        """Run the background update loop for live game channels."""
        await self.bot.wait_until_ready()
        while self.running:
            try:
                await self.update_all_live_game_channels()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in live game channel update loop: $1", e, exc_info=True
                )
                await asyncio.sleep(15)

    async def update_all_live_game_channels(self):
        """Update live game channels for all guilds with live_game_updates enabled."""
        guilds = await self.db.fetch_all(
            "SELECT guild_id FROM guild_settings WHERE live_game_updates = 1"
        )
        for guild_row in guilds:
            guild_id = guild_row["guild_id"]
            await self.update_guild_live_game_channels(guild_id)

    async def update_guild_live_game_channels(self, guild_id: int):
        """Update or create live game channels for a guild."""
        # Fetch active gameline bets, including parlay legs, excluding player props
        bets = await self.db.fetch_all(
            """
            SELECT DISTINCT COALESCE(b.api_game_id::text, l.api_game_id::text) as api_game_id,
                   g.home_team_name, g.away_team_name, g.start_time, g.status,
                   g.score, g.id as game_id
            FROM bets b
            LEFT JOIN bet_legs l ON b.bet_type = 'parlay' AND l.bet_id = b.bet_serial
            JOIN api_games g ON COALESCE(b.api_game_id::text, l.api_game_id::text) = g.api_game_id::text
            WHERE b.guild_id = $1 AND b.confirmed = 1
            AND (b.bet_type = 'game_line' OR l.bet_type = 'game_line')
            AND g.status NOT IN ('finished', 'Match Finished', 'Final', 'Ended')
            """,
            (guild_id,),
        )
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning("Guild %s not found", guild_id)
            return
        if guild_id not in self.guild_game_channels:
            self.guild_game_channels[guild_id] = {}
        tracked = self.guild_game_channels[guild_id]
        finished_statuses = {
            s.lower() for s in ["finished", "match finished", "final", "ended"]
        }
        # Remove finished games from tracked
        to_remove = []
        for api_game_id, channel_id in tracked.items():
            # Find the bet in bets
            bet = next((b for b in bets if b["api_game_id"] == api_game_id), None)
            if bet and bet.get("status", "").strip().lower() in finished_statuses:
                to_remove.append(api_game_id)
        for api_game_id in to_remove:
            logger.info(
                f"Removing finished game {api_game_id} from tracking for guild {guild_id}"
            )
            tracked.pop(api_game_id, None)
        for bet in bets:
            api_game_id = bet["api_game_id"]
            if not api_game_id:
                continue
            if api_game_id in tracked:
                # Update existing channel
                channel_id = tracked[api_game_id]
                await self._update_channel_name(guild, channel_id, bet)
            else:
                # Create new channel
                channel = await self._create_live_game_channel(guild, bet)
                if channel:
                    tracked[api_game_id] = channel.id
        # Cleanup finished games
        await self._cleanup_finished_channels(guild, tracked)

    async def _create_live_game_channel(
        self, guild: discord.Guild, bet: dict
    ) -> Optional[discord.TextChannel]:
        """Create a live game update channel for a bet."""
        home = bet.get("home_team_name", "Home")
        away = bet.get("away_team_name", "Away")
        status = bet.get("status", "scheduled")
        score = bet.get("score", "0:0")
        start_time = bet.get("start_time")
        api_game_id = bet.get("api_game_id")
        name = self._format_channel_name(home, away, status, score, start_time)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=False
            )
        }

        try:
            channel = await guild.create_text_channel(
                name=name[:100],
                overwrites=overwrites,
                reason="Live game update channel",
            )
            logger.info(
                "Created live game channel %s for game %s in guild %s",
                channel.name,
                api_game_id,
                guild.id,
            )
            return channel
        except discord.errors.Forbidden:
            logger.error(
                "Missing permissions to create channel in guild %s. Ensure the bot has 'Manage Channels' permission.",
                guild.id,
            )
            return None
        except discord.errors.HTTPException as http_err:
            logger.error(
                "HTTPException occurred while creating channel for game %s in guild %s: %s",
                api_game_id,
                guild.id,
                http_err,
            )
            return None
        except Exception as e:
            logger.error(
                "Unexpected error while creating live game channel for game %s in guild %s: %s",
                api_game_id,
                guild.id,
                e,
                exc_info=True,
            )
            return None

    async def _update_channel_name(
        self, guild: discord.Guild, channel_id: int, bet: dict
    ):
        """Update the name of a live game channel."""
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except discord.errors.NotFound:
                logger.warning("Channel %s not found in guild %s", channel_id, guild.id)
                return
            except Exception as e:
                logger.error(
                    "Failed to fetch channel %s in guild %s: %s",
                    channel_id,
                    guild.id,
                    e,
                )
                return
        home = bet.get("home_team_name", "Home")
        away = bet.get("away_team_name", "Away")
        status = bet.get("status", "scheduled")
        score = bet.get("score", "0:0")
        start_time = bet.get("start_time")
        bet.get("api_game_id")
        new_name = self._format_channel_name(home, away, status, score, start_time)
        if channel.name != new_name[:100]:
            try:
                await channel.edit(name=new_name[:100], reason="Update live game score")
                logger.debug(
                    "Updated channel $1 name to $2 in guild $3",
                    channel_id,
                    new_name[:100],
                    guild.id,
                )
            except discord.errors.Forbidden:
                logger.error(
                    "Missing permissions to edit channel %s in guild %s",
                    channel_id,
                    guild.id,
                )
            except Exception as e:
                logger.error(
                    "Failed to update channel $1 name in guild $2: $3",
                    channel_id,
                    guild.id,
                    e,
                )

    def _format_channel_name(
        self, home: str, away: str, status: str, score: str, start_time: Optional[str]
    ) -> str:
        """Format the channel name based on game status."""
        home_abbr = home[:3].upper() if home and isinstance(home, str) else "HME"
        away_abbr = away[:3].upper() if away and isinstance(away, str) else "AWY"
        if status.lower() in ("not started", "scheduled"):
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                est = dt.astimezone(pytz.timezone("US/Eastern"))
                time_str = est.strftime("%I:%M%p").lstrip("0").lower()
            except (ValueError, TypeError):
                time_str = "TBD"
            return f"{home_abbr}-Vs-{away_abbr}-{time_str}"
        else:
            if score and ":" in score and isinstance(score, str):
                return f"{home_abbr}-Vs-{away_abbr}-{score}"
            return f"{home_abbr}-Vs-{away_abbr}-Live"

    async def _cleanup_finished_channels(
        self, guild: discord.Guild, tracked: Dict[str, int]
    ):
        """Cleanup channels for finished games."""
        finished_games = await self.db.fetch_all(
            """
            SELECT api_game_id, id as game_id, status, end_time
            FROM api_games
            WHERE status IN ('finished', 'Match Finished', 'Final', 'Ended')
            """
        )
        now = datetime.now(pytz.UTC)
        for game in finished_games:
            api_game_id = game["api_game_id"]
            if api_game_id in tracked:
                channel_id = tracked[api_game_id]
                end_time = game.get("end_time")
                if end_time:
                    try:
                        dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        dt = now
                else:
                    dt = now
                delay = max(0, (dt + timedelta(hours=1) - now).total_seconds())
                task = asyncio.create_task(
                    self._delete_channel_later(
                        guild, channel_id, delay, api_game_id, tracked
                    )
                )
                self.cleanup_tasks.add(task)
                task.add_done_callback(lambda t: self.cleanup_tasks.discard(t))

    async def _delete_channel_later(
        self,
        guild: discord.Guild,
        channel_id: int,
        delay: float,
        api_game_id: str,
        tracked: Dict[str, int],
    ):
        """Delete a channel after a delay."""
        await asyncio.sleep(delay)
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except discord.errors.NotFound:
                logger.warning(
                    "Channel %s not found for deletion in guild %s",
                    channel_id,
                    guild.id,
                )
                tracked.pop(api_game_id, None)
                return
            except Exception as e:
                logger.error(
                    "Failed to fetch channel %s for deletion in guild %s: %s",
                    channel_id,
                    guild.id,
                    e,
                )
                return
        try:
            await channel.delete(
                reason="Game finished, deleting live update channel after 1 hour"
            )
            logger.info(
                "Deleted live game channel $1 for game $2 in guild $3",
                channel_id,
                api_game_id,
                guild.id,
            )
        except discord.errors.Forbidden:
            logger.error(
                "Missing permissions to delete channel $1 in guild $2",
                channel_id,
                guild.id,
            )
        except Exception as e:
            logger.error(
                "Failed to delete channel $1 in guild $2: $3", channel_id, guild.id, e
            )
        tracked.pop(api_game_id, None)
