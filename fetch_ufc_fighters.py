#!/usr/bin/env python3
"""
UFC Fighter Fetcher
Fetches all UFC fighters by category and saves their data and logos.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UFC API categories
UFC_CATEGORIES = [
    "Bantamweight", "Catch Weight", "Catchweight", "Featherweight", "Flyweight",
    "Heavyweight", "Light Heavyweight", "Lightweight", "Middleweight", "Open Weight",
    "Super Heavyweight", "Welterweight", "Women's Bantamweight", "Women's Catch Weight",
    "Women's Featherweight", "Women's Flyweight", "Women's Lightweight", "Women's Strawweight"
]

class UFCFighterFetcher:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            logger.info("🔑 API_KEY not found in environment variables!")
            self.api_key = input("Please enter your API-Sports API key: ").strip()
            if not self.api_key:
                logger.error("❌ No API key provided!")
                import sys
                sys.exit(1)
            
        self.base_url = "https://v1.mma.api-sports.io"
        self.headers = {
            "x-rapidapi-host": "v1.mma.api-sports.io",
            "x-rapidapi-key": self.api_key
        }
        self.fighters_data = {}
        
    async def fetch_fighters_by_category(self, session: aiohttp.ClientSession, category: str) -> List[Dict]:
        """Fetch fighters for a specific category."""
        url = f"{self.base_url}/fighters"
        params = {"category": category}
        
        try:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    fighters = data.get("response", [])
                    logger.info(f"Fetched {len(fighters)} fighters for category: {category}")
                    return fighters
                else:
                    logger.error(f"Error fetching {category}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Network error fetching {category}: {e}")
            return []
    
    async def fetch_fighter_logo(self, session: aiohttp.ClientSession, fighter_id: int) -> Optional[str]:
        """Fetch fighter logo URL."""
        url = f"{self.base_url}/fighters"
        params = {"id": fighter_id}
        
        try:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    fighters = data.get("response", [])
                    if fighters:
                        fighter = fighters[0]
                        # Try different possible logo fields
                        logo_url = (
                            fighter.get("photo") or 
                            fighter.get("image") or 
                            fighter.get("logo") or
                            None
                        )
                        return logo_url
                return None
        except Exception as e:
            logger.error(f"Error fetching logo for fighter {fighter_id}: {e}")
            return None
    
    def save_fighter_to_database(self, fighter: Dict, category: str):
        """Save fighter data to memory dict."""
        try:
            fighter_id = fighter.get("id")
            name = fighter.get("name", "").lower()  # lowercase name as requested
            nationality = fighter.get("nationality", "")
            height = fighter.get("height")
            weight = fighter.get("weight")
            reach = fighter.get("reach")
            wins = fighter.get("wins", 0)
            losses = fighter.get("losses", 0)
            draws = fighter.get("draws", 0)
            
            # Store in memory dict
            self.fighters_data[fighter_id] = {
                "id": fighter_id,
                "name": name,
                "category": category,
                "nationality": nationality,
                "height": height,
                "weight": weight,
                "reach": reach,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "raw_data": fighter,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Saved fighter data: {name} (ID: {fighter_id})")
            
        except Exception as e:
            logger.error(f"Error saving fighter data: {e}")
    
    async def download_and_save_logo(self, session: aiohttp.ClientSession, fighter_id: int, logo_url: str, fighter_name: str):
        """Download and save fighter logo."""
        try:
            # Create directory if it doesn't exist
            logo_dir = "bot/static/logos/teams/MMA/UFC"
            os.makedirs(logo_dir, exist_ok=True)
            
            # Download logo
            async with session.get(logo_url) as response:
                if response.status == 200:
                    # Save with fighter name as filename
                    filename = f"{fighter_name.replace(' ', '_').lower()}.png"
                    filepath = os.path.join(logo_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
                    
                    logger.info(f"Saved logo for {fighter_name}: {filepath}")
                    return filepath
                else:
                    logger.error(f"Failed to download logo for {fighter_name}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error downloading logo for {fighter_name}: {e}")
            return None
    
    async def fetch_all_fighters(self):
        """Fetch all fighters from all categories."""
        logger.info("🥊 Starting UFC fighter fetch...")
        
        async with aiohttp.ClientSession() as session:
            for category in UFC_CATEGORIES:
                logger.info(f"Fetching fighters for category: {category}")
                
                # Fetch fighters for this category
                fighters = await self.fetch_fighters_by_category(session, category)
                
                for fighter in fighters:
                    # Save fighter data
                    self.save_fighter_to_database(fighter, category)
                    
                    # Fetch and save logo
                    fighter_id = fighter.get("id")
                    fighter_name = fighter.get("name", "").lower()
                    
                    if fighter_id:
                        logo_url = await self.fetch_fighter_logo(session, fighter_id)
                        if logo_url:
                            await self.download_and_save_logo(session, fighter_id, logo_url, fighter_name)
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
                # Category rate limiting
                await asyncio.sleep(1)
        
        # Save all fighter data to JSON file
        with open("ufc_fighters_data.json", "w") as f:
            json.dump(self.fighters_data, f, indent=2)
        
        logger.info(f"🥊 Completed! Fetched {len(self.fighters_data)} fighters")
        logger.info("📁 Fighter data saved to: ufc_fighters_data.json")
        logger.info("📁 Logos saved to: bot/static/logos/teams/MMA/UFC/")

async def main():
    """Main function."""
    fetcher = UFCFighterFetcher()
    await fetcher.fetch_all_fighters()

if __name__ == "__main__":
    import sys
    asyncio.run(main()) 