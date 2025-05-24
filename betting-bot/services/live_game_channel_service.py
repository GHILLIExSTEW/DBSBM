import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set
import discord

logger = logging.getLogger(__name__)

class LiveGameChannelService:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db = db_manager
        self.running = False
        self._update_task: Optional[asyncio.Task] = None
        self.guild_game_channels: Dict[int, Dict[str, int]] = {}  # guild_id -> {api_game_id: channel_id}
        self.cleanup_tasks: Set[asyncio.Task] = set()

    async def start(self):
        self.running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("LiveGameChannelService started.")

    async def stop(self):
        self.running = False
        if self._update_task:
            self._update_task.cancel()
        for task in self.cleanup_tasks:
            task.cancel()
        logger.info("LiveGameChannelService stopped.")

    async def _update_loop(self):
        await self.bot.wait_until_ready()
        while self.running:
            try:
                await self.update_all_live_game_channels()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live game channel update loop: {e}")
                await asyncio.sleep(15)

    async def update_all_live_game_channels(self):
        # Fetch all guilds with live_game_updates enabled
        guilds = await self.db.fetch_all("SELECT guild_id FROM guild_settings WHERE live_game_updates = 1")
        for guild_row in guilds:
            guild_id = guild_row['guild_id']
            await self.update_guild_live_game_channels(guild_id)

    async def update_guild_live_game_channels(self, guild_id: int):
        # Get all active gameline bets for this guild (not player props/parlay legs that are player props)
        bets = await self.db.fetch_all(
            """
            SELECT DISTINCT b.api_game_id, g.home_team_name, g.away_team_name, g.start_time, g.status, g.score, g.id as game_id
            FROM bets b
            JOIN api_games g ON b.api_game_id = g.api_game_id
            WHERE b.guild_id = %s AND b.confirmed = 1 AND b.bet_type = 'game_line' AND g.status NOT IN ('finished', 'Match Finished', 'Final', 'Ended')
            """,
            (guild_id,)
        )
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        if guild_id not in self.guild_game_channels:
            self.guild_game_channels[guild_id] = {}
        tracked = self.guild_game_channels[guild_id]
        for bet in bets:
            api_game_id = bet['api_game_id']
            if api_game_id in tracked:
                # Update channel name
                channel_id = tracked[api_game_id]
                await self._update_channel_name(guild, channel_id, bet)
            else:
                # Create channel
                channel = await self._create_live_game_channel(guild, bet)
                if channel:
                    tracked[api_game_id] = channel.id
        # Cleanup finished games
        await self._cleanup_finished_channels(guild, tracked)

    async def _create_live_game_channel(self, guild, bet):
        # Channel name: HomeAbbr Vs. AwayAbbr | home_score : away_score or start time
        home = bet['home_team_name']
        away = bet['away_team_name']
        status = bet['status']
        score = bet['score']
        start_time = bet['start_time']
        name = self._format_channel_name(home, away, status, score, start_time)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)}
        try:
            channel = await guild.create_text_channel(name=name[:100], overwrites=overwrites, reason="Live game update channel")
            logger.info(f"Created live game channel {channel.name} in guild {guild.id}")
            return channel
        except Exception as e:
            logger.error(f"Failed to create live game channel: {e}")
            return None

    async def _update_channel_name(self, guild, channel_id, bet):
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except Exception:
                return
        home = bet['home_team_name']
        away = bet['away_team_name']
        status = bet['status']
        score = bet['score']
        start_time = bet['start_time']
        new_name = self._format_channel_name(home, away, status, score, start_time)
        if channel.name != new_name[:100]:
            try:
                await channel.edit(name=new_name[:100], reason="Update live game score")
            except Exception as e:
                logger.error(f"Failed to update live game channel name: {e}")

    def _format_channel_name(self, home, away, status, score, start_time):
        # Use abbreviations if available, else full names
        home_abbr = home[:3].upper() if home else "HME"
        away_abbr = away[:3].upper() if away else "AWY"
        if status.lower() in ("not started", "scheduled"):
            # Show start time in EST
            try:
                dt = datetime.fromisoformat(start_time)
                est = dt.astimezone(timezone(timedelta(hours=-5)))
                time_str = est.strftime("%I:%M%p").lstrip('0').lower()
            except Exception:
                time_str = "TBD"
            return f"{home_abbr} Vs. {away_abbr} | {time_str}"
        else:
            # Show score if available
            if score and ":" in score:
                return f"{home_abbr} Vs. {away_abbr} | {score}"
            return f"{home_abbr} Vs. {away_abbr} | Live"

    async def _cleanup_finished_channels(self, guild, tracked):
        # Find games that are finished and schedule channel deletion 1 hour after finish
        finished_games = await self.db.fetch_all(
            """
            SELECT api_game_id, g.id as game_id, g.status, g.end_time
            FROM api_games g
            WHERE g.status IN ('finished', 'Match Finished', 'Final', 'Ended')
            """
        )
        now = datetime.now(timezone.utc)
        for game in finished_games:
            api_game_id = game['api_game_id']
            if api_game_id in tracked:
                channel_id = tracked[api_game_id]
                # Schedule deletion if not already scheduled
                end_time = game.get('end_time')
                if end_time:
                    try:
                        dt = datetime.fromisoformat(end_time)
                    except Exception:
                        dt = now
                else:
                    dt = now
                delay = max(0, (dt + timedelta(hours=1) - now).total_seconds())
                task = asyncio.create_task(self._delete_channel_later(guild, channel_id, delay, api_game_id, tracked))
                self.cleanup_tasks.add(task)

    async def _delete_channel_later(self, guild, channel_id, delay, api_game_id, tracked):
        await asyncio.sleep(delay)
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except Exception:
                return
        try:
            await channel.delete(reason="Game finished, deleting live update channel after 1 hour")
            logger.info(f"Deleted live game channel {channel_id} in guild {guild.id}")
        except Exception as e:
            logger.error(f"Failed to delete live game channel: {e}")
        tracked.pop(api_game_id, None)
