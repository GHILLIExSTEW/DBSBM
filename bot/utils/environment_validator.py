"""
Enhanced Environment validation utility for DBSBM.
Validates all required environment variables and provides comprehensive connectivity testing.
"""

import asyncio
import logging
import os
import sys
import aiohttp
import aiomysql
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Import the new centralized configuration
try:
    from config.settings import get_settings, validate_settings, get_database_config, get_api_config, get_discord_config
except ImportError:
    # Fallback - try to import from parent directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add multiple possible paths for different execution contexts
    possible_paths = [
        os.path.dirname(os.path.dirname(os.path.dirname(current_dir))),  # From bot/utils/
        os.path.dirname(os.path.dirname(current_dir)),  # From bot/
        os.path.dirname(current_dir),  # From utils/
    ]
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from config.settings import get_settings, validate_settings, get_database_config, get_api_config, get_discord_config
    except ImportError:
        # Final fallback - create mock functions for testing
        def get_settings():
            return None
        def validate_settings():
            return []
        def get_database_config():
            return {}
        def get_api_config():
            return {}
        def get_discord_config():
            return {}

logger = logging.getLogger(__name__)


class EnvironmentValidator:
    """Enhanced environment validator with connectivity testing."""

    # Required environment variables
    REQUIRED_VARS = {
        "DISCORD_TOKEN": "Discord bot token for authentication",
        "API_KEY": "API-Sports key for sports data access",
        "MYSQL_HOST": "MySQL database host address",
        "MYSQL_USER": "MySQL database username",
        "MYSQL_PASSWORD": "MySQL database password",
        "MYSQL_DB": "MySQL database name",
        "TEST_GUILD_ID": "Discord guild ID for testing",
    }

    # Optional environment variables with defaults
    OPTIONAL_VARS = {
        "ODDS_API_KEY": ("", "The Odds API key for additional odds data"),
        "LOG_LEVEL": ("INFO", "Logging level (DEBUG, INFO, WARNING, ERROR)"),
        "API_TIMEOUT": ("30", "API request timeout in seconds"),
        "API_RETRY_ATTEMPTS": ("3", "Number of API retry attempts"),
        "API_RETRY_DELAY": ("5", "Delay between API retries in seconds"),
        "MYSQL_PORT": ("3306", "MySQL database port"),
        "MYSQL_POOL_MIN_SIZE": ("1", "Minimum MySQL connection pool size"),
        "MYSQL_POOL_MAX_SIZE": ("10", "Maximum MySQL connection pool size"),
        "REDIS_URL": ("", "Redis connection URL for caching"),
        "CACHE_TTL": ("3600", "Default cache TTL in seconds"),
    }

    @classmethod
    def validate_all(cls) -> Tuple[bool, List[str]]:
        """Validate all environment configurations."""
        errors = []

        # Validate centralized configuration
        try:
            from config.settings import validate_settings
            config_errors = validate_settings()
            if config_errors:
                errors.extend(config_errors)
                logger.error("Centralized configuration validation failed")
        except Exception as e:
            errors.append(f"Centralized configuration validation error: {str(e)}")
            logger.error("Centralized configuration validation failed")

        # Validate database connection
        try:
            db_valid = cls.validate_database_connection()
            if not db_valid:
                errors.append("Database connection validation failed")
        except Exception as e:
            errors.append(f"Database connection validation error: {str(e)}")

        # Validate Redis connection
        try:
            redis_valid = cls.validate_redis_connection()
            if not redis_valid:
                errors.append("Redis connection validation failed")
        except Exception as e:
            errors.append(f"Redis connection validation error: {str(e)}")

        # Validate API connections
        try:
            api_valid = cls.validate_api_connections()
            if not api_valid:
                errors.append("API connection validation failed")
        except Exception as e:
            errors.append(f"API connection validation error: {str(e)}")

        # Validate Discord connection
        try:
            discord_valid = cls.validate_discord_connection()
            if not discord_valid:
                errors.append("Discord connection validation failed")
        except Exception as e:
            errors.append(f"Discord connection validation error: {str(e)}")

        is_valid = len(errors) == 0

        if not is_valid:
            logger.error("Environment validation failed")
            for error in errors:
                logger.error(f"  - {error}")
            logger.error("Environment validation failed!")
            logger.error("Please check your .env file and ensure all required variables are set.")

        return is_valid, errors

    @classmethod
    async def validate_database_connection(cls) -> Tuple[bool, str]:
        """
        Validate database connectivity.

        Returns:
            Tuple[bool, str]: (is_connected, error_message)
        """
        try:
            db_config = get_database_config()

            # Test connection
            conn = await aiomysql.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                db=db_config['database'],
                connect_timeout=10
            )

            # Test a simple query
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                if result and result[0] == 1:
                    await conn.close()
                    return True, "Database connection successful"

            await conn.close()
            return False, "Database query test failed"

        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    @classmethod
    async def validate_api_connection(cls) -> Tuple[bool, str]:
        """
        Validate API connectivity.

        Returns:
            Tuple[bool, str]: (is_connected, error_message)
        """
        try:
            api_config = get_api_config()

            if not api_config['key']:
                return False, "API key not configured"

            # Test API connection with a simple request
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-rapidapi-host': 'v3.football.api-sports.io',
                    'x-rapidapi-key': api_config['key']
                }

                # Test with a simple endpoint
                url = "https://v3.football.api-sports.io/status"
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return True, "API connection successful"
                    else:
                        return False, f"API request failed with status {response.status}"

        except Exception as e:
            return False, f"API connection failed: {str(e)}"

    @classmethod
    async def validate_discord_token(cls) -> Tuple[bool, str]:
        """
        Validate Discord token.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            discord_config = get_discord_config()

            if not discord_config['token']:
                return False, "Discord token not configured"

            # Test Discord API connection
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bot {discord_config["token"]}'
                }

                url = "https://discord.com/api/v10/users/@me"
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, f"Discord token valid for bot: {data.get('username', 'Unknown')}"
                    else:
                        return False, f"Discord token validation failed with status {response.status}"

        except Exception as e:
            return False, f"Discord token validation failed: {str(e)}"

    @classmethod
    async def validate_all_connections(cls) -> Dict[str, Tuple[bool, str]]:
        """
        Validate all external connections.

        Returns:
            Dict[str, Tuple[bool, str]]: Results for each connection type
        """
        results = {}

        # Validate database connection
        logger.info("🔍 Testing database connection...")
        db_result = await cls.validate_database_connection()
        results['database'] = db_result

        # Validate API connection
        logger.info("🔍 Testing API connection...")
        api_result = await cls.validate_api_connection()
        results['api'] = api_result

        # Validate Discord token
        logger.info("🔍 Testing Discord token...")
        discord_result = await cls.validate_discord_token()
        results['discord'] = discord_result

        return results

    @classmethod
    def _legacy_validate_all(cls) -> List[str]:
        """Legacy validation method as fallback."""
        errors = []

        # Check required variables
        missing_required = cls._check_required_vars()
        if missing_required:
            errors.extend(missing_required)

        # Check optional variables and set defaults
        optional_errors = cls._check_optional_vars()
        if optional_errors:
            errors.extend(optional_errors)

        return errors

    @classmethod
    def _check_required_vars(cls) -> List[str]:
        """Check for missing required environment variables."""
        errors = []

        for var_name, description in cls.REQUIRED_VARS.items():
            if not os.getenv(var_name):
                errors.append(
                    f"Missing required environment variable: {var_name} - {description}"
                )

        return errors

    @classmethod
    def _check_optional_vars(cls) -> List[str]:
        """Check optional variables and set defaults."""
        errors = []

        for var_name, (default_value, description) in cls.OPTIONAL_VARS.items():
            if not os.getenv(var_name):
                os.environ[var_name] = default_value
                logger.debug(f"Set default for {var_name}: {default_value}")

        return errors

    @classmethod
    def _validate_values(cls) -> List[str]:
        """Validate specific environment variable values."""
        errors = []

        # Validate LOG_LEVEL
        log_level = os.getenv("LOG_LEVEL", "INFO")
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid LOG_LEVEL: {log_level}. Must be one of: {', '.join(valid_log_levels)}"
            )

        # Validate numeric values
        numeric_vars = {
            "API_TIMEOUT": int,
            "API_RETRY_ATTEMPTS": int,
            "API_RETRY_DELAY": int,
            "MYSQL_PORT": int,
            "MYSQL_POOL_MIN_SIZE": int,
            "MYSQL_POOL_MAX_SIZE": int,
            "CACHE_TTL": int,
        }

        for var_name, var_type in numeric_vars.items():
            value = os.getenv(var_name)
            if value:
                try:
                    var_type(value)
                except ValueError:
                    errors.append(
                        f"Invalid {var_name}: {value}. Must be a valid {var_type.__name__}"
                    )

        # Validate TEST_GUILD_ID is a valid integer
        test_guild_id = os.getenv("TEST_GUILD_ID")
        if test_guild_id:
            try:
                int(test_guild_id)
            except ValueError:
                errors.append(
                    f"Invalid TEST_GUILD_ID: {test_guild_id}. Must be a valid integer"
                )

        # Validate MYSQL_POOL sizes
        min_size = int(os.getenv("MYSQL_POOL_MIN_SIZE", "1"))
        max_size = int(os.getenv("MYSQL_POOL_MAX_SIZE", "10"))
        if min_size > max_size:
            errors.append(
                f"MYSQL_POOL_MIN_SIZE ({min_size}) cannot be greater than MYSQL_POOL_MAX_SIZE ({max_size})"
            )

        return errors

    @classmethod
    def get_config_summary(cls) -> Dict[str, str]:
        """Get a summary of current configuration (without sensitive data)."""
        config = {}

        # Add required variables (mask sensitive ones)
        for var_name in cls.REQUIRED_VARS:
            value = os.getenv(var_name, "")
            if "PASSWORD" in var_name or "TOKEN" in var_name or "KEY" in var_name:
                config[var_name] = "***" if value else "NOT SET"
            else:
                config[var_name] = value or "NOT SET"

        # Add optional variables
        for var_name, (default_value, _) in cls.OPTIONAL_VARS.items():
            value = os.getenv(var_name, default_value)
            if "PASSWORD" in var_name or "TOKEN" in var_name or "KEY" in var_name:
                config[var_name] = (
                    "***" if value and value != default_value else default_value
                )
            else:
                config[var_name] = value

        return config

    @classmethod
    def print_config_summary(cls):
        """Print a formatted configuration summary."""
        config = cls.get_config_summary()

        logger.info("📋 Environment Configuration Summary:")
        logger.info("=" * 50)

        logger.info("🔐 Required Variables:")
        for var_name in cls.REQUIRED_VARS:
            value = config[var_name]
            status = "✅" if value != "NOT SET" else "❌"
            logger.info(f"  {status} {var_name}: {value}")

        logger.info("\n⚙️ Optional Variables:")
        for var_name, (default_value, _) in cls.OPTIONAL_VARS.items():
            value = config[var_name]
            status = "✅" if value != "NOT SET" else "⚪"
            logger.info(f"  {status} {var_name}: {value}")

        logger.info("=" * 50)


def validate_environment() -> bool:
    """
    Main function to validate environment variables.

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        is_valid, errors = EnvironmentValidator.validate_all()

        if is_valid:
            EnvironmentValidator.print_config_summary()
            return True
        else:
            logger.error("Environment validation failed!")
            logger.error(
                "Please check your .env file and ensure all required variables are set."
            )
            return False

    except Exception as e:
        logger.error(f"Error during environment validation: {e}")
        return False


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    success = validate_environment()
    sys.exit(0 if success else 1)
