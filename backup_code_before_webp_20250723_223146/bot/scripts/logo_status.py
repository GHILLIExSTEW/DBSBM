#!/usr/bin/env python3
"""
Logo Status Checker for Golf, Tennis, and F1
Shows the current status of all logo files and directories.
"""

import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def get_logo_status():
    """Get the status of all logo files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logos_dir = os.path.join(base_dir, "static", "logos", "leagues")

    # Define expected structure
    expected_structure = {
        "TENNIS": {
            "ATP": ["atp_tour.webp", "atp.webp"],
            "WTA": ["wta_tour.webp", "wta.webp"],
        },
        "GOLF": {
            "PGA": ["pga_tour.webp", "pga.webp"],
            "LPGA": ["lpga_tour.webp", "lpga.webp"],
            "EUROPEAN_TOUR": ["european_tour.webp"],
            "LIV_GOLF": ["liv_golf.webp"],
            "KORN_FERRY": ["korn_ferry.webp"],
            "CHAMPIONS_TOUR": ["champions_tour.webp"],
            "RYDER_CUP": ["ryder_cup.webp"],
            "PRESIDENTS_CUP": ["presidents_cup.webp"],
            "SOLHEIM_CUP": ["solheim_cup.webp"],
            "OLYMPIC_GOLF": ["olympic_golf.webp"],
        },
        "RACING": {"FORMULA1": ["formula_1.webp", "formula1.webp"]},
    }

    print("🏆 Logo Status Report for Golf, Tennis, and F1")
    print("=" * 60)

    total_expected = 0
    total_found = 0

    for sport, leagues in expected_structure.items():
        print(f"\n🎾 {sport}")
        print("-" * 40)

        for league, expected_files in leagues.items():
            league_dir = os.path.join(logos_dir, sport, league)
            print(f"  {league}:")

            if os.path.exists(league_dir):
                existing_files = [
                    f for f in os.listdir(league_dir) if f.endswith(".webp")
                ]

                for expected_file in expected_files:
                    total_expected += 1
                    file_path = os.path.join(league_dir, expected_file)

                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"    ✅ {expected_file} ({file_size} bytes)")
                        total_found += 1
                    else:
                        print(f"    ❌ {expected_file} (missing)")

                # Show any extra files
                extra_files = [f for f in existing_files if f not in expected_files]
                if extra_files:
                    print(f"    📁 Extra files: {', '.join(extra_files)}")
            else:
                print(f"    ❌ Directory missing")
                total_expected += len(expected_files)

    print("\n" + "=" * 60)
    print(f"📊 Summary: {total_found}/{total_expected} logo files found")

    if total_found == total_expected:
        print("🎉 All expected logos are present!")
        print("✅ Golf, Tennis, and F1 are now working like Darts!")
    else:
        missing = total_expected - total_found
        print(f"⚠️  {missing} logo files are missing")
        print("💡 Run the logo collection scripts to download missing logos")

    return total_found, total_expected


def show_directory_tree():
    """Show the directory tree structure."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logos_dir = os.path.join(base_dir, "static", "logos", "leagues")

    print("\n📁 Directory Tree Structure")
    print("=" * 40)

    def print_tree(path, prefix=""):
        if not os.path.exists(path):
            return

        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "

            if os.path.isdir(item_path):
                print(f"{prefix}{current_prefix}{item}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item_path, new_prefix)
            else:
                size = os.path.getsize(item_path)
                print(f"{prefix}{current_prefix}{item} ({size} bytes)")

    print_tree(logos_dir)


def main():
    """Main function."""
    found, expected = get_logo_status()
    show_directory_tree()

    print(f"\n🎯 Status: {'COMPLETE' if found == expected else 'INCOMPLETE'}")
    return found == expected


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
