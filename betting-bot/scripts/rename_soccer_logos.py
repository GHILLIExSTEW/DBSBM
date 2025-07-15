#!/usr/bin/env python3
"""
Script to rename all files named "logo.png" in the SOCCER leagues folder
to match their parent directory name.
"""

import sys
from pathlib import Path


def sanitize_filename(name):
    """Convert a directory name to a safe filename."""
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


def rename_soccer_logos():
    """Rename all logo.png files in SOCCER leagues to match their parent directory name."""

    # Base directory for SOCCER league logos
    soccer_dir = (
        Path(__file__).parent.parent / "static" / "logos" / "leagues" / "SOCCER"
    )

    if not soccer_dir.exists():
        print(f"❌ SOCCER leagues directory not found: {soccer_dir}")
        return

    print(f"📁 Scanning SOCCER leagues directory: {soccer_dir}")

    # Track statistics
    total_files = 0
    renamed_files = 0
    skipped_files = 0
    errors = 0

    # Process each league directory
    for league_dir in soccer_dir.iterdir():
        if not league_dir.is_dir():
            continue

        league_name = league_dir.name
        print(f"\n🏆 Processing {league_name}...")

        # Look for logo.png files in this directory
        logo_file = league_dir / "logo.png"

        if not logo_file.exists():
            print(f"  ⚠️  No logo.png found in {league_name}")
            continue

        total_files += 1

        # Create new filename based on parent directory name
        new_filename = sanitize_filename(league_name) + ".png"
        new_file_path = league_dir / new_filename

        # Check if file already has the correct name
        if logo_file.name == new_filename:
            print(f"    ✅ Already correctly named: {logo_file.name}")
            continue

        # Check if target file already exists
        if new_file_path.exists():
            print(f"    ⚠️  Target file already exists: {new_filename}")
            skipped_files += 1
            continue

        try:
            # Rename the file
            logo_file.rename(new_file_path)
            print(f"    ✅ Renamed: logo.png -> {new_filename}")
            renamed_files += 1
        except Exception as e:
            print(f"    ❌ Error renaming logo.png in {league_name}: {e}")
            errors += 1

    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total logo.png files found: {total_files}")
    print(f"  Files renamed: {renamed_files}")
    print(f"  Files skipped: {skipped_files}")
    print(f"  Errors: {errors}")

    if errors == 0:
        print(f"\n✅ SOCCER logo renaming completed successfully!")
    else:
        print(f"\n⚠️  Completed with {errors} errors.")


def main():
    """Main function."""
    print("🔄 Starting SOCCER logo renaming process...")

    try:
        rename_soccer_logos()
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
