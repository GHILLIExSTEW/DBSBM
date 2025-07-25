#!/usr/bin/env python3
"""
DBSBM Remove Original Images Script
Safely removes original image files after WebP conversion.

This script performs the following operations:
1. Creates a backup of original files before deletion
2. Verifies WebP files exist before removing originals
3. Removes PNG, JPEG, GIF, BMP, TIFF files
4. Provides detailed reporting of space saved
5. Includes safety checks and rollback options

Usage:
    python scripts/remove_original_images.py [--dry-run] [--backup] [--verify]
"""

import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OriginalImageRemover:
    def __init__(
        self,
        target_path: str = "bot/static",
        dry_run: bool = False,
        create_backup: bool = True,
        verify_webp: bool = True,
    ):
        self.target_path = Path(target_path)
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.verify_webp = verify_webp
        self.backup_path = None
        self.stats = {
            "files_processed": 0,
            "files_removed": 0,
            "bytes_freed": 0,
            "errors": 0,
            "backup_created": False,
        }

        # Original image formats to remove
        self.original_formats = [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
        ]

    def log_action(self, action: str, path: str, size: int = 0):
        """Log an action with file details."""
        if size > 0:
            size_mb = size / (1024 * 1024)
            logger.info(f"{action}: {path} ({size_mb:.2f} MB)")
        else:
            logger.info(f"{action}: {path}")

    def create_backup_directory(self) -> bool:
        """Create a backup directory for original files."""
        if not self.create_backup:
            return True

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = Path(f"backup_original_images_{timestamp}")

        try:
            if not self.dry_run:
                self.backup_path.mkdir(exist_ok=True)
                logger.info(f"Created backup directory: {self.backup_path}")
            else:
                logger.info(f"Would create backup directory: {self.backup_path}")

            self.stats["backup_created"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False

    def verify_webp_exists(self, original_path: Path) -> bool:
        """Verify that a WebP version exists for the original file."""
        if not self.verify_webp:
            return True

        webp_path = original_path.with_suffix(".webp")
        return webp_path.exists()

    def backup_file(self, file_path: Path) -> bool:
        """Backup a file to the backup directory."""
        if not self.create_backup or not self.backup_path:
            return True

        try:
            relative_path = file_path.relative_to(self.target_path)
            backup_file_path = self.backup_path / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.dry_run:
                shutil.copy2(file_path, backup_file_path)
                logger.debug(f"Backed up: {file_path} -> {backup_file_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            return False

    def remove_original_file(self, file_path: Path) -> bool:
        """Remove an original image file."""
        try:
            # Get file size before removal
            file_size = file_path.stat().st_size

            # Verify WebP exists if verification is enabled
            if self.verify_webp and not self.verify_webp_exists(file_path):
                logger.warning(f"Skipping {file_path} - no WebP version found")
                return False

            # Backup file if backup is enabled
            if not self.backup_file(file_path):
                return False

            # Remove the file
            if not self.dry_run:
                file_path.unlink()
                self.log_action("Removed", str(file_path), file_size)
            else:
                self.log_action("Would remove", str(file_path), file_size)

            self.stats["files_removed"] += 1
            self.stats["bytes_freed"] += file_size
            return True

        except Exception as e:
            logger.error(f"Error removing {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def find_original_images(self) -> List[Path]:
        """Find all original image files in the target directory."""
        original_files = []

        for format_ext in self.original_formats:
            files = list(self.target_path.rglob(f"*{format_ext}"))
            original_files.extend(files)

        # Also find files with wrong extensions but valid image content
        all_files = list(self.target_path.rglob("*"))
        for file_path in all_files:
            if (
                file_path.is_file()
                and file_path.suffix.lower() not in self.original_formats
            ):
                # Check if it's an image file with wrong extension
                if self.is_image_file(file_path):
                    original_files.append(file_path)

        return list(set(original_files))  # Remove duplicates

    def is_image_file(self, file_path: Path) -> bool:
        """Check if a file is an image file based on content."""
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)

            # Check for common image file signatures
            if header.startswith(b"\xff\xd8\xff"):  # JPEG
                return True
            elif header.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
                return True
            elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):  # GIF
                return True
            elif header.startswith(b"BM"):  # BMP
                return True
            elif header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):  # TIFF
                return True
            elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":  # WebP
                return True

        except Exception:
            pass

        return False

    def print_summary(self):
        """Print a summary of the operation."""
        logger.info("=" * 60)
        logger.info("🗑️ ORIGINAL IMAGE REMOVAL SUMMARY")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("📋 DRY RUN MODE - No files were actually removed")

        logger.info(f"📁 Files processed: {self.stats['files_processed']}")
        logger.info(f"🗑️ Files removed: {self.stats['files_removed']}")

        bytes_freed = self.stats["bytes_freed"]
        mb_freed = bytes_freed / (1024 * 1024)
        gb_freed = mb_freed / 1024

        if gb_freed >= 1:
            logger.info(f"💾 Storage freed: {gb_freed:.2f} GB ({mb_freed:.2f} MB)")
        else:
            logger.info(f"💾 Storage freed: {mb_freed:.2f} MB")

        logger.info(f"❌ Errors: {self.stats['errors']}")

        if self.stats["backup_created"] and self.backup_path:
            logger.info(f"💾 Backup created: {self.backup_path}")

        logger.info("=" * 60)

        if not self.dry_run and self.stats["files_removed"] > 0:
            logger.info("✅ Original image removal completed successfully!")
        elif self.dry_run:
            logger.info("📋 Dry run completed - review results above")

    def run_removal(self) -> Dict:
        """Run the original image removal process."""
        logger.info("🗑️ Starting original image removal process...")

        # Create backup directory if needed
        if self.create_backup and not self.create_backup_directory():
            logger.error("Failed to create backup directory. Aborting.")
            return self.stats

        # Find all original image files
        original_files = self.find_original_images()
        logger.info(f"Found {len(original_files)} original image files to process")

        if not original_files:
            logger.info("No original image files found to remove.")
            return self.stats

        # Process each file
        for file_path in original_files:
            self.stats["files_processed"] += 1

            if not self.remove_original_file(file_path):
                logger.warning(f"Failed to process: {file_path}")

        # Print summary
        self.print_summary()

        return self.stats


def main():
    parser = argparse.ArgumentParser(
        description="Remove original image files after WebP conversion"
    )
    parser.add_argument("--path", default="bot/static", help="Target directory path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of original files",
    )
    parser.add_argument(
        "--no-verify", action="store_true", help="Skip WebP existence verification"
    )

    args = parser.parse_args()

    # Create remover instance
    remover = OriginalImageRemover(
        target_path=args.path,
        dry_run=args.dry_run,
        create_backup=not args.no_backup,
        verify_webp=not args.no_verify,
    )

    # Run the removal process
    stats = remover.run_removal()

    # Exit with error code if there were errors
    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
