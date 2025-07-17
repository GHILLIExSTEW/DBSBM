#!/usr/bin/env python3
"""
Debug script to see what's happening with golf player scraping
"""

import sys
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# URLs
PGATOUR_BASE_URL = "https://www.pgatour.com"
LPGA_BASE_URL = "https://www.lpga.com"
PGATOUR_PLAYERS_URL = "https://www.pgatour.com/players"
LPGA_PLAYERS_URL = "https://www.lpga.com/athletes"


def debug_pgatour_scraping():
    """Debug PGA TOUR scraping to see what we're finding."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)

        try:
            print("Loading PGA TOUR players page...")
            driver.get(PGATOUR_PLAYERS_URL)
            time.sleep(5)

            # Scroll a few times to load some content
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                print(f"Scroll {i+1} complete")

            # Get the page source
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Look for all links with images
            image_links = soup.find_all("a", href=True)
            print(f"Found {len(image_links)} links with href")

            player_data = {}

            for i, link in enumerate(image_links[:20]):  # Just look at first 20
                # Find image within the link
                img_elem = link.find("img")
                if not img_elem:
                    continue

                # Get image URL
                img_src = img_elem.get("src", "")
                if not img_src:
                    continue

                # Convert relative URLs to absolute
                if img_src.startswith("//"):
                    img_src = "https:" + img_src
                elif img_src.startswith("/"):
                    img_src = urljoin(PGATOUR_BASE_URL, img_src)

                # Get profile URL
                profile_url = link.get("href", "")
                if profile_url:
                    if profile_url.startswith("//"):
                        profile_url = "https:" + profile_url
                    elif profile_url.startswith("/"):
                        profile_url = urljoin(PGATOUR_BASE_URL, profile_url)

                # Try to find player name
                player_name = None

                # Check if the link has title or alt text
                if link.get("title"):
                    player_name = link.get("title").strip()
                elif img_elem.get("alt"):
                    player_name = img_elem.get("alt").strip()

                # If no name found, look for nearby text elements
                if not player_name:
                    # Look for text within the link
                    text_elem = link.find(
                        ["span", "div", "h3", "h4", "h5"],
                        class_=lambda x: x
                        and any(term in x.lower() for term in ["name", "title"]),
                    )
                    if text_elem:
                        player_name = text_elem.get_text(strip=True)

                # If still no name, look at parent container
                if not player_name:
                    parent = link.parent
                    if parent:
                        name_elem = parent.find(
                            ["h3", "h4", "h5", "span", "div"],
                            class_=lambda x: x
                            and any(term in x.lower() for term in ["name", "title"]),
                        )
                        if name_elem:
                            player_name = name_elem.get_text(strip=True)

                if player_name and img_src:
                    player_data[player_name] = (img_src, profile_url)
                    print(
                        f"Found player {i+1}: '{player_name}' -> Image: {img_src[:50]}..."
                    )
                else:
                    print(
                        f"Link {i+1}: No name found. Alt: '{img_elem.get('alt', 'None')}', Title: '{link.get('title', 'None')}'"
                    )

            print(f"\nTotal players found: {len(player_data)}")
            print("Sample player names found:")
            for i, name in enumerate(list(player_data.keys())[:10]):
                print(f"  {i+1}. '{name}'")

            return player_data

        finally:
            driver.quit()

    except Exception as e:
        print(f"Error: {e}")
        return {}


if __name__ == "__main__":
    debug_pgatour_scraping()
