#!/usr/bin/env python3
"""
Runner script for FIFA World Cup data fetch.
This script provides a simple interface to run the FIFA World Cup data fetcher.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the parent directory to sys.path for imports
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / 'logs' / 'fifa_world_cup_runner.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def save_api_key_to_env(api_key: str):
    """Save API key to .env file."""
    env_file = BASE_DIR / '.env'
    
    try:
        # Read existing .env file if it exists
        env_content = ""
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
        
        # Check if API_KEY already exists in .env
        if 'API_KEY=' in env_content:
            # Update existing API_KEY
            lines = env_content.split('\n')
            updated_lines = []
            for line in lines:
                if line.startswith('API_KEY='):
                    updated_lines.append(f'API_KEY={api_key}')
                else:
                    updated_lines.append(line)
            env_content = '\n'.join(updated_lines)
        else:
            # Add new API_KEY
            if env_content and not env_content.endswith('\n'):
                env_content += '\n'
            env_content += f'API_KEY={api_key}\n'
        
        # Write back to .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f"SUCCESS: API key saved to {env_file}")
        
    except Exception as e:
        logger.error(f"ERROR: Failed to save API key to .env file: {e}")

def check_requirements():
    """Check if all requirements are met to run the script."""
    # Check if API key is set
    api_key = os.getenv('API_KEY')
    if not api_key:
        logger.warning("WARNING: API_KEY not found in environment variables")
        logger.info("Please enter your API-Sports API key:")
        
        # Prompt for API key
        try:
            api_key = input("API Key: ").strip()
            if not api_key:
                logger.error("ERROR: No API key provided. Exiting.")
                return False
            
            # Set the API key in environment for this session
            os.environ['API_KEY'] = api_key
            logger.info("SUCCESS: API key set for this session")
            
            # Ask if user wants to save to .env file
            save_to_env = input("Save API key to .env file for future use? (y/n): ").strip().lower()
            if save_to_env in ['y', 'yes']:
                save_api_key_to_env(api_key)
            
        except KeyboardInterrupt:
            logger.error("ERROR: User cancelled API key input. Exiting.")
            return False
        except Exception as e:
            logger.error(f"ERROR: Failed to get API key: {e}")
            return False
    
    # Check if required directories exist
    required_dirs = [
        BASE_DIR / 'config',
        BASE_DIR / 'utils',
        BASE_DIR / 'static',
        BASE_DIR / 'data',
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"ERROR: Required directory not found: {dir_path}")
            return False
    
    # Check if required files exist
    required_files = [
        BASE_DIR / 'config' / 'leagues.py',
        BASE_DIR / 'config' / 'team_mappings.py',
        BASE_DIR / 'config' / 'asset_paths.py',
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            logger.error(f"ERROR: Required file not found: {file_path}")
            return False
    
    logger.info("SUCCESS: All requirements met")
    return True

async def run_fifa_world_cup_fetch():
    """Run the FIFA World Cup data fetch script."""
    try:
        # Import the fetch script
        from scripts.fetch_fifa_world_cup_data import main as fetch_main
        
        logger.info("STARTING: FIFA World Cup data fetch...")
        await fetch_main()
        logger.info("SUCCESS: FIFA World Cup data fetch completed successfully!")
        
    except ImportError as e:
        logger.error(f"ERROR: Failed to import FIFA World Cup fetch script: {e}")
        return False
    except Exception as e:
        logger.error(f"ERROR: Error running FIFA World Cup fetch: {e}")
        return False
    
    return True

def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("FIFA World Cup Data Fetch Runner")
    logger.info("=" * 60)
    
    # Check requirements
    if not check_requirements():
        logger.error("ERROR: Requirements check failed. Exiting.")
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    logs_dir = BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Run the fetch
    success = asyncio.run(run_fifa_world_cup_fetch())
    
    if success:
        logger.info("SUCCESS: FIFA World Cup data fetch completed successfully!")
        logger.info("INFO: Check the following directories for downloaded data:")
        logger.info(f"   - Team logos: {BASE_DIR}/static/logos/teams/SOCCER/WORLDCUP/")
        logger.info(f"   - League logo: {BASE_DIR}/static/logos/leagues/SOCCER/")
        logger.info(f"   - Data files: {BASE_DIR}/data/")
        sys.exit(0)
    else:
        logger.error("ERROR: FIFA World Cup data fetch failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 