#!/usr/bin/env python3
"""
Command sync script that works with the bot's structure
"""

import sys
import os
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))

# Change to bot directory
os.chdir(bot_dir)

import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from bot directory
load_dotenv()

# Bot setup with proper intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is ready: {bot.user}')
    
    # Your guild IDs
    guild_ids = [
        1328116926903353398,  # Your first guild
        1328126227013439601,  # Your second guild
    ]
    
    print("🔄 Starting command sync...")
    
    for guild_id in guild_ids:
        try:
            guild = bot.get_guild(guild_id)
            if guild:
                print(f"📡 Syncing commands to guild: {guild.name} ({guild_id})")
                
                # Copy global commands to guild
                bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
                
                # Sync to this guild
                synced = await bot.tree.sync(guild=discord.Object(id=guild_id))
                
                print(f"✅ Successfully synced {len(synced)} commands to {guild.name}")
            else:
                print(f"❌ Guild {guild_id} not found")
        except Exception as e:
            print(f"❌ Error syncing to guild {guild_id}: {e}")
    
    print("🎉 Command sync complete!")
    print("\n📋 Next steps:")
    print("1. Commands should appear in your Discord servers within 1-2 minutes")
    print("2. Try using a command like /setup to test")
    print("3. If commands don't appear, check bot permissions")
    
    await bot.close()

# Run the sync
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN') or os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ Error: Discord token not found in environment variables!")
        print("Please make sure your bot/.env file contains DISCORD_TOKEN=your_token_here")
        exit(1)
    
    print(f"🔑 Using token: {token[:10]}...")
    bot.run(token) 