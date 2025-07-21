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
                    value="✅ Webhook Integrations\n"
                          "✅ Real-Time Alerts\n"
                          "✅ Data Export Tools\n"
                          "✅ Advanced Analytics\n"
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
                    value="🔗 Webhook Integrations\n"
                          "📊 Advanced Analytics\n"
                          "📤 Data Export Tools\n"
                          "🔌 Direct API Access\n"
                          "⚡ Real-Time Alerts\n"
                          "🎨 Custom Branding",
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

    @app_commands.command(name="webhook", description="Create a webhook integration (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_webhook(
        self,
        interaction: Interaction,
        webhook_name: str,
        webhook_url: str,
        webhook_type: str
    ):
        """Create a webhook integration for Platinum tier."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            # Validate webhook type
            valid_types = ["bet_created", "bet_resulted", "user_activity", "analytics", "general"]
            if webhook_type not in valid_types:
                await interaction.response.send_message(
                    f"❌ Invalid webhook type. Valid types: {', '.join(valid_types)}", 
                    ephemeral=True
                )
                return
            
            # Create webhook
            success = await self.bot.platinum_service.create_webhook(
                guild_id, webhook_name, webhook_url, webhook_type
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Webhook Created",
                    description=f"Webhook '{webhook_name}' has been created successfully!",
                    color=0x00ff00
                )
                embed.add_field(name="Type", value=webhook_type, inline=True)
                embed.add_field(name="URL", value=f"`{webhook_url[:50]}...`", inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Webhook Creation Failed",
                    description="Failed to create webhook. Please try again.",
                    color=0xff0000
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in create_webhook: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating the webhook.", ephemeral=True
            )

    @app_commands.command(name="export", description="Export server data (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def export_data(
        self,
        interaction: Interaction,
        export_type: str,
        format: str
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
            
            # Create export
            success = await self.bot.platinum_service.create_export(
                guild_id, export_type, format, interaction.user.id
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Export Created",
                    description=f"Data export '{export_type}' in {format.upper()} format is being prepared.",
                    color=0x00ff00
                )
                embed.add_field(name="Type", value=export_type, inline=True)
                embed.add_field(name="Format", value=format.upper(), inline=True)
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


async def setup(bot: commands.Bot):
    """Setup function for the Platinum cog."""
    await bot.add_cog(PlatinumCog(bot))
    logger.info("PlatinumCog loaded successfully") 