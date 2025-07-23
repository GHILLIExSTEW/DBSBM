"""
Push Notification Service for Discord Member Role Notifications

This service handles sending push notifications to Discord members with the member role,
providing standalone notifications that appear on their phones and devices.
"""

import logging
import asyncio
import discord
from discord import Embed, Webhook
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import json

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications to Discord member roles."""
    
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.notification_cooldowns = {}  # Prevent spam
        self.member_role_cache = {}  # Cache member role IDs
        
    async def start(self):
        """Initialize the push notification service."""
        logger.info("Starting Push Notification service...")
        await self.load_member_roles()
        logger.info("Push Notification service started successfully")
        
    async def load_member_roles(self):
        """Load member role IDs from all guilds."""
        try:
            guild_settings = await self.db_manager.fetch_all(
                "SELECT guild_id, member_role FROM guild_settings WHERE member_role IS NOT NULL"
            )
            for setting in guild_settings:
                self.member_role_cache[setting['guild_id']] = setting['member_role']
            logger.info(f"Loaded member roles for {len(guild_settings)} guilds")
        except Exception as e:
            logger.error(f"Error loading member roles: {e}")
            
    async def get_member_role_id(self, guild_id: int) -> Optional[int]:
        """Get the member role ID for a guild."""
        if guild_id not in self.member_role_cache:
            # Try to load from database
            setting = await self.db_manager.fetch_one(
                "SELECT member_role FROM guild_settings WHERE guild_id = %s",
                (guild_id,)
            )
            if setting and setting.get('member_role'):
                self.member_role_cache[guild_id] = setting['member_role']
            else:
                return None
        return self.member_role_cache.get(guild_id)
        
    async def send_push_notification(
        self,
        guild_id: int,
        channel_id: int,
        title: str,
        message: str,
        notification_type: str = "community",
        priority: str = "normal",
        include_mention: bool = True,
        embed_data: Optional[Dict] = None,
        cooldown_minutes: int = 5
    ) -> bool:
        """
        Send a push notification to all members with the member role.
        
        Args:
            guild_id: Discord guild ID
            channel_id: Channel to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification (community, bet, alert, etc.)
            priority: Priority level (low, normal, high, urgent)
            include_mention: Whether to include @member role mention
            embed_data: Optional embed data for rich notifications
            cooldown_minutes: Minutes to wait between notifications of same type
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Check cooldown
            cooldown_key = f"{guild_id}_{notification_type}"
            if cooldown_key in self.notification_cooldowns:
                last_sent = self.notification_cooldowns[cooldown_key]
                if datetime.now() - last_sent < timedelta(minutes=cooldown_minutes):
                    logger.info(f"Notification cooldown active for {notification_type} in guild {guild_id}")
                    return False
                    
            # Get member role ID
            member_role_id = await self.get_member_role_id(guild_id)
            if not member_role_id:
                logger.warning(f"No member role configured for guild {guild_id}")
                return False
                
            # Get channel
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found for guild {guild_id}")
                return False
                
            # Create notification content
            content = f"<@&{member_role_id}>" if include_mention else None
            
            # Create embed
            embed = self._create_notification_embed(
                title, message, notification_type, priority, embed_data
            )
            
            # Send notification
            await channel.send(content=content, embed=embed)
            
            # Update cooldown
            self.notification_cooldowns[cooldown_key] = datetime.now()
            
            # Log notification
            await self._log_notification(guild_id, channel_id, notification_type, title)
            
            logger.info(f"Push notification sent to guild {guild_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
            
    def _create_notification_embed(
        self,
        title: str,
        message: str,
        notification_type: str,
        priority: str,
        embed_data: Optional[Dict] = None
    ) -> Embed:
        """Create a Discord embed for the notification."""
        
        # Color based on priority
        colors = {
            "low": 0x808080,      # Gray
            "normal": 0x00ff00,   # Green
            "high": 0xffa500,     # Orange
            "urgent": 0xff0000    # Red
        }
        color = colors.get(priority, 0x00ff00)
        
        # Icon based on notification type
        icons = {
            "community": "👥",
            "bet": "🎯",
            "alert": "🚨",
            "achievement": "🏆",
            "event": "🎉",
            "reminder": "⏰",
            "update": "📢",
            "celebration": "🎊"
        }
        icon = icons.get(notification_type, "📢")
        
        embed = Embed(
            title=f"{icon} {title}",
            description=message,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Add notification type badge
        embed.add_field(
            name="📋 Type",
            value=notification_type.title(),
            inline=True
        )
        
        # Add priority badge
        embed.add_field(
            name="⚡ Priority",
            value=priority.title(),
            inline=True
        )
        
        # Add custom fields if provided
        if embed_data and embed_data.get('fields'):
            for field in embed_data['fields']:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
                
        # Add footer
        embed.set_footer(text="📱 Push Notification • Tap to view details")
        
        return embed
        
    async def _log_notification(
        self,
        guild_id: int,
        channel_id: int,
        notification_type: str,
        title: str
    ):
        """Log notification to database for analytics."""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO push_notifications (
                    guild_id, channel_id, notification_type, title, sent_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (guild_id, channel_id, notification_type, title, datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            
    # Community Engagement Notifications
    
    async def notify_new_capper_bet(
        self,
        guild_id: int,
        channel_id: int,
        capper_name: str,
        bet_details: str,
        sport: str
    ) -> bool:
        """Notify members when a new capper bet is posted."""
        title = f"New {sport.title()} Pick from {capper_name}!"
        message = f"**{capper_name}** just posted a new {sport} pick!\n\n{bet_details}\n\nTap to view the full bet and add your reactions!"
        
        embed_data = {
            "fields": [
                {"name": "🎯 Capper", "value": capper_name, "inline": True},
                {"name": "🏈 Sport", "value": sport.title(), "inline": True},
                {"name": "⏰ Posted", "value": "Just now", "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="bet", priority="high",
            embed_data=embed_data, cooldown_minutes=2
        )
        
    async def notify_popular_bet(
        self,
        guild_id: int,
        channel_id: int,
        bet_details: str,
        reaction_count: int
    ) -> bool:
        """Notify members when a bet becomes popular."""
        title = f"🔥 Hot Pick Alert! ({reaction_count} reactions)"
        message = f"This bet is getting lots of attention from the community!\n\n{bet_details}\n\nJoin the discussion and add your reaction!"
        
        embed_data = {
            "fields": [
                {"name": "🔥 Reactions", "value": str(reaction_count), "inline": True},
                {"name": "💬 Status", "value": "Trending", "inline": True},
                {"name": "⏰ Time", "value": "Just now", "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="community", priority="normal",
            embed_data=embed_data, cooldown_minutes=10
        )
        
    async def notify_community_event(
        self,
        guild_id: int,
        channel_id: int,
        event_name: str,
        event_description: str,
        event_time: str = "Now"
    ) -> bool:
        """Notify members about community events."""
        title = f"🎉 Community Event: {event_name}"
        message = f"**{event_name}** is happening {event_time}!\n\n{event_description}\n\nJoin in the fun and participate!"
        
        embed_data = {
            "fields": [
                {"name": "🎉 Event", "value": event_name, "inline": True},
                {"name": "⏰ Time", "value": event_time, "inline": True},
                {"name": "👥 Type", "value": "Community Event", "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="event", priority="normal",
            embed_data=embed_data, cooldown_minutes=30
        )
        
    async def notify_achievement_unlocked(
        self,
        guild_id: int,
        channel_id: int,
        user_name: str,
        achievement_name: str,
        achievement_description: str
    ) -> bool:
        """Notify members when someone unlocks an achievement."""
        title = f"🏆 Achievement Unlocked: {achievement_name}"
        message = f"**{user_name}** just unlocked the **{achievement_name}** achievement!\n\n{achievement_description}\n\nCongratulations! 🎉"
        
        embed_data = {
            "fields": [
                {"name": "🏆 Achievement", "value": achievement_name, "inline": True},
                {"name": "👤 User", "value": user_name, "inline": True},
                {"name": "🎯 Type", "value": "Community Achievement", "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="achievement", priority="normal",
            embed_data=embed_data, cooldown_minutes=5
        )
        
    async def notify_winning_streak(
        self,
        guild_id: int,
        channel_id: int,
        capper_name: str,
        streak_count: int,
        total_profit: str
    ) -> bool:
        """Notify members about winning streaks."""
        title = f"🔥 {capper_name} on {streak_count}-Bet Win Streak!"
        message = f"**{capper_name}** is absolutely crushing it with a **{streak_count}-bet winning streak**!\n\nTotal profit: **{total_profit}**\n\n🔥 The hot streak continues!"
        
        embed_data = {
            "fields": [
                {"name": "🔥 Streak", "value": f"{streak_count} wins", "inline": True},
                {"name": "💰 Profit", "value": total_profit, "inline": True},
                {"name": "👤 Capper", "value": capper_name, "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="celebration", priority="high",
            embed_data=embed_data, cooldown_minutes=15
        )
        
    async def notify_daily_reminder(
        self,
        guild_id: int,
        channel_id: int,
        reminder_type: str,
        message: str
    ) -> bool:
        """Send daily reminders to members."""
        title = f"⏰ Daily Reminder: {reminder_type}"
        message = f"**{reminder_type}**\n\n{message}\n\nDon't miss out on today's action!"
        
        embed_data = {
            "fields": [
                {"name": "⏰ Type", "value": "Daily Reminder", "inline": True},
                {"name": "📅 Date", "value": datetime.now().strftime("%B %d"), "inline": True},
                {"name": "🎯 Action", "value": "Check it out!", "inline": True}
            ]
        }
        
        return await self.send_push_notification(
            guild_id, channel_id, title, message,
            notification_type="reminder", priority="low",
            embed_data=embed_data, cooldown_minutes=60
        )
        
    # Utility Methods
    
    async def get_notification_stats(self, guild_id: int, days: int = 7) -> Dict[str, Any]:
        """Get notification statistics for a guild."""
        try:
            stats = await self.db_manager.fetch_all(
                """
                SELECT 
                    notification_type,
                    COUNT(*) as count,
                    DATE(sent_at) as date
                FROM push_notifications
                WHERE guild_id = %s 
                AND sent_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY notification_type, DATE(sent_at)
                ORDER BY date DESC, count DESC
                """,
                (guild_id, days)
            )
            return {"stats": stats, "total_days": days}
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {"stats": [], "total_days": days}
            
    async def clear_cooldowns(self, guild_id: Optional[int] = None):
        """Clear notification cooldowns."""
        if guild_id:
            # Clear cooldowns for specific guild
            keys_to_remove = [key for key in self.notification_cooldowns.keys() if key.startswith(f"{guild_id}_")]
            for key in keys_to_remove:
                del self.notification_cooldowns[key]
        else:
            # Clear all cooldowns
            self.notification_cooldowns.clear()
        logger.info(f"Cleared notification cooldowns for guild {guild_id if guild_id else 'all'}")
        
    async def send_push_only_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "test",
        priority: str = "normal",
        embed_data: Optional[Dict] = None
    ) -> bool:
        """
        Send a push notification to a specific user using Discord's webhook system.
        This ensures the user receives a notification on their device.
        
        Args:
            user_id: Discord user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            embed_data: Optional embed data
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Get user object
            user = self.bot.get_user(user_id)
            if not user:
                logger.warning(f"User {user_id} not found in bot's user cache")
                return False
                
            # Find a guild where the user is present
            target_guild = None
            for guild in self.bot.guilds:
                if guild.get_member(user_id):
                    target_guild = guild
                    break
            
            if not target_guild:
                logger.error(f"User {user_id} not found in any guild where bot is present")
                return False
            
            # Create embed for the notification
            embed = self._create_notification_embed(
                title, message, notification_type, priority, embed_data
            )
            
            # Add user-specific field
            embed.add_field(
                name="👤 Sent To",
                value=f"{user.display_name} ({user_id})",
                inline=False
            )
            
            # Find a suitable channel for the notification
            notification_channel = None
            
            # First try to get the stored notification channel from database
            try:
                stored_channel_setting = await self.db_manager.fetch_one(
                    "SELECT notification_channel_id FROM guild_settings WHERE guild_id = %s",
                    (target_guild.id,)
                )
                
                if stored_channel_setting and stored_channel_setting.get('notification_channel_id'):
                    stored_channel = target_guild.get_channel(stored_channel_setting['notification_channel_id'])
                    if stored_channel and stored_channel.permissions_for(target_guild.me).send_messages:
                        notification_channel = stored_channel
                        logger.info(f"Using stored notification channel: {stored_channel.name}")
            except Exception as e:
                logger.warning(f"Could not access stored notification channel: {e}")
            
            # Fallback to the designated private notification channel
            if not notification_channel:
                try:
                    designated_channel = target_guild.get_channel(1397388724979109899)
                    if designated_channel and designated_channel.permissions_for(target_guild.me).send_messages:
                        notification_channel = designated_channel
                        logger.info(f"Using designated private notification channel: {designated_channel.name}")
                except Exception as e:
                    logger.warning(f"Could not access designated channel: {e}")
            
            # Final fallback to other channels if no private channels available
            if not notification_channel:
                # Try to find a general or announcements channel
                for channel in target_guild.text_channels:
                    if channel.permissions_for(target_guild.me).send_messages:
                        if any(keyword in channel.name.lower() for keyword in ['general', 'announcements', 'notifications', 'bot']):
                            notification_channel = channel
                            break
                
                # If no specific channel found, use the first available channel
                if not notification_channel:
                    for channel in target_guild.text_channels:
                        if channel.permissions_for(target_guild.me).send_messages:
                            notification_channel = channel
                            break
            
            if not notification_channel:
                logger.error(f"No suitable channel found for notification to user {user_id}")
                return False
            
            # Create a webhook for reliable notification delivery
            try:
                # Create webhook
                webhook = await notification_channel.create_webhook(name="Notification System")
                
                # Send notification with user mention to ensure push notification
                await webhook.send(
                    content=f"<@{user_id}> {title}",
                    embed=embed,
                    username="Notification Bot",
                    avatar_url=self.bot.user.display_avatar.url if self.bot.user else None
                )
                
                # Clean up webhook
                await webhook.delete()
                
                # Log notification
                await self._log_push_notification(user_id, notification_type, title, target_guild.id, notification_channel.id)
                
                logger.info(f"Push notification sent to user {user_id} ({user.display_name}) via webhook: {title}")
                return True
                
            except discord.Forbidden:
                logger.error(f"Cannot create webhook in channel {notification_channel.id}")
                # Fallback to regular message
                try:
                    await notification_channel.send(
                        content=f"<@{user_id}> {title}",
                        embed=embed
                    )
                    await self._log_push_notification(user_id, notification_type, title, target_guild.id, notification_channel.id)
                    logger.info(f"Push notification sent to user {user_id} via fallback method: {title}")
                    return True
                except Exception as fallback_error:
                    logger.error(f"Fallback notification failed: {fallback_error}")
                    return False
                    
            except discord.HTTPException as e:
                logger.error(f"HTTP error creating webhook: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending push notification to user {user_id}: {e}")
            return False
            
    async def debug_user_notification_status(self, user_id: int) -> Dict[str, Any]:
        """
        Debug the notification status for a specific user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Dict with debug information
        """
        debug_info = {
            "user_id": user_id,
            "user_found": False,
            "guilds_found": [],
            "channels_available": [],
            "notification_settings": {},
            "errors": []
        }
        
        try:
            # Check if user exists in bot's cache
            user = self.bot.get_user(user_id)
            if user:
                debug_info["user_found"] = True
                debug_info["user_name"] = user.display_name
                debug_info["user_discriminator"] = user.discriminator
            else:
                debug_info["errors"].append("User not found in bot's user cache")
            
            # Check which guilds the user is in
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    guild_info = {
                        "guild_id": guild.id,
                        "guild_name": guild.name,
                        "member_roles": [role.name for role in member.roles],
                        "bot_permissions": []
                    }
                    
                    # Check bot permissions in this guild
                    bot_member = guild.get_member(self.bot.user.id)
                    if bot_member:
                        guild_info["bot_permissions"] = [perm[0] for perm, value in bot_member.guild_permissions if value]
                    
                    debug_info["guilds_found"].append(guild_info)
                    
                    # Check available channels
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            channel_info = {
                                "channel_id": channel.id,
                                "channel_name": channel.name,
                                "channel_type": str(channel.type),
                                "can_create_webhook": channel.permissions_for(guild.me).manage_webhooks
                            }
                            debug_info["channels_available"].append(channel_info)
            
            if not debug_info["guilds_found"]:
                debug_info["errors"].append("User not found in any guild where bot is present")
            
            # Check notification settings (if we can)
            if user:
                debug_info["notification_settings"] = {
                    "user_id": user.id,
                    "bot_user": user.bot,
                    "system_user": user.system
                }
            
        except Exception as e:
            debug_info["errors"].append(f"Debug error: {str(e)}")
            logger.error(f"Error in debug_user_notification_status: {e}")
        
        return debug_info
            
    async def send_direct_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "test",
        priority: str = "normal",
        embed_data: Optional[Dict] = None
    ) -> bool:
        """
        Send a direct notification to a specific user via DM.
        
        Args:
            user_id: Discord user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            embed_data: Optional embed data
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Get user object
            user = self.bot.get_user(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
                
            # Create embed
            embed = self._create_notification_embed(
                title, message, notification_type, priority, embed_data
            )
            
            # Add user-specific field
            embed.add_field(
                name="👤 Sent To",
                value=f"{user.display_name} ({user_id})",
                inline=False
            )
            
            # Send DM
            await user.send(embed=embed)
            
            # Log notification
            await self._log_direct_notification(user_id, notification_type, title)
            
            logger.info(f"Direct notification sent to user {user_id} ({user.display_name}): {title}")
            return True
            
        except discord.Forbidden:
            logger.warning(f"User {user_id} has DMs disabled")
            return False
        except Exception as e:
            logger.error(f"Error sending direct notification to user {user_id}: {e}")
            return False
            
    async def _log_push_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        guild_id: int,
        channel_id: int
    ):
        """Log push notification to database."""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO push_notifications (
                    guild_id, channel_id, notification_type, title, message, priority, sent_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (guild_id, channel_id, notification_type, title, f"Push notification to user {user_id}", "normal", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Error logging push notification: {e}")
            
    async def _log_direct_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str
    ):
        """Log direct notification to database."""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO push_notifications (
                    guild_id, channel_id, notification_type, title, message, priority, sent_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (0, 0, notification_type, title, f"Direct notification to user {user_id}", "normal", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Error logging direct notification: {e}")


# Database table creation for push notifications
async def create_push_notifications_table(db_manager):
    """Create the push_notifications table if it doesn't exist."""
    try:
        await db_manager.execute("""
            CREATE TABLE IF NOT EXISTS push_notifications (
                notification_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT,
                priority VARCHAR(20) DEFAULT 'normal',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_push_notifications_guild (guild_id),
                INDEX idx_push_notifications_type (notification_type),
                INDEX idx_push_notifications_time (sent_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        logger.info("Push notifications table created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating push notifications table: {e}") 