import os
import sys
import json
import requests
import time
from PIL import Image
import io

# Add the bot directory to the path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_settings import API_KEY


def download_and_save_logo(url, filepath, delay=1):
    """Download logo from URL and save to filepath"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Validate image
        img = Image.open(io.BytesIO(response.content))
        img.verify()

        # Save image
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"✓ Downloaded: {os.path.basename(filepath)}")
        time.sleep(delay)
        return True

    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False


def clean_league_name(name):
    """Clean league name for directory/filename use"""
    # Replace spaces and special characters with hyphens
    cleaned = name.replace(" ", "-").replace("/", "-").replace("\\", "-")
    # Remove any other special characters and make lowercase
    cleaned = "".join(c for c in cleaned if c.isalnum() or c == "-")
    return cleaned.lower()


def main():
    # API endpoint
    url = "https://v3.football.api-sports.io/leagues?search=brazil"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_KEY,
    }

    print("Fetching Brazil leagues from API...")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "response" not in data:
            print("No response data found")
            return

        leagues = data["response"]
        print(f"Found {len(leagues)} Brazil leagues")
        print()

        successful_downloads = 0

        for league in leagues:
            league_info = league.get("league", {})
            country_info = league.get("country", {})

            league_name = league_info.get("name", "Unknown")
            league_logo = league_info.get("logo")
            country_name = country_info.get("name", "Unknown")

            print(f"Processing: {league_name} ({country_name})")

            if not league_logo:
                print(f"  ✗ No logo URL found for {league_name}")
                continue

            # Create clean directory name
            clean_name = clean_league_name(league_name)
            league_dir = f"static/logos/leagues/SOCCER/{clean_name}"
            os.makedirs(league_dir, exist_ok=True)

            # Save league logo
            logo_filename = "league_logo.png"
            logo_path = os.path.join(league_dir, logo_filename)

            if download_and_save_logo(league_logo, logo_path):
                successful_downloads += 1
                print(f"  ✓ Saved to: {league_dir}")
            else:
                print(f"  ✗ Failed to download logo")

            print()

        print(f"Download complete!")
        print(
            f"Successfully downloaded: {successful_downloads}/{len(leagues)} league logos"
        )

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
