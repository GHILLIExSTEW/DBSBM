#!/usr/bin/env python3
"""
Download Brazil Serie A team logos and league logo from saved teams JSON and API-Sports
"""

import os
import requests
from PIL import Image
import io
import time


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


def main():
    # Create directory structure
    base_dir = "static/logos/teams/SOCCER/Brazil-Serie_A"
    os.makedirs(base_dir, exist_ok=True)

    # Brazil Serie A teams with their logo URLs
    teams = [
        {
            "name": "america-mg",
            "url": "https://media.api-sports.io/football/teams/196.png",
        },
        {
            "name": "athletico-pr",
            "url": "https://media.api-sports.io/football/teams/197.png",
        },
        {
            "name": "atletico-go",
            "url": "https://media.api-sports.io/football/teams/198.png",
        },
        {
            "name": "atletico-mg",
            "url": "https://media.api-sports.io/football/teams/199.png",
        },
        {"name": "bahia", "url": "https://media.api-sports.io/football/teams/200.png"},
        {
            "name": "botafogo",
            "url": "https://media.api-sports.io/football/teams/201.png",
        },
        {
            "name": "bragantino",
            "url": "https://media.api-sports.io/football/teams/202.png",
        },
        {
            "name": "corinthians",
            "url": "https://media.api-sports.io/football/teams/203.png",
        },
        {
            "name": "criciuma",
            "url": "https://media.api-sports.io/football/teams/204.png",
        },
        {
            "name": "cruzeiro",
            "url": "https://media.api-sports.io/football/teams/205.png",
        },
        {
            "name": "flamengo",
            "url": "https://media.api-sports.io/football/teams/206.png",
        },
        {
            "name": "fluminense",
            "url": "https://media.api-sports.io/football/teams/207.png",
        },
        {
            "name": "fortaleza",
            "url": "https://media.api-sports.io/football/teams/208.png",
        },
        {"name": "gremio", "url": "https://media.api-sports.io/football/teams/209.png"},
        {
            "name": "internacional",
            "url": "https://media.api-sports.io/football/teams/210.png",
        },
        {
            "name": "juventude",
            "url": "https://media.api-sports.io/football/teams/211.png",
        },
        {
            "name": "palmeiras",
            "url": "https://media.api-sports.io/football/teams/212.png",
        },
        {"name": "santos", "url": "https://media.api-sports.io/football/teams/213.png"},
        {
            "name": "sao-paulo",
            "url": "https://media.api-sports.io/football/teams/214.png",
        },
        {
            "name": "vasco-da-gama",
            "url": "https://media.api-sports.io/football/teams/215.png",
        },
    ]

    # League logo
    league_logo_url = "https://media.api-sports.io/football/leagues/71.png"
    league_logo_path = os.path.join(base_dir, "league_logo.png")

    print("Downloading Brazil Serie A logos...")
    print(f"Base directory: {base_dir}")
    print()

    # Download league logo
    print("Downloading league logo...")
    download_and_save_logo(league_logo_url, league_logo_path)
    print()

    # Download team logos
    print("Downloading team logos...")
    successful_downloads = 0

    for team in teams:
        filename = f"{team['name']}.png"
        filepath = os.path.join(base_dir, filename)

        if download_and_save_logo(team["url"], filepath):
            successful_downloads += 1

    print()
    print(f"Download complete!")
    print(f"Successfully downloaded: {successful_downloads}/{len(teams)} team logos")
    print(f"League logo: {'✓' if os.path.exists(league_logo_path) else '✗'}")
    print(f"Files saved to: {os.path.abspath(base_dir)}")


if __name__ == "__main__":
    main()
