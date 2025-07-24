"""
Utility module for converting relative image paths to absolute URLs for Discord webhooks.
"""

import os
from typing import Optional


def convert_image_path_to_url(image_path: str) -> Optional[str]:
    """
    Convert a relative image path to an absolute URL for Discord webhooks.

    Args:
        image_path: Relative path like '/static/guilds/123/users/456.webp'

    Returns:
        Absolute URL or None if conversion fails
    """
    if not image_path:
        return None

    # If it's already an absolute URL, return as is
    if image_path.startswith(("http://", "https://")):
        return image_path

    # If it's a relative path starting with /static/, convert to absolute URL
    if image_path.startswith("/static/"):
        # Get web server URL from environment or use the correct hostname
        web_server_url = os.getenv("WEB_SERVER_URL", "http://51.79.105.168:25594")

        # Remove leading slash and construct full URL
        relative_path = image_path.lstrip("/")
        return f"{web_server_url}/{relative_path}"

    # If it's a relative path without /static/, assume it's relative to static
    if not image_path.startswith("/"):
        web_server_url = os.getenv("WEB_SERVER_URL", "http://51.79.105.168:25594")
        return f"{web_server_url}/static/{image_path}"

    return None
