import discord
from discord import app_commands, Interaction
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")

TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "0"))


class MaintenanceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager

    @app_commands.command(
        name="down",
        description="Send server maintenance down notification (authorized users only)",
    )
    async def down_command(self, interaction: Interaction):
        """Send server maintenance down notification to all guild command channels"""
        # Check authorization
        if interaction.user.id != AUTHORIZED_USER_ID:
            await interaction.response.send_message(
                "❌ Unauthorized. Only authorized users can use this command.",
                ephemeral=True,
            )
            return

        # Check if command is used in test guild
        if interaction.guild_id != TEST_GUILD_ID:
            await interaction.response.send_message(
                "❌ This command can only be used in the configured test guild.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            # Get all guilds with their command channels
            guilds_query = """
                SELECT guild_id, command_channel_1, command_channel_2, bot_image_mask
                FROM guild_settings
                WHERE is_active = TRUE
            """
            guilds = await self.db_manager.fetch_all(guilds_query)

            sent_count = 0
            failed_count = 0

            for guild_data in guilds:
                guild_id = guild_data["guild_id"]
                command_channels = []
                # Collect command channels (handle both single values and lists)
                for key in ["command_channel_1", "command_channel_2"]:
                    val = guild_data.get(key)
                    if val:
                        if isinstance(val, list):
                            command_channels.extend(val)
                        else:
                            command_channels.append(val)
                if not command_channels:
                    logger.warning(
                        f"No command channels configured for guild {guild_id}"
                    )
                    continue

                # Create embed
                embed = discord.Embed(
                    title="🚨🚨🚨 ATTENTION 🚨🚨🚨",
                    description="The server will be shut down for scheduled maintenance. A status message will be sent when the server is operational again.",
                    color=discord.Color.red(),
                )

                # Set bot image if available
                if guild_data["bot_image_mask"]:
                    embed.set_thumbnail(url=guild_data["bot_image_mask"])

                # Send to each command channel
                for channel_id in command_channels:
                    try:
                        channel = self.bot.get_channel(int(channel_id))
                        if channel:
                            await channel.send(embed=embed)
                            sent_count += 1
                            logger.info(
                                f"Sent down notification to guild {guild_id}, channel {channel_id}"
                            )
                        else:
                            logger.error(
                                f"Could not find channel {channel_id} for guild {guild_id}"
                            )
                            failed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to send down notification to guild {guild_id}, channel {channel_id}: {e}"
                        )
                        failed_count += 1

            await interaction.followup.send(
                f"✅ Maintenance down notification sent to {sent_count} channels.\n"
                f"❌ Failed to send to {failed_count} channels.",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception(f"Error in down command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while sending maintenance notifications.",
                ephemeral=True,
            )

    @app_commands.command(
        name="up",
        description="Send server maintenance up notification (authorized users only)",
    )
    async def up_command(self, interaction: Interaction):
        """Send server maintenance up notification to all guild command channels"""
        # Check authorization
        if interaction.user.id != AUTHORIZED_USER_ID:
            await interaction.response.send_message(
                "❌ Unauthorized. Only authorized users can use this command.",
                ephemeral=True,
            )
            return

        # Check if command is used in test guild
        if interaction.guild_id != TEST_GUILD_ID:
            await interaction.response.send_message(
                "❌ This command can only be used in the configured test guild.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            # Get all guilds with their command channels
            guilds_query = """
                SELECT guild_id, command_channel_1, command_channel_2, bot_image_mask
                FROM guild_settings
                WHERE is_active = TRUE
            """
            guilds = await self.db_manager.fetch_all(guilds_query)

            sent_count = 0
            failed_count = 0

            for guild_data in guilds:
                guild_id = guild_data["guild_id"]
                command_channels = []
                # Collect command channels (handle both single values and lists)
                for key in ["command_channel_1", "command_channel_2"]:
                    val = guild_data.get(key)
                    if val:
                        if isinstance(val, list):
                            command_channels.extend(val)
                        else:
                            command_channels.append(val)
                if not command_channels:
                    logger.warning(
                        f"No command channels configured for guild {guild_id}"
                    )
                    continue

                # Create embed
                embed = discord.Embed(
                    title="🚨🚨🚨 ATTENTION 🚨🚨🚨",
                    description="The server is now up and operational",
                    color=discord.Color.green(),
                )

                # Set bot image if available
                if guild_data["bot_image_mask"]:
                    embed.set_thumbnail(url=guild_data["bot_image_mask"])

                # Send to each command channel
                for channel_id in command_channels:
                    try:
                        channel = self.bot.get_channel(int(channel_id))
                        if channel:
                            await channel.send(embed=embed)
                            sent_count += 1
                            logger.info(
                                f"Sent up notification to guild {guild_id}, channel {channel_id}"
                            )
                        else:
                            logger.error(
                                f"Could not find channel {channel_id} for guild {guild_id}"
                            )
                            failed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to send up notification to guild {guild_id}, channel {channel_id}: {e}"
                        )
                        failed_count += 1

            await interaction.followup.send(
                f"✅ Maintenance up notification sent to {sent_count} channels.\n"
                f"❌ Failed to send to {failed_count} channels.",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception(f"Error in up command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while sending maintenance notifications.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    cog = MaintenanceCog(bot)
    await bot.add_cog(cog)
    logger.info("MaintenanceCog loaded")
