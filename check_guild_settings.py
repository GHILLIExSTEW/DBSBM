#!/usr/bin/env python3
"""
Script to check guild_settings table structure
"""

import asyncio
import sys
import os
sys.path.append('bot')
from bot.data.db_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

async def check_guild_settings():
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Check if guild_settings table exists
        result = await db_manager.fetch_all('SHOW TABLES LIKE "guild_settings"')
        if not result:
            print('❌ guild_settings table does not exist!')
            return

        # Get table structure
        columns = await db_manager.fetch_all('DESCRIBE guild_settings')
        print('📋 Guild settings table columns:')
        for column in columns:
            print(f"  - {column['Field']}: {column['Type']} {column['Null']} {column['Key']} {column['Default']}")

        # Check if subscription_level column exists
        has_subscription = any(col['Field'] == 'subscription_level' for col in columns)
        if has_subscription:
            print('✅ subscription_level column exists')
        else:
            print('❌ subscription_level column missing')

    except Exception as e:
        print(f'❌ Error checking guild_settings: {e}')
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_guild_settings())
