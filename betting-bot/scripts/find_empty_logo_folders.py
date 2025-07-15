#!/usr/bin/env python3
"""
Find Empty Logo Folders
Scans static/logos/leagues/ and static/logos/teams/ for empty subfolders.
Outputs a list and a JSON file of empty folders.
"""
import json
import os
from pathlib import Path

LEAGUES_ROOT = Path("static/logos/leagues/")
TEAMS_ROOT = Path("static/logos/teams/")
OUTPUT_FILE = Path("scripts/empty_logo_folders.json")


def find_empty_folders(root):
    empty = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore .gitkeep and hidden files
        files = [f for f in filenames if not f.startswith(".") and f != ".gitkeep"]
        if not files and not dirnames:
            empty.append(os.path.relpath(dirpath, start=root))
    return empty


def main():
    print(f"Scanning for empty folders in {LEAGUES_ROOT} and {TEAMS_ROOT}...")
    empty_leagues = find_empty_folders(LEAGUES_ROOT)
    empty_teams = find_empty_folders(TEAMS_ROOT)

    print("\nEmpty league folders:")
    for folder in empty_leagues:
        print(f"  {LEAGUES_ROOT / folder}")
    print("\nEmpty team folders:")
    for folder in empty_teams:
        print(f"  {TEAMS_ROOT / folder}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(
            {"empty_league_folders": empty_leagues, "empty_team_folders": empty_teams},
            f,
            indent=2,
        )
    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
