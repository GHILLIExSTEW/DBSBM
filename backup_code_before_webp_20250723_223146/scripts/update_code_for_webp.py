#!/usr/bin/env python3
"""
DBSBM Update Code for WebP Support Script
Updates the codebase to handle WebP files instead of PNG files.

This script performs the following updates:
1. Updates file extension references from .webp to .webp
2. Updates image loading code to handle WebP format
3. Updates asset loader functions
4. Updates image generation functions
5. Provides backup and rollback capabilities

Usage:
    python scripts/update_code_for_webp.py [--dry-run] [--backup]
"""

import argparse
import logging
import os
import re
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


class WebPCodeUpdater:
    def __init__(self, dry_run: bool = False, create_backup: bool = True):
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.backup_path = None
        self.stats = {
            "files_processed": 0,
            "files_updated": 0,
            "lines_updated": 0,
            "errors": 0,
            "backup_created": False,
        }

        # Patterns to search for and replace
        self.patterns = [
            # File extension patterns
            (
                r"\.png(?=\s*[,\s\)\]\}\n])",
                ".webp",
            ),  # .webp followed by whitespace, comma, or closing brackets
            (r'\.png(?=\s*["\'])', ".webp"),  # .webp followed by quotes
            (r"\.png(?=\s*[;])", ".webp"),  # .webp followed by semicolon
            # Common image loading patterns
            (r'logo_path\s*=\s*(["\'])([^"\']*)\.png\1', r"logo_path = \1\2.webp\1"),
            (r'image_path\s*=\s*(["\'])([^"\']*)\.png\1', r"image_path = \1\2.webp\1"),
            (r'file_path\s*=\s*(["\'])([^"\']*)\.png\1', r"file_path = \1\2.webp\1"),
            # PIL/Pillow image format patterns
            (
                r"Image\.open\([^)]*\.png[^)]*\)",
                lambda m: m.group(0).replace(".webp", ".webp"),
            ),
            (
                r"img\.save\([^)]*\.png[^)]*\)",
                lambda m: m.group(0).replace(".webp", ".webp"),
            ),
            # Discord embed image patterns
            (r'url\s*=\s*(["\'])([^"\']*)\.png\1', r"url = \1\2.webp\1"),
            (r'thumbnail\s*=\s*(["\'])([^"\']*)\.png\1', r"thumbnail = \1\2.webp\1"),
            # File existence checks
            (
                r"os\.path\.exists\([^)]*\.png[^)]*\)",
                lambda m: m.group(0).replace(".webp", ".webp"),
            ),
            (
                r"Path\([^)]*\.png[^)]*\)\.exists\(\)",
                lambda m: m.group(0).replace(".webp", ".webp"),
            ),
        ]

        # Files to skip (don't update these)
        self.skip_files = [
            "scripts/update_code_for_webp.py",
            "scripts/remove_original_images.py",
            "scripts/comprehensive_image_optimizer.py",
            "scripts/image_optimizer.py",
            "scripts/image_diagnostic.py",
            "scripts/monitor_optimization.py",
            "*.pyc",
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
        ]

        # File extensions to process
        self.target_extensions = [
            ".py",
            ".html",
            ".js",
            ".css",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
        ]

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped."""
        file_str = str(file_path)

        for skip_pattern in self.skip_files:
            if skip_pattern in file_str:
                return True

        return False

    def create_backup_directory(self) -> bool:
        """Create a backup directory for original files."""
        if not self.create_backup:
            return True

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = Path(f"backup_code_before_webp_{timestamp}")

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

    def backup_file(self, file_path: Path) -> bool:
        """Backup a file to the backup directory."""
        if not self.create_backup or not self.backup_path:
            return True

        try:
            relative_path = file_path.relative_to(Path.cwd())
            backup_file_path = self.backup_path / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.dry_run:
                shutil.copy2(file_path, backup_file_path)
                logger.debug(f"Backed up: {file_path} -> {backup_file_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            return False

    def update_file_content(self, file_path: Path) -> bool:
        """Update the content of a single file."""
        try:
            # Read the original file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            updated_content = original_content
            lines_updated = 0

            # Apply each pattern
            for pattern, replacement in self.patterns:
                if callable(replacement):
                    # Use the replacement function
                    updated_content, count = re.subn(
                        pattern, replacement, updated_content
                    )
                else:
                    # Use the replacement string
                    updated_content, count = re.subn(
                        pattern, replacement, updated_content
                    )

                lines_updated += count

            # Check if any changes were made
            if updated_content != original_content:
                # Backup the file
                if not self.backup_file(file_path):
                    return False

                # Write the updated content
                if not self.dry_run:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    logger.info(f"Updated: {file_path} ({lines_updated} changes)")
                else:
                    logger.info(f"Would update: {file_path} ({lines_updated} changes)")

                self.stats["files_updated"] += 1
                self.stats["lines_updated"] += lines_updated
                return True

            return True

        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def find_files_to_update(self) -> List[Path]:
        """Find all files that need to be updated."""
        files_to_update = []

        for ext in self.target_extensions:
            for file_path in Path.cwd().rglob(f"*{ext}"):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    files_to_update.append(file_path)

        return files_to_update

    def print_summary(self):
        """Print a summary of the operation."""
        logger.info("=" * 60)
        logger.info("🔄 WEBP CODE UPDATE SUMMARY")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("📋 DRY RUN MODE - No files were actually updated")

        logger.info(f"📁 Files processed: {self.stats['files_processed']}")
        logger.info(f"🔄 Files updated: {self.stats['files_updated']}")
        logger.info(f"📝 Lines updated: {self.stats['lines_updated']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")

        if self.stats["backup_created"] and self.backup_path:
            logger.info(f"💾 Backup created: {self.backup_path}")

        logger.info("=" * 60)

        if not self.dry_run and self.stats["files_updated"] > 0:
            logger.info("✅ WebP code update completed successfully!")
        elif self.dry_run:
            logger.info("📋 Dry run completed - review results above")

    def run_update(self) -> Dict:
        """Run the WebP code update process."""
        logger.info("🔄 Starting WebP code update process...")

        # Create backup directory if needed
        if self.create_backup and not self.create_backup_directory():
            logger.error("Failed to create backup directory. Aborting.")
            return self.stats

        # Find all files to update
        files_to_update = self.find_files_to_update()
        logger.info(f"Found {len(files_to_update)} files to process")

        if not files_to_update:
            logger.info("No files found to update.")
            return self.stats

        # Process each file
        for file_path in files_to_update:
            self.stats["files_processed"] += 1

            if not self.update_file_content(file_path):
                logger.warning(f"Failed to process: {file_path}")

        # Print summary
        self.print_summary()

        return self.stats


def main():
    parser = argparse.ArgumentParser(description="Update codebase to handle WebP files")
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

    args = parser.parse_args()

    # Create updater instance
    updater = WebPCodeUpdater(dry_run=args.dry_run, create_backup=not args.no_backup)

    # Run the update process
    stats = updater.run_update()

    # Exit with error code if there were errors
    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
