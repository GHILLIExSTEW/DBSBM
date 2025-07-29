#!/usr/bin/env python3
"""
DBSBM Startup Checks

This script runs comprehensive startup checks including:
- Health checks for all services
- Environment validation
- Database connectivity
- Cache system status
- API connectivity
- Security checks
- Performance baseline

Run this before starting the bot to ensure everything is working properly.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Set environment variable for development mode
os.environ["DBSBM_ENV"] = "development"


class DBSBMStartupChecker:
    """Comprehensive startup checker for DBSBM system."""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            "environment": {},
            "health_checks": {},
            "security": {},
            "performance": {},
            "recommendations": [],
        }

    async def run_all_checks(self):
        """Run all startup checks."""
        logger.info("🚀 Starting DBSBM startup checks...")
        print("=" * 60)
        print("🔍 DBSBM STARTUP CHECKS")
        print("=" * 60)

        # Environment checks
        await self.check_environment()

        # Health checks
        await self.run_health_checks()

        # Security checks
        await self.check_security()

        # Performance checks
        await self.check_performance()

        # Generate recommendations
        self.generate_recommendations()

        # Print final report
        self.print_final_report()

    async def check_environment(self):
        """Check environment configuration."""
        logger.info("🔧 Checking environment configuration...")
        print("\n📋 ENVIRONMENT CHECKS")
        print("-" * 30)

        env_checks = {}

        # Check .env file
        env_file = self.project_root / "bot" / ".env"
        if env_file.exists():
            env_checks[".env File"] = "✅ Exists"
            logger.debug(f"Found .env file at: {env_file}")
        else:
            env_checks[".env File"] = "❌ Missing"
            logger.error("No .env file found")

        # Check required environment variables
        required_vars = ["DISCORD_TOKEN", "MYSQL_PASSWORD", "API_KEY", "REDIS_URL"]

        for var in required_vars:
            if os.getenv(var):
                env_checks[f"{var}"] = "✅ Set"
                logger.debug(f"Environment variable {var} is set")
            else:
                env_checks[f"{var}"] = "❌ Missing"
                logger.warning(f"Environment variable {var} is not set")

        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 9):
            env_checks["Python Version"] = (
                f"✅ {python_version.major}.{python_version.minor}.{python_version.micro}"
            )
        else:
            env_checks["Python Version"] = (
                f"❌ {python_version.major}.{python_version.minor}.{python_version.micro} (3.9+ required)"
            )

        # Check project structure
        required_dirs = ["bot", "bot/services", "bot/utils", "bot/commands"]
        for dir_path in required_dirs:
            if (self.project_root / dir_path).exists():
                env_checks[f"Directory: {dir_path}"] = "✅ Exists"
            else:
                env_checks[f"Directory: {dir_path}"] = "❌ Missing"

        self.results["environment"] = env_checks

        # Print environment results
        for check, status in env_checks.items():
            print(f"  {check}: {status}")

    async def run_health_checks(self):
        """Run comprehensive health checks."""
        logger.info("🏥 Running health checks...")
        print("\n🏥 HEALTH CHECKS")
        print("-" * 30)

        try:
            # Import health checker
            from bot.utils.health_checker import run_system_health_check

            # Run health checks
            health_results = await run_system_health_check()

            if health_results:
                for service, result in health_results.items():
                    if isinstance(result, dict):
                        status = result.get("status", "unknown")
                        response_time = result.get("response_time", 0)
                        error = result.get("error_message")

                        if status == "healthy":
                            print(f"  {service}: ✅ Healthy ({response_time:.2f}s)")
                            logger.debug(
                                f"Health check passed for {service}: {response_time:.2f}s"
                            )
                        elif status == "degraded":
                            print(f"  {service}: ⚠️ Degraded ({response_time:.2f}s)")
                            logger.warning(
                                f"Health check degraded for {service}: {error}"
                            )
                        else:
                            print(f"  {service}: ❌ Unhealthy ({response_time:.2f}s)")
                            logger.error(f"Health check failed for {service}: {error}")
                    else:
                        print(f"  {service}: ❓ Unknown result")

                self.results["health_checks"] = health_results
            else:
                print("  ❌ No health check results available")
                logger.error("No health check results returned")

        except Exception as e:
            print(f"  ❌ Health checks failed: {e}")
            logger.exception("Health checks failed")

    async def check_security(self):
        """Check security configuration."""
        logger.info("🔒 Checking security configuration...")
        print("\n🔒 SECURITY CHECKS")
        print("-" * 30)

        security_checks = {}

        # Check for hardcoded credentials
        try:
            from scripts.status_check import DBSBMStatusChecker

            checker = DBSBMStatusChecker()
            hardcoded = checker._check_hardcoded_credentials()

            if hardcoded:
                security_checks["Hardcoded Credentials"] = (
                    f"❌ Found {len(hardcoded)} instances"
                )
                logger.warning(f"Found hardcoded credentials in: {hardcoded}")
            else:
                security_checks["Hardcoded Credentials"] = "✅ None found"
                logger.debug("No hardcoded credentials found")
        except Exception as e:
            security_checks["Hardcoded Credentials"] = f"❓ Error: {e}"
            logger.error(f"Error checking hardcoded credentials: {e}")

        # Check file permissions
        sensitive_files = [".env", "bot/.env"]
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Check if file is readable by others
                    stat = full_path.stat()
                    if stat.st_mode & 0o077:  # Others can read/write/execute
                        security_checks[f"File Permissions: {file_path}"] = (
                            "❌ Too permissive"
                        )
                        logger.warning(
                            f"File {file_path} has overly permissive permissions"
                        )
                    else:
                        security_checks[f"File Permissions: {file_path}"] = "✅ Secure"
                        logger.debug(f"File {file_path} has secure permissions")
                except Exception as e:
                    security_checks[f"File Permissions: {file_path}"] = f"❓ Error: {e}"
            else:
                security_checks[f"File Permissions: {file_path}"] = "⚠️ File not found"

        self.results["security"] = security_checks

        # Print security results
        for check, status in security_checks.items():
            print(f"  {check}: {status}")

    async def check_performance(self):
        """Check performance baseline."""
        logger.info("⚡ Checking performance baseline...")
        print("\n⚡ PERFORMANCE CHECKS")
        print("-" * 30)

        perf_checks = {}

        # Check memory usage
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent < 80:
                perf_checks["Memory Usage"] = f"✅ {memory_percent:.1f}%"
            else:
                perf_checks["Memory Usage"] = f"⚠️ {memory_percent:.1f}% (High)"

            logger.debug(f"Memory usage: {memory_percent:.1f}%")
        except ImportError:
            perf_checks["Memory Usage"] = "❓ psutil not available"
        except Exception as e:
            perf_checks["Memory Usage"] = f"❓ Error: {e}"

        # Check disk space
        try:
            disk = psutil.disk_usage(self.project_root)
            disk_percent = (disk.used / disk.total) * 100

            if disk_percent < 90:
                perf_checks["Disk Space"] = f"✅ {disk_percent:.1f}% used"
            else:
                perf_checks["Disk Space"] = f"⚠️ {disk_percent:.1f}% used (Low space)"

            logger.debug(f"Disk usage: {disk_percent:.1f}%")
        except Exception as e:
            perf_checks["Disk Space"] = f"❓ Error: {e}"

        # Check import performance
        try:
            import time

            start_time = time.time()

            # Test importing key modules
            from bot.data.db_manager import DatabaseManager
            from bot.utils.enhanced_cache_manager import EnhancedCacheManager

            import_time = time.time() - start_time

            if import_time < 1.0:
                perf_checks["Module Import"] = f"✅ {import_time:.3f}s"
            else:
                perf_checks["Module Import"] = f"⚠️ {import_time:.3f}s (Slow)"

            logger.debug(f"Module import time: {import_time:.3f}s")
        except Exception as e:
            perf_checks["Module Import"] = f"❌ Error: {e}"
            logger.error(f"Module import failed: {e}")

        self.results["performance"] = perf_checks

        # Print performance results
        for check, status in perf_checks.items():
            print(f"  {check}: {status}")

    def generate_recommendations(self):
        """Generate recommendations based on check results."""
        logger.info("💡 Generating recommendations...")
        print("\n💡 RECOMMENDATIONS")
        print("-" * 30)

        recommendations = []

        # Environment recommendations
        env_results = self.results["environment"]
        if env_results.get(".env File") == "❌ Missing":
            recommendations.append(
                "Create a .env file with required environment variables"
            )

        missing_vars = [
            var
            for var, status in env_results.items()
            if "❌" in status and "DISCORD_TOKEN" in var
        ]
        if missing_vars:
            recommendations.append(
                "Set required environment variables (DISCORD_TOKEN, MYSQL_PASSWORD, etc.)"
            )

        # Health check recommendations
        health_results = self.results["health_checks"]
        if health_results:
            unhealthy_services = [
                service
                for service, result in health_results.items()
                if isinstance(result, dict) and result.get("status") == "unhealthy"
            ]
            if unhealthy_services:
                recommendations.append(
                    f"Fix unhealthy services: {', '.join(unhealthy_services)}"
                )

        # Security recommendations
        security_results = self.results["security"]
        if any("❌" in status for status in security_results.values()):
            recommendations.append("Address security issues before deployment")

        # Performance recommendations
        perf_results = self.results["performance"]
        if any("⚠️" in status for status in perf_results.values()):
            recommendations.append("Monitor performance metrics during operation")

        if not recommendations:
            recommendations.append("✅ All systems ready for startup!")

        self.results["recommendations"] = recommendations

        # Print recommendations
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    def print_final_report(self):
        """Print final startup report."""
        print("\n" + "=" * 60)
        print("📊 STARTUP CHECK SUMMARY")
        print("=" * 60)

        # Count results
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        warnings = 0

        for category, results in self.results.items():
            if category == "recommendations":
                continue

            for check, status in results.items():
                total_checks += 1
                if "✅" in status:
                    passed_checks += 1
                elif "❌" in status:
                    failed_checks += 1
                elif "⚠️" in status:
                    warnings += 1

        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"❌ Failed: {failed_checks}")

        if failed_checks == 0 and warnings == 0:
            print("\n🎉 All checks passed! Bot is ready to start.")
            logger.info("All startup checks passed successfully")
        elif failed_checks == 0:
            print("\n⚠️ Some warnings detected, but bot should start successfully.")
            logger.warning("Startup checks completed with warnings")
        else:
            print(
                f"\n❌ {failed_checks} critical issues detected. Please fix before starting bot."
            )
            logger.error(f"Startup checks failed: {failed_checks} critical issues")

        print("\n" + "=" * 60)


async def main():
    """Run startup checks."""
    checker = DBSBMStartupChecker()
    await checker.run_all_checks()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Startup checks interrupted by user")
    except Exception as e:
        print(f"\n❌ Startup checks failed: {e}")
        logger.exception("Startup checks failed")
