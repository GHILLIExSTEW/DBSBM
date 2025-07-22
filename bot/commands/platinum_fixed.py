import logging
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PlatinumCog(commands.Cog):
    """Platinum tier advanced features commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        """Handle errors for Platinum commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need 'Manage Server' permissions to use Platinum commands.", ephemeral=True
            )
        else:
            logger.error(f"Error in Platinum command: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.", ephemeral=True
            )

    @app_commands.command(name="platinum", description="Check Platinum tier status or upgrade")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def platinum_status(self, interaction: Interaction):
        """Check Platinum tier status or direct to subscription page."""
        try:
            guild_id = interaction.guild_id
            user = interaction.user
            
            # Check if user has authorized role - REQUIRED for all users
            guild_settings = await self.bot.admin_service.get_guild_settings(guild_id)
            if guild_settings and guild_settings.get('authorized_role'):
                authorized_role_id = guild_settings['authorized_role']
                has_authorized_role = any(role.id == authorized_role_id for role in user.roles)
                if not has_authorized_role:
                    await interaction.response.send_message(
                        "❌ You need the authorized user role to use this command.", ephemeral=True
                    )
                    return
            else:
                # If no authorized role is set, only allow admins
                if not user.guild_permissions.administrator:
                    await interaction.response.send_message(
                        "❌ You need administrator permissions to use this command.", ephemeral=True
                    )
                    return
            
            # Check if guild has Platinum subscription
            is_platinum = await self.bot.platinum_service.is_platinum_guild(guild_id)
            
            if is_platinum:
                # Get feature usage
                webhook_count = await self.bot.platinum_service.get_webhook_count(guild_id)
                export_count = await self.bot.platinum_service.get_export_count(guild_id, datetime.now().month)
                
                embed = discord.Embed(
                    title="💎 Platinum Tier - Active",
                    description="Thank you for your Platinum subscription!",
                    color=0x9b59b6
                )
                
                embed.add_field(
                    name="Active Features",
                    value="✅ Advanced Betting Tools\n"
                          "✅ Enhanced Analytics\n"
                          "✅ Custom Notifications\n"
                          "✅ Custom Branding\n"
                          "✅ Performance Tracking\n"
                          "✅ Priority Support\n"
                          "✅ Webhook Integrations\n"
                          "✅ Real-Time Alerts\n"
                          "✅ Data Export Tools\n"
                          "✅ Direct API Access",
                    inline=True
                )
                
                embed.add_field(
                    name="Usage",
                    value=f"Webhooks: {webhook_count}/10\n"
                          f"Exports (this month): {export_count}/50",
                    inline=True
                )
                
                embed.add_field(
                    name="Available Commands",
                    value="`/webhook` - Manage webhooks\n"
                          "`/export` - Export data\n"
                          "`/analytics` - View analytics\n"
                          "`/api_*` - Query sports APIs",
                    inline=False
                )
                
                embed.set_footer(text="Your Platinum subscription is active and ready to use!")
                
            else:
                # Check if user is admin for upgrade link
                is_admin = user.guild_permissions.administrator
                
                embed = discord.Embed(
                    title="💎 Platinum Tier - Upgrade Available",
                    description="Unlock advanced features with Platinum tier!",
                    color=0x9b59b6
                )
                
                embed.add_field(
                    name="Platinum Features",
                    value="🎯 Advanced Betting Tools\n"
                          "📊 Enhanced Analytics\n"
                          "🔔 Custom Notifications\n"
                          "🎨 Custom Branding\n"
                          "📈 Performance Tracking\n"
                          "⚡ Priority Support\n"
                          "🔗 Webhook Integrations\n"
                          "📤 Data Export Tools\n"
                          "🔌 Direct API Access\n"
                          "⚡ Real-Time Alerts",
                    inline=True
                )
                
                embed.add_field(
                    name="Pricing",
                    value="💎 **Platinum**: $99.99/month\n"
                          "⭐ **Premium**: $49.99/month",
                    inline=True
                )
                
                if is_admin:
                    embed.add_field(
                        name="Upgrade Now",
                        value="[Click here to upgrade](https://your-subscription-page.com)",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Contact Admin",
                        value="Please contact a server administrator to upgrade to Platinum tier.",
                        inline=False
                    )
                
                embed.set_footer(text="Upgrade to unlock these powerful features!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in platinum_status: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while checking Platinum status.", ephemeral=True
            )

    @app_commands.command(
        name="webhook", 
        description="🔗 Create webhook integrations for external notifications (Platinum only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_webhook(
        self,
        interaction: Interaction,
        webhook_name: str = app_commands.describe(
            "A descriptive name for your webhook (e.g., 'Bet Notifications', 'Analytics Feed')"
        ),
        webhook_url: str = app_commands.describe(
            "The webhook URL from your external service (Discord, Slack, etc.)"
        ),
        webhook_type: str = app_commands.describe(
            "Type of notifications to send to this webhook"
        )
    ):
        """
        🔗 Create webhook integrations for external notifications
        
        **Step-by-Step Instructions:**
        
        **Step 1: Choose Your External Service**
        • Discord: Create a webhook in your target channel
        • Slack: Create an incoming webhook in your workspace
        • Discord: Use a webhook URL from another server
        • Custom API: Use your own webhook endpoint
        
        **Step 2: Get Your Webhook URL**
        • **Discord:** Channel Settings → Integrations → Webhooks → New Webhook → Copy URL
        • **Slack:** Apps → Incoming Webhooks → Add Configuration → Copy Webhook URL
        • **Custom:** Your API endpoint that accepts POST requests
        
        **Step 3: Choose Webhook Type**
        • `bet_created` - When new bets are placed
        • `bet_resulted` - When bets are graded/resulted
        • `user_activity` - User registrations, logins, etc.
        • `analytics` - Daily/weekly analytics reports
        • `general` - All notifications combined
        
        **Step 4: Test Your Webhook**
        After creation, the system will send a test message to verify it works.
        """
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                embed = discord.Embed(
                    title="❌ Platinum Required",
                    description="This feature requires a **Platinum subscription**.\n\n"
                               "**Upgrade Benefits:**\n"
                               "• 🔗 Webhook integrations\n"
                               "• 📊 Advanced analytics\n"
                               "• 📁 Data exports\n"
                               "• 🎯 Custom notifications\n\n"
                               "Contact support to upgrade your subscription.",
                    color=0xff6b35
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Show detailed instructions first
            instructions_embed = discord.Embed(
                title="🔗 Webhook Setup Guide",
                description="Follow these steps to create your webhook integration:",
                color=0x9b59b6
            )
            
            instructions_embed.add_field(
                name="📋 **Step 1: Choose Your Service**",
                value="• **Discord:** Create webhook in target channel\n"
                      "• **Slack:** Create incoming webhook\n"
                      "• **Custom API:** Your own webhook endpoint",
                inline=False
            )
            
            instructions_embed.add_field(
                name="🔗 **Step 2: Get Webhook URL**",
                value="**Discord:** Channel Settings → Integrations → Webhooks → New Webhook → Copy URL\n"
                      "**Slack:** Apps → Incoming Webhooks → Add Configuration → Copy URL\n"
                      "**Custom:** Your API endpoint that accepts POST requests",
                inline=False
            )
            
            instructions_embed.add_field(
                name="📝 **Step 3: Choose Notification Type**",
                value="• `bet_created` - New bets placed\n"
                      "• `bet_resulted` - Bets graded/resulted\n"
                      "• `user_activity` - User registrations, logins\n"
                      "• `analytics` - Daily/weekly reports\n"
                      "• `general` - All notifications",
                inline=False
            )
            
            instructions_embed.add_field(
                name="✅ **Step 4: Test & Verify**",
                value="After creation, we'll send a test message to verify your webhook works correctly.",
                inline=False
            )
            
            instructions_embed.set_footer(text="💡 Tip: Use descriptive names like 'Bet Notifications' or 'Analytics Feed'")
            
            await interaction.response.send_message(embed=instructions_embed, ephemeral=True)
            
            # Validate webhook type with better descriptions
            webhook_types = {
                "bet_created": "📊 New bets placed by users",
                "bet_resulted": "✅ Bets graded and resulted",
                "user_activity": "👥 User registrations and activity",
                "analytics": "📈 Daily/weekly analytics reports",
                "general": "🔔 All notifications combined"
            }
            
            if webhook_type not in webhook_types:
                error_embed = discord.Embed(
                    title="❌ Invalid Webhook Type",
                    description="Please choose one of these webhook types:",
                    color=0xff0000
                )
                
                for wtype, description in webhook_types.items():
                    error_embed.add_field(
                        name=f"`{wtype}`",
                        value=description,
                        inline=False
                    )
                
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Validate webhook URL format
            if not webhook_url.startswith(('http://', 'https://')):
                error_embed = discord.Embed(
                    title="❌ Invalid Webhook URL",
                    description="Your webhook URL must start with `http://` or `https://`\n\n"
                               "**Example valid URLs:**\n"
                               "• `https://discord.com/api/webhooks/123456789/abcdef`\n"
                               "• `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`\n"
                               "• `https://your-api.com/webhook`",
                    color=0xff0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Create webhook
            success = await self.bot.platinum_service.create_webhook(
                guild_id, webhook_name, webhook_url, webhook_type
            )
            
            if success:
                success_embed = discord.Embed(
                    title="✅ Webhook Created Successfully!",
                    description=f"Your webhook **'{webhook_name}'** has been created and is ready to receive notifications.",
                    color=0x00ff00
                )
                
                success_embed.add_field(
                    name="📝 **Webhook Details**",
                    value=f"**Name:** {webhook_name}\n"
                          f"**Type:** {webhook_type}\n"
                          f"**Description:** {webhook_types[webhook_type]}\n"
                          f"**URL:** `{webhook_url[:50]}...`",
                    inline=False
                )
                
                success_embed.add_field(
                    name="🔔 **What Happens Next**",
                    value="• Test message will be sent to verify connection\n"
                          "• Notifications will start flowing automatically\n"
                          "• You can manage webhooks with `/webhook_list`\n"
                          "• Remove webhooks with `/webhook_remove`",
                    inline=False
                )
                
                success_embed.add_field(
                    name="📊 **Notification Examples**",
                    value="**Bet Created:** `User @John placed a $50 bet on Lakers -5.5`\n"
                          "**Bet Resulted:** `User @Sarah's bet on Warriors +3.5 WON (+$45.50)`\n"
                          "**Analytics:** `Daily Report: 25 bets, $1,250 volume, 68% win rate`",
                    inline=False
                )
                
                success_embed.set_footer(text="🎉 Your webhook is now active and receiving notifications!")
                
            else:
                success_embed = discord.Embed(
                    title="❌ Webhook Creation Failed",
                    description="Failed to create webhook. This could be due to:\n\n"
                               "• Invalid webhook URL\n"
                               "• Network connectivity issues\n"
                               "• Service temporarily unavailable\n\n"
                               "**Troubleshooting:**\n"
                               "1. Verify your webhook URL is correct\n"
                               "2. Test the URL in a browser\n"
                               "3. Check if the service is accessible\n"
                               "4. Try again in a few minutes",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in create_webhook: {e}")
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An error occurred while creating your webhook.\n\n"
                           "**Please try:**\n"
                           "1. Check your webhook URL format\n"
                           "2. Verify the external service is accessible\n"
                           "3. Contact support if the issue persists\n\n"
                           f"**Error:** {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="export", description="Export server data (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def export_data(
        self,
        interaction: Interaction,
        export_type: str,
        format: str,
        user: Optional[discord.Member] = None
    ):
        """Export server data for Platinum tier."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            # Validate export type
            valid_types = ["bets", "users", "analytics", "all"]
            if export_type not in valid_types:
                await interaction.response.send_message(
                    f"❌ Invalid export type. Valid types: {', '.join(valid_types)}", 
                    ephemeral=True
                )
                return
            
            # Validate format
            valid_formats = ["csv", "json", "xlsx"]
            if format not in valid_formats:
                await interaction.response.send_message(
                    f"❌ Invalid format. Valid formats: {', '.join(valid_formats)}", 
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Create export with user filter if specified
            success = await self.bot.platinum_service.create_export(
                guild_id, export_type, format, interaction.user.id, user.id if user else None
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Export Created",
                    description=f"Data export '{export_type}' in {format.upper()} format is being prepared.",
                    color=0x00ff00
                )
                embed.add_field(name="Type", value=export_type, inline=True)
                embed.add_field(name="Format", value=format.upper(), inline=True)
                if user:
                    embed.add_field(name="User Filter", value=f"@{user.display_name}", inline=True)
                else:
                    embed.add_field(name="User Filter", value="All Users", inline=True)
                embed.set_footer(text="You will receive a notification when the export is ready.")
            else:
                embed = discord.Embed(
                    title="❌ Export Failed",
                    description="Failed to create export. Please try again.",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in export_data: {e}")
            await interaction.followup.send(
                "❌ An error occurred while creating the export.", ephemeral=True
            )

    @app_commands.command(name="analytics", description="View Platinum analytics (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def view_analytics(self, interaction: Interaction):
        """View Platinum analytics for the server."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Get analytics data
            analytics = await self.bot.platinum_service.get_analytics(guild_id)
            
            embed = discord.Embed(
                title="📊 Platinum Analytics",
                description="Server analytics and usage statistics",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="Webhook Usage",
                value=f"Active: {analytics.get('webhook_count', 0)}/10",
                inline=True
            )
            
            embed.add_field(
                name="Export Usage",
                value=f"This month: {analytics.get('export_count', 0)}/50",
                inline=True
            )
            
            embed.add_field(
                name="API Usage",
                value=f"Requests: {analytics.get('api_requests', 0)}",
                inline=True
            )
            
            embed.add_field(
                name="Most Used Features",
                value=analytics.get('top_features', 'No data available'),
                inline=False
            )
            
            embed.set_footer(text="Analytics updated in real-time")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_analytics: {e}")
            await interaction.followup.send(
                "❌ An error occurred while loading analytics.", ephemeral=True
            )

    @app_commands.command(
        name="webhook_list", 
        description="📋 List all your webhook integrations (Platinum only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_webhooks(self, interaction: Interaction):
        """List all webhook integrations for the guild."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                embed = discord.Embed(
                    title="❌ Platinum Required",
                    description="This feature requires a **Platinum subscription**.",
                    color=0xff6b35
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get webhooks from service
            webhooks = await self.bot.platinum_service.get_webhooks(guild_id)
            
            if not webhooks:
                embed = discord.Embed(
                    title="📋 No Webhooks Found",
                    description="You haven't created any webhook integrations yet.\n\n"
                               "**To create your first webhook:**\n"
                               "Use `/webhook` to set up external notifications for:\n"
                               "• 📊 Bet notifications\n"
                               "• 📈 Analytics reports\n"
                               "• 👥 User activity\n"
                               "• 🔔 General updates",
                    color=0x9b59b6
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 Your Webhook Integrations",
                description=f"Found **{len(webhooks)}** webhook(s) configured:",
                color=0x9b59b6
            )
            
            webhook_types = {
                "bet_created": "📊 Bet Created",
                "bet_resulted": "✅ Bet Resulted", 
                "user_activity": "👥 User Activity",
                "analytics": "📈 Analytics",
                "general": "🔔 General"
            }
            
            for i, webhook in enumerate(webhooks, 1):
                webhook_type = webhook_types.get(webhook.get('type', 'unknown'), '❓ Unknown')
                status = "🟢 Active" if webhook.get('active', True) else "🔴 Inactive"
                
                embed.add_field(
                    name=f"{i}. {webhook.get('name', 'Unnamed Webhook')}",
                    value=f"**Type:** {webhook_type}\n"
                          f"**Status:** {status}\n"
                          f"**URL:** `{webhook.get('url', 'N/A')[:40]}...`\n"
                          f"**Created:** {webhook.get('created_at', 'Unknown')}",
                    inline=False
                )
            
            embed.add_field(
                name="🔧 **Management**",
                value="• Use `/webhook_remove` to delete webhooks\n"
                      "• Use `/webhook` to create new webhooks\n"
                      "• Contact support for advanced configuration",
                inline=False
            )
            
            embed.set_footer(text=f"Total webhooks: {len(webhooks)}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in list_webhooks: {e}")
            error_embed = discord.Embed(
                title="❌ Error Loading Webhooks",
                description="Failed to load your webhook list.\n\n"
                           "**Please try:**\n"
                           "1. Check your internet connection\n"
                           "2. Try again in a few minutes\n"
                           "3. Contact support if the issue persists",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="webhook_remove", 
        description="🗑️ Remove a webhook integration (Platinum only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_webhook(
        self,
        interaction: Interaction,
        webhook_name: str = app_commands.describe(
            "The exact name of the webhook to remove (use /webhook_list to see names)"
        )
    ):
        """Remove a webhook integration."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                embed = discord.Embed(
                    title="❌ Platinum Required",
                    description="This feature requires a **Platinum subscription**.",
                    color=0xff6b35
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Confirm removal
            confirm_embed = discord.Embed(
                title="🗑️ Confirm Webhook Removal",
                description=f"Are you sure you want to remove the webhook **'{webhook_name}'**?\n\n"
                           "**This action will:**\n"
                           "• Stop all notifications to this webhook\n"
                           "• Permanently delete the webhook configuration\n"
                           "• Cannot be undone\n\n"
                           "**To proceed:**\n"
                           "Click the ✅ button below to confirm removal.",
                color=0xff6b35
            )
            
            confirm_embed.add_field(
                name="💡 **Need to see your webhooks?**",
                value="Use `/webhook_list` to see all your configured webhooks.",
                inline=False
            )
            
            # Create confirmation view
            class ConfirmWebhookRemoval(discord.ui.View):
                def __init__(self, cog, webhook_name: str):
                    super().__init__(timeout=60)
                    self.cog = cog
                    self.webhook_name = webhook_name
                
                @discord.ui.button(label="✅ Confirm Removal", style=discord.ButtonStyle.danger)
                async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                    try:
                        # Remove webhook
                        success = await self.cog.bot.platinum_service.remove_webhook(
                            interaction.guild_id, self.webhook_name
                        )
                        
                        if success:
                            success_embed = discord.Embed(
                                title="✅ Webhook Removed",
                                description=f"The webhook **'{self.webhook_name}'** has been successfully removed.\n\n"
                                           "**What happened:**\n"
                                           "• Webhook configuration deleted\n"
                                           "• Notifications stopped\n"
                                           "• No more messages will be sent",
                                color=0x00ff00
                            )
                        else:
                            success_embed = discord.Embed(
                                title="❌ Removal Failed",
                                description=f"Failed to remove webhook **'{self.webhook_name}'**.\n\n"
                                           "**Possible reasons:**\n"
                                           "• Webhook doesn't exist\n"
                                           "• Database connection issue\n"
                                           "• Permission denied\n\n"
                                           "**Try:**\n"
                                           "1. Check the webhook name with `/webhook_list`\n"
                                           "2. Try again in a few minutes\n"
                                           "3. Contact support if needed",
                                color=0xff0000
                            )
                        
                        await interaction.response.edit_message(embed=success_embed, view=None)
                        
                    except Exception as e:
                        logger.error(f"Error in webhook removal: {e}")
                        error_embed = discord.Embed(
                            title="❌ Error",
                            description="An error occurred while removing the webhook.\n\n"
                                       f"**Error:** {str(e)}",
                            color=0xff0000
                        )
                        await interaction.response.edit_message(embed=error_embed, view=None)
                
                @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    cancel_embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Webhook removal was cancelled. No changes were made.",
                        color=0x9b59b6
                    )
                    await interaction.response.edit_message(embed=cancel_embed, view=None)
            
            view = ConfirmWebhookRemoval(self, webhook_name)
            await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in remove_webhook: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while processing your request.\n\n"
                           f"**Error:** {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the Platinum cog."""
    await bot.add_cog(PlatinumCog(bot))
    logger.info("PlatinumCog loaded successfully") 