#!/usr/bin/env python3
"""
Fix User Image Paths Script
Updates database paths for user images from .png to .webp extensions.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fix_user_image_paths():
    """Fix user image paths in the database."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")

        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()
        logger.info("✅ Database manager initialized")

        # Get all capper data with image paths
        cappers = await db_manager.fetch_all(
            "SELECT guild_id, user_id, display_name, image_path FROM cappers WHERE image_path IS NOT NULL"
        )

        logger.info(f"📋 Found {len(cappers)} cappers with image paths")

        fixed_count = 0
        for capper in cappers:
            guild_id = capper["guild_id"]
            user_id = capper["user_id"]
            display_name = capper["display_name"]
            image_path = capper["image_path"]

            logger.info(f"🔍 Checking {display_name} (Guild: {guild_id}, User: {user_id})")
            logger.info(f"   Current path: {image_path}")

            # Check if path ends with .png and needs to be updated to .webp
            if image_path.endswith(".png"):
                new_path = image_path.replace(".png", ".webp")
                logger.info(f"   Updating to: {new_path}")

                # Check if the .webp file actually exists on disk
                if new_path.startswith("/static/"):
                    relative_path = new_path.lstrip("/")
                    file_path = project_root / "bot" / relative_path
                else:
                    file_path = project_root / "bot" / "static" / new_path

                if file_path.exists():
                    # Update the database
                    await db_manager.execute(
                        "UPDATE cappers SET image_path = %s WHERE guild_id = %s AND user_id = %s",
                        (new_path, guild_id, user_id)
                    )
                    logger.info(f"   ✅ Updated database path")
                    fixed_count += 1
                else:
                    logger.warning(f"   ⚠️ .webp file not found on disk: {file_path}")
            else:
                logger.info(f"   ✅ Path already correct")

            logger.info("")  # Empty line for readability

        logger.info(f"🎉 Fixed {fixed_count} user image paths!")
        return True

    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()


async def main():
    """Main function to run the fix."""
    logger.info("🚀 Starting user image path fix...")
    
    success = await fix_user_image_paths()
    
    if success:
        logger.info("✅ Fix completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Fix failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 