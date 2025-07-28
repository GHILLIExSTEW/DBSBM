#!/usr/bin/env python3
"""
Production environment diagnostic script.
Run this in the production environment to check environment variables.
"""

import os
import sys
from dotenv import load_dotenv

def check_production_env():
    """Check environment variables in production."""
    print("🔍 Production Environment Diagnostic")
    print("=" * 50)

    # Check if we're in a production environment
    is_production = any([
        os.getenv("SCHEDULER_MODE"),
        os.getenv("FLASK_ENV") == "production",
        "container" in os.getenv("HOSTNAME", "").lower(),
        "/home/container" in os.getcwd()
    ])

    print(f"Environment Type: {'Production' if is_production else 'Development'}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Hostname: {os.getenv('HOSTNAME', 'Not set')}")

    # Check for .env files in various locations
    possible_env_paths = [
        ".env",
        "bot/.env",
        "/home/container/bot/.env",
        "/home/container/.env",
        os.path.join(os.getcwd(), "bot", ".env"),
        os.path.join(os.getcwd(), ".env")
    ]

    print("\n📁 Checking for .env files:")
    env_file_found = False
    for path in possible_env_paths:
        exists = os.path.exists(path)
        print(f"  {'✅' if exists else '❌'} {path}")
        if exists:
            env_file_found = True
            # Try to load from this path
            try:
                load_dotenv(dotenv_path=path)
                print(f"    ✅ Successfully loaded from {path}")
            except Exception as e:
                print(f"    ❌ Error loading from {path}: {e}")

    if not env_file_found:
        print("\n❌ No .env file found in any expected location!")
        print("💡 You need to create a .env file in the bot directory")
        return False

    # Check required variables
    required_vars = [
        "DISCORD_TOKEN", "API_KEY", "MYSQL_HOST", "MYSQL_USER",
        "MYSQL_PASSWORD", "MYSQL_DB", "TEST_GUILD_ID"
    ]

    print("\n📋 Required Environment Variables:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                print(f"  ✅ {var}: *** (masked)")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing_vars.append(var)

    # Check optional variables
    optional_vars = {
        "REDIS_URL": "Redis connection URL",
        "LOG_LEVEL": "Logging level",
        "API_TIMEOUT": "API timeout",
        "MYSQL_PORT": "MySQL port",
        "SCHEDULER_MODE": "Scheduler mode",
        "FLASK_ENV": "Flask environment"
    }

    print("\n📋 Optional Environment Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value} - {description}")
        else:
            print(f"  ⚪ {var}: NOT SET - {description}")

    # Check if variables are being overridden by system environment
    print("\n🔍 Checking for system environment overrides:")
    for var in required_vars:
        # Check if variable exists in os.environ (system environment)
        if var in os.environ:
            print(f"  ⚠️  {var}: Set by system environment")
        else:
            print(f"  ℹ️  {var}: Not set by system environment")

    # Summary
    print("\n" + "=" * 50)
    if missing_vars:
        print(f"❌ ENVIRONMENT VALIDATION FAILED")
        print(f"Missing {len(missing_vars)} required variables:")
        for var in missing_vars:
            print(f"  - {var}")

        print("\n💡 SOLUTIONS:")
        print("1. Create a .env file in the bot directory with all required variables")
        print("2. Check that the .env file has correct permissions (readable)")
        print("3. Ensure the .env file uses UTF-8 encoding")
        print("4. Verify no extra spaces or quotes in variable values")
        print("5. Make sure variable names are correct (case-sensitive)")

        return False
    else:
        print("✅ ENVIRONMENT VALIDATION PASSED")
        print("All required variables are set!")
        return True

def main():
    """Main diagnostic function."""
    success = check_production_env()

    if success:
        print("\n🎉 Environment looks good!")
        print("If the bot is still failing, check:")
        print("1. Database connectivity")
        print("2. Discord bot token validity")
        print("3. API key permissions")
        print("4. Network connectivity")
    else:
        print("\n🔧 Next steps:")
        print("1. Create/update the .env file with missing variables")
        print("2. Restart the application")
        print("3. Check the logs for any remaining errors")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
