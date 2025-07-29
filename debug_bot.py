#!/usr/bin/env python3
"""
Run DBSBM bot with debug logging enabled.
This script sets up debug logging and runs the bot with detailed console output.
"""

import asyncio
import logging
import os
import sys

# Set environment variable for development mode
os.environ["DBSBM_ENV"] = "development"

# Configure debug logging before importing bot modules
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set specific loggers to DEBUG level
debug_loggers = [
    "bot",
    "bot.services",
    "bot.utils",
    "bot.commands",
    "bot.data",
    "bot.api",
    "__main__",
]

for logger_name in debug_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

# Suppress noisy third-party loggers but keep them at INFO
noisy_loggers = [
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "asyncio",
    "discord.gateway",
    "discord.client",
    "websockets.protocol",
]

for logger_name in noisy_loggers:
    logging.getLogger(logger_name).setLevel(logging.INFO)

print("🔧 Debug logging enabled!")
print("📝 All debug messages will now appear in the console.")
print()

# Import and run startup checks first


async def run_startup_checks():
    """Run startup checks before starting the bot."""
    try:
        from startup_checks import DBSBMStartupChecker

        checker = DBSBMStartupChecker()
        await checker.run_all_checks()
        return True
    except Exception as e:
        print(f"❌ Startup checks failed: {e}")
        logging.exception("Startup checks failed")
        return False


# Import and run the bot
if __name__ == "__main__":
    try:
        # Run startup checks first
        print("🔍 Running startup checks...")
        checks_passed = asyncio.run(run_startup_checks())

        if checks_passed:
            print("\n🚀 Starting bot with detailed debug output...")
            print()
            from bot.main import main

            main()
        else:
            print("\n❌ Startup checks failed. Please fix issues before starting bot.")
            print("💡 Run 'python startup_checks.py' for detailed diagnostics.")

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logging.exception("Bot startup failed")
