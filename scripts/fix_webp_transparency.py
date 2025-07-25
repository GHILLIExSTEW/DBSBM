#!/usr/bin/env python3
"""
Script to fix WebP files that lost transparency during conversion.
This script re-converts all WebP files to properly preserve transparency.
"""

import os
import logging
from PIL import Image
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_webp_transparency():
    """Fix all WebP files to properly preserve transparency."""

    # Directories to process
    directories = [
        "bot/static/logos",
        "bot/static/logos/leagues",
        "bot/static/logos/teams",
        "bot/static/logos/players",
        "bot/static/guilds"
    ]

    fixed_count = 0
    error_count = 0

    for base_dir in directories:
        if not os.path.exists(base_dir):
            logger.info(f"Directory not found: {base_dir}")
            continue

        logger.info(f"Processing directory: {base_dir}")

        # Walk through all files recursively
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.webp'):
                    file_path = os.path.join(root, file)
                    try:
                        # Open the WebP file
                        with Image.open(file_path) as img:
                            # Check if it's already RGBA
                            if img.mode == 'RGBA':
                                logger.debug(f"File already RGBA: {file_path}")
                                continue

                            # Convert to RGBA to restore transparency
                            if img.mode in ('RGB', 'P', 'L', 'LA'):
                                # Create a new RGBA image
                                rgba_img = img.convert('RGBA')

                                # Create backup
                                backup_path = file_path + '.backup'
                                shutil.copy2(file_path, backup_path)

                                # Save as RGBA WebP
                                rgba_img.save(file_path, 'WEBP', quality=85)

                                logger.info(f"Fixed transparency: {file_path}")
                                fixed_count += 1
                            else:
                                logger.warning(f"Unknown image mode {img.mode} for {file_path}")

                    except Exception as e:
                        logger.error(f"Error fixing {file_path}: {e}")
                        error_count += 1

    logger.info(f"Transparency fix complete: {fixed_count} files fixed, {error_count} errors")
    return fixed_count, error_count

def check_original_png_files():
    """Check if we have original PNG files to re-convert properly."""

    # Look for backup directories
    backup_dirs = [
        "backup_original_images_20250723_223033",
        "backup_code_before_webp_20250723_223146",
        "backup_code_before_webp_20250723_224742"
    ]

    png_count = 0

    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            logger.info(f"Found backup directory: {backup_dir}")

            # Count PNG files
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.lower().endswith('.png'):
                        png_count += 1

    logger.info(f"Found {png_count} PNG files in backup directories")
    return png_count

def re_convert_from_png_backups():
    """Re-convert PNG files from backups to WebP with proper transparency."""

    backup_dirs = [
        "backup_original_images_20250723_223033",
        "backup_code_before_webp_20250723_223146",
        "backup_code_before_webp_20250723_224742"
    ]

    converted_count = 0
    error_count = 0

    for backup_dir in backup_dirs:
        if not os.path.exists(backup_dir):
            continue

        logger.info(f"Processing backup directory: {backup_dir}")

        # Walk through all PNG files
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                if file.lower().endswith('.png'):
                    png_path = os.path.join(root, file)

                    # Determine the target WebP path
                    relative_path = os.path.relpath(png_path, backup_dir)
                    target_dir = os.path.join("bot/static", os.path.dirname(relative_path))
                    target_file = os.path.splitext(os.path.basename(file))[0] + '.webp'
                    target_path = os.path.join(target_dir, target_file)

                    try:
                        # Create target directory if it doesn't exist
                        os.makedirs(target_dir, exist_ok=True)

                        # Open PNG and convert to RGBA WebP
                        with Image.open(png_path) as img:
                            # Convert to RGBA
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')

                            # Save as WebP with transparency
                            img.save(target_path, 'WEBP', quality=85)

                            logger.info(f"Re-converted: {png_path} -> {target_path}")
                            converted_count += 1

                    except Exception as e:
                        logger.error(f"Error re-converting {png_path}: {e}")
                        error_count += 1

    logger.info(f"Re-conversion complete: {converted_count} files converted, {error_count} errors")
    return converted_count, error_count

def main():
    """Main function to fix WebP transparency issues."""
    logger.info("Starting WebP transparency fix...")

    # Step 1: Check for PNG backups
    png_count = check_original_png_files()

    if png_count > 0:
        logger.info(f"Found {png_count} PNG files in backups. Re-converting with proper transparency...")
        re_convert_from_png_backups()
    else:
        logger.info("No PNG backups found. Attempting to fix existing WebP files...")
        fix_webp_transparency()

    logger.info("WebP transparency fix completed!")

if __name__ == "__main__":
    main()
