#!/usr/bin/env python3
"""
Script to check and recreate the guild_settings table if it's missing
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))


async def fix_guild_settings():
    """Check and recreate guild_settings table if missing"""
    print("Checking guild_settings table...")

    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), 'bot', '.env'))

    try:
        from bot.data.db_manager import DatabaseManager
        print("✓ DatabaseManager imported successfully")

        db_manager = DatabaseManager()
        print("✓ DatabaseManager instance created")

        # Connect to database
        print("Connecting to database...")
        pool = await db_manager.connect()
        print("✓ Connected to database")

        # Check if guild_settings table exists
        print("Checking if guild_settings table exists...")
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES LIKE 'guild_settings'")
                result = await cursor.fetchone()

                if result:
                    print("✓ guild_settings table exists")

                    # Check how many rows it has
                    await cursor.execute("SELECT COUNT(*) as count FROM guild_settings")
                    count_result = await cursor.fetchone()
                    count = count_result[0] if count_result else 0
                    print(f"✓ guild_settings table has {count} rows")

                else:
                    print("❌ guild_settings table does not exist")
                    print("Creating guild_settings table...")

                    # Create the table
                    await cursor.execute("""
                        CREATE TABLE guild_settings (
                            guild_id BIGINT PRIMARY KEY,
                            is_active BOOLEAN DEFAULT TRUE,
                            subscription_level VARCHAR(20) DEFAULT 'free',
                            is_paid BOOLEAN DEFAULT FALSE,
                            embed_channel_1 BIGINT NULL,
                            embed_channel_2 BIGINT NULL,
                            command_channel_1 BIGINT NULL,
                            command_channel_2 BIGINT NULL,
                            admin_channel_1 BIGINT NULL,
                            admin_role BIGINT NULL,
                            authorized_role BIGINT NULL,
                            voice_channel_id BIGINT NULL COMMENT 'Monthly VC',
                            yearly_channel_id BIGINT NULL COMMENT 'Yearly VC',
                            total_units_channel_id BIGINT NULL,
                            daily_report_time TEXT NULL,
                            member_role BIGINT NULL,
                            bot_name_mask TEXT NULL,
                            bot_image_mask TEXT NULL,
                            guild_default_image TEXT NULL,
                            default_parlay_thumbnail TEXT NULL,
                            total_result_value DECIMAL(15, 2) DEFAULT 0.0,
                            min_units DECIMAL(15, 2) DEFAULT 0.1,
                            max_units DECIMAL(15, 2) DEFAULT 10.0,
                            live_game_updates TINYINT(1) DEFAULT 0 COMMENT 'Enable 15s live game updates',
                            main_chat_channel_id BIGINT NULL,
                            units_display_mode VARCHAR(20) DEFAULT 'auto',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)

                    print("✓ guild_settings table created successfully")

        print("Database check completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db_manager' in locals():
            await db_manager.close()

if __name__ == "__main__":
    asyncio.run(fix_guild_settings())
