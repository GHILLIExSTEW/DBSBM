#!/usr/bin/env python3
"""
Simple script to check bot status and command availability
"""

import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BotChecker(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(intents=intents)
    
    async def on_ready(self):
        print(f"✅ Bot is online: {self.user}")
        
        # Check guilds
        guild_ids = [1328116926903353398, 1328126227013439601]
        
        for guild_id in guild_ids:
            guild = self.get_guild(guild_id)
            if guild:
                print(f"✅ Connected to guild: {guild.name} ({guild_id})")
                
                # Check if bot has permissions
                bot_member = guild.get_member(self.user.id)
                if bot_member:
                    permissions = bot_member.guild_permissions
                    if permissions.manage_guild:
                        print(f"✅ Bot has manage guild permissions in {guild.name}")
                    else:
                        print(f"❌ Bot missing manage guild permissions in {guild.name}")
            else:
                print(f"❌ Not connected to guild {guild_id}")
        
        print("\n🎯 Next steps:")
        print("1. Wait 1-2 minutes for commands to sync")
        print("2. Try using a command like /setup in your Discord server")
        print("3. If commands don't appear, check the bot logs for errors")
        
        await self.close()

# Run the checker
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN') or os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ Error: Discord token not found!")
        exit(1)
    
    client = BotChecker()
    client.run(token) 