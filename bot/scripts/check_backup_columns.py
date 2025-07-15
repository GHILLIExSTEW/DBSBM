#!/usr/bin/env python3
"""
Script to check the column structure of the backup file.
"""

import csv
import os

# File paths
BACKUP_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "players.csv.backup.20250715_161359"
)
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "players.csv")


def check_columns():
    """Check column structure of both files"""

    print("🔍 Checking column structure...")
    print("=" * 60)

    # Check backup file
    if os.path.exists(BACKUP_FILE):
        print(f"📁 Backup file: {BACKUP_FILE}")
        try:
            with open(BACKUP_FILE, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                backup_headers = reader.fieldnames
                print(f"📊 Backup file columns ({len(backup_headers)}):")
                for i, header in enumerate(backup_headers, 1):
                    print(f"  {i:2d}. {header}")
        except Exception as e:
            print(f"❌ Error reading backup file: {e}")
    else:
        print(f"❌ Backup file not found: {BACKUP_FILE}")

    print()

    # Check main file
    if os.path.exists(CSV_FILE):
        print(f"📁 Main file: {CSV_FILE}")
        try:
            with open(CSV_FILE, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                main_headers = reader.fieldnames
                print(f"📊 Main file columns ({len(main_headers)}):")
                for i, header in enumerate(main_headers, 1):
                    print(f"  {i:2d}. {header}")
        except Exception as e:
            print(f"❌ Error reading main file: {e}")
    else:
        print(f"❌ Main file not found: {CSV_FILE}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    check_columns()
