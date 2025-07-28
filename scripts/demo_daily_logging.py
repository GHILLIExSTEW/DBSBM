#!/usr/bin/env python3
"""
Demonstration script for daily logging configuration.
This script shows how console output is redirected to daily log files.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def demo_daily_logging():
    """Demonstrate the daily logging functionality."""

    print("Daily Logging Demonstration")
    print("=" * 40)
    print("This script demonstrates how console output is redirected to daily log files.")
    print("Only CRITICAL errors will appear in the console.")
    print("All other log messages will be written to db_logs/dbsbm_daily.log")
    print()

    # Import and configure logging
    try:
        from bot.utils.logging_config import auto_configure_logging
        auto_configure_logging()
        print("✓ Logging configured successfully")
    except Exception as e:
        print(f"✗ Failed to configure logging: {e}")
        return

    # Get logger
    logger = logging.getLogger(__name__)

    # Demonstrate different log levels
    print("\nGenerating log messages...")
    print("(These should NOT appear in the console)")

    # Info messages
    logger.info("Bot starting up...")
    logger.info("Loading configuration...")
    logger.info("Connecting to database...")

    # Warning messages
    logger.warning("API rate limit approaching")
    logger.warning("Cache miss for user data")

    # Error messages
    logger.error("Failed to fetch game data from API")
    logger.error("Database connection timeout")

    # Debug messages (should not appear in console)
    logger.debug("Processing user request")
    logger.debug("Validating bet parameters")

    print("\n✓ Log messages generated!")
    print("Check the db_logs/dbsbm_daily.log file to see the messages.")

    # Show a critical error (this WILL appear in console)
    print("\nNow generating a CRITICAL error (this WILL appear in console):")
    logger.critical("CRITICAL: Database connection lost - system shutting down")

    # Show log file info
    log_file = "db_logs/dbsbm_daily.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print(f"\nLog file contains {len(lines)} lines:")
            for i, line in enumerate(lines[-5:], 1):  # Show last 5 lines
                print(f"  {i}. {line}")

    print("\n" + "=" * 40)
    print("✓ Daily logging demonstration completed!")
    print("\nSummary:")
    print("- INFO, WARNING, ERROR, DEBUG messages → Written to log file only")
    print("- CRITICAL messages → Appear in both console and log file")
    print("- New log file created each day at midnight")
    print("- Log files kept for 30 days")

if __name__ == "__main__":
    demo_daily_logging()
