#!/usr/bin/env python3
"""
DBSBM Startup Performance Test

This script tests the startup performance of individual components
to identify bottlenecks that cause the bot to timeout.
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


class StartupPerformanceTester:
    """Test startup performance of individual components."""

    def __init__(self):
        self.results = {}
        self.timeouts = {}

    async def test_component(self, name: str, coro, timeout: float = 30.0):
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

    async def test_database_connection(self):
        """Test database connection."""
        from bot.data.db_manager import DatabaseManager

        db_manager = DatabaseManager()
        await db_manager.connect()
        await db_manager.close()

    async def test_environment_validation(self):
        """Test environment validation."""
        from bot.utils.environment_validator import EnvironmentValidator

        EnvironmentValidator.validate_all()

    async def test_cache_manager(self):
        """Test cache manager initialization."""
        from bot.utils.enhanced_cache_manager import EnhancedCacheManager

        cache_manager = EnhancedCacheManager()
        await cache_manager.initialize()
        await cache_manager.close()

    async def test_sports_api(self):
        """Test sports API initialization."""
        from bot.api.sports_api import SportsAPI

        api = SportsAPI()
        # Just test initialization, don't make actual API calls

    async def test_service_initialization(self):
        """Test individual service initialization."""
        from bot.api.sports_api import SportsAPI
        from bot.data.db_manager import DatabaseManager

        # Initialize dependencies
        db_manager = DatabaseManager()
        await db_manager.connect()

        sports_api = SportsAPI()

        # Test admin service
        from bot.services.admin_service import AdminService

        admin_service = AdminService(db_manager)
        await admin_service.start()
        await admin_service.stop()

        await db_manager.close()

    async def test_extension_loading(self):
        """Test extension loading."""
        # This would require a mock bot instance
        # For now, just test that extensions can be imported
        from bot.commands import add_user, admin

        print("✅ Extensions can be imported")

    async def run_all_tests(self):
        """Run all performance tests."""
        print("🚀 DBSBM STARTUP PERFORMANCE TESTS")
        print("=" * 50)

        tests = [
            ("Environment Validation", self.test_environment_validation, 10.0),
            ("Database Connection", self.test_database_connection, 15.0),
            ("Cache Manager", self.test_cache_manager, 10.0),
            ("Sports API", self.test_sports_api, 10.0),
            ("Service Initialization", self.test_service_initialization, 30.0),
            ("Extension Loading", self.test_extension_loading, 10.0),
        ]

        for name, test_func, timeout in tests:
            await self.test_component(name, test_func(), timeout)

        self.print_results()

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 50)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 50)

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

        print(f"\n💡 Recommendations:")
        if total_time > 60:
            print("  ⚠️ Total startup time exceeds 60 seconds")
            print("  🔧 Consider optimizing the slowest components")
        else:
            print("  ✅ Startup time is within acceptable limits")

        if self.timeouts:
            print("  🚨 Critical: Fix timed out components before deployment")


async def main():
    """Run startup performance tests."""
    tester = StartupPerformanceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
