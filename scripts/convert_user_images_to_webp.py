#!/usr/bin/env python3
"""
Script to convert existing PNG user images to WEBP format.
This fixes the issue where images were saved as PNG but paths stored with .webp extension.
"""

import os
import logging
from PIL import Image
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_user_images_to_webp():
    """Convert all PNG user images to WEBP format."""
    base_dir = Path("bot/static/guilds")

    if not base_dir.exists():
        logger.info("No guilds directory found, nothing to convert")
        return

    converted_count = 0
    error_count = 0

    # Walk through all guild directories
    for guild_dir in base_dir.iterdir():
        if not guild_dir.is_dir():
            continue

        users_dir = guild_dir / "users"
        if not users_dir.exists():
            continue

        logger.info(f"Processing guild: {guild_dir.name}")

        # Process each user image
        for image_file in users_dir.iterdir():
            if not image_file.is_file():
                continue

            # Check if it's a PNG file
            if image_file.suffix.lower() == '.png':
                try:
                    # Open the PNG image
                    with Image.open(image_file) as img:
                        # Convert to RGBA if needed
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Create the WEBP filename
                        webp_path = image_file.with_suffix('.webp')

                        # Save as WEBP
                        img.save(webp_path, 'WEBP')

                        # Remove the original PNG file
                        image_file.unlink()

                        logger.info(f"Converted: {image_file} -> {webp_path}")
                        converted_count += 1

                except Exception as e:
                    logger.error(f"Error converting {image_file}: {e}")
                    error_count += 1

    logger.info(f"Conversion complete: {converted_count} files converted, {error_count} errors")

def check_database_paths():
    """Check if database paths need updating."""
    import asyncio
    import aiomysql

    async def check_paths():
        try:
            # Connect to database
            pool = await aiomysql.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                db=os.getenv('DB_NAME', 'betting_bot'),
                autocommit=True
            )

            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check for PNG paths in database
                    await cursor.execute(
                        "SELECT guild_id, user_id, image_path FROM cappers WHERE image_path LIKE '%.png'"
                    )
                    png_paths = await cursor.fetchall()

                    if png_paths:
                        logger.info(f"Found {len(png_paths)} PNG paths in database that need updating")
                        for guild_id, user_id, image_path in png_paths:
                            new_path = image_path.replace('.png', '.webp')
                            await cursor.execute(
                                "UPDATE cappers SET image_path = %s WHERE guild_id = %s AND user_id = %s",
                                (new_path, guild_id, user_id)
                            )
                            logger.info(f"Updated database path: {image_path} -> {new_path}")
                    else:
                        logger.info("No PNG paths found in database")

            pool.close()
            await pool.wait_closed()

        except Exception as e:
            logger.error(f"Database error: {e}")

    asyncio.run(check_paths())

if __name__ == "__main__":
    logger.info("Starting user image conversion...")
    convert_user_images_to_webp()
    logger.info("Checking database paths...")
    check_database_paths()
    logger.info("Conversion script completed!")
