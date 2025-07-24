# download_team_logos.py
import os
import sys

# --- Path Setup ---
# SCRIPT_DIR is the directory where this script (download_team_logos.py) lives: betting-bot/utils/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR is the parent of SCRIPT_DIR, which should be the 'betting-bot' root directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Add BASE_DIR to sys.path to allow imports like 'from bot.config.asset_paths'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Now your regular imports should work
import csv
import logging
import time
from io import BytesIO

import requests
from PIL import Image, UnidentifiedImageError

try:
    from bot.config.asset_paths import (
        DEFAULT_FALLBACK_CATEGORY,
        get_sport_category_for_path,
    )
    from bot.config.leagues import LEAGUE_IDS  # Contains league name to sport mapping
    from bot.config.team_mappings import normalize_team_name  # For sanitizing team names
except ImportError as e:
    print(
        f"CRITICAL ERROR: Could not import from config package: {e}. "
        f"Ensure this script is in a subdirectory of 'betting-bot' (e.g., utils/) "
        f"and that the 'config' package is in 'betting-bot/config/'. "
        f"BASE_DIR was: {BASE_DIR}",
        file=sys.stderr,
    )
    sys.exit(1)  # IMPORTANT: Exit with a non-zero code for errors


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - DL_SCRIPT - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# --- Configuration ---
# CSV_FILE_PATH: betting-bot/data/team_logos.csv
CSV_FILE_PATH = os.path.join(BASE_DIR, "data", "team_logos.csv")

# STATIC_DIR for saving logos: betting-bot/static/
STATIC_DIR = os.path.join(BASE_DIR, "static")
SAVE_BASE_PATH = os.path.join(
    STATIC_DIR, "logos", "teams"
)  # This will be static/logos/teams/

REQUEST_DELAY_SECONDS = 0.25
DOWNLOAD_TIMEOUT_SECONDS = 15


def get_sport_folder_name(sport_name: str) -> str:
    """Determines a consistent folder name for the sport using the canonical mapping."""
    category = get_sport_category_for_path(sport_name)
    if category:
        return category.upper()
    logger.warning(
        f"Could not determine a standard sport folder for '{sport_name}'. Using '{DEFAULT_FALLBACK_CATEGORY}'."
    )
    return DEFAULT_FALLBACK_CATEGORY.upper()


def get_league_code(league_name_from_csv: str) -> str:
    """Gets a short code for the league to use in file paths."""
    for code, details in LEAGUE_IDS.items():
        if details["name"].lower() == league_name_from_csv.lower():
            return code  # Return the key like "NFL", "EPL"
    # Fallback: sanitize the league name itself
    return "".join(filter(str.isalnum, league_name_from_csv)).upper()


def download_and_save_image(league_name: str, team_name: str, logo_url: str):
    """
    Downloads an image from logo_url and saves it to the appropriate
    folder structure based on league and team name.
    Prints status to stdout/stderr.
    """
    # Standard output for confirmations, standard error for issues.
    # The logger calls will also go to wherever the logger is configured (e.g. file and console).

    if (
        not logo_url
        or not isinstance(logo_url, str)
        or not logo_url.startswith(("http://", "https://"))
    ):
        message = f"SKIPPED: Team '{team_name}' (League: '{league_name}') - Invalid or missing logo URL ('{logo_url}')."
        print(message, file=sys.stderr)  # Also print to stderr for main.py to catch
        logger.warning(message)
        return

    try:
        # ... (path determination logic remains the same) ...
        current_league_sport = "OTHER_SPORTS"
        league_code_for_path = league_name.upper().replace(" ", "_")

        for l_code, l_details in LEAGUE_IDS.items():
            if l_details["name"].lower() == league_name.lower():
                current_league_sport = l_details["sport"]
                league_code_for_path = l_code
                break

        sport_folder = get_sport_folder_name(current_league_sport)
        sanitized_team_name = normalize_team_name(team_name)

        if not sanitized_team_name:
            message = f"ERROR: Could not generate a valid filename for team '{team_name}'. Skipping."
            print(message, file=sys.stderr)
            logger.error(message)
            return

        team_logo_dir = os.path.join(SAVE_BASE_PATH, sport_folder, league_code_for_path)
        os.makedirs(team_logo_dir, exist_ok=True)

        file_extension = ".webp"
        file_name = f"{sanitized_team_name}{file_extension}"
        full_save_path = os.path.join(team_logo_dir, file_name)

        if os.path.exists(full_save_path):
            message = f"EXISTS: Logo for '{team_name}' (League: '{league_name}') already at {full_save_path}. Skipping."
            print(message)  # Print to stdout
            logger.info(message)
            return

        print(
            f"ATTEMPTING: Download for '{team_name}' (League: '{league_name}') from '{logo_url}' to '{full_save_path}'"
        )  # Print to stdout
        logger.info(
            f"Downloading logo for '{team_name}' from '{logo_url}' to '{full_save_path}'"
        )

        response = requests.get(logo_url, stream=True, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()

        try:
            img_bytes = BytesIO(response.content)
            with Image.open(img_bytes) as img:
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                img.save(full_save_path, "PNG", optimize=True)
            message = f"SUCCESS: Saved logo for '{team_name}' (League: '{league_name}') to {full_save_path}"
            print(message)  # Print to stdout
            logger.info(message)

        except UnidentifiedImageError:
            message = f"ERROR: Cannot identify image file from URL for '{team_name}' (League: '{league_name}'): {logo_url}"
            print(message, file=sys.stderr)
            logger.error(message)
        except Exception as e_img:
            message = f"ERROR: Processing image for '{team_name}' (League: '{league_name}') from {logo_url}: {e_img}"
            print(message, file=sys.stderr)
            logger.error(message)

        time.sleep(REQUEST_DELAY_SECONDS)

    except requests.exceptions.RequestException as e:
        message = f"ERROR: Downloading logo for '{team_name}' (League: '{league_name}') from {logo_url}: {e}"
        print(message, file=sys.stderr)
        logger.error(message)
    except IOError as e:
        message = f"ERROR: Saving file for '{team_name}' (League: '{league_name}') to {full_save_path}: {e}"
        print(message, file=sys.stderr)
        logger.error(message)
    except Exception as e:
        message = f"UNEXPECTED ERROR: For team '{team_name}' (League: '{league_name}'), URL {logo_url}: {e}"
        print(message, file=sys.stderr)
        logger.error(message)


def main():
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"CSV file not found: {CSV_FILE_PATH}")
        return

    # Ensure base save directory exists
    os.makedirs(SAVE_BASE_PATH, exist_ok=True)
    logger.info(f"Base save path for team logos: {SAVE_BASE_PATH}")

    processed_count = 0
    with open(CSV_FILE_PATH, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames or not all(
            f in reader.fieldnames for f in ["league", "team_name", "logo_url"]
        ):
            logger.error(
                "CSV file is missing required columns: 'league', 'team_name', 'logo_url'"
            )
            return

        for row in reader:
            league_name = row["league"]
            team_name = row["team_name"]
            logo_url = row["logo_url"]
            download_and_save_image(league_name, team_name, logo_url)
            processed_count += 1

    logger.info(f"Finished processing {processed_count} entries from {CSV_FILE_PATH}.")


if __name__ == "__main__":
    main()
