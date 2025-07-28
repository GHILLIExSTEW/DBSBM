#!/usr/bin/env python3
"""
Diagnostic script to check environment variables in production.
"""

import os
import sys
from typing import Dict, List, Tuple


def check_environment_variables() -> Tuple[bool, List[str], Dict[str, str]]:
    """Check all required and optional environment variables."""

    # Required environment variables (from EnvironmentValidator)
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

    errors = []
    current_values = {}

    print("🔍 Checking Environment Variables...")
    print("=" * 50)

    # Check required variables
    print("\n📋 REQUIRED VARIABLES:")
    for var_name, description in REQUIRED_VARS.items():
        value = os.getenv(var_name)
        current_values[var_name] = value

        if not value:
            print(f"  ❌ {var_name}: NOT SET - {description}")
            errors.append(f"Missing required variable: {var_name}")
        else:
            # Mask sensitive values
            if "PASSWORD" in var_name or "TOKEN" in var_name or "KEY" in var_name:
                masked_value = "***" if value else "NOT SET"
                print(f"  ✅ {var_name}: {masked_value} - {description}")
            else:
                print(f"  ✅ {var_name}: {value} - {description}")

    # Check optional variables
    print("\n📋 OPTIONAL VARIABLES:")
    for var_name, (default_value, description) in OPTIONAL_VARS.items():
        value = os.getenv(var_name, default_value)
        current_values[var_name] = value

        if "PASSWORD" in var_name or "TOKEN" in var_name or "KEY" in var_name:
            masked_value = "***" if value and value != default_value else default_value
            print(
                f"  {'✅' if value else '⚪'} {var_name}: {masked_value} - {description}")
        else:
            print(f"  {'✅' if value else '⚪'} {var_name}: {value} - {description}")

    # Check for any other environment variables that might be relevant
    print("\n📋 OTHER ENVIRONMENT VARIABLES:")
    relevant_vars = [
        "PYTHONPATH", "PATH", "HOME", "USER", "HOSTNAME",
        "SCHEDULER_MODE", "FLASK_DEBUG", "FLASK_ENV"
    ]

    for var_name in relevant_vars:
        value = os.getenv(var_name)
        if value:
            print(f"  ℹ️  {var_name}: {value}")

    print("\n" + "=" * 50)

    if errors:
        print(f"\n❌ ENVIRONMENT VALIDATION FAILED")
        print(f"Missing {len(errors)} required variables:")
        for error in errors:
            print(f"  - {error}")
        return False, errors, current_values
    else:
        print(f"\n✅ ENVIRONMENT VALIDATION PASSED")
        print(f"All required variables are set!")
        return True, [], current_values


def main():
    """Main diagnostic function."""
    print("🚀 DBSBM Environment Diagnostic Tool")
    print("=" * 50)

    # Check if we're in a production-like environment
    is_production = any([
        os.getenv("SCHEDULER_MODE"),
        os.getenv("FLASK_ENV") == "production",
        "container" in os.getenv("HOSTNAME", "").lower(),
        "/home/container" in os.getcwd()
    ])

    print(
        f"Environment Type: {'Production' if is_production else 'Development'}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")

    # Check environment variables
    is_valid, errors, values = check_environment_variables()

    # Provide recommendations
    print("\n💡 RECOMMENDATIONS:")

    if not is_valid:
        print("1. Set the missing required environment variables in your .env file")
        print("2. Ensure your .env file is being loaded correctly")
        print("3. Check that the .env file path is correct")

        # Show example .env structure
        print("\n📝 Example .env file structure:")
        print("DISCORD_TOKEN=your_discord_token_here")
        print("API_KEY=your_api_sports_key_here")
        print("MYSQL_HOST=your_mysql_host")
        print("MYSQL_USER=your_mysql_user")
        print("MYSQL_PASSWORD=your_mysql_password")
        print("MYSQL_DB=your_mysql_database")
        print("TEST_GUILD_ID=your_test_guild_id")
        print("REDIS_URL=your_redis_url (optional)")
    else:
        print("1. Environment looks good!")
        print(
            "2. If you're still having issues, check the logs for specific error messages")
        print("3. Verify that the database and Redis connections are working")

    print("\n🔧 TROUBLESHOOTING TIPS:")
    print("1. Check if .env file exists and is readable")
    print("2. Verify environment variable names are correct (case-sensitive)")
    print("3. Ensure no extra spaces or quotes in .env values")
    print("4. Check file permissions on .env file")
    print("5. Restart the application after making changes")

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
