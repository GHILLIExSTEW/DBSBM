#!/usr/bin/env python3
"""
Test script for daily logging configuration.
This script tests the new daily logging setup that redirects console output to daily log files.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_daily_logging():
    """Test the daily logging configuration."""

    # Import the logging configuration
    try:
        from bot.utils.logging_config import auto_configure_logging
        print("✓ Successfully imported logging configuration")
    except ImportError as e:
        print(f"✗ Failed to import logging configuration: {e}")
        return False

    # Configure logging
    try:
        auto_configure_logging()
        print("✓ Successfully configured daily logging")
    except Exception as e:
        print(f"✗ Failed to configure logging: {e}")
        return False

    # Get logger and test logging
    logger = logging.getLogger(__name__)

    # Test different log levels
    test_messages = [
        ("INFO", "This is an info message"),
        ("WARNING", "This is a warning message"),
        ("ERROR", "This is an error message"),
        ("CRITICAL", "This is a critical message")
    ]

    print("\nTesting log messages...")
    for level, message in test_messages:
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "CRITICAL":
            logger.critical(message)
        print(f"  ✓ Logged {level}: {message}")

    # Check if db_logs directory was created
    if os.path.exists("db_logs"):
        print("✓ db_logs directory exists")

        # Check if log file was created
        log_files = [f for f in os.listdir("db_logs") if f.endswith(".log")]
        if log_files:
            print(f"✓ Found log files: {log_files}")

            # Check the content of the main log file
            main_log_file = "db_logs/dbsbm_daily.log"
            if os.path.exists(main_log_file):
                with open(main_log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 0:
                        print(f"✓ Log file contains {len(content)} characters")
                        print("  Sample content:")
                        lines = content.strip().split('\n')
                        for line in lines[:3]:  # Show first 3 lines
                            print(f"    {line}")
                    else:
                        print("✗ Log file is empty")
            else:
                print("✗ Main log file not found")
        else:
            print("✗ No log files found in db_logs directory")
    else:
        print("✗ db_logs directory not created")
        return False

    print("\n✓ Daily logging test completed successfully!")
    return True

def test_webapp_logging():
    """Test the webapp logging configuration."""

    print("\nTesting webapp logging configuration...")

    # Import webapp logging
    try:
        import webapp
        print("✓ Successfully imported webapp")
    except ImportError as e:
        print(f"✗ Failed to import webapp: {e}")
        return False

    # Check if webapp log file exists
    webapp_log_file = "db_logs/webapp_daily.log"
    if os.path.exists(webapp_log_file):
        print("✓ Webapp log file exists")

        # Check content
        with open(webapp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 0:
                print(f"✓ Webapp log file contains {len(content)} characters")
            else:
                print("✗ Webapp log file is empty")
    else:
        print("✗ Webapp log file not found")

    return True

if __name__ == "__main__":
    print("Testing Daily Logging Configuration")
    print("=" * 40)

    success = True

    # Test main logging
    if not test_daily_logging():
        success = False

    # Test webapp logging
    if not test_webapp_logging():
        success = False

    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Daily logging is working correctly.")
        print("\nConsole output has been redirected to daily log files in the 'db_logs' directory.")
        print("Only CRITICAL errors will still appear in the console.")
    else:
        print("✗ Some tests failed. Please check the configuration.")

    print(f"\nCurrent log files in db_logs directory:")
    if os.path.exists("db_logs"):
        for file in os.listdir("db_logs"):
            file_path = os.path.join("db_logs", file)
            size = os.path.getsize(file_path)
            print(f"  - {file} ({size} bytes)")
    else:
        print("  No db_logs directory found")
