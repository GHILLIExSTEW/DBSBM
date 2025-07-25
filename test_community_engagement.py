#!/usr/bin/env python3
"""
Comprehensive Community Engagement Testing Script
Tests all community engagement features to ensure they work correctly.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "bot"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class CommunityEngagementTester:
    def __init__(self):
        self.test_results = {}
        self.db_manager = None
        self.community_events_service = None
        self.community_analytics_service = None

    async def setup(self):
        """Initialize testing environment."""
        logger.info("🔧 Setting up Community Engagement Testing Environment...")

        try:
            # Import required modules
            from bot.data.db_manager import DatabaseManager
            from bot.services.community_analytics import CommunityAnalyticsService
            from bot.services.community_events import CommunityEventsService

            # Initialize database manager
            self.db_manager = DatabaseManager()
            await self.db_manager.connect()

            # Initialize community services
            self.community_events_service = CommunityEventsService(
                None, self.db_manager
            )
            self.community_analytics_service = CommunityAnalyticsService(
                None, self.db_manager
            )

            logger.info("✅ Testing environment setup complete")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup testing environment: {e}")
            return False

    async def cleanup(self):
        """Clean up testing environment."""
        if self.db_manager:
            await self.db_manager.close()
        logger.info("🧹 Testing environment cleaned up")

    async def test_database_tables(self):
        """Test that all community engagement database tables exist."""
        logger.info("🗄️ Testing Database Tables...")

        required_tables = [
            "community_metrics",
            "community_achievements",
            "user_metrics",
            "community_events",
            "bet_reactions",
        ]

        for table in required_tables:
            try:
                # Get a connection from the pool
                async with self.db_manager._pool.acquire() as conn:
                    exists = await self.db_manager.table_exists(conn, table)
                    self.test_results[f"table_{table}"] = exists
                    status = "✅" if exists else "❌"
                    logger.info(
                        f"{status} Table '{table}': {'EXISTS' if exists else 'MISSING'}"
                    )
            except Exception as e:
                self.test_results[f"table_{table}"] = False
                logger.error(f"❌ Error checking table '{table}': {e}")

        return all(
            self.test_results.get(f"table_{table}", False) for table in required_tables
        )

    async def test_community_metrics_tracking(self):
        """Test community metrics tracking functionality."""
        logger.info("📊 Testing Community Metrics Tracking...")

        try:
            # Test metric tracking
            guild_id = 123456789
            await self.community_analytics_service.track_metric(
                guild_id, "test_metric", 1.0
            )

            # Verify metric was recorded
            query = """
                SELECT metric_value FROM community_metrics
                WHERE guild_id = %s AND metric_type = 'test_metric'
                ORDER BY recorded_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id,))

            success = result is not None and result["metric_value"] == 1.0
            self.test_results["metrics_tracking"] = success

            if success:
                logger.info("✅ Community metrics tracking working")
            else:
                logger.error("❌ Community metrics tracking failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing metrics tracking: {e}")
            self.test_results["metrics_tracking"] = False
            return False

    async def test_user_metrics_tracking(self):
        """Test user metrics tracking functionality."""
        logger.info("👤 Testing User Metrics Tracking...")

        try:
            guild_id = 123456789
            user_id = 987654321

            # Test user metric tracking
            await self.community_analytics_service.track_user_metric(
                guild_id, user_id, "test_user_metric", 5.0
            )

            # Verify user metric was recorded
            query = """
                SELECT metric_value FROM user_metrics
                WHERE guild_id = %s AND user_id = %s AND metric_type = 'test_user_metric'
                ORDER BY recorded_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))

            success = result is not None and result["metric_value"] >= 5.0
            self.test_results["user_metrics_tracking"] = success

            if success:
                logger.info("✅ User metrics tracking working")
            else:
                logger.error("❌ User metrics tracking failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing user metrics tracking: {e}")
            self.test_results["user_metrics_tracking"] = False
            return False

    async def test_achievement_system(self):
        """Test achievement system functionality."""
        logger.info("🏆 Testing Achievement System...")

        try:
            guild_id = 123456789
            user_id = 987654321

            # Test achievement granting
            await self.community_analytics_service.grant_achievement(
                guild_id, user_id, "test_achievement"
            )

            # Verify achievement was granted
            query = """
                SELECT achievement_name FROM community_achievements
                WHERE guild_id = %s AND user_id = %s AND achievement_type = 'test_achievement'
                ORDER BY earned_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))

            success = result is not None
            self.test_results["achievement_system"] = success

            if success:
                logger.info("✅ Achievement system working")
            else:
                logger.error("❌ Achievement system failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing achievement system: {e}")
            self.test_results["achievement_system"] = False
            return False

    async def test_reaction_tracking(self):
        """Test reaction tracking functionality."""
        logger.info("👍 Testing Reaction Tracking...")

        try:
            guild_id = 123456789
            user_id = 987654321
            bet_serial = 1001
            emoji = "🔥"

            # Test reaction activity tracking
            await self.community_analytics_service.track_reaction_activity(
                guild_id, user_id, bet_serial, emoji
            )

            # Verify reaction metrics were tracked
            query = """
                SELECT metric_value FROM user_metrics
                WHERE guild_id = %s AND user_id = %s AND metric_type = 'total_reactions'
                ORDER BY recorded_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))

            success = result is not None and result["metric_value"] > 0
            self.test_results["reaction_tracking"] = success

            if success:
                logger.info("✅ Reaction tracking working")
            else:
                logger.error("❌ Reaction tracking failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing reaction tracking: {e}")
            self.test_results["reaction_tracking"] = False
            return False

    async def test_community_events(self):
        """Test community events functionality."""
        logger.info("🎉 Testing Community Events...")

        try:
            guild_id = 123456789

            # Test event tracking
            await self.community_events_service.track_event(
                guild_id, "test", "Test Event"
            )

            # Verify event was tracked
            query = """
                SELECT event_name FROM community_events
                WHERE guild_id = %s AND event_type = 'test'
                ORDER BY started_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id,))

            success = result is not None and result["event_name"] == "Test Event"
            self.test_results["community_events"] = success

            if success:
                logger.info("✅ Community events working")
            else:
                logger.error("❌ Community events failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing community events: {e}")
            self.test_results["community_events"] = False
            return False

    async def test_leaderboard_data(self):
        """Test leaderboard data generation."""
        logger.info("🏅 Testing Leaderboard Data...")

        try:
            guild_id = 123456789

            # Test leaderboard data retrieval
            leaderboard_data = await self.community_analytics_service.get_leaderboard(
                guild_id, "reactions", 5
            )

            success = isinstance(leaderboard_data, list)
            self.test_results["leaderboard_data"] = success

            if success:
                logger.info("✅ Leaderboard data generation working")
            else:
                logger.error("❌ Leaderboard data generation failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing leaderboard data: {e}")
            self.test_results["leaderboard_data"] = False
            return False

    async def test_community_health_metrics(self):
        """Test community health metrics."""
        logger.info("❤️ Testing Community Health Metrics...")

        try:
            guild_id = 123456789

            # Test community health retrieval
            health_metrics = (
                await self.community_analytics_service.get_community_health(guild_id, 7)
            )

            success = isinstance(health_metrics, list)
            self.test_results["community_health"] = success

            if success:
                logger.info("✅ Community health metrics working")
            else:
                logger.error("❌ Community health metrics failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing community health metrics: {e}")
            self.test_results["community_health"] = False
            return False

    async def test_achievement_checking(self):
        """Test achievement checking functionality."""
        logger.info("🔍 Testing Achievement Checking...")

        try:
            guild_id = 123456789
            user_id = 987654321

            # Test achievement checking
            await self.community_analytics_service.check_reaction_achievements(
                guild_id, user_id
            )

            # This should not raise an exception
            success = True
            self.test_results["achievement_checking"] = success

            if success:
                logger.info("✅ Achievement checking working")
            else:
                logger.error("❌ Achievement checking failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing achievement checking: {e}")
            self.test_results["achievement_checking"] = False
            return False

    async def test_command_tracking(self):
        """Test command tracking functionality."""
        logger.info("⌨️ Testing Command Tracking...")

        try:
            guild_id = 123456789
            user_id = 987654321
            command_name = "test_command"

            # Test command tracking
            await self.community_analytics_service.track_community_command(
                guild_id, user_id, command_name
            )

            # Verify command was tracked
            query = """
                SELECT metric_value FROM user_metrics
                WHERE guild_id = %s AND user_id = %s AND metric_type = 'commands_test_command'
                ORDER BY recorded_at DESC LIMIT 1
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))

            success = result is not None and result["metric_value"] >= 1.0
            self.test_results["command_tracking"] = success

            if success:
                logger.info("✅ Command tracking working")
            else:
                logger.error("❌ Command tracking failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing command tracking: {e}")
            self.test_results["command_tracking"] = False
            return False

    async def test_event_scheduling(self):
        """Test event scheduling functionality."""
        logger.info("📅 Testing Event Scheduling...")

        try:
            # Test daily event scheduling
            await self.community_events_service.schedule_daily_events()

            # This should not raise an exception
            success = True
            self.test_results["event_scheduling"] = success

            if success:
                logger.info("✅ Event scheduling working")
            else:
                logger.error("❌ Event scheduling failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing event scheduling: {e}")
            self.test_results["event_scheduling"] = False
            return False

    async def test_engagement_summary(self):
        """Test engagement summary generation."""
        logger.info("📈 Testing Engagement Summary...")

        try:
            guild_id = 123456789

            # Test engagement summary
            summary = await self.community_analytics_service.get_engagement_summary(
                guild_id, 7
            )

            success = isinstance(summary, dict)
            self.test_results["engagement_summary"] = success

            if success:
                logger.info("✅ Engagement summary working")
            else:
                logger.error("❌ Engagement summary failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing engagement summary: {e}")
            self.test_results["engagement_summary"] = False
            return False

    async def run_all_tests(self):
        """Run all community engagement tests."""
        logger.info("🚀 Starting Comprehensive Community Engagement Testing...")

        # Setup
        if not await self.setup():
            logger.error("❌ Failed to setup testing environment")
            return False

        try:
            # Run all tests
            tests = [
                ("Database Tables", self.test_database_tables),
                ("Community Metrics Tracking", self.test_community_metrics_tracking),
                ("User Metrics Tracking", self.test_user_metrics_tracking),
                ("Achievement System", self.test_achievement_system),
                ("Reaction Tracking", self.test_reaction_tracking),
                ("Community Events", self.test_community_events),
                ("Leaderboard Data", self.test_leaderboard_data),
                ("Community Health Metrics", self.test_community_health_metrics),
                ("Achievement Checking", self.test_achievement_checking),
                ("Command Tracking", self.test_command_tracking),
                ("Event Scheduling", self.test_event_scheduling),
                ("Engagement Summary", self.test_engagement_summary),
            ]

            for test_name, test_func in tests:
                logger.info(f"\n{'='*50}")
                logger.info(f"Running Test: {test_name}")
                logger.info(f"{'='*50}")

                try:
                    await test_func()
                except Exception as e:
                    logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
                    self.test_results[test_name.lower().replace(" ", "_")] = False

            # Generate test report
            await self.generate_test_report()

        finally:
            await self.cleanup()

    async def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info(f"\n{'='*60}")
        logger.info("📋 COMMUNITY ENGAGEMENT TEST REPORT")
        logger.info(f"{'='*60}")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        logger.info(f"\n{'='*60}")
        logger.info("DETAILED RESULTS:")
        logger.info(f"{'='*60}")

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")

        if failed_tests == 0:
            logger.info(
                f"\n🎉 ALL TESTS PASSED! Community engagement system is ready for production!"
            )
        else:
            logger.info(
                f"\n⚠️  {failed_tests} tests failed. Please review the errors above."
            )

        logger.info(f"\n{'='*60}")


async def main():
    """Main testing function."""
    tester = CommunityEngagementTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
