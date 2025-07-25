#!/usr/bin/env python3
"""
DBSBM System Cleanup Script
Automates cleanup tasks identified in the comprehensive audit.

This script performs the following cleanup operations:
1. Removes broken files (.broken extensions)
2. Removes empty files
3. Cleans up old backup files
4. Removes small cache files
5. Removes empty directories
6. Consolidates duplicate documentation

Usage:
    python scripts/system_cleanup.py [--dry-run] [--backup-count 3] [--cache-size-limit 1024]
"""

import argparse
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemCleanup:
    def __init__(
        self, dry_run: bool = False, backup_count: int = 3, cache_size_limit: int = 1024
    ):
        self.dry_run = dry_run
        self.backup_count = backup_count
        self.cache_size_limit = cache_size_limit
        self.project_root = Path(__file__).parent.parent
        self.stats = {
            "files_removed": 0,
            "bytes_freed": 0,
            "directories_removed": 0,
            "backups_cleaned": 0,
            "cache_files_removed": 0,
        }

    def log_action(self, action: str, path: str, size: int = 0):
        """Log an action with appropriate prefix for dry run."""
        prefix = "[DRY RUN] " if self.dry_run else ""
        size_str = f" ({size} bytes)" if size > 0 else ""
        logger.info(f"{prefix}{action}: {path}{size_str}")

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file and update statistics."""
        try:
            if file_path.exists():
                size = file_path.stat().st_size
                if not self.dry_run:
                    file_path.unlink()
                self.log_action("Removing file", str(file_path), size)
                self.stats["files_removed"] += 1
                self.stats["bytes_freed"] += size
                return True
        except Exception as e:
            logger.error(f"Error removing {file_path}: {e}")
        return False

    def remove_directory(self, dir_path: Path) -> bool:
        """Remove an empty directory."""
        try:
            if dir_path.exists() and dir_path.is_dir():
                if not self.dry_run:
                    dir_path.rmdir()
                self.log_action("Removing empty directory", str(dir_path))
                self.stats["directories_removed"] += 1
                return True
        except Exception as e:
            logger.error(f"Error removing directory {dir_path}: {e}")
        return False

    def cleanup_broken_files(self) -> int:
        """Remove files with .broken extension."""
        logger.info("🔧 Cleaning up broken files...")
        removed_count = 0

        for broken_file in self.project_root.rglob("*.broken"):
            if self.remove_file(broken_file):
                removed_count += 1

        logger.info(f"✅ Removed {removed_count} broken files")
        return removed_count

    def cleanup_empty_files(self) -> int:
        """Remove completely empty files."""
        logger.info("🧹 Cleaning up empty files...")
        removed_count = 0

        # Common empty files to check
        empty_files = [
            self.project_root / "bot" / "commands" / "add_capper.py",
        ]

        for file_path in empty_files:
            if file_path.exists() and file_path.stat().st_size == 0:
                if self.remove_file(file_path):
                    removed_count += 1

        # Also check for any other empty Python files
        for py_file in self.project_root.rglob("*.py"):
            if py_file.exists() and py_file.stat().st_size == 0:
                if self.remove_file(py_file):
                    removed_count += 1

        logger.info(f"✅ Removed {removed_count} empty files")
        return removed_count

    def cleanup_backup_files(self) -> int:
        """Clean up old backup files, keeping only the most recent ones."""
        logger.info("💾 Cleaning up backup files...")
        removed_count = 0

        backup_dir = self.project_root / "bot" / "data" / "backups"
        if not backup_dir.exists():
            logger.info("No backup directory found")
            return 0

        # Group backup files by base name
        backup_groups = {}
        for backup_file in backup_dir.glob("*.backup.*"):
            base_name = backup_file.stem.split(".backup.")[0]
            if base_name not in backup_groups:
                backup_groups[base_name] = []
            backup_groups[base_name].append(backup_file)

        for base_name, files in backup_groups.items():
            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Keep only the most recent files
            files_to_remove = files[self.backup_count :]

            for file_path in files_to_remove:
                if self.remove_file(file_path):
                    removed_count += 1
                    self.stats["backups_cleaned"] += 1

        logger.info(f"✅ Cleaned up {removed_count} old backup files")
        return removed_count

    def cleanup_cache_files(self) -> int:
        """Remove small cache files."""
        logger.info("🗂️ Cleaning up small cache files...")
        removed_count = 0

        cache_dir = self.project_root / "bot" / "data" / "cache"
        if not cache_dir.exists():
            logger.info("No cache directory found")
            return 0

        for cache_file in cache_dir.glob("*.json"):
            if cache_file.exists():
                size = cache_file.stat().st_size
                if size < self.cache_size_limit:
                    if self.remove_file(cache_file):
                        removed_count += 1
                        self.stats["cache_files_removed"] += 1

        logger.info(f"✅ Removed {removed_count} small cache files")
        return removed_count

    def cleanup_empty_directories(self) -> int:
        """Remove empty directories."""
        logger.info("📁 Cleaning up empty directories...")
        removed_count = 0

        # Specific empty directories to remove
        empty_dirs = [
            self.project_root / "TEMP",
            self.project_root / "PEM",
        ]

        for dir_path in empty_dirs:
            if dir_path.exists() and dir_path.is_dir():
                # Check if directory is empty
                if not any(dir_path.iterdir()):
                    if self.remove_directory(dir_path):
                        removed_count += 1

        logger.info(f"✅ Removed {removed_count} empty directories")
        return removed_count

    def cleanup_duplicate_documentation(self) -> int:
        """Identify duplicate documentation files for manual review."""
        logger.info("📚 Analyzing duplicate documentation...")

        # Look for duplicate strategy documents
        strategy_files = [
            "COMMUNITY_ENGAGEMENT_STRATEGIES.md",
            "COMMUNITY_ENGAGEMENT_STRATEGIES_REVISED.md",
            "COMMUNITY_ENGAGEMENT_STRATEGIES_UPDATED.md",
        ]

        existing_files = []
        for filename in strategy_files:
            file_path = self.project_root / filename
            if file_path.exists():
                existing_files.append(file_path)

        if len(existing_files) > 1:
            logger.warning(f"Found {len(existing_files)} duplicate strategy documents:")
            for file_path in existing_files:
                size = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                logger.warning(
                    f"  - {file_path.name} ({size} bytes, modified {mtime.strftime('%Y-%m-%d %H:%M')})"
                )
            logger.warning("Please manually review and consolidate these files")

        return len(existing_files)

    def cleanup_deprecated_code(self) -> int:
        """Identify deprecated code for manual review."""
        logger.info("🔍 Scanning for deprecated code...")

        deprecated_patterns = ["deprecated", "TODO:", "FIXME:", "XXX:", "HACK:"]

        found_count = 0
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pattern in deprecated_patterns:
                        if pattern in content:
                            logger.warning(f"Found '{pattern}' in {py_file}")
                            found_count += 1
                            break
            except Exception as e:
                logger.error(f"Error reading {py_file}: {e}")

        logger.info(f"Found {found_count} files with deprecated code patterns")
        return found_count

    def print_summary(self):
        """Print cleanup summary."""
        logger.info("\n" + "=" * 50)
        logger.info("🧹 CLEANUP SUMMARY")
        logger.info("=" * 50)

        if self.dry_run:
            logger.info("📋 DRY RUN MODE - No files were actually removed")

        logger.info(f"📁 Files removed: {self.stats['files_removed']}")
        logger.info(f"💾 Bytes freed: {self.stats['bytes_freed']:,}")
        logger.info(f"📂 Directories removed: {self.stats['directories_removed']}")
        logger.info(f"💾 Backup files cleaned: {self.stats['backups_cleaned']}")
        logger.info(f"🗂️ Cache files removed: {self.stats['cache_files_removed']}")

        if self.stats["bytes_freed"] > 0:
            mb_freed = self.stats["bytes_freed"] / (1024 * 1024)
            logger.info(f"💾 Storage freed: {mb_freed:.2f} MB")

        logger.info("=" * 50)

    def run_cleanup(self) -> Dict:
        """Run all cleanup operations."""
        logger.info("🚀 Starting DBSBM System Cleanup")
        logger.info(f"Project root: {self.project_root}")

        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no files will be modified")

        # Run cleanup operations
        self.cleanup_broken_files()
        self.cleanup_empty_files()
        self.cleanup_backup_files()
        self.cleanup_cache_files()
        self.cleanup_empty_directories()
        self.cleanup_duplicate_documentation()
        self.cleanup_deprecated_code()

        # Print summary
        self.print_summary()

        return self.stats


def main():
    parser = argparse.ArgumentParser(description="DBSBM System Cleanup Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually removing files",
    )
    parser.add_argument(
        "--backup-count",
        type=int,
        default=3,
        help="Number of recent backup files to keep (default: 3)",
    )
    parser.add_argument(
        "--cache-size-limit",
        type=int,
        default=1024,
        help="Minimum size in bytes for cache files to keep (default: 1024)",
    )

    args = parser.parse_args()

    # Create cleanup instance
    cleanup = SystemCleanup(
        dry_run=args.dry_run,
        backup_count=args.backup_count,
        cache_size_limit=args.cache_size_limit,
    )

    # Run cleanup
    try:
        stats = cleanup.run_cleanup()

        if not args.dry_run and stats["files_removed"] > 0:
            logger.info("✅ Cleanup completed successfully!")
        elif args.dry_run:
            logger.info("✅ Dry run completed - review the output above")
        else:
            logger.info("✅ No cleanup needed - system is already clean")

    except KeyboardInterrupt:
        logger.info("❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
