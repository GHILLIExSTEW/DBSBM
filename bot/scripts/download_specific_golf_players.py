#!/usr/bin/env python3
"""
Download photos for specific golf players only
"""

import asyncio
import json
import logging
import os
import sys
import re
import time
from urllib.parse import quote, urljoin
import aiohttp
import aiofiles
from PIL import Image
import io
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs
PGATOUR_BASE_URL = "https://www.pgatour.com"
LPGA_BASE_URL = "https://www.lpga.com"
PGATOUR_PLAYERS_URL = "https://www.pgatour.com/players"
LPGA_PLAYERS_URL = "https://www.lpga.com/athletes"

# Base directory for saving photos
BASE_PHOTO_DIR = "static/logos/players/golf"

# Quality filters
MIN_WIDTH = 200
MIN_HEIGHT = 200
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
MIN_ASPECT_RATIO = 0.5
MAX_ASPECT_RATIO = 2.0

# Specific players to search for (from user's messages)
SPECIFIC_PLAYERS = [
    # PGA TOUR players from user's message
    "Anders Albertson",
    "Byeong Hun An",
    "Mason Andersen",
    "Ludvig Åberg",
    "Aaron Baddeley",
    "Daniel Berger",
    "Christiaan Bezuidenhout",
    "Akshay Bhatia",
    "Zac Blair",
    "Keegan Bradley",
    "Joseph Bramlett",
    "Ryan Brehm",
    "Jacob Bridgeman",
    "Wesley Bryan",
    "Hayden Buckley",
    "Sam Burns",
    "Brian Campbell",
    "Rafael Campos",
    "Patrick Cantlay",
    "Frankie Capan III",
    "Ricky Castillo",
    "Bud Cauley",
    "Cameron Champ",
    "Will Chandler",
    "Kevin Chappell",
    "Stewart Cink",
    "Luke Clanton",
    "Wyndham Clark",
    "Eric Cole",
    "Trevor Cone",
    "Corey Conners",
    "Parker Coody",
    "Pierceson Coody",
    "Austin Cook",
    "Vince Covello",
    "Trace Crowe",
    "Quade Cummins",
    "Joel Dahmen",
    "Cam Davis",
    "Jason Day",
    "Cristobal Del Solar",
    "Thomas Detry",
    "Taylor Dickson",
    "Adrien Dumont de Chassart",
    "Tyler Duncan",
    "Nick Dunlap",
    "Nico Echavarria",
    "Austin Eckroat",
    "Harrison Endycott",
    "Harris English",
    "Tony Finau",
    "Patrick Fishburn",
    "Steven Fisk",
    "Matt Fitzpatrick",
    "Tommy Fleetwood",
    "David Ford",
    "Rickie Fowler",
    "Ryan Fox",
    "Brice Garnett",
    "Brian Gay",
    "Ryan Gerard",
    "Doug Ghim",
    "Lucas Glover",
    "Fabián Gómez",
    "Noah Goodwin",
    "Will Gordon",
    "Chris Gotterup",
    "Max Greyserman",
    "Ben Griffin",
    "Lanto Griffin",
    "Emiliano Grillo",
    "Bill Haas",
    "Chesson Hadley",
    "Adam Hadwin",
    "James Hahn",
    "Harry Hall",
    "Nick Hardy",
    "Brian Harman",
    "Russell Henley",
    "Kramer Hickok",
    "Garrick Higgo",
    "Harry Higgs",
    "Joe Highsmith",
    "Ryo Hisatsune",
    "Lee Hodges",
    "Rico Hoey",
    "Charley Hoffman",
    "Tom Hoge",
    "Nicolai Højgaard",
    "Rasmus Højgaard",
    "J.B. Holmes",
    "Max Homa",
    "Billy Horschel",
    "Rikuya Hoshino",
    "Beau Hossler",
    "Viktor Hovland",
    "Mark Hubbard",
    "Mackenzie Hughes",
    "John Huh",
    "Sungjae Im",
    "Stephan Jaeger",
    "Zach Johnson",
    "Takumi Kanaya",
    "Chan Kim",
    "Michael Kim",
    "S.H. Kim",
    "Si Woo Kim",
    "Tom Kim",
    "Chris Kirk",
    "Kevin Kisner",
    "Kurt Kitayama",
    "Patton Kizzire",
    "Jake Knapp",
    "Philip Knowles",
    "Russell Knox",
    "Ben Kohles",
    "Matt Kuchar",
    "Martin Laird",
    "Nate Lashley",
    "Thriston Lawrence",
    "K.H. Lee",
    "Min Woo Lee",
    "Nicholas Lindheim",
    "David Lingmerth",
    "David Lipsky",
    "Luke List",
    "Adam Long",
    "Justin Lower",
    "Shane Lowry",
    "Robert MacIntyre",
    "Peter Malnati",
    "Matteo Manassero",
    "Ben Martin",
    "Hideki Matsuyama",
    "Brandon Matthews",
    "Denny McCarthy",
    "Matt McCarty",
    "Tyler McCumber",
    "Max McGreevy",
    "Rory McIlroy",
    "Maverick McNealy",
    "Mac Meissner",
    "Troy Merritt",
    "Keith Mitchell",
    "Francesco Molinari",
    "Taylor Montgomery",
    "Ryan Moore",
    "Taylor Moore",
    "Collin Morikawa",
    "William Mouw",
    "Trey Mullinax",
    "Matt NeSmith",
    "S.Y. Noh",
    "Alex Noren",
    "Niklas Norgaard",
    "Henrik Norlander",
    "Vincent Norrman",
    "Andrew Novak",
    "Sean O'Hair",
    "Thorbjørn Olesen",
    "Kaito Onishi",
    "John Pak",
    "Ryan Palmer",
    "Rod Pampling",
    "C.T. Pan",
    "Jeremy Paul",
    "Matthieu Pavon",
    "Taylor Pendrith",
    "Victor Perez",
    "Paul Peterson",
    "Chandler Phillips",
    "Scott Piercy",
    "J.T. Poston",
    "Aldrich Potgieter",
    "Seamus Power",
    "Andrew Putnam",
    "Aaron Rai",
    "Chad Ramey",
    "Chez Reavie",
    "Matthew Riedel",
    "Davis Riley",
    "Patrick Rodgers",
    "Justin Rose",
    "Thomas Rosenmueller",
    "Kevin Roy",
    "Antoine Rozner",
    "Sam Ryder",
    "Isaiah Salinda",
    "Gordon Sargent",
    "Xander Schauffele",
    "Scottie Scheffler",
    "Adam Schenk",
    "Matti Schmid",
    "Adam Scott",
    "Robby Shelton",
    "Greyson Sigg",
    "Ben Silverman",
    "Webb Simpson",
    "Vijay Singh",
    "David Skinns",
    "Alex Smalley",
    "Brandt Snedeker",
    "J.J. Spaun",
    "Jordan Spieth",
    "Hayden Springer",
    "Scott Stallings",
    "Jimmy Stanger",
    "Kyle Stanley",
    "Sam Stevens",
    "Sepp Straka",
    "Kevin Streelman",
    "Jackson Suber",
    "Adam Svensson",
    "Jesper Svensson",
    "Nick Taylor",
    "Sahith Theegala",
    "Justin Thomas",
    "Davis Thompson",
    "Michael Thompson",
    "Michael Thorbjornsen",
    "Braden Thornberry",
    "Brendon Todd",
    "Alejandro Tosti",
    "Martin Trainer",
    "Kevin Tway",
    "Sami Valimaki",
    "Erik van Rooyen",
    "Jhonattan Vegas",
    "Kevin Velo",
    "Kris Ventura",
    "Karl Vilips",
    "Camilo Villegas",
    "Danny Walker",
    "Jimmy Walker",
    "Matt Wallace",
    "Paul Waring",
    "Nick Watney",
    "Vince Whaley",
    "Tim Widing",
    "Danny Willett",
    "Aaron Wise",
    "Gary Woodland",
    "Tiger Woods",
    "Brandon Wu",
    "Dylan Wu",
    "Norman Xiong",
    "Cameron Young",
    "Carson Young",
    "Kevin Yu",
    "Carl Yuan",
    "Will Zalatoris",
    # LPGA players from user's message
    "Marina Alex",
    "Brittany Altomare",
    "Narin An",
    "Pajaree Anannarukarn",
    "Dottie Ardina",
    "Aditi Ashok",
    "Saki Baba",
    "Jenny Bae",
    "Laetitia Beck",
    "Ana Belac",
    "Jaravee Boonchant",
    "Celine Borge",
    "Celine Boutier",
    "Heather Bowie Young",
    "Nicole Broch Estrup",
    "Ashleigh Buhai",
    "Dori Carter",
    "Matilda Castren",
    "Silvia Cavalleri",
    "Adela Cernousek",
    "Tiffany Chan",
    "Jennifer Chang",
    "Ssu-Chia Cheng",
    "Peiyun Chien",
    "Robyn Choi",
    "Hye-Jin Choi",
    "In Gee Chun",
    "Carlota Ciganda",
    "Cydney Clanton",
    "Jenny Coleman",
    "Allisen Corpuz",
    "Lauren Coughlin",
    "Olivia Cowan",
    "Paula Creamer",
    "Daniela Darquea",
    "Karis Davidson",
    "Manon De Roey",
    "Perrine Delacour",
    "Brianna Do",
    "Amanda Doherty",
    "Gemma Dryburgh",
    "Lindy Duncan",
    "Jodi Ewart Shadoff",
    "Ally Ewing",
    "Dana Fall",
    "Maria Fassi",
    "Fatima Fernandez Cano",
    "Isabella Fierro",
    "Alexandra Forsterling",
    "Meaghan Francella",
    "Ayaka Furue",
    "Sandra Gal",
    "Mariel Galdiano",
    "Sofia Garcia",
    "Kristen Gillman",
    "Linn Grant",
    "Hannah Green",
    "Savannah Grewal",
    "Natalie Gulbis",
    "Nataliya Guseva",
    "Georgia Hall",
    "Katherine Hamski",
    "Lauren Hartlage",
    "Nasa Hataoka",
    "Muni He",
    "Brooke M. Henderson",
    "Esther Henseleit",
    "Celine Herbin",
    "Dani Holmqvist",
    "Wei-Ling Hsu",
    "Charley Hull",
    "Vicky Hurst",
    "Daniela Iacobelli",
    "Jin Hee Im",
    "Mone Inami",
    "Caroline Inglis",
    "Nuria Iturrioz",
    "Chisato Iwai",
    "Akie Iwai",
    "Hyo Joon Jang",
    "Jiwon Jeon",
    "Eun-Hee Ji",
    "Soo Bin Joo",
    "Moriya Jutanugarn",
    "Ariya Jutanugarn",
    "Danielle Kang",
    "Minji Kang",
    "Haeji Kang",
    "Minami Katsu",
    "Kim Kaufman",
    "Gurleen Kaur",
    "Sarah Kemp",
    "Cristie Kerr",
    "Megan Khang",
    "Auston Kim",
    "Sei Young Kim",
    "A Lim Kim",
    "Grace Kim",
    "In Kyung Kim",
    "Hyo Joo Kim",
    "Christina Kim",
    "Frida Kinhult",
    "Cheyenne Knight",
    "Lydia Ko",
    "Jin Young Ko",
    "Nanna Koerstz Madsen",
    "Nelly Korda",
    "Aline Krauter",
    "Mina Kreiter",
    "Jennifer Kupcho",
    "Stephanie Kyriacou",
    "Cindy LaCrosse",
    "Brittany Lang",
    "Bronte Law",
    "Maude-Aimee Leblanc",
    "Andrea Lee",
    "Alison Lee",
    "Minjee Lee",
    "Mirim Lee",
    "Min Lee",
    "Mi Hyang Lee",
    "Somi Lee",
    "Ilhee Lee",
    "Jeongeun Lee5",
    "Jeongeun Lee6",
    "Stacy Lewis",
    "Amelia Lewis",
    "Lucy Li",
    "Xiyu Janet Lin",
    "Heather Lin",
    "Brittany Lincicome",
    "Pernilla Lindberg",
    "Ingrid Lindblad",
    "Leta Lindley",
    "Yan Liu",
    "Yu Liu",
    "Mary Liu",
    "Ruixin Liu",
    "Gaby Lopez",
    "Lee Lopez",
    "Julia Lopez Ramirez",
    "Polly Mack",
    "Leona Maguire",
    "Caroline Masson",
    "Catriona Matthew",
    "Brooke Matthews",
    "Jill McGill",
    "Caley McGinty",
    "Kristy McPherson",
    "Stephanie Meadow",
    "Wichanee Meechai",
    "Morgane Metraux",
    "Sydnee Michaels",
    "Haru Moon",
    "Benedetta Moresco",
    "Lauren Morris",
    "Azahara Munoz",
    "Malia Nam",
    "Hira Naveed",
    "Yuna Nishimura",
    "Yealimi Noh",
    "Anna Nordqvist",
    "Su Oh",
    "Ryann O'Toole",
    "Lee-Anne Pace",
    "Bianca Pagdanganan",
    "Alexa Pano",
    "Kaitlyn Papp Budde",
    "Sung Hyun Park",
    "Hee Young Park",
    "Annie Park",
    "Kumkang Park",
    "Emily Kristine Pedersen",
    "Ana Pelaez Trivino",
    "Pornanong Phatlum",
    "Sophia Popov",
    "Cassie Porter",
    "Jessica Porvasnik",
    "Mel Reid",
    "Yue Ren",
    "Paula Reto",
    "Kiira Riihijarvi",
    "Pauline Roussin-Bouchard",
    "Gabriela Ruffels",
    "So Yeon Ryu",
    "Haeran Ryu",
    "Madelene Sagstrom",
    "Mao Saigo",
    "Lizette Salas",
    "Yuka Saso",
    "Sarah Schmelzel",
    "Alena Sharp",
    "Hinako Shibuno",
    "Jenny Shin",
    "Sarah Jane Smith",
    "Kate Smith-Stroh",
    "Jennifer Song",
    "Mariah Stackhouse",
    "Angela Stanford",
    "Maja Stark",
    "Marissa Steen",
    "Gigi Stoll",
    "Linnea Strom",
    "Jasmine Suwannapura",
    "Elizabeth Szokol",
    "Rio Takeda",
    "Emma Talley",
    "Kris Tamulis",
    "Kelly Tan",
    "Bailey Tardy",
    "Patty Tavatanakit",
    "Jeeno Thitikul",
    "Lexi Thompson",
    "Maria Torres",
    "Yani Tseng",
    "Ayako Uehara",
    "Mariajo Uribe",
    "Alana Uriell",
    "Albane Valenzuela",
    "Natthakritta Vongtaveelap",
    "Lilia Vu",
    "Alison Walshe",
    "Miranda Wang",
    "Chanettee Wannasaen",
    "Wendy Ward",
    "Lindsey Weaver-Wright",
    "Karrie Webb",
    "Dewi Weber",
    "Kim Williams",
    "Lottie Woad",
    "Fiona Xu",
    "Miyu Yamashita",
    "Jing Yan",
    "Amy Yang",
    "Ruoning Yin",
    "Xiaowen Yin",
    "Angel Yin",
    "Pavarisa Yoktuan",
    "Ina Yoon",
    "Yuri Yoshida",
    "Madison Young",
    "Arpichaya Yubol",
    "Liqi Zeng",
    "Weiwei Zhang",
    "Rose Zhang",
    "Yahui Zhang",
]


