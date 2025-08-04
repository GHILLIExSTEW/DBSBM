"""
League Discovery Utility for API-Sports
Automatically discovers and configures all available leagues from the API-Sports API.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Set

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

logger = logging.getLogger(__name__)

# API-Sports Base URLs for all sports
SPORT_ENDPOINTS = {
    "football": "https://v3.football.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "baseball": "https://v1.baseball.api-sports.io",
    "hockey": "https://v1.hockey.api-sports.io",
    "american-football": "https://v1.american-football.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "afl": "https://v1.afl.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
    "tennis": "https://v1.tennis.api-sports.io",
    "golf": "https://v1.golf.api-sports.io",
    "darts": "https://v1.darts.api-sports.io",
    "cricket": "https://v1.cricket.api-sports.io",
    "boxing": "https://v1.boxing.api-sports.io",
    "cycling": "https://v1.cycling.api-sports.io",
    "esports": "https://v1.esports.api-sports.io",
    "futsal": "https://v1.futsal.api-sports.io",
    "table-tennis": "https://v1.table-tennis.api-sports.io",
    "badminton": "https://v1.badminton.api-sports.io",
    "beach-volleyball": "https://v1.beach-volleyball.api-sports.io",
    "field-hockey": "https://v1.field-hockey.api-sports.io",
    "ice-hockey": "https://v1.ice-hockey.api-sports.io",
    "motorsport": "https://v1.motorsport.api-sports.io",
    "snooker": "https://v1.snooker.api-sports.io",
    "squash": "https://v1.squash.api-sports.io",
    "water-polo": "https://v1.water-polo.api-sports.io",
    "winter-sports": "https://v1.winter-sports.api-sports.io",
}


# Rate limiter for API calls
class APIRateLimiter:
    # Increased from 30 to 60 for hourly operation
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = datetime.now().timestamp()
            # Remove calls older than 1 minute
            self.calls = [call for call in self.calls if now - call < 60]

            if len(self.calls) >= self.calls_per_minute:
                # Wait until we can make another call
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.calls = self.calls[1:]

            self.calls.append(now)


class LeagueDiscovery:
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")

        self.rate_limiter = APIRateLimiter()
        self.session = None
        self.discovered_leagues = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def discover_all_leagues(self) -> Dict[str, List[Dict]]:
        """Discover all available leagues from all sports APIs."""
        logger.info("Starting comprehensive league discovery...")

        all_leagues = {}
        current_year = datetime.now().year

        for sport, base_url in SPORT_ENDPOINTS.items():
            try:
                logger.info(f"Discovering leagues for {sport}...")
                leagues = await self._discover_sport_leagues(
                    sport, base_url, current_year
                )
                if leagues:
                    all_leagues[sport] = leagues
                    logger.info(f"Found {len(leagues)} leagues for {sport}")
                else:
                    logger.warning(f"No leagues found for {sport}")

                # Rate limiting between sports - reduced for hourly operation
                await asyncio.sleep(1)  # Reduced from 2s to 1s

            except Exception as e:
                logger.error(f"Error discovering leagues for {sport}: {e}")
                continue

        logger.info(
            f"League discovery completed. Found leagues for {len(all_leagues)} sports"
        )
        return all_leagues

    async def _discover_sport_leagues(
        self, sport: str, base_url: str, season: int
    ) -> List[Dict]:
        """Discover leagues for a specific sport."""
        await self.rate_limiter.acquire()

        url = f"{base_url}/leagues"
        headers = {"x-apisports-key": self.api_key}
        params = {"season": season}

        try:
            async with self.session.get(
                url, headers=headers, params=params
            ) as response:
                if response.status == 429:  # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for {sport}, waiting...")
                    await asyncio.sleep(60)
                    return await self._discover_sport_leagues(sport, base_url, season)

                response.raise_for_status()
                data = await response.json()

                if "errors" in data and data["errors"]:
                    logger.warning(f"API errors for {sport}: {data['errors']}")
                    return []

                leagues = []
                for league_data in data.get("response", []):
                    league = league_data.get("league", {})
                    country = league_data.get("country", {})

                    if league and league.get("id"):
                        league_info = {
                            "id": league["id"],
                            "name": league.get("name", ""),
                            "type": league.get("type", ""),
                            "logo": league.get("logo", ""),
                            "country": country.get("name", ""),
                            "country_code": country.get("code", ""),
                            "flag": country.get("flag", ""),
                            "season": season,
                            "sport": sport,
                        }
                        leagues.append(league_info)

                return leagues

        except aiohttp.ClientError as e:
            logger.error(f"API request failed for {sport}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error discovering leagues for {sport}: {e}")
            return []

    def generate_league_ids_config(
        self, discovered_leagues: Dict[str, List[Dict]]
    ) -> str:
        """Generate the LEAGUE_IDS configuration string."""
        config_lines = ["# Auto-generated LEAGUE_IDS configuration", ""]
        config_lines.append("LEAGUE_IDS = {")

        for sport, leagues in discovered_leagues.items():
            config_lines.append(f"    # {sport.title()}")
            for league in leagues:
                # Create a safe key name
                safe_name = self._create_safe_key(league["name"])
                config_lines.append(
                    f'    "{safe_name}": {{"id": {league["id"]}, "sport": "{sport}", "name": "{league["name"]}"}},'
                )
            config_lines.append("")

        config_lines.append("}")
        return "\n".join(config_lines)

    def _create_safe_key(self, league_name: str) -> str:
        """Create a safe key name for the league."""
        # Remove special characters and replace spaces with underscores
        safe_name = "".join(c for c in league_name if c.isalnum() or c.isspace())
        safe_name = safe_name.replace(" ", "").replace("&", "And")

        # Handle common abbreviations
        abbreviations = {
            "PremierLeague": "EPL",
            "LaLiga": "LaLiga",
            "Bundesliga": "Bundesliga",
            "SerieA": "SerieA",
            "Ligue1": "Ligue1",
            "MajorLeagueSoccer": "MLS",
            "UEFAChampionsLeague": "ChampionsLeague",
            "UEFAEuropaLeague": "EuropaLeague",
            "FIFAWorldCup": "WorldCup",
            "NationalBasketballAssociation": "NBA",
            "WNBA": "WNBA",
            "EuroLeague": "EuroLeague",
            "MajorLeagueBaseball": "MLB",
            "NipponProfessionalBaseball": "NPB",
            "KoreaBaseballOrganization": "KBO",
            "NationalHockeyLeague": "NHL",
            "KontinentalHockeyLeague": "KHL",
            "NationalFootballLeague": "NFL",
            "NCAAFootball": "NCAA",
            "CanadianFootballLeague": "CFL",
            "SuperRugby": "SuperRugby",
            "SixNationsChampionship": "SixNations",
            "FIVBWorldLeague": "FIVB",
            "EHFChampionsLeague": "EHF",
            "AFL": "AFL",
            "Formula1": "Formula1",
            "UltimateFightingChampionship": "UFC",
            "BellatorMMA": "Bellator",
            "ATPTour": "ATP",
            "WTATour": "WTA",
            "PGATour": "PGA",
            "LPGATour": "LPGA",
            "EuropeanTour": "EuropeanTour",
            "LIVGolf": "LIVGolf",
            "RyderCup": "RyderCup",
            "PresidentsCup": "PresidentsCup",
            "ProfessionalDartsCorporation": "PDC",
            "BritishDartsOrganisation": "BDO",
            "WorldDartsFederation": "WDF",
            "PremierLeagueDarts": "PremierLeagueDarts",
            "WorldMatchplay": "WorldMatchplay",
            "WorldGrandPrix": "WorldGrandPrix",
            "UKOpen": "UKOpen",
            "GrandSlamofDarts": "GrandSlam",
            "PlayersChampionship": "PlayersChampionship",
            "EuropeanChampionship": "EuropeanChampionship",
            "Masters": "Masters",
        }

        return abbreviations.get(safe_name, safe_name)

    async def save_discovered_leagues(
        self,
        discovered_leagues: Dict[str, List[Dict]],
        output_file: str = "discovered_leagues.json",
    ):
        """Save discovered leagues to a JSON file."""
        import json

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(discovered_leagues, f, indent=2, ensure_ascii=False)

        logger.info(f"Discovered leagues saved to {output_file}")

    async def update_league_config(
        self,
        discovered_leagues: Dict[str, List[Dict]],
        config_file: str = "bot/config/leagues.py",
    ):
        """Update the leagues.py configuration file with discovered leagues."""
        config_content = self.generate_league_ids_config(discovered_leagues)

        # Read existing file
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            return False

        # Find and replace the LEAGUE_IDS section
        import re

        pattern = r"LEAGUE_IDS\s*=\s*\{[^}]*\}"
        replacement = config_content

        if re.search(pattern, existing_content, re.DOTALL):
            new_content = re.sub(
                pattern, replacement, existing_content, flags=re.DOTALL
            )
        else:
            # If no existing LEAGUE_IDS, add it before the ENDPOINTS section
            pattern = r"(ENDPOINTS\s*=\s*\{)"
            replacement = f"{config_content}\n\n# API endpoints\n\\1"
            new_content = re.sub(pattern, replacement, existing_content)

        # Write updated content
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"Updated {config_file} with discovered leagues")
        return True


async def main():
    """Main function to run league discovery."""
    async with LeagueDiscovery() as discoverer:
        # Discover all leagues
        discovered_leagues = await discoverer.discover_all_leagues()

        # Save to JSON file
        await discoverer.save_discovered_leagues(discovered_leagues)

        # Update configuration file
        await discoverer.update_league_config(discovered_leagues)

        # Print summary
        total_leagues = sum(len(leagues) for leagues in discovered_leagues.values())
        logger.info(
            f"Discovery complete! Found {total_leagues} leagues across {len(discovered_leagues)} sports"
        )


if __name__ == "__main__":
    asyncio.run(main())
