#!/usr/bin/env python3
"""
Test script to verify bot startup fixes
"""

import asyncio
import logging
import os
import sys

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

async def test_bot_startup():
    """Test the bot startup process with timeouts."""
    try:
        from main import run_bot

        logger = logging.getLogger(__name__)
        logger.info("Starting bot startup test...")

        # Set a shorter timeout for testing
        await asyncio.wait_for(run_bot(), timeout=180.0)  # 3 minutes max

    except asyncio.TimeoutError:
        print("❌ Bot startup test timed out after 3 minutes")
        return False
    except Exception as e:
        print(f"❌ Bot startup test failed: {e}")
        return False

    print("✅ Bot startup test completed successfully")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_bot_startup())
    sys.exit(0 if success else 1)