def is_valid_person_image(image_data: bytes) -> tuple[bool, dict]:
    """Check if the image is likely a valid person photo."""
    try:
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size

        metadata = {
            "width": width,
            "height": height,
            "format": img.format,
            "mode": img.mode,
            "file_size": len(image_data),
        }

        # Basic dimension checks
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            return False, metadata
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            return False, metadata

        # Aspect ratio check
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            return False, metadata

        # Minimum area check
        if width * height < 40000:  # 200x200 minimum area
            return False, metadata

        return True, metadata

    except Exception as e:
        logger.warning(f"Error validating image: {e}")
        return False, {"error": str(e)}


def generate_profile_urls(player_name: str) -> list[str]:
    """Generate possible profile URLs for a player."""
    # Clean player name
    clean_name = player_name.split(",")[0] if "," in player_name else player_name

    # Remove special characters and convert to URL-friendly format
    url_name = re.sub(r"[^a-zA-Z\s]", "", clean_name)
    url_name = url_name.strip().lower().replace(" ", "-")

    urls = []

    # PGA TOUR patterns
    urls.extend(
        [
            f"{PGATOUR_BASE_URL}/players/{url_name}",
            f"{PGATOUR_BASE_URL}/players/{url_name}.html",
            f"{PGATOUR_BASE_URL}/player/{url_name}",
            f"{PGATOUR_BASE_URL}/player/{url_name}.html",
        ]
    )

    # LPGA patterns
    urls.extend(
        [
            f"{LPGA_BASE_URL}/athletes/{url_name}",
            f"{LPGA_BASE_URL}/athletes/{url_name}.html",
            f"{LPGA_BASE_URL}/player/{url_name}",
            f"{LPGA_BASE_URL}/player/{url_name}.html",
        ]
    )

    # Also try with first initial + last name
    name_parts = clean_name.split()
    if len(name_parts) >= 2:
        first_initial = name_parts[0][0].lower()
        last_name = name_parts[-1].lower()

        # PGA TOUR
        urls.extend(
            [
                f"{PGATOUR_BASE_URL}/players/{first_initial}-{last_name}",
                f"{PGATOUR_BASE_URL}/players/{first_initial}-{last_name}.html",
            ]
        )

        # LPGA
        urls.extend(
            [
                f"{LPGA_BASE_URL}/athletes/{first_initial}-{last_name}",
                f"{LPGA_BASE_URL}/athletes/{first_initial}-{last_name}.html",
            ]
        )

    # Handle special cases like "J.B. Holmes" -> "jb-holmes"
    if "." in clean_name:
        no_periods = clean_name.replace(".", "").replace(" ", "-").lower()
        urls.extend(
            [
                f"{PGATOUR_BASE_URL}/players/{no_periods}",
                f"{PGATOUR_BASE_URL}/players/{no_periods}.html",
                f"{LPGA_BASE_URL}/athletes/{no_periods}",
                f"{LPGA_BASE_URL}/athletes/{no_periods}.html",
            ]
        )

    # Handle special cases like "S.H. Kim" -> "sh-kim"
    if len(name_parts) >= 2 and "." in name_parts[0]:
        initials = "".join([part[0] for part in name_parts[:-1]]).lower()
        last_name = name_parts[-1].lower()
        urls.extend(
            [
                f"{PGATOUR_BASE_URL}/players/{initials}-{last_name}",
                f"{PGATOUR_BASE_URL}/players/{initials}-{last_name}.html",
                f"{LPGA_BASE_URL}/athletes/{initials}-{last_name}",
                f"{LPGA_BASE_URL}/athletes/{initials}-{last_name}.html",
            ]
        )

    return urls


