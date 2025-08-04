"""
Utility module for converting relative image paths to absolute URLs for Discord webhooks.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def convert_image_path_to_url(image_path: str) -> Optional[str]:
    """
    Convert a relative image path to an absolute URL for Discord webhooks.

    Args:
        image_path: Relative path like '/static/guilds/123/users/456.webp'

    Returns:
        Absolute URL or None if conversion fails
    """
    if not image_path:
        logger.debug("convert_image_path_to_url: Empty image_path provided")
        return None

    logger.debug(f"convert_image_path_to_url: Converting path: {image_path}")

    # If it's already an absolute URL, return as is
    if image_path.startswith(("http://", "https://")):
        logger.debug(f"convert_image_path_to_url: Already absolute URL: {image_path}")
        return image_path

    # If it's a relative path starting with /static/, convert to absolute URL
    if image_path.startswith("/static/"):
        # Get web server URL from environment or use the correct hostname
        web_server_url = os.getenv("WEB_SERVER_URL")

        if not web_server_url:
            # Check if we're running in a containerized environment (production)
            if os.path.exists("/home/container"):
                # We're in production (PebbleHost or similar), use the server's IP/domain
                web_server_url = "http://51.79.105.168:25594"
            else:
                # Local development - use localhost but warn about Discord webhook limitations
                web_server_url = "http://localhost:25594"
                logger.warning(
                    "Using localhost URL - Discord webhooks may not be able to access this. Set WEB_SERVER_URL environment variable for production."
                )

        # Remove leading slash and construct full URL
        relative_path = image_path.lstrip("/")
        full_url = f"{web_server_url}/{relative_path}"
        logger.debug(f"convert_image_path_to_url: Converted to: {full_url}")
        return full_url

    # If it's a relative path without /static/, assume it's relative to static
    if not image_path.startswith("/"):
        web_server_url = os.getenv("WEB_SERVER_URL")

        if not web_server_url:
            # Check if we're running in a containerized environment (production)
            if os.path.exists("/home/container"):
                # We're in production (PebbleHost or similar), use the server's IP/domain
                web_server_url = "http://51.79.105.168:25594"
            else:
                # Local development
                web_server_url = "http://localhost:25594"
                logger.warning(
                    "Using localhost URL - Discord webhooks may not be able to access this. Set WEB_SERVER_URL environment variable for production."
                )

        full_url = f"{web_server_url}/static/{image_path}"
        logger.debug(f"convert_image_path_to_url: Converted to: {full_url}")
        return full_url

    logger.warning(f"convert_image_path_to_url: Could not convert path: {image_path}")
    return None
