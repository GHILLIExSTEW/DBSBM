#!/usr/bin/env python3
"""
Run the targeted player image downloader with the provided API key.
"""

import os
import sys
import asyncio

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

try:
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from bot.config.leagues import LEAGUE_IDS, get_current_season
    from bot.utils.api_sports import ENDPOINTS_MAP

from targeted_player_image_downloader import TargetedPlayerImageDownloader

async def main():
    """Main function with the provided API key."""
    print("=" * 60)
    print("TARGETED PLAYER IMAGE DOWNLOADER")
    print("=" * 60)
    
    # Use the provided API key
    api_key = "59d5fa03fb6bd373f9ee6cac5f39c689"
    print(f"Using API key: {api_key[:8]}...")
    
    # Priority leagues to download (focusing on the most important ones first)
    priority_leagues = [
        'NBA',      # Basketball - High priority
        'MLB',      # Baseball - High priority
        'NFL',      # American Football - High priority
        'NHL',      # Hockey - High priority
    ]
    
    print(f"\nWill download images for priority leagues:")
    for league in priority_leagues:
        print(f"  - {league}")
    
    print("\nStarting download...")
    print("This will download player images with robust error checking.")
    print("Progress will be shown in real-time.")
    
    async with TargetedPlayerImageDownloader(api_key) as downloader:
        await downloader.run(priority_leagues)

if __name__ == "__main__":
    asyncio.run(main()) 