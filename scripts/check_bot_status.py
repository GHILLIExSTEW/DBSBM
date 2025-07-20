#!/usr/bin/env python3
"""
Script to check bot status and diagnose command loading issues.
"""

import os
import sys
import logging

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_bot_files():
    """Check if all required bot files exist."""
    bot_dir = os.path.join(os.path.dirname(__file__), '..', 'bot')
    commands_dir = os.path.join(bot_dir, 'commands')
    
    required_files = [
        'main.py',
        'commands/stats.py',
        'commands/sync_cog.py',
        'commands/admin.py',
        'commands/betting.py',
        'commands/enhanced_player_props.py',
        'commands/parlay_betting.py',
        'commands/remove_user.py',
        'commands/setid.py',
        'commands/add_user.py',
        'commands/load_logos.py',
        'commands/schedule.py',
        'commands/maintenance.py',
        'commands/odds.py',
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(bot_dir, file_path)
        if os.path.exists(full_path):
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    logger.info(f"Bot directory: {bot_dir}")
    logger.info(f"Commands directory: {commands_dir}")
    logger.info(f"Existing files: {len(existing_files)}")
    logger.info(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        logger.warning("Missing files:")
        for file in missing_files:
            logger.warning(f"  - {file}")
    else:
        logger.info("All required files exist!")
    
    return len(missing_files) == 0

def check_environment():
    """Check if environment variables are set."""
    required_vars = [
        'DISCORD_TOKEN',
        'API_KEY',
        'MYSQL_HOST',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
        'MYSQL_DB',
        'TEST_GUILD_ID'
    ]
    
    missing_vars = []
    existing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            existing_vars.append(var)
        else:
            missing_vars.append(var)
    
    logger.info(f"Environment variables:")
    logger.info(f"  Set: {len(existing_vars)}")
    logger.info(f"  Missing: {len(missing_vars)}")
    
    if missing_vars:
        logger.warning("Missing environment variables:")
        for var in missing_vars:
            logger.warning(f"  - {var}")
    else:
        logger.info("All required environment variables are set!")
    
    return len(missing_vars) == 0

def main():
    """Main function to check bot status."""
    logger.info("=== Bot Status Check ===")
    
    # Check files
    files_ok = check_bot_files()
    
    # Check environment
    env_ok = check_environment()
    
    logger.info("=== Recommendations ===")
    
    if not files_ok:
        logger.error("❌ Missing required files. Please check the file structure.")
    
    if not env_ok:
        logger.error("❌ Missing environment variables. Please check your .env file.")
    
    if files_ok and env_ok:
        logger.info("✅ All checks passed!")
        logger.info("If the bot is still having issues:")
        logger.info("1. Try using the /sync command in Discord (admin only)")
        logger.info("2. Restart the bot to reload commands")
        logger.info("3. Check the bot logs for specific error messages")
    
    logger.info("=== Download Status ===")
    logger.info("The player image download script is running in the background.")
    logger.info("This is separate from the Discord bot issues.")

if __name__ == "__main__":
    main() 