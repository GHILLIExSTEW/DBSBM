"""
Push Notification Commands

Commands for managing push notifications to the member role.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PushNotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(
        name="notify",
        description="📱 Send a push notification to the member role"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def send_notification(
        self,
        interaction: discord.Interaction,
        title: str,
        message: str,
        notification_type: str = "community",
        priority: str = "normal",
        channel: discord.TextChannel = None
    ):
        """
        Send a push notification to all members with the member role.
        
        **Parameters:**
        - **title**: The notification title (required)
        - **message**: The notification message (required)
        - **notification_type**: Type of notification (optional)
        - **priority**: Priority level (optional)
        - **channel**: Channel to send to (optional, defaults to current channel)
        """
        
        # Validate notification type
        valid_types = ["community", "bet", "alert", "achievement", "event", "reminder", "update", "celebration"]
        if notification_type not in valid_types:
            await interaction.response.send_message(
                f"❌ Invalid notification type. Choose from: {', '.join(valid_types)}",
                ephemeral=True
            )
            return
            
        # Validate priority
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            await interaction.response.send_message(
                f"❌ Invalid priority. Choose from: {', '.join(valid_priorities)}",
                ephemeral=True
            )
            return
            
        # Use current channel if none specified
        target_channel = channel or interaction.channel
        
        # Check if push notification service exists
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available. Please contact support.",
                ephemeral=True
            )
            return
            
        # Send notification
        success = await self.bot.push_notification_service.send_push_notification(
            guild_id=interaction.guild_id,
            channel_id=target_channel.id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority
        )
        
        if success:
            embed = discord.Embed(
                title="✅ Push Notification Sent!",
                description=f"Your notification has been sent to the member role in {target_channel.mention}",
                color=0x00ff00
            )
            embed.add_field(name="📱 Title", value=title, inline=False)
            embed.add_field(name="💬 Message", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
            embed.add_field(name="📋 Type", value=notification_type.title(), inline=True)
            embed.add_field(name="⚡ Priority", value=priority.title(), inline=True)
            embed.add_field(name="📺 Channel", value=target_channel.mention, inline=True)
            embed.set_footer(text="📱 Members will receive this as a push notification on their devices")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Failed to send push notification. Check if member role is configured.",
                ephemeral=True
            )
            
    @app_commands.command(
        name="notify_capper_bet",
        description="📱 Notify members about a new capper bet"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def notify_capper_bet(
        self,
        interaction: discord.Interaction,
        capper_name: str,
        bet_details: str,
        sport: str,
        channel: discord.TextChannel = None
    ):
        """
        Send a notification about a new capper bet.
        
        **Parameters:**
        - **capper_name**: Name of the capper
        - **bet_details**: Details about the bet
        - **sport**: Sport type (football, basketball, etc.)
        - **channel**: Channel to send to (optional)
        """
        
        target_channel = channel or interaction.channel
        
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available.",
                ephemeral=True
            )
            return
            
        success = await self.bot.push_notification_service.notify_new_capper_bet(
            guild_id=interaction.guild_id,
            channel_id=target_channel.id,
            capper_name=capper_name,
            bet_details=bet_details,
            sport=sport
        )
        
        if success:
            embed = discord.Embed(
                title="✅ Capper Bet Notification Sent!",
                description=f"Members have been notified about {capper_name}'s new {sport} pick!",
                color=0x00ff00
            )
            embed.add_field(name="👤 Capper", value=capper_name, inline=True)
            embed.add_field(name="🏈 Sport", value=sport.title(), inline=True)
            embed.add_field(name="📺 Channel", value=target_channel.mention, inline=True)
            embed.set_footer(text="📱 Members received this as a push notification")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Failed to send capper bet notification.",
                ephemeral=True
            )
            
    @app_commands.command(
        name="notify_event",
        description="📱 Notify members about a community event"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def notify_event(
        self,
        interaction: discord.Interaction,
        event_name: str,
        event_description: str,
        event_time: str = "Now",
        channel: discord.TextChannel = None
    ):
        """
        Send a notification about a community event.
        
        **Parameters:**
        - **event_name**: Name of the event
        - **event_description**: Description of the event
        - **event_time**: When the event is happening (optional)
        - **channel**: Channel to send to (optional)
        """
        
        target_channel = channel or interaction.channel
        
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available.",
                ephemeral=True
            )
            return
            
        success = await self.bot.push_notification_service.notify_community_event(
            guild_id=interaction.guild_id,
            channel_id=target_channel.id,
            event_name=event_name,
            event_description=event_description,
            event_time=event_time
        )
        
        if success:
            embed = discord.Embed(
                title="✅ Event Notification Sent!",
                description=f"Members have been notified about **{event_name}**!",
                color=0x00ff00
            )
            embed.add_field(name="🎉 Event", value=event_name, inline=True)
            embed.add_field(name="⏰ Time", value=event_time, inline=True)
            embed.add_field(name="📺 Channel", value=target_channel.mention, inline=True)
            embed.set_footer(text="📱 Members received this as a push notification")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Failed to send event notification.",
                ephemeral=True
            )
            
    @app_commands.command(
        name="notification_stats",
        description="📊 View push notification statistics"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def notification_stats(
        self,
        interaction: discord.Interaction,
        days: int = 7
    ):
        """
        View push notification statistics for the server.
        
        **Parameters:**
        - **days**: Number of days to look back (default: 7)
        """
        
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available.",
                ephemeral=True
            )
            return
            
        stats = await self.bot.push_notification_service.get_notification_stats(
            guild_id=interaction.guild_id,
            days=days
        )
        
        if not stats['stats']:
            embed = discord.Embed(
                title="📊 Push Notification Statistics",
                description=f"No notifications sent in the last {days} days.",
                color=0x808080
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Group stats by type
        type_stats = {}
        for stat in stats['stats']:
            notification_type = stat['notification_type']
            if notification_type not in type_stats:
                type_stats[notification_type] = 0
            type_stats[notification_type] += stat['count']
            
        embed = discord.Embed(
            title="📊 Push Notification Statistics",
            description=f"Statistics for the last {days} days",
            color=0x00ff00
        )
        
        total_notifications = sum(type_stats.values())
        embed.add_field(
            name="📱 Total Notifications",
            value=str(total_notifications),
            inline=False
        )
        
        for notification_type, count in type_stats.items():
            percentage = (count / total_notifications * 100) if total_notifications > 0 else 0
            embed.add_field(
                name=f"📋 {notification_type.title()}",
                value=f"{count} ({percentage:.1f}%)",
                inline=True
            )
            
        embed.set_footer(text=f"📊 Data from the last {days} days")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(
        name="clear_notification_cooldowns",
        description="🔄 Clear notification cooldowns"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_cooldowns(self, interaction: discord.Interaction):
        """Clear all notification cooldowns for this server."""
        
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available.",
                ephemeral=True
            )
            return
            
        await self.bot.push_notification_service.clear_cooldowns(
            guild_id=interaction.guild_id
        )
        
        embed = discord.Embed(
            title="✅ Notification Cooldowns Cleared!",
            description="All notification cooldowns for this server have been cleared.",
            color=0x00ff00
        )
        embed.add_field(
            name="🔄 What this means",
            value="You can now send notifications immediately without waiting for cooldowns.",
            inline=False
        )
        embed.set_footer(text="⚠️ Use this carefully to avoid spam")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(
        name="test_notification",
        description="🧪 Send a test push notification to specific users (no DMs)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def test_notification(
        self,
        interaction: discord.Interaction,
        title: str = "🧪 Test Notification",
        message: str = "This is a test push notification!",
        user_ids: str = "761388542965448767,1182482264110665841"
    ):
        """
        Send a test push notification to specific users by their IDs.
        This sends a notification that appears on their device without sending a DM.
        
        **Parameters:**
        - **title**: Notification title (optional, defaults to "Test Notification")
        - **message**: Notification message (optional, defaults to test message)
        - **user_ids**: Comma-separated list of user IDs (optional, defaults to your test users)
        """
        
        # Parse user IDs
        try:
            user_id_list = [int(uid.strip()) for uid in user_ids.split(',')]
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid user ID format. Please provide comma-separated user IDs (e.g., 123456789,987654321)",
                ephemeral=True
            )
            return
            
        # Check if push notification service exists
        if not hasattr(self.bot, 'push_notification_service'):
            await interaction.response.send_message(
                "❌ Push notification service not available. Please contact support.",
                ephemeral=True
            )
            return
            
        # Send test notifications
        success_count = 0
        failed_users = []
        
        for user_id in user_id_list:
            try:
                # Use the push notification service to send push-only notification
                success = await self.bot.push_notification_service.send_push_only_notification(
                    user_id=user_id,
                    title=f"🧪 {title}",
                    message=message,
                    notification_type="test",
                    priority="normal"
                )
                
                if success:
                    success_count += 1
                else:
                    user = self.bot.get_user(user_id)
                    user_name = user.display_name if user else "Unknown"
                    failed_users.append(f"{user_id} ({user_name}) - Failed to send")
                    
            except Exception as e:
                failed_users.append(f"{user_id} - Error: {str(e)}")
                logger.error(f"Error sending test notification to user {user_id}: {e}")
                
        # Create response embed
        if success_count > 0:
            embed = discord.Embed(
                title="✅ Test Notifications Sent!",
                description=f"Successfully sent test notifications to {success_count} user(s).",
                color=0x00ff00
            )
            embed.add_field(
                name="📱 Title",
                value=title,
                inline=False
            )
            embed.add_field(
                name="💬 Message",
                value=message[:100] + "..." if len(message) > 100 else message,
                inline=False
            )
            embed.add_field(
                name="👥 Successfully Sent To",
                value=f"{success_count} user(s)",
                inline=True
            )
            
            if failed_users:
                embed.add_field(
                    name="❌ Failed Users",
                    value="\n".join(failed_users[:5]) + ("..." if len(failed_users) > 5 else ""),
                    inline=False
                )
                embed.color = 0xffa500  # Orange for partial success
                
            embed.set_footer(text="🧪 Test notifications sent via direct messages")
            
        else:
            embed = discord.Embed(
                title="❌ Test Notifications Failed",
                description="Failed to send test notifications to any users.",
                color=0xff0000
            )
            embed.add_field(
                name="❌ Failed Users",
                value="\n".join(failed_users),
                inline=False
            )
            embed.set_footer(text="🧪 Check user IDs and DM permissions")
            
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(
        name="debug_push",
        description="🔧 Debug push notification system"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def debug_push(self, interaction: discord.Interaction):
        """Debug the push notification system."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            embed = discord.Embed(
                title="🔧 Push Notification System Debug",
                description="Checking system status...",
                color=0x00ff00
            )
            
            # Check if service exists
            service_exists = hasattr(self.bot, 'push_notification_service')
            embed.add_field(
                name="📱 Push Service",
                value="✅ Available" if service_exists else "❌ Not Available",
                inline=True
            )
            
            # Check if commands are loaded
            all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
            push_commands = ["test_notification", "notify", "notify_capper_bet", "notify_event", "notification_stats"]
            available_push = [cmd for cmd in push_commands if cmd in all_commands]
            
            embed.add_field(
                name="📋 Push Commands",
                value=f"Available: {len(available_push)}/{len(push_commands)}",
                inline=True
            )
            
            if available_push:
                embed.add_field(
                    name="✅ Available Commands",
                    value="\n".join([f"• `/{cmd}`" for cmd in available_push]),
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ Missing Commands",
                    value="\n".join([f"• `/{cmd}`" for cmd in push_commands]),
                    inline=False
                )
                
            # Check member role configuration
            if service_exists:
                member_role = await self.bot.push_notification_service.get_member_role_id(interaction.guild_id)
                embed.add_field(
                    name="👥 Member Role",
                    value=f"✅ Configured ({member_role})" if member_role else "❌ Not Configured",
                    inline=True
                )
            else:
                embed.add_field(
                    name="👥 Member Role",
                    value="❌ Service not available",
                    inline=True
                )
                
            # Check database connection
            try:
                await self.bot.db_manager.fetch_one("SELECT 1")
                db_status = "✅ Connected"
            except Exception as e:
                db_status = f"❌ Error: {str(e)[:50]}"
                
            embed.add_field(
                name="🗄️ Database",
                value=db_status,
                inline=True
            )
            
            embed.set_footer(text=f"Guild ID: {interaction.guild_id} • Debug at {discord.utils.utcnow().strftime('%H:%M:%S')}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Debug command failed: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ Debug Failed",
                description=f"Error: {str(e)}",
                color=0xff0000
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot):
    try:
        await bot.add_cog(PushNotificationCog(bot))
        logger.info("PushNotificationCog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load PushNotificationCog: {e}", exc_info=True)
        raise 