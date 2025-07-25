#!/usr/bin/env python3
"""
Quick Bot Loading Verification Script
Verifies that all community engagement commands load correctly.
"""

import asyncio
import logging
import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "bot"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_bot_loading():
    """Verify that the bot loads all community engagement commands."""
    logger.info("🔍 Verifying Bot Command Loading...")

    try:
        # Import the bot
        from bot.main import BettingBot

        # Create bot instance
        bot = BettingBot()

        # Load extensions
        await bot.load_extensions()

        # Get all loaded commands
        commands = bot.tree.get_commands()
        command_names = [cmd.name for cmd in commands]

        logger.info(f"✅ Bot loaded successfully!")
        logger.info(f"📋 Total commands loaded: {len(commands)}")

        # Check for community engagement commands
        community_commands = [
            "discuss",
            "funfact",
            "celebrate",
            "encourage",
            "help_community",
            "thanks",
            "shoutout",
            "poll",
            "community_leaderboard",
            "my_achievements",
            "community_stats",
        ]

        logger.info(f"\n🔍 Checking Community Engagement Commands:")
        logger.info(f"{'='*50}")

        found_commands = []
        missing_commands = []

        for cmd_name in community_commands:
            if cmd_name in command_names:
                found_commands.append(cmd_name)
                logger.info(f"✅ {cmd_name}")
            else:
                missing_commands.append(cmd_name)
                logger.info(f"❌ {cmd_name}")

        logger.info(f"\n📊 Summary:")
        logger.info(
            f"✅ Found: {len(found_commands)}/{len(community_commands)} community commands"
        )
        logger.info(f"❌ Missing: {len(missing_commands)} commands")

        if missing_commands:
            logger.warning(f"⚠️  Missing commands: {', '.join(missing_commands)}")
        else:
            logger.info("🎉 All community engagement commands loaded successfully!")

        # Show all available commands
        logger.info(f"\n📋 All Available Commands:")
        logger.info(f"{'='*50}")
        for cmd_name in sorted(command_names):
            logger.info(f"• {cmd_name}")

        return len(missing_commands) == 0

    except Exception as e:
        logger.error(f"❌ Error verifying bot loading: {e}")
        return False


async def main():
    """Main verification function."""
    success = await verify_bot_loading()

    if success:
        logger.info("\n🎉 Bot verification completed successfully!")
        logger.info("✅ All community engagement features are ready for testing!")
    else:
        logger.error("\n❌ Bot verification failed!")
        logger.error("⚠️  Please check the errors above and fix any issues.")


if __name__ == "__main__":
    asyncio.run(main())
