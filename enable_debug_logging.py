#!/usr/bin/env python3
"""
Enable debug logging for DBSBM bot.
Run this script to enable detailed debug output in the console.
"""

import logging
import os
import sys

# Set environment variable for development mode
os.environ["DBSBM_ENV"] = "development"

# Configure debug logging
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
print("🚀 You can now run your bot with detailed debug output.")
print()
print("To run the bot with debug logging:")
print("python bot/main.py")
print()
print("Or set the environment variable manually:")
print("set DBSBM_ENV=development")
print("python bot/main.py")
