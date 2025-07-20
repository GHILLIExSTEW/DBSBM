#!/usr/bin/env python3
"""
Wrapper script to run the targeted player image downloader with API key from environment.
"""

import os
import sys
import asyncio
from targeted_player_image_downloader import TargetedPlayerImageDownloader

async def main():
    """Main function with API key from environment."""
    print("=" * 50)
    print("TARGETED PLAYER IMAGE DOWNLOADER")
    print("=" * 50)
    
    # Get API key from environment variable
    api_key = os.getenv('API_SPORTS_KEY')
    
    if not api_key:
        print("API_SPORTS_KEY environment variable not set!")
        print("Please set it with: set API_SPORTS_KEY=your_key_here")
        return
    
    print(f"Using API key: {api_key[:8]}...")
    
    # Priority leagues to download
    priority_leagues = [
        'NBA',      # Basketball - High priority
        'MLB',      # Baseball - High priority
        'NFL',      # American Football - High priority
        'NHL',      # Hockey - High priority
        'EPL',      # Soccer - Medium priority
        'LaLiga',   # Soccer - Medium priority
        'Bundesliga', # Soccer - Medium priority
    ]
    
    print(f"\nWill download images for priority leagues:")
    for league in priority_leagues:
        print(f"  - {league}")
    
    confirm = input("\nContinue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    async with TargetedPlayerImageDownloader(api_key) as downloader:
        await downloader.run(priority_leagues)

if __name__ == "__main__":
    asyncio.run(main()) 