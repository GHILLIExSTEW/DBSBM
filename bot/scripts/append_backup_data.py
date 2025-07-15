#!/usr/bin/env python3
"""
Script to append backup player data to the main CSV file, skipping duplicates and handling column mismatches.
"""

import csv
import os
from datetime import datetime

# File paths
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "players.csv")
BACKUP_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "players.csv.backup.20250715_161359"
)

# Mapping from backup columns to main columns (if needed)
COLUMN_MAPPING = {
    "player_name": "strPlayer",
    "strCutout": "strCutouts",
    "strEthnicity": "strNationality",
    "league": "strLeague",
    "idPlayer": "strPlayerID",
    "dateBorn": "strBirthDate",
    "idTeam": "strTeamID",
    # Add more mappings if needed
}

# Columns to ignore from backup if not in main
IGNORE_COLUMNS = set(
    [
        "player_name",
        "strCutout",
        "strEthnicity",
        "league",
        "idPlayer",
        "dateBorn",
        "idTeam",
    ]
)


def append_backup_data():
    """Append backup data to main CSV file, skipping duplicates and handling columns."""
    # Check if backup file exists
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file not found: {BACKUP_FILE}")
        return
    # Check if main CSV file exists
    if not os.path.exists(CSV_FILE):
        print(f"❌ Main CSV file not found: {CSV_FILE}")
        return
    print(f"📁 Reading backup file: {BACKUP_FILE}")
    print(f"📁 Reading main file: {CSV_FILE}")
    # Read main file headers
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        main_headers = reader.fieldnames
        main_players = list(reader)
    existing_players = set()
    for row in main_players:
        player_key = f"{row.get('strPlayer', '')}_{row.get('strTeam', '')}_{row.get('strSport', '')}"
        existing_players.add(player_key)
    print(f"📊 Found {len(main_players)} existing players in main file")
    # Read backup file and filter out duplicates, mapping columns
    backup_players = []
    new_players = []
    duplicates = 0
    with open(BACKUP_FILE, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Map backup columns to main columns
            mapped_row = {}
            for key, value in row.items():
                # Map if in mapping, else keep if in main headers
                new_key = COLUMN_MAPPING.get(key, key)
                if new_key in main_headers:
                    mapped_row[new_key] = value
            # Create unique key for deduplication
            player_name = mapped_row.get("strPlayer", row.get("player_name", ""))
            team_name = mapped_row.get("strTeam", row.get("strTeam", ""))
            sport_name = mapped_row.get("strSport", row.get("strSport", ""))
            player_key = f"{player_name}_{team_name}_{sport_name}"
            if player_key not in existing_players:
                new_players.append(mapped_row)
            else:
                duplicates += 1
            backup_players.append(row)
    print(f"📊 Found {len(backup_players)} players in backup file")
    print(f"📊 Found {len(new_players)} new players to add")
    print(f"📊 Skipped {duplicates} duplicate players")
    if not new_players:
        print("✅ No new players to add - all players already exist in main file")
        return
    # Create backup of current main file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_main = f"{CSV_FILE}.backup.{timestamp}"
    os.rename(CSV_FILE, backup_main)
    print(f"📦 Created backup of main file: {backup_main}")
    # Write combined data to main file
    try:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=main_headers)
            writer.writeheader()
            writer.writerows(main_players)
            writer.writerows(new_players)
        print(f"✅ Successfully appended {len(new_players)} new players to {CSV_FILE}")
        print(f"📊 Total players in file: {len(main_players) + len(new_players)}")
    except Exception as e:
        print(f"❌ Error writing combined CSV file: {e}")
        # Restore original file
        if os.path.exists(backup_main):
            try:
                if os.path.exists(CSV_FILE):
                    os.remove(CSV_FILE)
                os.rename(backup_main, CSV_FILE)
                print("🔄 Restored original main file")
            except Exception as restore_error:
                print(f"❌ Error restoring original file: {restore_error}")
        return


if __name__ == "__main__":
    print("🔄 Appending backup player data to main CSV file...")
    print("=" * 60)
    append_backup_data()
    print("=" * 60)
    print("✅ Done!")
