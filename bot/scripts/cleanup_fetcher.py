#!/usr/bin/env python3
"""
Cleanup script for the fetcher process.
Removes stale lock files and checks for orphaned processes.
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime


def cleanup_fetcher():
    """Clean up stale fetcher processes and lock files."""
    lock_file = Path(tempfile.gettempdir()) / "dbsbm_fetcher.lock"

    print("🧹 Cleaning up fetcher processes...")

    if lock_file.exists():
        try:
            # Check if the lock is stale (older than 10 minutes)
            lock_age = datetime.now() - datetime.fromtimestamp(
                lock_file.stat().st_mtime
            )
            if lock_age.total_seconds() > 600:  # 10 minutes
                print(
                    f"🗑️  Removing stale lock file (age: {lock_age.total_seconds()/60:.1f} minutes)"
                )
                lock_file.unlink()
            else:
                print(
                    f"⚠️  Lock file exists and is recent (age: {lock_age.total_seconds()/60:.1f} minutes)"
                )
                print(
                    "   If the fetcher is not running, you can manually delete the lock file."
                )
        except Exception as e:
            print(f"❌ Error checking lock file: {e}")
    else:
        print("✅ No lock file found")

    # Check for Python processes that might be the fetcher
    try:
        import psutil

        fetcher_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] == "python.exe":
                    cmdline = proc.info["cmdline"]
                    if cmdline and any("fetcher" in arg.lower() for arg in cmdline):
                        fetcher_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if fetcher_processes:
            print(f"🔍 Found {len(fetcher_processes)} potential fetcher processes:")
            for proc in fetcher_processes:
                print(f"   PID {proc.pid}: {' '.join(proc.info['cmdline'])}")
        else:
            print("✅ No fetcher processes found")

    except ImportError:
        print("⚠️  psutil not available - cannot check for processes")

    print("✨ Cleanup complete!")


if __name__ == "__main__":
    cleanup_fetcher()
