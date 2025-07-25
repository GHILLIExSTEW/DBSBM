import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import discord

logger = logging.getLogger(__name__)


class CommunityEventsService:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.daily_events = {
            "monday": {
                "name": "Meme Monday",
                "description": "Share your best betting memes! 🎭",
                "emoji": "😂",
                "color": 0xFF69B4,
                "channel": "general-chat",
            },
            "tuesday": {
                "name": "Trivia Tuesday",
                "description": "Sports and betting trivia questions! 🧠",
                "emoji": "🧠",
                "color": 0x4169E1,
                "channel": "sports-discussion",
            },
            "wednesday": {
                "name": "Prediction Wednesday",
                "description": "Community prediction contests! 🔮",
                "emoji": "🔮",
                "color": 0x9932CC,
                "channel": "betting-strategies",
            },
            "thursday": {
                "name": "Throwback Thursday",
                "description": "Share your best past bets! 📸",
                "emoji": "📸",
                "color": 0xFF8C00,
                "channel": "success-stories",
            },
            "friday": {
                "name": "Fun Fact Friday",
                "description": "Share interesting sports facts! 📚",
                "emoji": "📚",
                "color": 0xFFD700,
                "channel": "sports-discussion",
            },
            "saturday": {
                "name": "Streak Saturday",
                "description": "Celebrate winning streaks! 🔥",
                "emoji": "🔥",
                "color": 0xFF4500,
                "channel": "success-stories",
            },
            "sunday": {
                "name": "Sunday Funday",
                "description": "Relaxed community hangout! ☀️",
                "emoji": "☀️",
                "color": 0x32CD32,
                "channel": "general-chat",
            },
        }

        # Weekly events
        self.weekly_events = {
            "betting_challenge": {
                "name": "Weekly Betting Challenge",
                "description": "Compete for the best betting performance! 🏆",
                "emoji": "🏆",
                "color": 0xFFD700,
                "day": "monday",
            },
            "community_spotlight": {
                "name": "Community Member Spotlight",
                "description": "Highlight outstanding community members! ⭐",
                "emoji": "⭐",
                "color": 0x9370DB,
                "day": "wednesday",
            },
            "strategy_share": {
                "name": "Strategy Share Saturday",
                "description": "Share and discuss betting strategies! 💡",
                "emoji": "💡",
                "color": 0x00FF7F,
                "day": "saturday",
            },
        }

    async def start_daily_event(self, guild_id: int, channel_id: Optional[int] = None):
        """Start a daily community event."""
        # Get current day of week
        current_day = datetime.now().strftime("%A").lower()

        if current_day in self.daily_events:
            event = self.daily_events[current_day]

            embed = discord.Embed(
                title=f"{event['emoji']} {event['name']}",
                description=event["description"],
                color=event["color"],
                timestamp=datetime.utcnow(),
            )
            embed.add_field(
                name="Event Details",
                value="This is a daily community event. Participate to earn recognition and build community bonds!",
                inline=False,
            )
            embed.set_footer(text="Community Event • Daily")

            try:
                # Try to find the channel
                channel = None
                if channel_id:
                    channel = self.bot.get_channel(channel_id)

                if not channel:
                    # Get main chat channel from guild settings
                    guild_settings = await self.db_manager.fetch_one(
                        "SELECT main_chat_channel_id FROM guild_settings WHERE guild_id = %s",
                        (guild_id,)
                    )

                    if guild_settings and guild_settings.get("main_chat_channel_id"):
                        # Use the configured main chat channel
                        channel = self.bot.get_channel(guild_settings["main_chat_channel_id"])
                        logger.info(f"Using configured main chat channel {guild_settings['main_chat_channel_id']} for daily event")

                if not channel:
                    # Fallback: try to find channel by name
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        channel_name = event.get("channel", "main-chat")
                        channel = discord.utils.get(guild.channels, name=channel_name)

                        if not channel:
                            # Try general-chat as fallback
                            channel = discord.utils.get(guild.channels, name="general-chat")

                        if not channel:
                            # Final fallback to first text channel
                            channel = discord.utils.get(
                                guild.channels, type=discord.ChannelType.text
                            )

                if channel:
                    await channel.send(embed=embed)
                    logger.info(
                        f"Started daily event {event['name']} in guild {guild_id} in channel {channel.name}"
                    )

                    # Track event in database
                    await self.track_event(guild_id, "daily", event["name"])
                else:
                    logger.warning(
                        f"Could not find channel for daily event in guild {guild_id}"
                    )

            except Exception as e:
                logger.error(f"Failed to start daily event: {e}")

    async def start_weekly_event(
        self, guild_id: int, event_type: str, channel_id: Optional[int] = None
    ):
        """Start a weekly community event."""
        if event_type in self.weekly_events:
            event = self.weekly_events[event_type]

            embed = discord.Embed(
                title=f"{event['emoji']} {event['name']}",
                description=event["description"],
                color=event["color"],
                timestamp=datetime.utcnow(),
            )
            embed.add_field(
                name="Event Details",
                value="This is a weekly community event. Participate to earn recognition and build community bonds!",
                inline=False,
            )
            embed.set_footer(text="Community Event • Weekly")

            try:
                channel = None
                if channel_id:
                    channel = self.bot.get_channel(channel_id)

                if not channel:
                    # Get main chat channel from guild settings
                    guild_settings = await self.db_manager.fetch_one(
                        "SELECT main_chat_channel_id FROM guild_settings WHERE guild_id = %s",
                        (guild_id,)
                    )

                    if guild_settings and guild_settings.get("main_chat_channel_id"):
                        # Use the configured main chat channel
                        channel = self.bot.get_channel(guild_settings["main_chat_channel_id"])
                        logger.info(f"Using configured main chat channel {guild_settings['main_chat_channel_id']} for weekly event")

                if not channel:
                    # Fallback: try to find channel by name
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        channel = discord.utils.get(guild.channels, name="main-chat")

                        if not channel:
                            channel = discord.utils.get(guild.channels, name="general-chat")

                        if not channel:
                            # Final fallback to first text channel
                            channel = discord.utils.get(
                                guild.channels, type=discord.ChannelType.text
                            )

                if channel:
                    await channel.send(embed=embed)
                    logger.info(
                        f"Started weekly event {event['name']} in guild {guild_id} in channel {channel.name}"
                    )

                    # Track event in database
                    await self.track_event(guild_id, "weekly", event["name"])
                else:
                    logger.warning(
                        f"Could not find channel for weekly event in guild {guild_id}"
                    )

            except Exception as e:
                logger.error(f"Failed to start weekly event: {e}")

    async def track_event(self, guild_id: int, event_type: str, event_name: str):
        """Track event participation in database."""
        try:
            query = """
                INSERT INTO community_events (guild_id, event_type, event_name, started_at)
                VALUES (%s, %s, %s, %s)
            """
            await self.db_manager.execute(
                query, (guild_id, event_type, event_name, datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Failed to track event: {e}")

    async def notify_cross_channel(
        self, guild_id: int, source_channel: str, target_channel: str, message: str
    ):
        """Send notifications across channels."""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            source = discord.utils.get(guild.channels, name=source_channel)
            target = discord.utils.get(guild.channels, name=target_channel)

            if source and target:
                embed = discord.Embed(
                    title="📢 Cross-Channel Update",
                    description=message,
                    color=0x4169E1,
                    timestamp=datetime.utcnow(),
                )
                embed.set_footer(text=f"From #{source_channel} to #{target_channel}")

                await target.send(embed=embed)
                logger.info(
                    f"Cross-channel notification: {source_channel} -> {target_channel}"
                )

        except Exception as e:
            logger.error(f"Failed to send cross-channel notification: {e}")

    async def highlight_popular_bet(
        self, guild_id: int, bet_serial: int, reaction_count: int
    ):
        """Highlight popular bets in main chat."""
        if reaction_count >= 10:  # Threshold for "popular" bet
            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return

                # Find main chat channel
                main_channel = discord.utils.get(guild.channels, name="general-chat")
                if not main_channel:
                    main_channel = discord.utils.get(
                        guild.channels, type=discord.ChannelType.text
                    )

                if main_channel:
                    embed = discord.Embed(
                        title="🔥 Popular Bet Alert!",
                        description=f"A bet has received {reaction_count} reactions and is getting community attention!",
                        color=0xFF4500,
                        timestamp=datetime.utcnow(),
                    )
                    embed.add_field(
                        name="Bet Serial", value=f"#{bet_serial}", inline=True
                    )
                    embed.add_field(
                        name="Reactions",
                        value=f"{reaction_count} reactions",
                        inline=True,
                    )
                    embed.set_footer(text="Check out this popular bet!")

                    await main_channel.send(embed=embed)
                    logger.info(
                        f"Highlighted popular bet {bet_serial} with {reaction_count} reactions"
                    )

            except Exception as e:
                logger.error(f"Failed to highlight popular bet: {e}")

    async def get_event_stats(self, guild_id: int, days: int = 7):
        """Get event participation statistics."""
        try:
            query = """
                SELECT
                    event_type,
                    event_name,
                    COUNT(*) as event_count,
                    MIN(started_at) as first_event,
                    MAX(started_at) as last_event
                FROM community_events
                WHERE guild_id = %s
                AND started_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY event_type, event_name
                ORDER BY event_count DESC
            """
            return await self.db_manager.fetch_all(query, (guild_id, days))
        except Exception as e:
            logger.error(f"Failed to get event stats: {e}")
            return []

    async def schedule_daily_events(self):
        """Schedule daily events for all guilds."""
        try:
            # Get all guilds
            guilds_query = "SELECT guild_id FROM guild_settings"
            guilds = await self.db_manager.fetch_all(guilds_query)

            for guild in guilds:
                guild_id = guild["guild_id"]
                await self.start_daily_event(guild_id)

        except Exception as e:
            logger.error(f"Failed to schedule daily events: {e}")

    async def start(self):
        """Start the community events service."""
        logger.info("Starting Community Events Service")

        # Schedule daily events
        await self.schedule_daily_events()

        # Set up periodic tasks
        asyncio.create_task(self._daily_event_loop())

    async def stop(self):
        """Stop the community events service."""
        logger.info("Stopping Community Events Service")

    async def _daily_event_loop(self):
        """Background loop for daily events."""
        while True:
            try:
                # Wait until next day at 9 AM
                now = datetime.now()
                next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(wait_seconds)

                # Start daily events
                await self.schedule_daily_events()

            except Exception as e:
                logger.error(f"Error in daily event loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
