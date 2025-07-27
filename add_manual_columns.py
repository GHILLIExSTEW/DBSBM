#!/usr/bin/env python3
"""
Script to add manual bet columns to the bets table
"""

import asyncio
import os
import sys

sys.path.append("bot")
from dotenv import load_dotenv

from bot.data.db_manager import DatabaseManager

load_dotenv()


async def add_manual_columns():
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Add is_manual column
        await db_manager.execute(
            """
            ALTER TABLE bets ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE
            COMMENT 'Whether this bet was entered manually'
        """
        )

        # Add home_team and away_team columns
        await db_manager.execute(
            """
            ALTER TABLE bets ADD COLUMN IF NOT EXISTS home_team VARCHAR(150) DEFAULT NULL
            COMMENT 'Home team name for manual bets'
        """
        )

        await db_manager.execute(
            """
            ALTER TABLE bets ADD COLUMN IF NOT EXISTS away_team VARCHAR(150) DEFAULT NULL
            COMMENT 'Away team name for manual bets'
        """
        )

        # Add bet_selection column
        await db_manager.execute(
            """
            ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_selection VARCHAR(255) DEFAULT NULL
            COMMENT 'Bet selection for manual bets'
        """
        )

        # Add bet_amount column
        await db_manager.execute(
            """
            ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_amount DECIMAL(10,2) DEFAULT NULL
            COMMENT 'Bet amount for manual bets'
        """
        )

        print("✅ Manual bet columns added successfully!")

    except Exception as e:
        print(f"❌ Error adding manual columns: {e}")
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(add_manual_columns())
