#!/usr/bin/env python3
"""
DBSBM Discord Startup Test

This script tests the Discord bot startup process to identify
the actual cause of the timeout during deployment.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv

    env_file = project_root / "bot" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from: {env_file}")
    else:
        print(f"⚠️ No .env file found at: {env_file}")
except ImportError:
    print("⚠️ python-dotenv not installed, skipping .env loading")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class DiscordStartupTester:
    """Test Discord bot startup process."""

    def __init__(self):
        self.results = {}
        self.timeouts = {}

    async def test_component(self, name: str, coro, timeout: float = 60.0):
        """Test a component with timeout."""
        print(f"\n🔍 Testing {name}...")
        start_time = time.time()

        try:
            await asyncio.wait_for(coro, timeout=timeout)
            duration = time.time() - start_time
            self.results[name] = duration
            print(f"✅ {name}: {duration:.2f}s")
            return True
        except asyncio.TimeoutError:
            self.timeouts[name] = timeout
            print(f"❌ {name}: TIMEOUT after {timeout}s")
            return False
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            return False

    async def test_discord_connection(self):
        """Test Discord connection without full bot startup."""
        import discord
        from discord.ext import commands

        # Create a minimal bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(f"✅ Bot logged in as {bot.user}")

        # Try to connect to Discord
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment")

        try:
            await bot.start(token)
        except Exception as e:
            print(f"❌ Discord connection failed: {e}")
            raise
        finally:
            await bot.close()

    async def test_minimal_bot_startup(self):
        """Test minimal bot startup without heavy initialization."""
        from bot.main import BettingBot

        # Create bot instance but don't start it
        bot = BettingBot()

        # Test setup_hook with timeout
        try:
            await asyncio.wait_for(bot._setup_hook_internal(), timeout=60.0)
            print("✅ Setup hook completed successfully")
        except asyncio.TimeoutError:
            print("❌ Setup hook timed out")
            raise
        except Exception as e:
            print(f"❌ Setup hook failed: {e}")
            raise
        finally:
            await bot.close()

    async def test_environment_validation(self):
        """Test environment validation."""
        from bot.utils.environment_validator import EnvironmentValidator

        is_valid, errors = EnvironmentValidator.validate_all()
        if not is_valid:
            print(f"❌ Environment validation failed: {errors}")
            raise ValueError("Environment validation failed")
        print("✅ Environment validation passed")

    async def test_database_connection(self):
        """Test database connection."""
        from bot.data.db_manager import DatabaseManager

        db_manager = DatabaseManager()
        await db_manager.connect()
        await db_manager.close()

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 60)
        print("📊 DISCORD STARTUP TEST RESULTS")
        print("=" * 60)

        total_time = sum(self.results.values())
        print(f"Total successful tests: {len(self.results)}")
        print(f"Total time: {total_time:.2f}s")

        if self.results:
            print("\n✅ Successful Tests:")
            for name, duration in sorted(
                self.results.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {name}: {duration:.2f}s")

        if self.timeouts:
            print("\n❌ Timed Out Tests:")
            for name, timeout in self.timeouts.items():
                print(f"  {name}: >{timeout}s")

        print(f"\n💡 Analysis:")
        if self.timeouts:
            print("  🚨 CRITICAL: Found timeout issues")
            print("  🔧 These components are causing bot startup failure")
        else:
            print("  ✅ No timeout issues detected")
            print("  🔍 The timeout may be happening during Discord connection")

    async def run_all_tests(self):
        """Run all Discord startup tests."""
        print("🚀 DBSBM DISCORD STARTUP TESTS")
        print("=" * 60)

        # Test environment and database first
        await self.test_component(
            "Environment Validation", self.test_environment_validation(), 10.0
        )
        await self.test_component(
            "Database Connection", self.test_database_connection(), 15.0
        )

        # Test minimal bot startup
        await self.test_component(
            "Minimal Bot Startup", self.test_minimal_bot_startup(), 60.0
        )

        # Test Discord connection (this might timeout)
        await self.test_component(
            "Discord Connection", self.test_discord_connection(), 30.0
        )

        self.print_results()


async def main():
    """Run Discord startup tests."""
    tester = DiscordStartupTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
