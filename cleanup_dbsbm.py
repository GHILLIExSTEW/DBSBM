#!/usr/bin/env python3
"""
DBSBM Cleanup Script
Safely removes unnecessary files and directories to free up space.

This script removes:
- Cache files and directories
- Old log files
- Temporary test files
- Duplicate documentation
- Old backup files
- Empty files

Author: DBSBM Development Team
Date: 2025
"""

import glob
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DBSBMCleanup:
    """Cleanup utility for DBSBM project."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path.cwd()
        self.stats = {
            "files_deleted": 0,
            "directories_deleted": 0,
            "bytes_freed": 0,
            "errors": 0,
        }

        # Files and directories to delete
        self.cache_dirs = ["__pycache__", ".pytest_cache", "htmlcov", ".coverage"]

        self.empty_files = [
            "long_functions_report.txt",
            "ervices and cleanup data files",
        ]

        self.temp_test_files = [
            "test_bot_startup.py",
            "test_redis_timeout.py",
            "debug_env_test.py",
        ]

        self.duplicate_docs = [
            "DBSBM_AUDIT_SUMMARY.md",
            "DBSBM_TASK_LIST.md",
            "DBSBM_TASK_LIST_IMPLEMENTATION.md",
            "BOT_FREEZING_FIXES.md",
            "CRITICAL_TASKS_COMPLETED.md",
            "EXPERIMENTAL_SYSTEMS_IMPLEMENTATION_SUMMARY.md",
        ]

        self.migration_logs = [
            "migration_018_system_integration.log",
            "migration_017_advanced_analytics.log",
            "migration_016_advanced_ai.log",
            "migration_014_compliance_automation.log",
            "migration_013_data_protection.log",
        ]

        # Keep only recent backup files (within 7 days)
        self.backup_retention_days = 7

    def log_action(self, action: str, path: str, size: int = 0):
        """Log cleanup action."""
        if self.dry_run:
            logger.info(f"[DRY RUN] {action}: {path}")
        else:
            logger.info(f"{action}: {path}")
            if size > 0:
                self.stats["bytes_freed"] += size

    def safe_delete_file(self, file_path: Path) -> bool:
        """Safely delete a file."""
        try:
            if not file_path.exists():
                return False

            size = file_path.stat().st_size
            self.log_action("DELETE FILE", str(file_path), size)

            if not self.dry_run:
                file_path.unlink()
                self.stats["files_deleted"] += 1

            return True
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def safe_delete_directory(self, dir_path: Path) -> bool:
        """Safely delete a directory."""
        try:
            if not dir_path.exists():
                return False

            # Calculate directory size
            total_size = 0
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        total_size += file_path.stat().st_size

            self.log_action("DELETE DIRECTORY", str(dir_path), total_size)

            if not self.dry_run:
                shutil.rmtree(dir_path)
                self.stats["directories_deleted"] += 1

            return True
        except Exception as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")
            self.stats["errors"] += 1
            return False

    def cleanup_cache_directories(self):
        """Remove cache directories."""
        logger.info("🧹 Cleaning up cache directories...")

        for cache_dir in self.cache_dirs:
            cache_path = self.project_root / cache_dir
            if cache_path.exists():
                self.safe_delete_directory(cache_path)

    def cleanup_empty_files(self):
        """Remove empty and corrupted files."""
        logger.info("🗑️ Cleaning up empty files...")

        for empty_file in self.empty_files:
            file_path = self.project_root / empty_file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def cleanup_temp_test_files(self):
        """Remove temporary test files."""
        logger.info("🧪 Cleaning up temporary test files...")

        for temp_file in self.temp_test_files:
            file_path = self.project_root / temp_file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def cleanup_duplicate_docs(self):
        """Remove duplicate documentation files."""
        logger.info("📚 Cleaning up duplicate documentation...")

        for doc_file in self.duplicate_docs:
            file_path = self.project_root / doc_file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def cleanup_migration_logs(self):
        """Remove old migration log files."""
        logger.info("📋 Cleaning up migration logs...")

        for log_file in self.migration_logs:
            file_path = self.project_root / log_file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def cleanup_old_logs(self):
        """Remove old log files."""
        logger.info("📝 Cleaning up old log files...")

        log_dirs = ["logs", "db_logs"]
        cutoff_date = datetime.now() - timedelta(days=7)

        for log_dir in log_dirs:
            log_path = self.project_root / log_dir
            if not log_path.exists():
                continue

            for log_file in log_path.glob("*.log"):
                try:
                    # Check if file is older than 7 days
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        self.safe_delete_file(log_file)
                except Exception as e:
                    logger.error(f"Error processing log file {log_file}: {e}")

    def cleanup_old_backups(self):
        """Remove old backup files."""
        logger.info("💾 Cleaning up old backup files...")

        backup_dir = self.project_root / "bot" / "data" / "backups"
        if not backup_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

        for backup_file in backup_dir.glob("*.backup.*"):
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    self.safe_delete_file(backup_file)
            except Exception as e:
                logger.error(f"Error processing backup file {backup_file}: {e}")

    def cleanup_old_cache_files(self):
        """Remove old cache files."""
        logger.info("🗂️ Cleaning up old cache files...")

        cache_dir = self.project_root / "bot" / "data" / "cache"
        if not cache_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=3)

        for cache_file in cache_dir.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_date:
                    self.safe_delete_file(cache_file)
            except Exception as e:
                logger.error(f"Error processing cache file {cache_file}: {e}")

    def cleanup_large_files(self):
        """Remove large unnecessary files."""
        logger.info("📦 Cleaning up large files...")

        # Large files that can be regenerated
        large_files = [
            "bot/data/Schedule.jpg",  # 11MB image
        ]

        for large_file in large_files:
            file_path = self.project_root / large_file
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                logger.info(f"Large file found: {file_path} ({size_mb:.1f}MB)")

                if not self.dry_run:
                    response = input(f"Delete {file_path}? (y/N): ")
                    if response.lower() == "y":
                        self.safe_delete_file(file_path)

    def cleanup_virtual_environment(self):
        """Remove virtual environment (can be recreated)."""
        logger.info("🐍 Checking virtual environment...")

        venv_dir = self.project_root / ".venv310"
        if venv_dir.exists():
            size_mb = sum(
                f.stat().st_size for f in venv_dir.rglob("*") if f.is_file()
            ) / (1024 * 1024)

            logger.info(f"Virtual environment found: {venv_dir} ({size_mb:.1f}MB)")

            if not self.dry_run:
                response = input(f"Delete virtual environment {venv_dir}? (y/N): ")
                if response.lower() == "y":
                    self.safe_delete_directory(venv_dir)

    def print_stats(self):
        """Print cleanup statistics."""
        logger.info("📊 Cleanup Statistics:")
        logger.info(f"  Files deleted: {self.stats['files_deleted']}")
        logger.info(f"  Directories deleted: {self.stats['directories_deleted']}")
        logger.info(f"  Errors encountered: {self.stats['errors']}")

        if self.stats["bytes_freed"] > 0:
            mb_freed = self.stats["bytes_freed"] / (1024 * 1024)
            logger.info(f"  Space freed: {mb_freed:.1f}MB")

    def run_cleanup(self):
        """Run the complete cleanup process."""
        logger.info("🚀 Starting DBSBM cleanup process...")

        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No files will be deleted")

        # Run cleanup tasks
        self.cleanup_cache_directories()
        self.cleanup_empty_files()
        self.cleanup_temp_test_files()
        self.cleanup_duplicate_docs()
        self.cleanup_migration_logs()
        self.cleanup_old_logs()
        self.cleanup_old_backups()
        self.cleanup_old_cache_files()
        self.cleanup_large_files()
        self.cleanup_virtual_environment()

        logger.info("✅ Cleanup process completed!")
        self.print_stats()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="DBSBM Cleanup Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Create cleanup instance
    cleanup = DBSBMCleanup(dry_run=args.dry_run)

    # Run cleanup
    try:
        cleanup.run_cleanup()
    except KeyboardInterrupt:
        logger.info("❌ Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