def scrape_pgatour_players_page() -> dict[str, tuple[str, str]]:
    """Scrape PGA TOUR players page and extract player name -> (image_url, profile_url) mappings."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
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
            logger.info("Loading PGA TOUR players page...")
            driver.get(PGATOUR_PLAYERS_URL)

            # Wait for initial content to load
            time.sleep(5)

            player_data = {}
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20  # Limit scrolling to avoid infinite loops

            while scroll_attempts < max_scroll_attempts:
                # Scroll to bottom to load more content
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Wait for content to load

                # Get current page content
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Look for clickable image links
                image_links = soup.find_all("a", href=True)
                current_count = 0

                for link in image_links:
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

                    # Try to find player name from the link or nearby elements
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
                                and any(
                                    term in x.lower() for term in ["name", "title"]
                                ),
                            )
                            if name_elem:
                                player_name = name_elem.get_text(strip=True)

                    if player_name and img_src:
                        player_data[player_name] = (img_src, profile_url)
                        current_count += 1

                logger.info(f"Found {len(player_data)} players so far...")

                # Check if we're still finding new players
                if current_count == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # Reset counter if we found new players

                last_count = current_count

                # If we haven't found new players in a while, stop scrolling
                if scroll_attempts >= 3:
                    logger.info(
                        "No new players found after 3 scroll attempts, stopping..."
                    )
                    break

            logger.info(f"Total PGA TOUR players found: {len(player_data)}")
            return player_data

        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"Error scraping PGA TOUR players page: {e}")
        return {}


def scrape_lpga_players_page() -> dict[str, tuple[str, str]]:
    """Scrape LPGA players page and extract player name -> (image_url, profile_url) mappings."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
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
            logger.info("Loading LPGA players page...")
            driver.get(LPGA_PLAYERS_URL)

            # Wait for initial content to load
            time.sleep(5)

            player_data = {}
            last_count = 0
            button_attempts = 0
            max_button_attempts = 20  # Limit button clicks to avoid infinite loops

            while button_attempts < max_button_attempts:
                # Try to find and click "View more Athletes" button
                try:
                    # Look for various possible button texts
                    button_selectors = [
                        "//button[contains(text(), 'View more Athletes')]",
                        "//button[contains(text(), 'View More')]",
                        "//button[contains(text(), 'Load More')]",
                        "//a[contains(text(), 'View more Athletes')]",
                        "//a[contains(text(), 'View More')]",
                        "//a[contains(text(), 'Load More')]",
                        "//div[contains(text(), 'View more Athletes')]",
                        "//span[contains(text(), 'View more Athletes')]",
                    ]

                    button_found = False
                    for selector in button_selectors:
                        try:
                            button = wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            button.click()
                            button_found = True
                            logger.info("Clicked 'View more Athletes' button")
                            time.sleep(3)  # Wait for content to load
                            break
                        except TimeoutException:
                            continue

                    if not button_found:
                        logger.info(
                            "No 'View more Athletes' button found, trying to scroll instead..."
                        )
                        # If no button, try scrolling
                        driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);"
                        )
                        time.sleep(3)

                except Exception as e:
                    logger.debug(f"Error clicking button: {e}")
                    # If button clicking fails, try scrolling
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(3)

                # Get current page content
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Look for clickable image links
                image_links = soup.find_all("a", href=True)
                current_count = 0

                for link in image_links:
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
                        img_src = urljoin(LPGA_BASE_URL, img_src)

                    # Get profile URL
                    profile_url = link.get("href", "")
                    if profile_url:
                        if profile_url.startswith("//"):
                            profile_url = "https:" + profile_url
                        elif profile_url.startswith("/"):
                            profile_url = urljoin(LPGA_BASE_URL, profile_url)

                    # Try to find player name from the link or nearby elements
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
                                and any(
                                    term in x.lower() for term in ["name", "title"]
                                ),
                            )
                            if name_elem:
                                player_name = name_elem.get_text(strip=True)

                    if player_name and img_src:
                        player_data[player_name] = (img_src, profile_url)
                        current_count += 1

                logger.info(f"Found {len(player_data)} LPGA players so far...")

                # Check if we're still finding new players
                if current_count == last_count:
                    button_attempts += 1
                else:
                    button_attempts = 0  # Reset counter if we found new players

                last_count = current_count

                # If we haven't found new players in a while, stop
                if button_attempts >= 3:
                    logger.info("No new players found after 3 attempts, stopping...")
                    break

            logger.info(f"Total LPGA players found: {len(player_data)}")
            return player_data

        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"Error scraping LPGA players page: {e}")
        return {}


