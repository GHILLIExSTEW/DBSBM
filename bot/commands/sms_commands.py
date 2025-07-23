"""
SMS Commands for managing phone numbers and sending SMS notifications.
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class SMSCommands(commands.Cog):
    """Commands for SMS functionality."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="add_phone",
        description="📱 Add your phone number for SMS notifications"
    )
    async def add_phone(self, interaction: discord.Interaction, phone_number: str, country_code: str = "+1"):
        """Add your phone number to receive SMS notifications."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Check if SMS service is available
            if not hasattr(self.bot, 'sms_service') or not self.bot.sms_service.twilio_client:
                await interaction.followup.send(
                    "❌ SMS service is not configured. Please contact an administrator.",
                    ephemeral=True
                )
                return
            
            # Add phone number
            success = await self.bot.sms_service.add_user_phone(
                user_id=interaction.user.id,
                phone_number=phone_number,
                country_code=country_code
            )
            
            if success:
                embed = discord.Embed(
                    title="📱 Phone Number Added",
                    description="A verification code has been sent to your phone number.",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📞 Phone Number",
                    value=f"`{country_code}{phone_number}`",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Next Step",
                    value="Use `/verify_phone <code>` to verify your number",
                    inline=True
                )
                
                embed.add_field(
                    name="🔒 Privacy",
                    value="Your phone number is stored securely and only used for notifications",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    "❌ Failed to send verification code. Please check your phone number and try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Add phone command failed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="verify_phone",
        description="✅ Verify your phone number with the code sent via SMS"
    )
    async def verify_phone(self, interaction: discord.Interaction, verification_code: str):
        """Verify your phone number with the 6-digit code."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Verify phone number
            success = await self.bot.sms_service.verify_user_phone(
                user_id=interaction.user.id,
                verification_code=verification_code
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Phone Number Verified",
                    description="Your phone number has been verified successfully!",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📱 Status",
                    value="✅ Ready to receive SMS notifications",
                    inline=True
                )
                
                embed.add_field(
                    name="🔔 Notifications",
                    value="You will now receive text messages for important updates",
                    inline=True
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    "❌ Invalid or expired verification code. Please try again or use `/add_phone` to get a new code.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Verify phone command failed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="my_phone",
        description="📱 Check your phone number status"
    )
    async def my_phone(self, interaction: discord.Interaction):
        """Check your phone number status and settings."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Get phone status
            phone_status = await self.bot.sms_service.get_user_phone_status(interaction.user.id)
            
            if "error" in phone_status:
                await interaction.followup.send(
                    f"❌ Error checking phone status: {phone_status['error']}",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📱 Phone Number Status",
                description="Your phone number information",
                color=0x00ff00 if phone_status["has_phone"] and phone_status["verified"] else 0xffa500
            )
            
            if phone_status["has_phone"]:
                embed.add_field(
                    name="📞 Phone Number",
                    value=f"`{phone_status['phone_number']}`",
                    inline=True
                )
                
                embed.add_field(
                    name="✅ Status",
                    value="✅ Verified" if phone_status["verified"] else "⏳ Pending Verification",
                    inline=True
                )
                
                if phone_status["verified"]:
                    embed.add_field(
                        name="🔔 Notifications",
                        value="✅ SMS notifications enabled",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="🔔 Notifications",
                        value="❌ SMS notifications disabled (not verified)",
                        inline=True
                    )
                
                embed.add_field(
                    name="📅 Added",
                    value=f"<t:{int(phone_status['created_at'].timestamp())}:R>",
                    inline=True
                )
                
                if phone_status["verified"]:
                    embed.add_field(
                        name="📅 Verified",
                        value=f"<t:{int(phone_status['updated_at'].timestamp())}:R>",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="📱 Status",
                    value="❌ No phone number added",
                    inline=False
                )
                
                embed.add_field(
                    name="➕ Add Phone",
                    value="Use `/add_phone <number>` to add your phone number",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"My phone command failed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="send_sms",
        description="📱 Send SMS notification to a user (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def send_sms(
        self,
        interaction: discord.Interaction,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "admin"
    ):
        """Send an SMS notification to a specific user."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Check if SMS service is available
            if not hasattr(self.bot, 'sms_service') or not self.bot.sms_service.twilio_client:
                await interaction.followup.send(
                    "❌ SMS service is not configured.",
                    ephemeral=True
                )
                return
            
            # Parse user ID
            try:
                target_user_id = int(user_id)
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid user ID format.",
                    ephemeral=True
                )
                return
            
            # Check if user has verified phone number
            phone_status = await self.bot.sms_service.get_user_phone_status(target_user_id)
            
            if not phone_status.get("has_phone") or not phone_status.get("verified"):
                await interaction.followup.send(
                    f"❌ User {target_user_id} does not have a verified phone number.",
                    ephemeral=True
                )
                return
            
            # Send SMS
            success = await self.bot.sms_service.send_sms_notification(
                user_id=target_user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority="high"
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ SMS Sent Successfully",
                    description=f"SMS notification sent to user {target_user_id}",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📱 Recipient",
                    value=f"User ID: `{target_user_id}`\nPhone: `{phone_status['phone_number']}`",
                    inline=False
                )
                
                embed.add_field(
                    name="📝 Message",
                    value=f"**Title:** {title}\n**Content:** {message[:100]}{'...' if len(message) > 100 else ''}",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Type",
                    value=notification_type,
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Sent",
                    value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>",
                    inline=True
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"❌ Failed to send SMS to user {target_user_id}. Check logs for details.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Send SMS command failed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="sms_stats",
        description="📊 View SMS statistics (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sms_stats(self, interaction: discord.Interaction, days: int = 7):
        """View SMS statistics for the specified number of days."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Check if SMS service is available
            if not hasattr(self.bot, 'sms_service'):
                await interaction.followup.send(
                    "❌ SMS service is not configured.",
                    ephemeral=True
                )
                return
            
            # Get SMS stats
            stats = await self.bot.sms_service.get_sms_stats(days)
            
            if "error" in stats:
                await interaction.followup.send(
                    f"❌ Error getting SMS stats: {stats['error']}",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📊 SMS Statistics",
                description=f"SMS activity for the last {days} days",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📱 Total SMS",
                value=str(stats["total_sms"]),
                inline=True
            )
            
            embed.add_field(
                name="✅ Successful",
                value=str(stats["successful_sms"]),
                inline=True
            )
            
            embed.add_field(
                name="❌ Failed",
                value=str(stats["failed_sms"]),
                inline=True
            )
            
            # Calculate success rate
            if stats["total_sms"] > 0:
                success_rate = (stats["successful_sms"] / stats["total_sms"]) * 100
                embed.add_field(
                    name="📈 Success Rate",
                    value=f"{success_rate:.1f}%",
                    inline=True
                )
            
            # Show recent SMS
            if stats["recent_sms"]:
                recent_text = ""
                for sms in stats["recent_sms"][:5]:  # Show last 5
                    status_emoji = "✅" if sms["status"] == "sent" else "❌"
                    recent_text += f"{status_emoji} User {sms['user_id']} - {sms['message_type']}\n"
                
                embed.add_field(
                    name="🕒 Recent SMS",
                    value=recent_text or "No recent SMS",
                    inline=False
                )
            
            embed.set_footer(text=f"Stats for last {days} days")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"SMS stats command failed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Setup function for the SMS commands cog."""
    try:
        await bot.add_cog(SMSCommands(bot))
        logger.info("SMSCommands cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load SMSCommands cog: {e}", exc_info=True)
        raise 