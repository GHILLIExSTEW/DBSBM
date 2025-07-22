#!/usr/bin/env python3
"""
Quick fix script to restore commands after sync issue
"""

import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready: {bot.user}')
    
    # Get your guild IDs from environment or hardcode them
    guild_ids = [
        1328116926903353398,  # Your first guild
        1328126227013439601,  # Your second guild
        # Add more guild IDs as needed
    ]
    
    print("Starting command sync...")
    
    for guild_id in guild_ids:
        try:
            guild = bot.get_guild(guild_id)
            if guild:
                print(f"Syncing commands to guild: {guild.name} ({guild_id})")
                
                # Sync all commands to this guild
                bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
                await bot.tree.sync(guild=discord.Object(id=guild_id))
                
                print(f"✅ Successfully synced commands to {guild.name}")
            else:
                print(f"❌ Guild {guild_id} not found")
        except Exception as e:
            print(f"❌ Error syncing to guild {guild_id}: {e}")
    
    print("Command sync complete!")
    await bot.close()

# Run the bot
if __name__ == "__main__":
    # Try different possible token environment variable names
    token = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN') or os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ Error: Discord token not found in environment variables!")
        print("Please make sure your .env file contains DISCORD_TOKEN=your_token_here")
        exit(1)
    
    print(f"Using token: {token[:10]}...")
    bot.run(token) 