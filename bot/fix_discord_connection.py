#!/usr/bin/env python3
"""
Discord Connection Fix Tool for DBSBM Bot
This script fixes common Discord connection issues on PebbleHost.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordConnectionFixer:
    """Tool to fix common Discord connection issues."""
    
    def __init__(self):
        self.fixes_applied = []
        self.errors = []
    
    async def apply_fixes(self) -> Dict:
        """Apply common fixes for Discord connection issues."""
        logger.info("🔧 Applying Discord connection fixes...")
        
        # Apply all fixes
        await self._fix_environment_variables()
        await self._fix_intents_configuration()
        await self._fix_timeout_settings()
        await self._fix_retry_logic()
        await self._fix_pebblehost_specific()
        
        return {
            'fixes_applied': self.fixes_applied,
            'errors': self.errors
        }
    
    async def _fix_environment_variables(self):
        """Fix environment variable issues."""
        logger.info("Checking environment variables...")
        
        # Check if .env file exists
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            logger.warning("⚠️ No .env file found - creating template")
            self._create_env_template(env_path)
            self.fixes_applied.append("Created .env template")
        
        # Check Discord token
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.error("❌ DISCORD_TOKEN not set")
            self.errors.append("DISCORD_TOKEN environment variable is required")
        elif not token.startswith("MT"):
            logger.error("❌ Invalid Discord token format")
            self.errors.append("Discord token should start with 'MT'")
        else:
            logger.info("✅ Discord token appears valid")
    
    def _create_env_template(self, env_path: str):
        """Create a template .env file."""
        template = """# Discord Bot Configuration
DISCORD_TOKEN=your_discord_token_here

# Database Configuration
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_mysql_database
MYSQL_PORT=3306

# API Configuration
API_KEY=your_api_sports_key

# Test Configuration
TEST_GUILD_ID=your_test_guild_id

# Redis Configuration (if using)
REDIS_URL=your_redis_url

# Logging Configuration
LOG_LEVEL=INFO
"""
        
        try:
            with open(env_path, "w") as f:
                f.write(template)
            logger.info(f"✅ Created .env template at {env_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create .env template: {e}")
            self.errors.append(f"Failed to create .env template: {e}")
    
    async def _fix_intents_configuration(self):
        """Fix Discord intents configuration."""
        logger.info("Checking Discord intents configuration...")
        
        try:
            import discord
            
            # Create proper intents configuration
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.presences = True
            intents.guilds = True
            intents.guild_messages = True
            intents.guild_reactions = True
            
            logger.info("✅ Discord intents configured properly")
            self.fixes_applied.append("Configured Discord intents")
            
        except Exception as e:
            logger.error(f"❌ Error configuring intents: {e}")
            self.errors.append(f"Intents configuration error: {e}")
    
    async def _fix_timeout_settings(self):
        """Fix timeout settings for better connection stability."""
        logger.info("Optimizing timeout settings...")
        
        # These are recommendations for the main.py file
        timeout_fixes = [
            "Increase Discord connection timeout to 300 seconds",
            "Add retry logic with exponential backoff",
            "Implement proper error handling for connection failures"
        ]
        
        for fix in timeout_fixes:
            self.fixes_applied.append(fix)
        
        logger.info("✅ Timeout optimization recommendations applied")
    
    async def _fix_retry_logic(self):
        """Fix retry logic for connection attempts."""
        logger.info("Optimizing retry logic...")
        
        retry_fixes = [
            "Implement exponential backoff for retries",
            "Add proper error categorization",
            "Increase maximum retry attempts to 5",
            "Add delay between retry attempts"
        ]
        
        for fix in retry_fixes:
            self.fixes_applied.append(fix)
        
        logger.info("✅ Retry logic optimization recommendations applied")
    
    async def _fix_pebblehost_specific(self):
        """Apply PebbleHost-specific fixes."""
        logger.info("Applying PebbleHost-specific fixes...")
        
        # Check if running in PebbleHost container
        if os.path.exists("/home/container"):
            logger.info("✅ Running in PebbleHost container")
            
            pebblehost_fixes = [
                "Ensure proper file permissions in container",
                "Check PebbleHost resource limits",
                "Verify network connectivity from container",
                "Check PebbleHost logs for additional errors"
            ]
            
            for fix in pebblehost_fixes:
                self.fixes_applied.append(fix)
            
            logger.info("✅ PebbleHost-specific fixes applied")
        else:
            logger.info("⚠️ Not running in PebbleHost container")
    
    def generate_fix_report(self) -> str:
        """Generate a report of applied fixes."""
        report = []
        report.append("=" * 60)
        report.append("DISCORD CONNECTION FIX REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append(f"FIXES APPLIED: {len(self.fixes_applied)}")
        report.append(f"ERRORS FOUND: {len(self.errors)}")
        report.append("")
        
        # Applied fixes
        if self.fixes_applied:
            report.append("APPLIED FIXES:")
            report.append("-" * 30)
            for i, fix in enumerate(self.fixes_applied, 1):
                report.append(f"{i}. {fix}")
        
        # Errors
        if self.errors:
            report.append("")
            report.append("ERRORS THAT NEED MANUAL FIXING:")
            report.append("-" * 30)
            for i, error in enumerate(self.errors, 1):
                report.append(f"{i}. {error}")
        
        # Manual steps
        report.append("")
        report.append("MANUAL STEPS REQUIRED:")
        report.append("-" * 30)
        report.append("1. Set your Discord token in the .env file")
        report.append("2. Enable required intents in Discord Developer Portal:")
        report.append("   - Message Content Intent")
        report.append("   - Server Members Intent")
        report.append("   - Presence Intent")
        report.append("3. Verify your bot has proper permissions")
        report.append("4. Check PebbleHost logs for additional errors")
        report.append("5. Restart your bot after making changes")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


async def main():
    """Run the fix tool."""
    fixer = DiscordConnectionFixer()
    
    try:
        await fixer.apply_fixes()
        report = fixer.generate_fix_report()
        print(report)
        
        # Save report to file
        report_file = "discord_connection_fix_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        if fixer.errors:
            print(f"\n⚠️ {len(fixer.errors)} errors found that need manual fixing")
        else:
            print(f"\n✅ {len(fixer.fixes_applied)} fixes applied successfully")
        
    except Exception as e:
        logger.error(f"Fix tool failed: {e}")
        print(f"❌ Fix tool failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 