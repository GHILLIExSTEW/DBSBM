#!/usr/bin/env python3
"""
Test Webhook Avatars Script
Tests webhook avatar functionality and helps diagnose user image loading issues.
"""

import asyncio
import logging
import os
import sys
import requests
from pathlib import Path

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


async def test_webhook_avatars():
    """Test webhook avatar functionality."""
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

        # Check current web server URL configuration
        web_server_url = os.getenv("WEB_SERVER_URL")
        if web_server_url:
            logger.info(f"🌐 Web server URL configured: {web_server_url}")
        else:
            logger.warning("⚠️ No WEB_SERVER_URL environment variable set")
            if os.path.exists("/home/container"):
                logger.info("🔍 Detected production environment (/home/container exists)")
                logger.info("💡 Consider setting WEB_SERVER_URL to your public domain")
            else:
                logger.info("🔍 Detected local development environment")
                logger.warning("⚠️ Discord webhooks cannot access localhost URLs")

        for capper in cappers:
            guild_id = capper["guild_id"]
            user_id = capper["user_id"]
            display_name = capper["display_name"]
            image_path = capper["image_path"]

            logger.info(f"🔍 Testing avatar for {display_name} (Guild: {guild_id}, User: {user_id})")
            logger.info(f"   Database path: {image_path}")

            # Convert to URL
            avatar_url = convert_image_path_to_url(image_path)
            if avatar_url:
                logger.info(f"   Converted URL: {avatar_url}")

                # Test if URL is accessible
                try:
                    response = requests.head(avatar_url, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"   ✅ URL accessible (Status: {response.status_code})")
                        logger.info(f"   📏 Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
                        logger.info(f"   📄 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                    else:
                        logger.warning(f"   ⚠️ URL not accessible (Status: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    logger.error(f"   ❌ Error accessing URL: {e}")
            else:
                logger.error(f"   ❌ Failed to convert image path to URL")

            logger.info("")  # Empty line for readability

        # Test Discord webhook avatar requirements
        logger.info("🔧 Discord Webhook Avatar Requirements:")
        logger.info("   - URL must be publicly accessible (not localhost)")
        logger.info("   - URL must return a valid image file")
        logger.info("   - Image format should be PNG, JPG, or WEBP")
        logger.info("   - File size should be under 5MB")
        logger.info("   - URL must use HTTP or HTTPS protocol")

        # Recommendations
        logger.info("💡 Recommendations:")
        if not web_server_url:
            if os.path.exists("/home/container"):
                logger.info("   - Set WEB_SERVER_URL environment variable to your public domain")
                logger.info("   - Example: export WEB_SERVER_URL=https://your-domain.com")
            else:
                logger.info("   - For local testing: Use ngrok to expose your local server")
                logger.info("   - Command: ngrok http 25594")
                logger.info("   - Then set: export WEB_SERVER_URL=https://your-ngrok-url.ngrok.io")
        else:
            logger.info("   - Your web server URL is configured")
            logger.info("   - Test if Discord can access your domain")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_webhook_avatars())
