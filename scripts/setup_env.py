#!/usr/bin/env python3
"""
Environment setup script for DBSBM.
Creates .env template and validates environment configuration.
"""

import os
import sys
from pathlib import Path


def create_env_template():
    """Create a .env template file with all required variables."""
    template = """# DBSBM Environment Configuration
# Copy this file to .env and fill in your actual values

# Required Variables
DISCORD_TOKEN=your_discord_bot_token_here
API_KEY=your_api_sports_key_here
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_mysql_database_name
TEST_GUILD_ID=your_discord_guild_id

# Optional Variables
ODDS_API_KEY=your_odds_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
DATAGOLF_API_KEY=your_datagolf_api_key_here
LOG_LEVEL=INFO
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=5
MYSQL_PORT=3306
MYSQL_POOL_MIN_SIZE=1
MYSQL_POOL_MAX_SIZE=10
REDIS_URL=your_redis_url_here
CACHE_TTL=3600

# Production Settings
SCHEDULER_MODE=false
FLASK_ENV=production
"""

    env_file = ".env"
    if os.path.exists(env_file):
        print(
            f"⚠️  {env_file} already exists. Creating {env_file}.template instead.")
        env_file = ".env.template"

    with open(env_file, "w") as f:
        f.write(template)

    print(f"✅ Created {env_file} with template values")
    print("📝 Please edit the file and replace the placeholder values with your actual credentials")


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = ".env"

    if not os.path.exists(env_file):
        print(f"❌ {env_file} file not found")
        return False

    print(f"✅ {env_file} file found")

    # Read and check the file
    with open(env_file, "r") as f:
        content = f.read()

    required_vars = [
        "DISCORD_TOKEN", "API_KEY", "MYSQL_HOST", "MYSQL_USER",
        "MYSQL_PASSWORD", "MYSQL_DB", "TEST_GUILD_ID"
    ]

    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing required variables in {env_file}:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    else:
        print(f"✅ All required variables found in {env_file}")
        return True


def validate_env_values():
    """Validate that environment variables have actual values (not placeholders)."""
    required_vars = {
        "DISCORD_TOKEN": "Discord bot token",
        "API_KEY": "API-Sports key",
        "MYSQL_HOST": "MySQL host",
        "MYSQL_USER": "MySQL username",
        "MYSQL_PASSWORD": "MySQL password",
        "MYSQL_DB": "MySQL database",
        "TEST_GUILD_ID": "Discord guild ID"
    }

    # Optional API keys that should be validated if present
    optional_api_vars = {
        "RAPIDAPI_KEY": "RapidAPI key",
        "DATAGOLF_API_KEY": "DataGolf API key",
        "ODDS_API_KEY": "Odds API key"
    }

    invalid_vars = []

    # Check required variables
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value or value.startswith("your_") or value == "placeholder":
            invalid_vars.append(f"{var_name} ({description})")

    # Check optional API variables if they're set
    for var_name, description in optional_api_vars.items():
        value = os.getenv(var_name)
        if value and (value.startswith("your_") or value == "placeholder"):
            invalid_vars.append(f"{var_name} ({description})")

    if invalid_vars:
        print("❌ Found placeholder values for required variables:")
        for var in invalid_vars:
            print(f"  - {var}")
        return False
    else:
        print("✅ All required variables have actual values")
        return True


def main():
    """Main function to run environment setup."""
    print("🔧 DBSBM Environment Setup")
    print("=" * 40)

    # Check if .env exists
    if not os.path.exists(".env"):
        print("📝 Creating .env template...")
        create_env_template()
        print("\n📋 Next steps:")
        print("1. Edit the .env file with your actual credentials")
        print("2. Run this script again to validate your configuration")
        return

    # Check environment file
    print("🔍 Checking environment configuration...")
    if not check_env_file():
        print("\n❌ Please fix the missing variables and run again")
        return

    # Validate environment values
    print("\n✅ Environment file is properly configured")
    if validate_env_values():
        print("\n🎉 Environment setup is complete!")
        print("You can now run the DBSBM bot")
    else:
        print("\n❌ Please update the placeholder values in your .env file")


if __name__ == "__main__":
    main()
