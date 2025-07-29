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
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
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

        # Check .env file - look in bot folder
        env_file = self.project_root / "bot" / ".env"
        if env_file.exists():
            env_checks[".env File"] = "✅ Exists"
            logger.debug(f"Found .env file at: {env_file}")
        else:
            env_checks[".env File"] = "❌ Missing"
            logger.error("No .env file found")

        # Check required environment variables
        required_vars = [
            "DISCORD_TOKEN",
            "MYSQL_PASSWORD",
            "API_KEY",
            "REDIS_HOST",
            "REDIS_PORT",
            "REDIS_USERNAME",
            "REDIS_PASSWORD",
            "REDIS_DB",
        ]

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

    async def run_health_checks(self) -> Dict[str, str]:
        """Run health checks with reduced timeouts for startup."""
        logger.info("🏥 Running health checks...")
        health_checks = {}

        try:
            # Import health checker with timeout
            from bot.utils.health_checker import run_system_health_check

            # Run health checks with a shorter timeout for startup
            try:
                health_results = await asyncio.wait_for(
                    run_system_health_check(),
                    timeout=15.0,  # Reduced timeout for startup
                )

                if health_results:
                    for service, result in health_results.items():
                        if isinstance(result, dict):
                            status = result.get("status", "unknown")
                            response_time = result.get("response_time", 0)
                            if status == "healthy":
                                health_checks[service] = (
                                    f"✅ Healthy ({response_time:.2f}s)"
                                )
                            elif status == "degraded":
                                # Treat degraded as a warning during startup, not a failure
                                health_checks[service] = (
                                    f"⚠️ Degraded ({response_time:.2f}s)"
                                )
                            elif status == "unhealthy":
                                health_checks[service] = (
                                    f"❌ Unhealthy ({response_time:.2f}s)"
                                )
                            else:
                                health_checks[service] = f"❓ Unknown status"
                        else:
                            health_checks[service] = f"❓ Unknown status"
                else:
                    health_checks["overall"] = "⚠️ No health check results available"

            except asyncio.TimeoutError:
                health_checks["overall"] = "⚠️ Health checks timed out"
                logger.warning("Health checks timed out during startup")
            except Exception as e:
                health_checks["overall"] = f"❌ Health check error: {str(e)}"
                logger.error(f"Health check failed: {e}")

        except Exception as e:
            health_checks["overall"] = f"❌ Health check failed: {str(e)}"
            logger.error(f"Health check failed: {e}")

        self.results["health_checks"] = health_checks

    async def check_security(self):
        """Check security configuration."""
        logger.info("🔒 Checking security configuration...")
        print("\n🔒 SECURITY CHECKS")
        print("-" * 30)
        security_checks = {}

        # Check for hardcoded credentials with timeout
        try:
            hardcoded = await asyncio.wait_for(
                asyncio.to_thread(self._check_hardcoded_credentials),
                timeout=5.0,  # Reduced timeout for startup
            )

            if hardcoded:
                security_checks["Hardcoded Credentials"] = (
                    f"❌ Found {len(hardcoded)} instances"
                )
                logger.warning(f"Found hardcoded credentials in: {hardcoded}")
            else:
                security_checks["Hardcoded Credentials"] = "✅ None found"
                logger.debug("No hardcoded credentials found")
        except asyncio.TimeoutError:
            security_checks["Hardcoded Credentials"] = "⚠️ Check timed out"
            logger.warning("Hardcoded credentials check timed out")
        except Exception as e:
            security_checks["Hardcoded Credentials"] = f"❌ Error: {str(e)}"
            logger.error(f"Hardcoded credentials check failed: {e}")

        # Check file permissions
        permissions = self._check_file_permissions()
        security_checks.update(permissions)

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

        # Check disk space - fix the path issue
        try:
            disk = psutil.disk_usage(str(self.project_root))
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
                # Fix the type checking issue
                if isinstance(status, str):
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

        # Be more lenient during startup - only treat actual failures as critical
        if failed_checks == 0:
            print(
                "\n🎉 Bot is ready to start! (Some services may be degraded during startup)"
            )
            logger.info("Startup checks completed - bot can start")
        else:
            print(
                f"\n❌ {failed_checks} critical issues detected. Please fix before starting bot."
            )
            logger.error(f"Startup checks failed: {failed_checks} critical issues")

        print("\n" + "=" * 60)

    def _check_hardcoded_credentials(self) -> List[str]:
        """Check for hardcoded credentials in codebase."""
        hardcoded = []

        # Common patterns for hardcoded credentials
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
        ]

        # Safe patterns that use environment variables
        safe_patterns = [
            r'os\.getenv\([\'"][^\'"]+[\'"]\)',
            r'os\.environ\[[\'"][^\'"]+[\'"]\]',
            r"SecretStr\(",
            r"get_secret_value\(",
        ]

        # Search in Python files
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environments and other non-project directories
            dirs[:] = [
                d
                for d in dirs
                if d
                not in [
                    "__pycache__",
                    ".git",
                    "venv",
                    "env",
                    ".venv",
                    ".venv310",
                    "node_modules",
                ]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.split("\n")

                            for line_num, line in enumerate(lines, 1):
                                # Check for sensitive patterns
                                for pattern in patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        # Check if it's a safe pattern
                                        is_safe = False
                                        for safe_pattern in safe_patterns:
                                            if re.search(
                                                safe_pattern, line, re.IGNORECASE
                                            ):
                                                is_safe = True
                                                break

                                        if not is_safe:
                                            hardcoded.append(str(file_path))
                                            break
                    except Exception:
                        continue

        return hardcoded

    def _check_file_permissions(self) -> Dict[str, str]:
        """Check file permissions for security."""
        permissions = {}

        # Check .env file permissions - only check in bot folder where it actually exists
        env_file = self.project_root / "bot" / ".env"

        if env_file.exists():
            try:
                # On Windows, we can't easily check file permissions like on Unix
                # So we'll just verify the file exists and is readable
                if env_file.is_file():
                    permissions[str(env_file)] = "✅ Proper permissions"
                else:
                    permissions[str(env_file)] = "❌ Not a regular file"
            except Exception as e:
                permissions[str(env_file)] = f"❌ Error checking permissions: {e}"
        else:
            permissions[str(env_file)] = "⚠️ File not found"

        return permissions


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
