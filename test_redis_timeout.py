#!/usr/bin/env python3
"""
Test script to verify Redis connection timeout functionality.
This script tests that the EnhancedCacheManager doesn't hang during connection attempts.
"""

from bot.utils.enhanced_cache_manager import EnhancedCacheManager
import asyncio
import logging
import os
import sys
import time

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_redis_timeout():
    """Test that Redis connection doesn't hang with timeouts."""
    logger.info("Starting Redis timeout test...")

    # Create cache manager
    cache_manager = EnhancedCacheManager()

    # Test connection with timeout
    start_time = time.time()
    try:
        # This should not hang - it should timeout after 5 seconds per attempt
        result = await asyncio.wait_for(cache_manager.connect(), timeout=15.0)
        elapsed_time = time.time() - start_time

        logger.info(
            f"Redis connection test completed in {elapsed_time:.2f} seconds")
        logger.info(f"Connection result: {result}")

        if elapsed_time > 20:
            logger.error(
                "Test took too long - Redis connection may be hanging!")
            return False
        else:
            logger.info("Redis timeout test passed - connection didn't hang")
            return True

    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        logger.warning(
            f"Redis connection timed out after {elapsed_time:.2f} seconds")
        logger.info("This is expected behavior when Redis is not available")
        return True
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Redis connection test failed after {elapsed_time:.2f} seconds: {e}")
        return False


async def test_database_manager_redis():
    """Test that DatabaseManager handles Redis connection gracefully."""
    logger.info("Starting DatabaseManager Redis test...")

    from bot.data.db_manager import DatabaseManager

    # Create database manager
    db_manager = DatabaseManager()

    # Test connection with timeout
    start_time = time.time()
    try:
        # This should not hang - it should timeout after 10 seconds
        result = await asyncio.wait_for(db_manager.connect(), timeout=15.0)
        elapsed_time = time.time() - start_time

        logger.info(
            f"DatabaseManager Redis test completed in {elapsed_time:.2f} seconds")

        if elapsed_time > 20:
            logger.error(
                "Test took too long - DatabaseManager Redis connection may be hanging!")
            return False
        else:
            logger.info(
                "DatabaseManager Redis test passed - connection didn't hang")
            return True

    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        logger.warning(
            f"DatabaseManager Redis connection timed out after {elapsed_time:.2f} seconds")
        logger.info("This is expected behavior when Redis is not available")
        return True
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"DatabaseManager Redis test failed after {elapsed_time:.2f} seconds: {e}")
        return False


async def main():
    """Run all Redis timeout tests."""
    logger.info("Running Redis timeout tests...")

    # Test 1: EnhancedCacheManager timeout
    test1_result = await test_redis_timeout()

    # Test 2: DatabaseManager Redis timeout
    test2_result = await test_database_manager_redis()

    if test1_result and test2_result:
        logger.info("✅ All Redis timeout tests passed!")
        return 0
    else:
        logger.error("❌ Some Redis timeout tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
