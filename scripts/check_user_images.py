#!/usr/bin/env python3
"""
Check User Images Script
Verifies that user images are in the correct format and accessible via web server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from PIL import Image
import requests

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment
from bot.utils.image_url_converter import convert_image_path_to_url

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_user_images():
    """Check all user images and verify they're accessible."""
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

        for capper in cappers:
            guild_id = capper["guild_id"]
            user_id = capper["user_id"]
            display_name = capper["display_name"]
            image_path = capper["image_path"]

            logger.info(f"🔍 Checking image for {display_name} (Guild: {guild_id}, User: {user_id})")
            logger.info(f"   Database path: {image_path}")

            # Check if file exists on disk
            if image_path.startswith("/static/"):
                relative_path = image_path.lstrip("/")
                file_path = project_root / "bot" / relative_path
            else:
                file_path = project_root / "bot" / "static" / image_path

            if file_path.exists():
                logger.info(f"   ✅ File exists on disk: {file_path}")
                
                # Check file format
                try:
                    with Image.open(file_path) as img:
                        logger.info(f"   📷 Image format: {img.format}, Size: {img.size}")
                        
                        # Convert to WEBP if not already
                        if img.format != "WEBP":
                            logger.info(f"   🔄 Converting {img.format} to WEBP...")
                            webp_path = file_path.with_suffix(".webp")
                            img.save(webp_path, "WEBP")
                            
                            # Update database path
                            new_path = f"/static/guilds/{guild_id}/users/{user_id}.webp"
                            await db_manager.execute(
                                "UPDATE cappers SET image_path = %s WHERE guild_id = %s AND user_id = %s",
                                (new_path, guild_id, user_id)
                            )
                            logger.info(f"   ✅ Converted and updated database path to: {new_path}")
                            
                            # Remove old file
                            file_path.unlink()
                            logger.info(f"   🗑️ Removed old {img.format} file")
                        else:
                            logger.info(f"   ✅ Already in WEBP format")
                            
                except Exception as e:
                    logger.error(f"   ❌ Error processing image: {e}")
            else:
                logger.warning(f"   ⚠️ File not found on disk: {file_path}")

            # Test web server accessibility
            web_url = convert_image_path_to_url(image_path)
            if web_url:
                logger.info(f"   🌐 Web URL: {web_url}")
                try:
                    response = requests.head(web_url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"   ✅ Web server accessible")
                    else:
                        logger.warning(f"   ⚠️ Web server returned status {response.status_code}")
                except Exception as e:
                    logger.error(f"   ❌ Web server error: {e}")
            else:
                logger.error(f"   ❌ Could not convert to web URL")

            logger.info("")  # Empty line for readability

        logger.info("🎉 User image check completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Check failed: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()


async def main():
    """Main function to run the check."""
    logger.info("🚀 Starting user image check...")
    
    success = await check_user_images()
    
    if success:
        logger.info("✅ Check completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Check failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 