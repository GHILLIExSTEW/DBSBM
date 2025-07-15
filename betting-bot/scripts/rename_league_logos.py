#!/usr/bin/env python3
"""
Script to rename league logo files to match their proper league names.
This script will rename files like 'epl.png' to 'English Premier League.png'
based on the LEAGUE_IDS configuration.
"""

import os
import shutil
import sys
from pathlib import Path

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.leagues import LEAGUE_IDS


def sanitize_filename(name):
    """Convert a league name to a safe filename."""
    # Replace problematic characters
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


def rename_league_logos():
    """Rename all league logo files to match their proper league names."""

    # Base directory for league logos
    base_dir = Path(__file__).parent.parent / "static" / "logos" / "leagues"

    if not base_dir.exists():
        print(f"❌ League logos directory not found: {base_dir}")
        return

    print(f"📁 Scanning league logos directory: {base_dir}")

    # Track statistics
    total_files = 0
    renamed_files = 0
    skipped_files = 0
    errors = 0

    # Process each sport directory
    for sport_dir in base_dir.iterdir():
        if not sport_dir.is_dir():
            continue

        sport_name = sport_dir.name
        print(f"\n🏆 Processing {sport_name} leagues...")

        # Process each league directory within the sport
        for league_dir in sport_dir.iterdir():
            if not league_dir.is_dir():
                continue

            league_code = league_dir.name

            # Find the corresponding league info in LEAGUE_IDS
            league_info = None
            for code, info in LEAGUE_IDS.items():
                if code.upper() == league_code.upper():
                    league_info = info
                    break

            if not league_info:
                print(f"  ⚠️  No league info found for {league_code}")
                continue

            league_name = league_info.get("name", league_code)
            print(f"  📋 {league_code} -> {league_name}")

            # Process files in the league directory
            for file_path in league_dir.iterdir():
                if not file_path.is_file():
                    continue

                total_files += 1
                file_ext = file_path.suffix.lower()

                # Skip non-image files
                if file_ext not in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    print(f"    ⚠️  Skipping non-image file: {file_path.name}")
                    skipped_files += 1
                    continue

                # Create new filename
                new_filename = sanitize_filename(league_name) + file_ext
                new_file_path = league_dir / new_filename

                # Check if file already has the correct name
                if file_path.name == new_filename:
                    print(f"    ✅ Already correctly named: {file_path.name}")
                    continue

                # Check if target file already exists
                if new_file_path.exists():
                    print(f"    ⚠️  Target file already exists: {new_filename}")
                    skipped_files += 1
                    continue

                try:
                    # Rename the file
                    file_path.rename(new_file_path)
                    print(f"    ✅ Renamed: {file_path.name} -> {new_filename}")
                    renamed_files += 1
                except Exception as e:
                    print(f"    ❌ Error renaming {file_path.name}: {e}")
                    errors += 1

    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files renamed: {renamed_files}")
    print(f"  Files skipped: {skipped_files}")
    print(f"  Errors: {errors}")

    if errors == 0:
        print(f"\n✅ League logo renaming completed successfully!")
    else:
        print(f"\n⚠️  Completed with {errors} errors.")


def main():
    """Main function."""
    print("🔄 Starting league logo renaming process...")

    try:
        rename_league_logos()
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
