#!/usr/bin/env python3
"""
DBSBM Final Cleanup Script
Removes unnecessary files and optimizes the system for production.
"""

import os
import shutil
import time
from pathlib import Path


class SystemCleaner:
    def __init__(self):
        self.removed_files = []
        self.removed_dirs = []
        self.total_size_freed = 0
        self.start_time = time.time()

    def log_removal(self, path, size=0):
        """Log a file/directory removal."""
        self.removed_files.append(path)
        self.total_size_freed += size
        print(f"🗑️ Removed: {path}")

    def cleanup_backup_files(self):
        """Remove old backup files."""
        print("\n📦 Cleaning up backup files...")

        backup_patterns = ["*.backup.*", "*.bak", "*.old", "*.tmp", "*.temp"]

        for root, dirs, files in os.walk("."):
            if "backup" in root.lower():
                continue  # Skip actual backup directories

            for file in files:
                file_path = os.path.join(root, file)

                # Check if file matches backup patterns
                is_backup = any(
                    file.endswith(pattern.replace("*", ""))
                    for pattern in backup_patterns
                )

                # Check for timestamp patterns in filename
                if any(char.isdigit() for char in file.split(".")[-1]):
                    if len(file.split(".")[-1]) >= 8:  # Likely a timestamp
                        is_backup = True

                if is_backup:
                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        self.log_removal(file_path, size)
                    except Exception as e:
                        print(f"⚠️ Could not remove {file_path}: {e}")

    def cleanup_cache_files(self):
        """Remove cache files."""
        print("\n🗂️ Cleaning up cache files...")

        cache_dirs = ["bot/static/cache", "data/cache", "__pycache__", ".pytest_cache"]

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    size = self.get_dir_size(cache_dir)
                    shutil.rmtree(cache_dir)
                    self.log_removal(cache_dir, size)
                except Exception as e:
                    print(f"⚠️ Could not remove {cache_dir}: {e}")

    def cleanup_log_files(self):
        """Remove old log files."""
        print("\n📝 Cleaning up log files...")

        log_patterns = ["*.log", "*.log.*", "debug_*.txt", "error_*.txt"]

        for root, dirs, files in os.walk("."):
            for file in files:
                file_path = os.path.join(root, file)

                # Check if file matches log patterns
                is_log = any(
                    file.endswith(pattern.replace("*", "")) for pattern in log_patterns
                )

                if is_log and "logs" not in root:  # Don't touch logs directory
                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        self.log_removal(file_path, size)
                    except Exception as e:
                        print(f"⚠️ Could not remove {file_path}: {e}")

    def cleanup_duplicate_docs(self):
        """Remove duplicate documentation files."""
        print("\n📚 Cleaning up duplicate documentation...")

        # Remove old audit reports (keep only the latest)
        audit_files = [
            "audit_reports/COMPREHENSIVE_SYSTEM_AUDIT_REPORT.md",
            "audit_reports/CLEANUP_SUMMARY.md",
            "audit_reports/BLACK_FORMATTING_SUMMARY.md",
        ]

        for file_path in audit_files:
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    self.log_removal(file_path, size)
                except Exception as e:
                    print(f"⚠️ Could not remove {file_path}: {e}")

    def cleanup_temp_files(self):
        """Remove temporary files."""
        print("\n📄 Cleaning up temporary files...")

        temp_patterns = ["*.tmp", "*.temp", "*.swp", "*.swo", "~*", ".#*"]

        for root, dirs, files in os.walk("."):
            for file in files:
                file_path = os.path.join(root, file)

                # Check if file matches temp patterns
                is_temp = (
                    any(
                        file.endswith(pattern.replace("*", ""))
                        for pattern in temp_patterns
                    )
                    or file.startswith("~")
                    or file.startswith(".#")
                )

                if is_temp:
                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        self.log_removal(file_path, size)
                    except Exception as e:
                        print(f"⚠️ Could not remove {file_path}: {e}")

    def cleanup_empty_dirs(self):
        """Remove empty directories."""
        print("\n📁 Cleaning up empty directories...")

        for root, dirs, files in os.walk(".", topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)

                # Skip important directories
                if any(
                    skip in dir_path
                    for skip in [
                        ".git",
                        "bot/static/logos",
                        "bot/commands",
                        "bot/services",
                        "bot/utils",
                        "migrations",
                    ]
                ):
                    continue

                try:
                    if not os.listdir(dir_path):  # Directory is empty
                        os.rmdir(dir_path)
                        self.log_removal(dir_path)
                except Exception as e:
                    print(f"⚠️ Could not remove {dir_path}: {e}")

    def cleanup_old_scripts(self):
        """Remove old/obsolete scripts."""
        print("\n🔧 Cleaning up old scripts...")

        obsolete_scripts = [
            "scripts/image_optimizer.py",  # Replaced by comprehensive version
            "scripts/remove_original_images.py",  # No longer needed
            "scripts/update_code_for_webp.py",  # Already executed
            "scripts/monitor_optimization.py",  # No longer needed
            "scripts/image_diagnostic.py",  # No longer needed
            "scripts/comprehensive_image_optimizer.py",  # Already executed
        ]

        for script_path in obsolete_scripts:
            if os.path.exists(script_path):
                try:
                    size = os.path.getsize(script_path)
                    os.remove(script_path)
                    self.log_removal(script_path, size)
                except Exception as e:
                    print(f"⚠️ Could not remove {script_path}: {e}")

    def get_dir_size(self, path):
        """Get total size of a directory."""
        total_size = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except:
                    pass
        return total_size

    def run_cleanup(self):
        """Run all cleanup operations."""
        print("🧹 DBSBM Final Cleanup Script")
        print("=" * 50)

        operations = [
            ("Backup Files", self.cleanup_backup_files),
            ("Cache Files", self.cleanup_cache_files),
            ("Log Files", self.cleanup_log_files),
            ("Duplicate Docs", self.cleanup_duplicate_docs),
            ("Temp Files", self.cleanup_temp_files),
            ("Empty Directories", self.cleanup_empty_dirs),
            ("Old Scripts", self.cleanup_old_scripts),
        ]

        for operation_name, operation_func in operations:
            try:
                operation_func()
            except Exception as e:
                print(f"❌ Error in {operation_name}: {e}")

        # Generate summary
        end_time = time.time()
        duration = end_time - self.start_time

        print("\n" + "=" * 50)
        print("📊 CLEANUP SUMMARY:")
        print(f"🗑️ Files removed: {len(self.removed_files)}")
        print(f"📁 Directories removed: {len(self.removed_dirs)}")
        print(f"💾 Space freed: {self.total_size_freed / (1024*1024):.2f} MB")
        print(f"⏱️ Duration: {duration:.2f} seconds")

        if self.removed_files:
            print("\nRemoved files:")
            for file in self.removed_files[:10]:  # Show first 10
                print(f"  - {file}")
            if len(self.removed_files) > 10:
                print(f"  ... and {len(self.removed_files) - 10} more")

        print("\n✅ Cleanup completed successfully!")


def main():
    """Main cleanup function."""
    cleaner = SystemCleaner()
    cleaner.run_cleanup()


if __name__ == "__main__":
    main()
