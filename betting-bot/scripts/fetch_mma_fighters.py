import json
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests

# API Configuration
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
if not API_SPORTS_KEY:
    API_SPORTS_KEY = input("Enter your API-Sports key: ").strip()

# Remove "API_KEY=" prefix if present
if API_SPORTS_KEY.startswith("API_KEY="):
    API_SPORTS_KEY = API_SPORTS_KEY[8:]

# MMA weight categories
MMA_CATEGORIES = [
    "Bantamweight",
    "Catch Weight",
    "Catchweight",
    "Featherweight",
    "Flyweight",
    "Heavyweight",
    "Light Heavyweight",
    "Lightweight",
    "Middleweight",
    "Open Weight",
    "Super Heavyweight",
    "Welterweight",
    "Women's Bantamweight",
    "Women's Catch Weight",
    "Women's Featherweight",
    "Women's Flyweight",
    "Women's Lightweight",
    "Women's Strawweight",
]

# Setup directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static" / "logos" / "players" / "mma"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

headers = {"x-apisports-key": API_SPORTS_KEY}


def sanitize_filename(name):
    """Convert fighter name to safe filename"""
    # Remove or replace problematic characters
    safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
    safe_name = safe_name.replace("*", "_").replace("?", "_").replace('"', "_")
    safe_name = safe_name.replace("<", "_").replace(">", "_").replace("|", "_")
    safe_name = safe_name.replace(" ", "_").strip()
    return safe_name


def download_image(url, filepath):
    """Download image from URL and save to filepath"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"    Failed to download image: {response.status_code}")
            return False
    except Exception as e:
        print(f"    Error downloading image: {e}")
        return False


def fetch_fighters_by_category(category):
    """Fetch fighters for a specific category"""
    print(f"\nFetching fighters for category: {category}")

    url = "https://v1.mma.api-sports.io/fighters"
    params = {"category": category}

    print(f"  URL: {url}")
    print(f"  Params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"  Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"  Error response: {response.text}")
            return []

        data = response.json()
        print(f"  Response keys: {list(data.keys())}")

        fighters = data.get("response", [])
        print(f"  Found {len(fighters)} fighters")

        return fighters

    except Exception as e:
        print(f"  Failed to fetch fighters for {category}: {e}")
        return []


def save_fighter_data(fighters, category):
    """Save fighter data to JSON file"""
    if not fighters:
        return

    # Create category directory
    category_dir = STATIC_DIR / category.replace(" ", "_").replace("'", "_")
    category_dir.mkdir(exist_ok=True)

    # Save fighter data
    safe_category = category.replace(" ", "_").replace("'", "_")
    data_filename = f"mma_{safe_category}_fighters.json"
    data_filepath = BASE_DIR / "data" / data_filename

    with open(data_filepath, "w", encoding="utf-8") as f:
        json.dump(fighters, f, indent=2, ensure_ascii=False)

    print(f"  Saved fighter data to {data_filename}")

    # Download fighter images
    for fighter in fighters:
        fighter_name = fighter.get("name", "Unknown")
        image_url = fighter.get("photo")

        if image_url:
            # Create safe filename
            safe_name = sanitize_filename(fighter_name)
            image_filename = f"{safe_name}.png"
            image_filepath = category_dir / image_filename

            print(f"    Downloading image for {fighter_name}...")
            success = download_image(image_url, image_filepath)
            if success:
                print(f"      Saved image: {image_filename}")
            else:
                print(f"      Failed to save image for {fighter_name}")
        else:
            print(f"    No image URL for {fighter_name}")


def main():
    """Main function to fetch all MMA fighters by category"""
    print("Starting MMA fighter data collection...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Static directory: {STATIC_DIR}")

    all_fighters_data = {}

    for category in MMA_CATEGORIES:
        fighters = fetch_fighters_by_category(category)
        if fighters:
            save_fighter_data(fighters, category)
            all_fighters_data[category] = fighters

        # Rate limiting - wait between requests
        time.sleep(1)

    # Save combined data
    combined_filename = "mma_all_fighters.json"
    combined_filepath = BASE_DIR / "data" / combined_filename

    with open(combined_filepath, "w", encoding="utf-8") as f:
        json.dump(all_fighters_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved combined fighter data to {combined_filename}")

    # Print summary
    total_fighters = sum(len(fighters) for fighters in all_fighters_data.values())
    print(f"\nSummary:")
    print(f"Categories processed: {len(all_fighters_data)}")
    print(f"Total fighters: {total_fighters}")

    for category, fighters in all_fighters_data.items():
        print(f"  {category}: {len(fighters)} fighters")


if __name__ == "__main__":
    main()
