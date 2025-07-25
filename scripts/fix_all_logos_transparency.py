#!/usr/bin/env python3
"""
Comprehensive script to fix all logo transparency issues.
This script will re-convert all logos from PNG backups to WebP with proper transparency.
"""

import os
import logging
from PIL import Image
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_png_backups():
    """Find all PNG files in backup directories."""
    backup_dirs = [
        "backup_original_images_20250723_223033",
        "backup_code_before_webp_20250723_223146",
        "backup_code_before_webp_20250723_224742"
    ]

    png_files = []

    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            logger.info(f"Scanning backup directory: {backup_dir}")

            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.lower().endswith('.png'):
                        png_path = os.path.join(root, file)
                        png_files.append((backup_dir, png_path))

    logger.info(f"Found {len(png_files)} PNG files in backup directories")
    return png_files

def convert_png_to_webp_with_transparency(png_path, target_path):
    """Convert PNG to WebP while preserving transparency."""
    try:
        with Image.open(png_path) as img:
            # Convert to RGBA to preserve transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Save as WebP with transparency
            img.save(target_path, 'WEBP', quality=85)

            logger.info(f"Converted: {png_path} -> {target_path}")
            return True

    except Exception as e:
        logger.error(f"Error converting {png_path}: {e}")
        return False

def fix_all_logos():
    """Fix all logo transparency issues."""

    # Step 1: Find all PNG backups
    png_files = find_png_backups()

    if not png_files:
        logger.warning("No PNG backup files found!")
        return False

    converted_count = 0
    error_count = 0

    # Step 2: Convert each PNG to WebP with proper transparency
    for backup_dir, png_path in png_files:
        try:
            # Determine the target WebP path
            relative_path = os.path.relpath(png_path, backup_dir)

            # Map backup paths to current structure
            if relative_path.startswith('logos/'):
                # Direct logos mapping
                target_path = os.path.join("bot/static", relative_path.replace('.png', '.webp'))
            elif relative_path.startswith('guilds/'):
                # Guild images mapping
                target_path = os.path.join("bot/static", relative_path.replace('.png', '.webp'))
            else:
                # Other files
                target_path = os.path.join("bot/static", relative_path.replace('.png', '.webp'))

            # Convert the file
            if convert_png_to_webp_with_transparency(png_path, target_path):
                converted_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Error processing {png_path}: {e}")
            error_count += 1

    logger.info(f"Logo conversion complete: {converted_count} files converted, {error_count} errors")
    return converted_count > 0

def fix_existing_webp_files():
    """Fix existing WebP files that lost transparency."""

    directories = [
        "bot/static/logos",
        "bot/static/guilds"
    ]

    fixed_count = 0
    error_count = 0

    for base_dir in directories:
        if not os.path.exists(base_dir):
            continue

        logger.info(f"Fixing existing WebP files in: {base_dir}")

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.webp'):
                    file_path = os.path.join(root, file)
                    try:
                        with Image.open(file_path) as img:
                            # Check if it needs transparency fix
                            if img.mode != 'RGBA':
                                # Create backup
                                backup_path = file_path + '.backup'
                                shutil.copy2(file_path, backup_path)

                                # Convert to RGBA
                                rgba_img = img.convert('RGBA')
                                rgba_img.save(file_path, 'WEBP', quality=85)

                                logger.info(f"Fixed transparency: {file_path}")
                                fixed_count += 1

                    except Exception as e:
                        logger.error(f"Error fixing {file_path}: {e}")
                        error_count += 1

    logger.info(f"Existing WebP fix complete: {fixed_count} files fixed, {error_count} errors")
    return fixed_count, error_count

def verify_transparency():
    """Verify that WebP files have proper transparency."""

    directories = [
        "bot/static/logos",
        "bot/static/guilds"
    ]

    rgba_count = 0
    non_rgba_count = 0

    for base_dir in directories:
        if not os.path.exists(base_dir):
            continue

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.webp'):
                    file_path = os.path.join(root, file)
                    try:
                        with Image.open(file_path) as img:
                            if img.mode == 'RGBA':
                                rgba_count += 1
                            else:
                                non_rgba_count += 1
                                logger.warning(f"Non-RGBA WebP file: {file_path} (mode: {img.mode})")

                    except Exception as e:
                        logger.error(f"Error checking {file_path}: {e}")

    logger.info(f"Transparency verification: {rgba_count} RGBA files, {non_rgba_count} non-RGBA files")
    return rgba_count, non_rgba_count

def main():
    """Main function to fix all logo transparency issues."""
    logger.info("🚀 Starting comprehensive logo transparency fix...")

    # Step 1: Try to re-convert from PNG backups
    logger.info("📁 Step 1: Re-converting from PNG backups...")
    success = fix_all_logos()

    if not success:
        logger.warning("⚠️ No PNG backups found or conversion failed!")

        # Step 2: Fix existing WebP files
        logger.info("🔧 Step 2: Fixing existing WebP files...")
        fix_existing_webp_files()

    # Step 3: Verify transparency
    logger.info("✅ Step 3: Verifying transparency...")
    rgba_count, non_rgba_count = verify_transparency()

    if non_rgba_count == 0:
        logger.info("🎉 SUCCESS: All WebP files now have proper transparency!")
    else:
        logger.warning(f"⚠️ WARNING: {non_rgba_count} files still don't have transparency")

    logger.info("🏁 Logo transparency fix completed!")

if __name__ == "__main__":
    main()
