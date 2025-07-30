import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# --- Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    pass
except ImportError as e:
    print(
        f"CRITICAL ERROR: Could not import LEAGUE_IDS: {e}. "
        f"Ensure config/leagues.py exists in {BASE_DIR}/config/.",
        file=sys.stderr,
    )
    sys.exit(1)

# Corrected LEAGUE_IDS to override config.leagues
CORRECTED_LEAGUE_IDS = {
    "NFL": {"id": "1", "sport": "american-football", "name": "NFL"},
    "EPL": {"id": "39", "sport": "football", "name": "English Premier League"},
    "NBA": {"id": "12", "sport": "basketball", "name": "NBA"},
    "MLB": {"id": "1", "sport": "baseball", "name": "MLB"},
    "NHL": {"id": "57", "sport": "hockey", "name": "NHL"},
    "LaLiga": {"id": "140", "sport": "football", "name": "La Liga"},
    "NCAA": {"id": "2", "sport": "american-football", "name": "NCAA Football"},
    "Bundesliga": {"id": "78", "sport": "football", "name": "Bundesliga"},
    "SerieA": {"id": "135", "sport": "football", "name": "Serie A"},
    "Ligue1": {"id": "61", "sport": "football", "name": "Ligue 1"},
    "MLS": {"id": "253", "sport": "football", "name": "MLS"},
    "Formula-1": {"id": "1", "sport": "formula-1", "name": "Formula 1"},
    "MMA": {"id": "1", "sport": "mma", "name": "UFC"},
    "WNBA": {"id": "13", "sport": "basketball", "name": "WNBA"},
    "AFL": {"id": "1", "sport": "afl", "name": "AFL"},
    "EuroLeague": {"id": "1", "sport": "basketball", "name": "EuroLeague"},
}


def fetch_and_save_league_data(json_output_path):
    """
    Fetch league data from TheSportsDB V1 API and save raw JSON to a file.

    Args:
        json_output_path (Path): Path to save the raw JSON file.

    Returns:
        dict: API response data, or None if the request fails.
    """
    url = "https://www.thesportsdb.com/api/v1/json/3/all_leagues.php"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Raw JSON saved to {json_output_path}")

        return data

    except requests.exceptions.HTTPError as e:
        print(
            f"HTTP Error: {e}. Status Code: {response.status_code}. Response: {response.text}",
            file=sys.stderr,
        )
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}. Check your internet connection.", file=sys.stderr)
        return None
    except ValueError as e:
        print(f"JSON Decode Error: {e}. Response: {response.text}", file=sys.stderr)
        return None


def fetch_league_badge(league_id, retries=3, delay=1.0):
    """
    Fetch badge URL for a specific league using league ID with retries.

    Args:
        league_id (str): The league ID.
        retries (int): Number of retry attempts.
        delay (float): Delay between retries in seconds.

    Returns:
        str: Badge URL or empty string if not found or on error.
    """
    url = f"https://www.thesportsdb.com/api/v1/json/3/lookupleague.php?id={league_id}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            badge = data.get("leagues", [{}])[0].get("strBadge", "")
            if not badge:
                print(
                    f"No badge URL for league ID {league_id}. Response: {data}",
                    file=sys.stderr,
                )
            return badge
        except requests.exceptions.HTTPError as e:
            print(
                f"Attempt {attempt + 1}/{retries} - HTTP Error for league ID {league_id}: {e}. Status: {response.status_code}",
                file=sys.stderr,
            )
        except requests.exceptions.RequestException as e:
            print(
                f"Attempt {attempt + 1}/{retries} - Network Error for league ID {league_id}: {e}",
                file=sys.stderr,
            )
        except ValueError as e:
            print(
                f"Attempt {attempt + 1}/{retries} - JSON Decode Error for league ID {league_id}: {e}",
                file=sys.stderr,
            )
        if attempt < retries - 1:
            time.sleep(delay)
    print(
        f"Failed to fetch badge for league ID {league_id} after {retries} attempts.",
        file=sys.stderr,
    )
    return ""


def normalize_and_save_csv(data, csv_output_path):
    """
    Normalize JSON data, fetch badge URLs, and save to a CSV file.

    Args:
        data (dict): Raw API response data.
        csv_output_path (Path): Path to save the CSV file.

    Returns:
        bool: True if CSV was written, False otherwise.
    """
    if not data:
        print("No data to normalize.", file=sys.stderr)
        return False

    leagues = data.get("leagues", [])
    if not leagues:
        print("Warning: API returned no leagues. Response:", data, file=sys.stderr)
        return False

    # Create DataFrame from LEAGUE_IDS
    league_data = [
        {"strLeague": details["name"], "idLeague": details["id"]}
        for code, details in CORRECTED_LEAGUE_IDS.items()
        if details["id"] is not None
    ]
    df = pd.DataFrame(league_data)

    if df.empty:
        print("No valid leagues with IDs in LEAGUE_IDS.", file=sys.stderr)
        return False

    df["logo_path"] = ""

    print(f"Fetching badge URLs for {len(df)} leagues...")
    badge_count = 0
    for idx, row in df.iterrows():
        league_id = row["idLeague"]
        badge_url = fetch_league_badge(league_id)
        df.at[idx, "logo_path"] = badge_url
        if badge_url:
            badge_count += 1
        print(f"League: {row['strLeague']}, ID: {league_id}, Badge: {badge_url}")
        time.sleep(0.6)  # Rate limit: 100 requests/minute

    df = df[["strLeague", "logo_path"]].rename(columns={"strLeague": "league"})

    print(f"Processed {len(df)} leagues, {badge_count} with badge URLs")

    if df.empty:
        print("Warning: No valid league data after processing.", file=sys.stderr)
        return False

    df.to_csv(csv_output_path, index=False, encoding="utf-8")
    print(f"CSV saved to {csv_output_path} with {len(df)} leagues")
    return True


def main():
    output_dir = Path(BASE_DIR) / "static"
    output_dir.mkdir(exist_ok=True)
    json_output_path = output_dir / "raw_leagues.json"
    csv_output_path = output_dir / "leagues.csv"

    data = fetch_and_save_league_data(json_output_path)

    if data:
        normalize_and_save_csv(data, csv_output_path)
    else:
        print("Failed to retrieve league data. No CSV generated.", file=sys.stderr)


if __name__ == "__main__":
    main()
