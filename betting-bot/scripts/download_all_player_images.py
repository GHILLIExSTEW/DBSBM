#!/usr/bin/env python3
"""
Master Player Image Downloader
Downloads player images from Wikipedia for darts, tennis, and golf.
Can run all sports or individual ones based on command line arguments.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_name, sport_name):
    """Run a specific download script."""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting {sport_name.upper()} player download")
        logger.info(f"{'='*60}")
        
        script_path = Path(__file__).parent / script_name
        
        # Run with real-time output instead of capturing
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',  # Handle encoding errors gracefully
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output in real-time
        while True:
            try:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            except UnicodeDecodeError:
                # Skip problematic lines
                continue
        
        # Wait for process to complete
        return_code = process.poll()
        
        if return_code == 0:
            logger.info(f"✅ {sport_name} download completed successfully")
            return True
        else:
            logger.error(f"❌ {sport_name} download failed with return code {return_code}")
            return False
        
    except Exception as e:
        logger.error(f"Error running {sport_name} script: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Download player images from Wikipedia for darts, tennis, and golf"
    )
    parser.add_argument(
        '--sport', 
        choices=['tennis', 'darts', 'golf', 'all'],
        default='all',
        help='Which sport to download (default: all)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip sports that already have downloaded images'
    )
    
    args = parser.parse_args()
    
    # Define scripts for each sport
    scripts = {
        'tennis': 'download_tennis_players.py',
        'darts': 'download_darts_players.py', 
        'golf': 'download_golf_players.py'
    }
    
    base_dir = Path(__file__).parent.parent
    players_dir = base_dir / "static" / "logos" / "players"
    
    logger.info("🎯 Starting Player Image Download from Wikipedia")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Players directory: {players_dir}")
    
    if args.sport == 'all':
        sports_to_run = list(scripts.keys())
    else:
        sports_to_run = [args.sport]
    
    successful_sports = []
    failed_sports = []
    
    for sport in sports_to_run:
        if args.skip_existing:
            # Check if sport directory exists and has images
            sport_dir = players_dir / sport
            if sport_dir.exists():
                # Count PNG files in subdirectories
                png_count = 0
                for subdir in sport_dir.iterdir():
                    if subdir.is_dir():
                        png_count += len(list(subdir.glob("*.png")))
                
                if png_count > 0:
                    logger.info(f"⏭️ Skipping {sport} - {png_count} images already exist")
                    continue
        
        success = run_script(scripts[sport], sport)
        if success:
            successful_sports.append(sport)
        else:
            failed_sports.append(sport)
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*60}")
    
    if successful_sports:
        logger.info(f"✅ Successful: {', '.join(successful_sports)}")
    
    if failed_sports:
        logger.info(f"❌ Failed: {', '.join(failed_sports)}")
    
    logger.info(f"\nTotal sports processed: {len(sports_to_run)}")
    logger.info(f"Successful: {len(successful_sports)}")
    logger.info(f"Failed: {len(failed_sports)}")
    
    if failed_sports:
        logger.info(f"\nTo retry failed sports, run:")
        for sport in failed_sports:
            logger.info(f"  python scripts/{scripts[sport]}")
    
    logger.info("\n🎉 Player image download process completed!")

if __name__ == "__main__":
    main() 