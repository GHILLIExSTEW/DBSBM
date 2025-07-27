#!/usr/bin/env python3
"""
Script to test platinum setup by setting a guild to platinum
"""

import asyncio
import sys
import os
sys.path.append('bot')
from bot.data.db_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

async def test_platinum_setup():
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Test guild ID (you can change this to your actual guild ID)
        test_guild_id = 1328116926903353398  # This appears to be one of your guilds

        # Check current subscription level
        result = await db_manager.fetch_one(
            "SELECT subscription_level FROM guild_settings WHERE guild_id = %s",
            test_guild_id
        )

        if result:
            print(f"📋 Current subscription level for guild {test_guild_id}: {result['subscription_level']}")
        else:
            print(f"📋 No guild settings found for guild {test_guild_id}")

        # Set to platinum
        await db_manager.execute(
            """
            INSERT INTO guild_settings (guild_id, subscription_level, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            subscription_level = VALUES(subscription_level),
            updated_at = NOW()
            """,
            test_guild_id,
            "platinum"
        )

        # Verify the change
        result = await db_manager.fetch_one(
            "SELECT subscription_level FROM guild_settings WHERE guild_id = %s",
            test_guild_id
        )

        if result:
            print(f"✅ Updated subscription level for guild {test_guild_id}: {result['subscription_level']}")
        else:
            print(f"❌ Failed to update subscription level for guild {test_guild_id}")

    except Exception as e:
        print(f'❌ Error testing platinum setup: {e}')
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_platinum_setup())
