#!/usr/bin/env python3
"""
Script to set the main_chat_channel_id for existing guilds by finding their "Main_Chat" channel.
This script will update the guild_settings table to point achievement notifications to the Main_Chat channel.
"""

import asyncio
import logging
import os
import discord
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup (minimal for this script)
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def set_main_chat_channels():
    """Set main_chat_channel_id for all guilds that have a Main_Chat channel."""

    # Database connection setup
    import aiomysql

    try:
        # Connect to database
        pool = await aiomysql.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            db=os.getenv('DB_NAME', 'betting_bot'),
            autocommit=True
        )

        updated_count = 0
        not_found_count = 0

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Get all guilds from guild_settings
                await cursor.execute("SELECT guild_id FROM guild_settings")
                guilds = await cursor.fetchall()

                logger.info(f"Found {len(guilds)} guilds to process")

                for (guild_id,) in guilds:
                    try:
                        # Get the guild from Discord
                        guild = bot.get_guild(guild_id)
                        if not guild:
                            logger.warning(f"Could not find guild {guild_id} in Discord")
                            not_found_count += 1
                            continue

                        # Look for Main_Chat channel
                        main_chat_channel = discord.utils.get(guild.channels, name="Main_Chat")

                        if main_chat_channel:
                            # Update the guild_settings table
                            await cursor.execute(
                                "UPDATE guild_settings SET main_chat_channel_id = %s WHERE guild_id = %s",
                                (main_chat_channel.id, guild_id)
                            )

                            logger.info(f"Updated guild {guild_id} ({guild.name}) to use Main_Chat channel {main_chat_channel.id}")
                            updated_count += 1
                        else:
                            # Try alternative names
                            alternative_names = ["main-chat", "main_chat", "general-chat", "general"]
                            found_channel = None

                            for name in alternative_names:
                                found_channel = discord.utils.get(guild.channels, name=name)
                                if found_channel:
                                    logger.info(f"Found alternative channel '{name}' for guild {guild_id}")
                                    break

                            if found_channel:
                                await cursor.execute(
                                    "UPDATE guild_settings SET main_chat_channel_id = %s WHERE guild_id = %s",
                                    (found_channel.id, guild_id)
                                )
                                logger.info(f"Updated guild {guild_id} ({guild.name}) to use alternative channel {found_channel.name} ({found_channel.id})")
                                updated_count += 1
                            else:
                                logger.warning(f"No Main_Chat or alternative channel found for guild {guild_id} ({guild.name})")
                                not_found_count += 1

                    except Exception as e:
                        logger.error(f"Error processing guild {guild_id}: {e}")
                        not_found_count += 1

        pool.close()
        await pool.wait_closed()

        logger.info(f"Script completed: {updated_count} guilds updated, {not_found_count} guilds not found")

    except Exception as e:
        logger.error(f"Database error: {e}")

@bot.event
async def on_ready():
    """Bot ready event."""
    logger.info(f"Bot logged in as {bot.user}")
    logger.info("Starting main chat channel setup...")

    await set_main_chat_channels()

    logger.info("Main chat channel setup completed. Logging out...")
    await bot.close()

async def main():
    """Main function."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return

    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
