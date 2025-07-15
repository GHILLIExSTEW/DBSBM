import csv
import os
import sqlite3
from urllib.parse import urlparse

import requests

# Configuration
CSV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "players.csv"
)  # CSV file is in betting-bot/data/players.csv
DB_FILE = "players.db"
BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "logos", "players"
)

# Ensure the base directory exists
os.makedirs(BASE_DIR, exist_ok=True)


# Function to download an image from a URL and save it to the specified path
def download_image(url, save_path):
    if not url:
        return False
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


# Function to create the directory structure and save the image
def save_player_image(player_name, sport, league, team, image_url):
    # Sanitize directory names (replace spaces with underscores and convert to lowercase)
    sport_dir = sport.lower().replace(" ", "_")
    league_dir = league.lower().replace(" ", "_")
    team_dir = team.lower().replace(" ", "_")
    player_name_sanitized = player_name.lower().replace(" ", "_")

    # Determine if this is a team sport or an individual sport
    is_team_sport = team and team.strip() != ""

    # Create the directory path based on the sport type
    if is_team_sport:
        dir_path = os.path.join(BASE_DIR, sport_dir, league_dir)
    else:
        dir_path = os.path.join(BASE_DIR, sport_dir, league_dir)

    os.makedirs(dir_path, exist_ok=True)

    # Define the image file path
    image_path = os.path.join(dir_path, f"{player_name_sanitized}.png")

    # Download and save the image
    return download_image(image_url, image_path)


# Read the CSV file and process each row
def process_csv():
    # Read the CSV file to get the column names
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Get the header row

        # Process each row
        for row in reader:
            # Create a dictionary mapping column names to values
            player_data = dict(zip(headers, row))

            # Determine the image URL (strCutout or strThumb)
            image_url = player_data.get("strCutouts") or player_data.get("strThumb")
            if not image_url:
                print(f"No image URL for player: {player_data.get('strPlayer')}")
                continue

            # Save the player image
            sport = player_data.get("strSport", "")
            league = player_data.get("strTeam", "")  # Assuming strTeam is the league
            team = player_data.get("strTeam", "")  # Assuming strTeam is the team
            player_name = player_data.get("strPlayer", "")

            if save_player_image(player_name, sport, league, team, image_url):
                print(f"Saved image for {player_name}")

            # Note: Database table creation and insertion should be handled by db.manager
            # Insert the player data into the database
            # placeholders = ', '.join(['?' for _ in headers])
            # insert_sql = f"INSERT INTO players VALUES ({placeholders})"
            # cursor.execute(insert_sql, row)

    # Commit the changes and close the connection
    # conn.commit()
    # conn.close()


def main():
    process_csv()
    print("Processing complete.")


# Function to be called from the bot's startup code
def run_with_bot_startup():
    main()


if __name__ == "__main__":
    main()
