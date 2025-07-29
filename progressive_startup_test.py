#!/usr/bin/env python3
"""
DBSBM Progressive Startup Test

This script tests the new progressive startup approach that
connects to Discord first, then initializes heavy components.
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


class ProgressiveStartupTester:
    """Test the progressive startup approach."""

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

    async def test_minimal_setup_hook(self):
        """Test the minimal setup_hook (core components only)."""
        from bot.main import BettingBot

        bot = BettingBot()

        try:
            # Test only the minimal initialization
            await bot._setup_hook_internal()
            print("✅ Minimal setup_hook completed successfully")
            return True
        except Exception as e:
            print(f"❌ Minimal setup_hook failed: {e}")
            return False
        finally:
            await bot.close()

    async def test_discord_connection_only(self):
        """Test Discord connection without heavy initialization."""
        import discord
        from discord.ext import commands

        # Create a minimal bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(f"✅ Discord connection successful: {bot.user}")
            print(f"✅ Connected to {len(bot.guilds)} guilds")
            print(f"✅ Latency: {bot.latency * 1000:.2f}ms")

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

    async def test_progressive_startup_simulation(self):
        """Test the full progressive startup process."""
        from bot.main import BettingBot

        bot = BettingBot()

        try:
            print("🔄 Testing progressive startup...")

            # Step 1: Minimal initialization
            print("Step 1: Minimal initialization...")
            await asyncio.wait_for(bot._setup_hook_internal(), timeout=60.0)
            print("✅ Minimal initialization completed")

            # Step 2: Discord connection
            print("Step 2: Discord connection...")
            token = os.getenv("DISCORD_TOKEN")

            # Create a task for Discord connection
            connection_task = asyncio.create_task(bot.start(token))

            # Wait for connection with timeout
            try:
                await asyncio.wait_for(connection_task, timeout=120.0)
                print("✅ Discord connection successful")
                return True
            except asyncio.TimeoutError:
                print("❌ Discord connection timed out")
                return False
            except Exception as e:
                print(f"❌ Discord connection failed: {e}")
                return False

        except Exception as e:
            print(f"❌ Progressive startup failed: {e}")
            return False
        finally:
            await bot.close()

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 60)
        print("📊 PROGRESSIVE STARTUP TEST RESULTS")
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
            print("  🚨 CRITICAL: Progressive startup issues detected")
        else:
            print("  ✅ Progressive startup approach working correctly")
            print("  🎯 This should resolve the bot timeout issues")

    async def run_all_tests(self):
        """Run all progressive startup tests."""
        print("🚀 DBSBM PROGRESSIVE STARTUP TESTS")
        print("=" * 60)

        # Test minimal setup_hook
        await self.test_component(
            "Minimal Setup Hook", self.test_minimal_setup_hook(), 60.0
        )

        # Test Discord connection only
        await self.test_component(
            "Discord Connection Only", self.test_discord_connection_only(), 60.0
        )

        # Test progressive startup simulation
        await self.test_component(
            "Progressive Startup", self.test_progressive_startup_simulation(), 180.0
        )

        self.print_results()


async def main():
    """Run progressive startup tests."""
    tester = ProgressiveStartupTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