async def download_image(
    session: aiohttp.ClientSession, image_url: str, file_path: str, metadata: dict
) -> bool:
    """Download an image and save it to the specified path."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

        async with session.get(image_url, headers=headers) as response:
            if response.status == 200:
                image_data = await response.read()

                # Final validation
                is_valid, final_metadata = is_valid_person_image(image_data)
                if not is_valid:
                    return False

                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Save image
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(image_data)

                # Save metadata
                metadata_file = file_path.replace(".png", "_metadata.json")
                async with aiofiles.open(metadata_file, "w") as f:
                    await f.write(json.dumps(final_metadata, indent=2, default=str))

                return True
        return False
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return False


def clean_filename(name: str) -> str:
    """Clean a player name for use as a filename."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "", name)
    cleaned = cleaned.replace(" ", "_")
    return cleaned


async def download_specific_golf_players():
    """Main function to download photos for specific players only."""
    logger.info("Starting specific golf player photo download...")
    logger.info(f"Processing {len(SPECIFIC_PLAYERS)} specific players")

    # Create base directory
    os.makedirs(BASE_PHOTO_DIR, exist_ok=True)

    # Track progress
    total_players = len(SPECIFIC_PLAYERS)
    successful_downloads = 0
    failed_downloads = 0

    # First, scrape both main pages to get all available players (synchronous)
    logger.info("Scraping PGA TOUR players page...")
    pgatour_players = scrape_pgatour_players_page()
    logger.info(f"Found {len(pgatour_players)} PGA TOUR players")

    logger.info("Scraping LPGA players page...")
    lpga_players = scrape_lpga_players_page()
    logger.info(f"Found {len(lpga_players)} LPGA players")

    # Combine all found players
    all_players = {**pgatour_players, **lpga_players}
    logger.info(f"Total players found: {len(all_players)}")

    # Create session with longer timeout for downloading images
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Process only the specific players we want
        for i, player_name in enumerate(SPECIFIC_PLAYERS, 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")

            try:
                # Check if we found this player
                if player_name not in all_players:
                    logger.warning(f"Player {player_name} not found on main pages")
                    failed_downloads += 1
                    continue

                # Get the image URL and profile URL
                image_url, profile_url = all_players[player_name]

                if not image_url:
                    logger.warning(f"No image URL found for {player_name}")
                    failed_downloads += 1
                    continue

                logger.info(f"Found {player_name}: Image: {image_url}")

                # Download and validate the image
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    }

                    async with session.get(image_url, headers=headers) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            is_valid, metadata = is_valid_person_image(image_data)

                            if not is_valid:
                                logger.warning(
                                    f"Image for {player_name} failed validation"
                                )
                                failed_downloads += 1
                                continue

                            logger.info(
                                f"Valid image for {player_name}: {metadata['width']}x{metadata['height']}"
                            )

                            # Determine league based on profile URL
                            if "pgatour.com" in profile_url:
                                league = "PGA_TOUR"
                            elif "lpga.com" in profile_url:
                                league = "LPGA"
                            else:
                                league = "UNKNOWN"

                            # Create file path
                            clean_name = clean_filename(player_name)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            file_path = os.path.join(
                                BASE_PHOTO_DIR,
                                league,
                                f"{clean_name}_main_page_{timestamp}.png",
                            )

                            # Save the image
                            if await download_image(
                                session, image_url, file_path, metadata
                            ):
                                logger.info(
                                    f"Successfully downloaded photo for {player_name}"
                                )
                                successful_downloads += 1
                            else:
                                logger.warning(
                                    f"Failed to download photo for {player_name}"
                                )
                                failed_downloads += 1
                        else:
                            logger.warning(
                                f"Failed to download image for {player_name}: HTTP {response.status}"
                            )
                            failed_downloads += 1

                except Exception as e:
                    logger.error(f"Error downloading image for {player_name}: {e}")
                    failed_downloads += 1

                # 10-second delay between players to avoid being blocked
                logger.info(f"Waiting 10 seconds before next player...")
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1

    logger.info(
        f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}"
    )


if __name__ == "__main__":
    asyncio.run(download_specific_golf_players())
