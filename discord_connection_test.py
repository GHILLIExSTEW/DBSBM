#!/usr/bin/env python3
"""
DBSBM Discord Connection Test

This script specifically tests Discord connection to identify
the root cause of the connection timeout issue.
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


class DiscordConnectionTester:
    """Test Discord connection specifically."""

    def __init__(self):
        self.results = {}
        self.timeouts = {}

    async def test_minimal_discord_connection(self):
        """Test minimal Discord connection without bot features."""
        import discord
        from discord.ext import commands

        # Create a minimal bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(f"✅ Minimal bot logged in as {bot.user}")
            print(f"✅ Connected to {len(bot.guilds)} guilds")
            print(f"✅ Latency: {bot.latency * 1000:.2f}ms")

        # Try to connect to Discord
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment")

        try:
            print("🔄 Attempting minimal Discord connection...")
            await bot.start(token)
        except Exception as e:
            print(f"❌ Minimal Discord connection failed: {e}")
            raise
        finally:
            await bot.close()

    async def test_discord_gateway_connection(self):
        """Test Discord gateway connection specifically."""
        import json

        import aiohttp

        # Test Discord Gateway endpoint
        gateway_url = "https://discord.com/api/v10/gateway"

        try:
            print("🔄 Testing Discord Gateway endpoint...")
            async with aiohttp.ClientSession() as session:
                async with session.get(gateway_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(
                            f"✅ Gateway endpoint accessible: {data.get('url', 'Unknown')}"
                        )
                        return True
                    else:
                        print(f"❌ Gateway endpoint returned status {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Gateway endpoint test failed: {e}")
            return False

    async def test_discord_api_connection(self):
        """Test Discord API connection."""
        import aiohttp

        # Test Discord API endpoint
        api_url = "https://discord.com/api/v10/users/@me"
        token = os.getenv("DISCORD_TOKEN")

        if not token:
            print("❌ DISCORD_TOKEN not found")
            return False

        headers = {"Authorization": f"Bot {token}"}

        try:
            print("🔄 Testing Discord API endpoint...")
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(
                            f"✅ API endpoint accessible: {data.get('username', 'Unknown')}"
                        )
                        return True
                    else:
                        print(f"❌ API endpoint returned status {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
            return False

    async def test_network_connectivity(self):
        """Test basic network connectivity."""
        import aiohttp

        # Test basic internet connectivity
        test_urls = [
            "https://www.google.com",
            "https://discord.com",
            "https://api.discord.com",
        ]

        results = {}

        for url in test_urls:
            try:
                print(f"🔄 Testing connectivity to {url}...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            print(f"✅ {url}: Accessible")
                            results[url] = True
                        else:
                            print(f"⚠️ {url}: Status {response.status}")
                            results[url] = False
            except Exception as e:
                print(f"❌ {url}: Failed - {e}")
                results[url] = False

        return results

    async def test_full_bot_connection(self):
        """Test full bot connection with timeout monitoring."""
        from bot.main import BettingBot

        # Create bot instance
        bot = BettingBot()

        try:
            print("🔄 Testing full bot connection...")
            start_time = time.time()

            # Initialize core components first
            print("Step 1: Initializing core components...")
            await asyncio.wait_for(bot._setup_hook_internal(), timeout=60.0)
            print("✅ Core components initialized")

            # Test Discord connection with detailed monitoring
            print("Step 2: Testing Discord connection...")
            token = os.getenv("DISCORD_TOKEN")

            connection_start = time.time()
            await asyncio.wait_for(bot.start(token), timeout=300.0)
            connection_time = time.time() - connection_start

            print(f"✅ Full bot connection successful in {connection_time:.2f}s")
            return True

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ Full bot connection timed out after {elapsed:.2f}s")
            return False
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Full bot connection failed after {elapsed:.2f}s: {e}")
            return False
        finally:
            await bot.close()

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 60)
        print("📊 DISCORD CONNECTION TEST RESULTS")
        print("=" * 60)

        if self.results:
            print("\n✅ Successful Tests:")
            for name, duration in self.results.items():
                print(f"  {name}: {duration:.2f}s")

        if self.timeouts:
            print("\n❌ Timed Out Tests:")
            for name, timeout in self.timeouts.items():
                print(f"  {name}: >{timeout}s")

        print(f"\n💡 Recommendations:")
        if self.timeouts:
            print("  🚨 CRITICAL: Discord connection issues detected")
            print("  🔧 Check network connectivity and Discord API status")
        else:
            print("  ✅ Discord connection tests passed")

    async def run_all_tests(self):
        """Run all Discord connection tests."""
        print("🚀 DBSBM DISCORD CONNECTION TESTS")
        print("=" * 60)

        # Test network connectivity first
        print("\n🔍 Testing network connectivity...")
        network_results = await self.test_network_connectivity()

        # Test Discord gateway
        print("\n🔍 Testing Discord Gateway...")
        gateway_success = await self.test_discord_gateway_connection()

        # Test Discord API
        print("\n🔍 Testing Discord API...")
        api_success = await self.test_discord_api_connection()

        # Test minimal Discord connection
        print("\n🔍 Testing minimal Discord connection...")
        try:
            start_time = time.time()
            await self.test_minimal_discord_connection()
            duration = time.time() - start_time
            self.results["Minimal Discord Connection"] = duration
        except Exception as e:
            print(f"❌ Minimal Discord connection failed: {e}")

        # Test full bot connection
        print("\n🔍 Testing full bot connection...")
        try:
            start_time = time.time()
            success = await self.test_full_bot_connection()
            if success:
                duration = time.time() - start_time
                self.results["Full Bot Connection"] = duration
        except Exception as e:
            print(f"❌ Full bot connection failed: {e}")

        self.print_results()


async def main():
    """Run Discord connection tests."""
    tester = DiscordConnectionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
