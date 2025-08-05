"""
Startup checks for DBSBM bot.
This module provides comprehensive startup validation for the Discord bot.
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DBSBMStartupChecker:
    """Comprehensive startup checker for DBSBM bot."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0

    async def run_all_checks(self) -> Tuple[bool, List[str]]:
        """Run all startup checks and return success status and errors."""
        logger.info("[INFO] Running comprehensive startup checks...")

        # Reset counters
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0

        # Run all checks
        await self._check_environment_variables()
        await self._check_discord_token()
        await self._check_database_connection()
        await self._check_api_connection()
        await self._check_file_permissions()
        await self._check_dependencies()

        # Log results
        logger.info(
            f"[OK] Startup checks completed: {self.checks_passed}/{self.total_checks} passed"
        )
        if self.warnings:
            logger.warning(f"[WARNING] {len(self.warnings)} warnings found")
        if self.errors:
            logger.error(f"[ERROR] {len(self.errors)} errors found")

        return len(self.errors) == 0, self.errors

    async def _check_environment_variables(self):
        """Check that all required environment variables are set."""
        self.total_checks += 1
        logger.debug("[INFO] Checking environment variables...")

        required_vars = [
            "DISCORD_TOKEN",
            "API_KEY",
            "POSTGRES_HOST",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "TEST_GUILD_ID",
        ]

        missing_vars = []
        present_vars = []

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                logger.debug(f"[ERROR] {var}: NOT SET")
            else:
                present_vars.append(var)
                # Mask sensitive values for logging
                if "TOKEN" in var or "PASSWORD" in var or "KEY" in var:
                    masked_value = (
                        value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                    )
                    logger.debug(f"[OK] {var}: {masked_value}")
                else:
                    logger.debug(f"[OK] {var}: {value}")

        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            self.errors.append(error_msg)
            logger.error(error_msg)
        else:
            self.checks_passed += 1
            logger.info("[OK] All required environment variables are set")
            logger.debug(f"Found {len(present_vars)} environment variables")

    async def _check_discord_token(self):
        """Validate Discord token format."""
        self.total_checks += 1

        token = os.getenv("DISCORD_TOKEN")
        logger.debug(f"Checking Discord token...")
        logger.debug(f"Token length: {len(token) if token else 0}")
        logger.debug(
            f"Token starts with MT: {token.startswith('MT') if token else False}"
        )

        if not token:
            error_msg = "Discord token is not set"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return

        # Basic format validation
        if not token.startswith("MT") or len(token) < 50:
            error_msg = f"Discord token format appears invalid (length: {len(token)}, starts with MT: {token.startswith('MT')})"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return

        # Additional validation
        logger.debug(f"Token format validation passed")
        logger.debug(f"Token preview: {token[:10]}...{token[-5:]}")

        self.checks_passed += 1
        logger.info("[OK] Discord token format appears valid")

    async def _check_database_connection(self):
        """Test database connection."""
        self.total_checks += 1
        logger.debug("[INFO] Testing PostgreSQL database connection...")

        try:
            import asyncpg

            # Get database configuration
            host = os.getenv("POSTGRES_HOST")
            port = int(os.getenv("POSTGRES_PORT", 5432))
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            database = os.getenv("POSTGRES_DB")

            logger.debug(f"Database host: {host}")
            logger.debug(f"Database port: {port}")
            logger.debug(f"Database user: {user}")
            logger.debug(f"Database name: {database}")
            logger.debug(f"Database password: {'***' if password else 'NOT SET'}")

            # Test connection with timeout
            logger.debug("Attempting PostgreSQL connection...")
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                ),
                timeout=10.0,
            )
            await conn.close()
            self.checks_passed += 1
            logger.info("[OK] PostgreSQL database connection successful")

        except Exception as e:
            error_msg = f"PostgreSQL database connection failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            logger.debug(f"Database connection exception type: {type(e).__name__}")
            logger.debug(f"Database connection exception details: {str(e)}")

    async def _check_api_connection(self):
        """Test API connection."""
        self.total_checks += 1
        logger.debug("[INFO] Testing API connection...")

        try:
            import aiohttp

            api_key = os.getenv("API_KEY")
            logger.debug(f"API key length: {len(api_key) if api_key else 0}")
            logger.debug(
                f"API key preview: {api_key[:10]}...{api_key[-5:] if api_key and len(api_key) > 15 else '***'}"
            )

            if not api_key:
                error_msg = "API key is not set"
                self.errors.append(error_msg)
                logger.error(error_msg)
                return

            # Test API with a simple request
            test_url = "https://v3.football.api-sports.io/status"
            headers = {"x-rapidapi-key": api_key}

            logger.debug(f"Testing API endpoint: {test_url}")
            logger.debug(f"API headers: {headers}")

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers) as response:
                    logger.debug(f"API response status: {response.status}")
                    logger.debug(f"API response headers: {dict(response.headers)}")

                    if response.status == 200:
                        response_text = await response.text()
                        logger.debug(f"API response content: {response_text[:200]}...")
                        self.checks_passed += 1
                        logger.info("[OK] API connection successful")
                    else:
                        error_msg = (
                            f"API connection failed with status {response.status}"
                        )
                        self.errors.append(error_msg)
                        logger.error(error_msg)

        except Exception as e:
            error_msg = f"API connection test failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            logger.debug(f"API connection exception type: {type(e).__name__}")
            logger.debug(f"API connection exception details: {str(e)}")

    async def _check_file_permissions(self):
        """Check file permissions for critical directories."""
        self.total_checks += 1
        logger.debug("[INFO] Checking file permissions and critical directories...")

        critical_dirs = ["data", "logs", "static", "templates"]

        missing_dirs = []
        existing_dirs = []

        for dir_name in critical_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)
                logger.debug(f"[MISSING] Directory missing: {dir_name}")
            else:
                existing_dirs.append(dir_name)
                logger.debug(f"[OK] Directory exists: {dir_name}")
                # Check if directory is writable
                try:
                    test_file = os.path.join(dir_name, ".test_write")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    logger.debug(f"[OK] Directory writable: {dir_name}")
                except Exception as e:
                    logger.debug(f"[WARNING] Directory not writable: {dir_name} - {e}")

        if missing_dirs:
            warning_msg = f"Missing directories: {', '.join(missing_dirs)}"
            self.warnings.append(warning_msg)
            logger.warning(warning_msg)
        else:
            self.checks_passed += 1
            logger.info("[OK] All critical directories exist")
            logger.debug(f"Found {len(existing_dirs)} existing directories")

    async def _check_dependencies(self):
        """Check that all required dependencies are available."""
        self.total_checks += 1
        logger.debug("[INFO] Checking required dependencies...")

        required_modules = ["discord", "asyncpg", "aiohttp", "asyncio", "logging"]

        missing_modules = []
        available_modules = []

        for module in required_modules:
            try:
                imported_module = __import__(module)
                available_modules.append(module)
                logger.debug(f"[OK] Module available: {module}")
                # Log version if available
                try:
                    version = getattr(imported_module, "__version__", "unknown")
                    logger.debug(f"  Version: {version}")
                except:
                    pass
            except ImportError as e:
                missing_modules.append(module)
                logger.debug(f"[ERROR] Module missing: {module} - {e}")

        if missing_modules:
            error_msg = f"Missing required modules: {', '.join(missing_modules)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
        else:
            self.checks_passed += 1
            logger.info("[OK] All required dependencies are available")
            logger.debug(f"Found {len(available_modules)} available modules")
