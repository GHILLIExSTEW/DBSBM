#!/usr/bin/env python3
"""
Script to rename all directories in betting-bot/static/logos/teams/SOCCER
so that their names match the full league names from LEAGUE_IDS.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.leagues import LEAGUE_IDS


def sanitize_filename(name):
    """Convert a league name to a safe directory name."""
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace(":", "_")
    name = name.replace("*", "_")
    name = name.replace("?", "_")
    name = name.replace('"', "_")
    name = name.replace("<", "_")
    name = name.replace(">", "_")
    name = name.replace("|", "_")
    name = name.replace(" ", "_")
    return name


def rename_soccer_team_dirs():
    """Rename all team directories in SOCCER to match full league names."""
    teams_dir = Path(__file__).parent.parent / "static" / "logos" / "teams" / "SOCCER"
    if not teams_dir.exists():
        print(f"❌ SOCCER teams directory not found: {teams_dir}")
        return
    print(f"📁 Scanning SOCCER teams directory: {teams_dir}")
    total_dirs = 0
    renamed_dirs = 0
    skipped_dirs = 0
    errors = 0
    for league_dir in teams_dir.iterdir():
        if not league_dir.is_dir():
            continue
        league_code = league_dir.name
        league_info = None
        for code, info in LEAGUE_IDS.items():
            if code.upper() == league_code.upper():
                league_info = info
                break
        if not league_info:
            print(f"  ⚠️  No league info found for {league_code}")
            skipped_dirs += 1
            continue
        league_name = league_info.get("name", league_code)
        new_dir_name = sanitize_filename(league_name)
        new_dir_path = league_dir.parent / new_dir_name
        if league_dir.name == new_dir_name:
            print(f"    ✅ Already correctly named: {league_dir.name}")
            continue
        if new_dir_path.exists():
            print(f"    ⚠️  Target directory already exists: {new_dir_name}")
            skipped_dirs += 1
            continue
        try:
            league_dir.rename(new_dir_path)
            print(f"    ✅ Renamed: {league_dir.name} -> {new_dir_name}")
            renamed_dirs += 1
        except Exception as e:
            print(f"    ❌ Error renaming {league_dir.name}: {e}")
            errors += 1
        total_dirs += 1
    print(f"\n📊 Summary:")
    print(f"  Total directories processed: {total_dirs}")
    print(f"  Directories renamed: {renamed_dirs}")
    print(f"  Directories skipped: {skipped_dirs}")
    print(f"  Errors: {errors}")
    if errors == 0:
        print(f"\n✅ SOCCER team directory renaming completed successfully!")
    else:
        print(f"\n⚠️  Completed with {errors} errors.")


def main():
    print("🔄 Starting SOCCER team directory renaming process...")
    try:
        rename_soccer_team_dirs()
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
