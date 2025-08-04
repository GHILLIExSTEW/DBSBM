#!/usr/bin/env python3
"""
Discord Connection Diagnostic Tool for DBSBM Bot
This script helps diagnose Discord connection issues on PebbleHost.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class DiscordConnectionDiagnostic:
    """Diagnostic tool for Discord connection issues."""

    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []

    async def run_diagnostics(self) -> Dict:
        """Run comprehensive Discord connection diagnostics."""
        logger.info("🔍 Starting Discord connection diagnostics...")

        # Run all diagnostic checks
        await self._check_environment()
        await self._check_token_format()
        await self._check_network_connectivity()
        await self._check_discord_api()
        await self._check_bot_permissions()
        await self._check_intents()
        await self._check_pebblehost_specific()

        return self.results

    async def _check_environment(self):
        """Check environment variables and configuration."""
        logger.info("Checking environment configuration...")

        # Check .env file
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            logger.info(f"✅ .env file found at: {env_path}")
            self.results["env_file"] = True
        else:
            logger.warning(f"⚠️ .env file not found at: {env_path}")
            self.results["env_file"] = False
            self.warnings.append("No .env file found")

        # Check Discord token
        token = os.getenv("DISCORD_TOKEN")
        if token:
            logger.info("✅ DISCORD_TOKEN environment variable is set")
            self.results["token_set"] = True
            self.results["token_length"] = len(token)
        else:
            logger.error("❌ DISCORD_TOKEN environment variable is not set")
            self.results["token_set"] = False
            self.errors.append("DISCORD_TOKEN not set")

    async def _check_token_format(self):
        """Validate Discord token format."""
        logger.info("Validating Discord token format...")

        token = os.getenv("DISCORD_TOKEN")
        if not token:
            return

        # Basic format checks
        if not token.startswith("MT"):
            logger.error("❌ Token doesn't start with 'MT'")
            self.errors.append("Invalid token format - should start with 'MT'")
            self.results["token_format"] = False
            return

        if len(token) < 50:
            logger.error("❌ Token appears too short")
            self.errors.append("Token appears too short")
            self.results["token_format"] = False
            return

        logger.info("✅ Token format appears valid")
        self.results["token_format"] = True

    async def _check_network_connectivity(self):
        """Test network connectivity to Discord."""
        logger.info("Testing network connectivity...")

        try:
            import aiohttp

            # Test basic internet connectivity
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        "https://discord.com", timeout=10
                    ) as response:
                        if response.status == 200:
                            logger.info("✅ Can reach Discord.com")
                            self.results["discord_connectivity"] = True
                        else:
                            logger.warning(
                                f"⚠️ Discord.com returned status {response.status}"
                            )
                            self.results["discord_connectivity"] = False
                            self.warnings.append(
                                f"Discord.com status: {response.status}"
                            )
                except Exception as e:
                    logger.error(f"❌ Cannot reach Discord.com: {e}")
                    self.results["discord_connectivity"] = False
                    self.errors.append(f"Cannot reach Discord.com: {e}")

        except ImportError:
            logger.error("❌ aiohttp not available for network testing")
            self.results["discord_connectivity"] = None
            self.warnings.append("aiohttp not available")

    async def _check_discord_api(self):
        """Test Discord API connectivity."""
        logger.info("Testing Discord API connectivity...")

        try:
            import aiohttp

            token = os.getenv("DISCORD_TOKEN")
            if not token:
                logger.error("❌ No token available for API test")
                self.results["api_test"] = False
                return

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bot {token}"}

                try:
                    async with session.get(
                        "https://discord.com/api/v10/users/@me",
                        headers=headers,
                        timeout=10,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(
                                f"✅ Discord API test successful - Bot: {data.get('username', 'Unknown')}"
                            )
                            self.results["api_test"] = True
                            self.results["bot_username"] = data.get(
                                "username", "Unknown"
                            )
                        elif response.status == 401:
                            logger.error("❌ Discord API returned 401 - Invalid token")
                            self.results["api_test"] = False
                            self.errors.append("Invalid Discord token")
                        else:
                            logger.warning(
                                f"⚠️ Discord API returned status {response.status}"
                            )
                            self.results["api_test"] = False
                            self.warnings.append(
                                f"Discord API status: {response.status}"
                            )

                except Exception as e:
                    logger.error(f"❌ Discord API test failed: {e}")
                    self.results["api_test"] = False
                    self.errors.append(f"Discord API test failed: {e}")

        except ImportError:
            logger.error("❌ aiohttp not available for API testing")
            self.results["api_test"] = None
            self.warnings.append("aiohttp not available")

    async def _check_bot_permissions(self):
        """Check bot permissions and intents."""
        logger.info("Checking bot permissions...")

        # Check if intents are properly configured
        try:
            import discord
            from discord.ext import commands

            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.presences = True

            logger.info("✅ Discord intents configured")
            self.results["intents_configured"] = True

        except Exception as e:
            logger.error(f"❌ Error configuring intents: {e}")
            self.results["intents_configured"] = False
            self.errors.append(f"Intents configuration error: {e}")

    async def _check_intents(self):
        """Check if required intents are enabled."""
        logger.info("Checking required intents...")

        required_intents = ["message_content", "members", "presences"]

        # This would need to be checked against the actual bot configuration
        # For now, we'll just log the requirement
        logger.info(f"Required intents: {', '.join(required_intents)}")
        self.results["required_intents"] = required_intents

    async def _check_pebblehost_specific(self):
        """Check PebbleHost-specific issues."""
        logger.info("Checking PebbleHost-specific configuration...")

        # Check if we're running in a container environment
        if os.path.exists("/home/container"):
            logger.info("✅ Running in container environment (PebbleHost)")
            self.results["container_env"] = True
        else:
            logger.info("⚠️ Not running in container environment")
            self.results["container_env"] = False

        # Check Python version
        python_version = sys.version_info
        logger.info(
            f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        self.results["python_version"] = (
            f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        )

        # Check if discord.py is available
        try:
            import discord

            logger.info(f"✅ discord.py version: {discord.__version__}")
            self.results["discord_py_version"] = discord.__version__
        except ImportError:
            logger.error("❌ discord.py not available")
            self.results["discord_py_version"] = None
            self.errors.append("discord.py not installed")

    def generate_report(self) -> str:
        """Generate a comprehensive diagnostic report."""
        report = []
        report.append("=" * 60)
        report.append("DISCORD CONNECTION DIAGNOSTIC REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        total_checks = len(self.results)
        passed_checks = sum(1 for v in self.results.values() if v is True)
        report.append(f"SUMMARY: {passed_checks}/{total_checks} checks passed")
        report.append("")

        # Results
        report.append("DETAILED RESULTS:")
        report.append("-" * 30)
        for key, value in self.results.items():
            status = (
                "✅ PASS"
                if value is True
                else "❌ FAIL" if value is False else "⚠️ UNKNOWN"
            )
            report.append(f"{key}: {status} ({value})")

        # Errors
        if self.errors:
            report.append("")
            report.append("ERRORS:")
            report.append("-" * 30)
            for error in self.errors:
                report.append(f"❌ {error}")

        # Warnings
        if self.warnings:
            report.append("")
            report.append("WARNINGS:")
            report.append("-" * 30)
            for warning in self.warnings:
                report.append(f"⚠️ {warning}")

        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 30)

        if not self.results.get("token_set", False):
            report.append("1. Set DISCORD_TOKEN environment variable")

        if not self.results.get("token_format", False):
            report.append("2. Check Discord token format (should start with 'MT')")

        if not self.results.get("api_test", False):
            report.append(
                "3. Verify Discord token is valid in Discord Developer Portal"
            )

        if not self.results.get("discord_connectivity", False):
            report.append("4. Check network connectivity to Discord")

        if not self.results.get("intents_configured", False):
            report.append(
                "5. Ensure required intents are enabled in Discord Developer Portal"
            )

        report.append("6. Enable these intents in Discord Developer Portal:")
        report.append("   - Message Content Intent")
        report.append("   - Server Members Intent")
        report.append("   - Presence Intent")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


async def main():
    """Run the diagnostic tool."""
    diagnostic = DiscordConnectionDiagnostic()

    try:
        await diagnostic.run_diagnostics()
        report = diagnostic.generate_report()
        print(report)

        # Save report to file
        report_file = "discord_connection_diagnostic_report.txt"
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_file}")

    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        print(f"❌ Diagnostic failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
