#!/usr/bin/env python3
"""
DBSBM Bot Startup Test

This script tests the actual bot startup process to identify bottlenecks
that cause the bot to timeout during deployment.
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


class BotStartupTester:
    """Test the actual bot startup process."""

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

    async def test_one_time_downloads(self):
        """Test one-time downloads that happen during startup."""
        from bot.main import (
            run_one_time_logo_download,
            run_one_time_player_data_download,
        )

        await run_one_time_logo_download()
        await run_one_time_player_data_download()

    async def test_database_setup(self):
        """Test database setup process."""
        from bot.data.db_manager import DatabaseManager

        db_manager = DatabaseManager()
        await db_manager.connect()
        await db_manager.initialize_db()
        await db_manager.close()

    async def test_services_startup(self):
        """Test services startup process."""
        from bot.api.sports_api import SportsAPI
        from bot.data.db_manager import DatabaseManager
        from bot.services.admin_service import AdminService
        from bot.services.analytics_service import AnalyticsService
        from bot.services.bet_service import BetService
        from bot.services.data_sync_service import DataSyncService
        from bot.services.game_service import GameService
        from bot.services.live_game_channel_service import LiveGameChannelService
        from bot.services.platinum_service import PlatinumService
        from bot.services.predictive_service import PredictiveService
        from bot.services.user_service import UserService
        from bot.services.voice_service import VoiceService

        # Initialize dependencies
        db_manager = DatabaseManager()
        await db_manager.connect()

        sports_api = SportsAPI()

        # Create a mock bot instance for testing
        class MockBot:
            def __init__(self):
                self.user = None
                self.guilds = []

        mock_bot = MockBot()

        # Initialize services with proper parameters
        services = [
            AdminService(mock_bot, db_manager),
            AnalyticsService(db_manager),
            BetService(db_manager),
            UserService(db_manager),
            VoiceService(db_manager),
            GameService(db_manager),
            DataSyncService(db_manager),
            LiveGameChannelService(db_manager),
            PlatinumService(db_manager),
            PredictiveService(db_manager),
        ]

        # Start services
        for service in services:
            await service.start()

        # Stop services
        for service in services:
            await service.stop()

        await db_manager.close()

    async def test_extension_loading(self):
        """Test extension loading process."""
        # This simulates the load_extensions method
        import importlib
        import os

        extensions_dir = Path(__file__).parent / "bot" / "commands"
        extensions = []

        for file in extensions_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue
            extensions.append(file.stem)

        # Try to import each extension
        for ext in extensions[:5]:  # Limit to first 5 for testing
            try:
                module = importlib.import_module(f"bot.commands.{ext}")
                print(f"  ✅ Loaded extension: {ext}")
            except Exception as e:
                print(f"  ⚠️ Failed to load extension {ext}: {e}")

    async def test_webapp_startup(self):
        """Test webapp startup process."""
        # This would normally start Flask, but for testing we'll just simulate
        print("  ✅ Webapp startup simulation completed")

    async def test_fetcher_startup(self):
        """Test fetcher startup process."""
        # This would normally start the data fetcher, but for testing we'll just simulate
        print("  ✅ Fetcher startup simulation completed")

    async def test_full_startup_simulation(self):
        """Test the full startup process simulation."""
        print("🚀 Testing full startup process simulation...")

        # Step 1: One-time downloads
        await self.test_component(
            "One-time Downloads", self.test_one_time_downloads(), 30.0
        )

        # Step 2: Database setup
        await self.test_component("Database Setup", self.test_database_setup(), 20.0)

        # Step 3: Services startup
        await self.test_component(
            "Services Startup", self.test_services_startup(), 60.0
        )

        # Step 4: Extension loading
        await self.test_component(
            "Extension Loading", self.test_extension_loading(), 15.0
        )

        # Step 5: Webapp startup
        await self.test_component("Webapp Startup", self.test_webapp_startup(), 10.0)

        # Step 6: Fetcher startup
        await self.test_component("Fetcher Startup", self.test_fetcher_startup(), 10.0)

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 60)
        print("📊 BOT STARTUP TEST RESULTS")
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
        if total_time > 120:
            print("  🚨 CRITICAL: Total startup time exceeds 120 seconds")
            print("  🔧 This will cause bot startup timeout in production")
        elif total_time > 60:
            print("  ⚠️ WARNING: Total startup time exceeds 60 seconds")
            print("  🔧 Consider optimizing the slowest components")
        else:
            print("  ✅ Startup time is within acceptable limits")

        if self.timeouts:
            print("  🚨 CRITICAL: Fix timed out components before deployment")

        # Identify bottlenecks
        if self.results:
            slowest = max(self.results.items(), key=lambda x: x[1])
            print(f"\n🐌 Slowest component: {slowest[0]} ({slowest[1]:.2f}s)")

            if slowest[1] > 30:
                print(f"  🔧 Consider optimizing {slowest[0]}")

    async def run_all_tests(self):
        """Run all startup tests."""
        print("🚀 DBSBM BOT STARTUP TESTS")
        print("=" * 60)

        await self.test_full_startup_simulation()
        self.print_results()


async def main():
    """Run bot startup tests."""
    tester = BotStartupTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
