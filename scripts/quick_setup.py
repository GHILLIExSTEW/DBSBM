#!/usr/bin/env python3
"""
Quick setup script for DBSBM production environment.
This script helps set up the required environment variables.
"""

import os
import sys
import getpass
from typing import Dict, List


def get_user_input(prompt: str, is_password: bool = False) -> str:
    """Get user input, optionally hiding passwords."""
    if is_password:
        return getpass.getpass(prompt)
    else:
        return input(prompt)


def create_env_file():
    """Create .env file with user input."""
    print("🚀 DBSBM Production Environment Setup")
    print("=" * 50)
    print("This script will help you create a .env file with all required variables.")
    print("Please have your credentials ready.\n")

    # Get required variables
    env_vars = {}

    print("📋 Required Variables:")
    print("-" * 30)

    env_vars['DISCORD_TOKEN'] = get_user_input("Discord Bot Token: ")
    env_vars['API_KEY'] = get_user_input("API-Sports Key: ")
    env_vars['MYSQL_HOST'] = get_user_input("MySQL Host (e.g., localhost): ")
    env_vars['MYSQL_USER'] = get_user_input("MySQL Username: ")
    env_vars['MYSQL_PASSWORD'] = get_user_input(
        "MySQL Password: ", is_password=True)
    env_vars['MYSQL_DB'] = get_user_input("MySQL Database Name: ")
    env_vars['TEST_GUILD_ID'] = get_user_input("Discord Guild ID: ")

    print("\n📋 Optional Variables:")
    print("-" * 30)

    redis_url = get_user_input("Redis URL (optional, press Enter to skip): ")
    if redis_url:
        env_vars['REDIS_URL'] = redis_url

    # Set defaults for optional variables
    env_vars.setdefault('LOG_LEVEL', 'INFO')
    env_vars.setdefault('API_TIMEOUT', '30')
    env_vars.setdefault('API_RETRY_ATTEMPTS', '3')
    env_vars.setdefault('API_RETRY_DELAY', '5')
    env_vars.setdefault('MYSQL_PORT', '3306')
    env_vars.setdefault('MYSQL_POOL_MIN_SIZE', '1')
    env_vars.setdefault('MYSQL_POOL_MAX_SIZE', '10')
    env_vars.setdefault('CACHE_TTL', '3600')
    env_vars.setdefault('SCHEDULER_MODE', 'false')
    env_vars.setdefault('FLASK_ENV', 'production')

    # Create .env content
    env_content = f"""# DBSBM Environment Configuration
# Copy this file to bot/.env and fill in your actual values

# Discord Bot Configuration
DISCORD_TOKEN={env_vars['DISCORD_TOKEN']}

# Database Configuration
MYSQL_HOST={env_vars['MYSQL_HOST']}
MYSQL_PORT={env_vars['MYSQL_PORT']}
MYSQL_USER={env_vars['MYSQL_USER']}
MYSQL_PASSWORD={env_vars['MYSQL_PASSWORD']}
MYSQL_DATABASE={env_vars['MYSQL_DB']}

# API Configuration
API_KEY={env_vars['API_KEY']}

# Redis Configuration
REDIS_HOST={env_vars['REDIS_URL'].split(':')[0]}
REDIS_PORT={env_vars['REDIS_URL'].split(':')[1].split('/')[0]}
REDIS_USERNAME={env_vars['REDIS_URL'].split('@')[0].split(':')[0]}
REDIS_PASSWORD={env_vars['REDIS_URL'].split('@')[0].split(':')[1].split('/')[0]}
REDIS_DB={env_vars['REDIS_URL'].split('/')[1]}

# Environment
ENV=production
"""

    # Create .env file in bot folder
    env_file = "bot/.env"

    # Check if .env already exists
    if os.path.exists(env_file):
        overwrite = input(
            "⚠️  .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("❌ Setup cancelled.")
            return

    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"\n✅ Created {env_file} file successfully!")
    print(f"📁 File location: {os.path.abspath(env_file)}")

    return env_vars


def validate_setup(env_vars: Dict[str, str]):
    """Validate the setup by checking if all required variables are set."""
    required_vars = [
        'DISCORD_TOKEN', 'API_KEY', 'MYSQL_HOST', 'MYSQL_USER',
        'MYSQL_PASSWORD', 'MYSQL_DB', 'TEST_GUILD_ID'
    ]

    missing_vars = []
    for var in required_vars:
        if not env_vars.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required variables are set!")
        return True


def main():
    """Main setup function."""
    try:
        # Check if .env already exists
        if os.path.exists(".env"):
            overwrite = input(
                "⚠️  .env file already exists. Overwrite? (y/N): ").lower()
            if overwrite != 'y':
                print("Setup cancelled.")
                return 1

        # Create environment file
        env_vars = create_env_file()

        # Validate setup
        if validate_setup(env_vars):
            print("\n🎉 Setup completed successfully!")
            print("\n📝 Next steps:")
            print("1. Verify your credentials are correct")
            print("2. Test the connection by running: python scripts/diagnose_env.py")
            print("3. Start the bot: python bot/main.py")
            return 0
        else:
            print("\n❌ Setup incomplete. Please check the missing variables.")
            return 1

    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
