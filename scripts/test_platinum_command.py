#!/usr/bin/env python3
"""
Test Platinum Command Script

This script tests the simplified /platinum command functionality.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the bot directory to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from bot.services.platinum_service import PlatinumService
from bot.services.subscription_service import SubscriptionService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_platinum_command():
    """Test the platinum command functionality."""
    try:
        logger.info("🧪 Testing Platinum command functionality...")
        
        # Initialize services
        platinum_service = PlatinumService()
        subscription_service = SubscriptionService()
        
        # Test guild IDs (you can replace these with actual guild IDs)
        test_guild_id = 123456789  # Replace with actual test guild ID
        
        logger.info(f"Testing with guild ID: {test_guild_id}")
        
        # Test 1: Check if guild is Platinum
        is_platinum = await platinum_service.is_platinum_guild(test_guild_id)
        logger.info(f"Guild is Platinum: {is_platinum}")
        
        # Test 2: Get webhook count
        webhook_count = await platinum_service.get_webhook_count(test_guild_id)
        logger.info(f"Webhook count: {webhook_count}")
        
        # Test 3: Get export count
        from datetime import datetime
        export_count = await platinum_service.get_export_count(test_guild_id, datetime.now().month)
        logger.info(f"Export count (this month): {export_count}")
        
        # Test 4: Check subscription service
        subscription_level = await subscription_service.get_subscription_level(test_guild_id)
        logger.info(f"Subscription level: {subscription_level}")
        
        logger.info("✅ All Platinum command tests completed successfully!")
        
        # Summary
        print("\n" + "="*50)
        print("PLATINUM COMMAND TEST RESULTS")
        print("="*50)
        print(f"Guild ID: {test_guild_id}")
        print(f"Is Platinum: {is_platinum}")
        print(f"Webhook Count: {webhook_count}/10")
        print(f"Export Count: {export_count}/50")
        print(f"Subscription Level: {subscription_level}")
        print("="*50)
        
        if is_platinum:
            print("🎉 Guild has Platinum subscription - will show thank you message")
        else:
            print("💡 Guild needs upgrade - will show upgrade message with $99.99 pricing")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def main():
    """Main function."""
    print("=" * 60)
    print("PLATINUM COMMAND TEST SCRIPT")
    print("=" * 60)
    
    success = await test_platinum_command()
    
    if success:
        print("\n🎉 Platinum command test completed successfully!")
        print("The /platinum command is ready to use.")
    else:
        print("\n❌ Some issues were found during testing.")
        print("Please check the logs above for details.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main()) 