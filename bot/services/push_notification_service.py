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