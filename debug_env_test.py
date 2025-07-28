#!/usr/bin/env python3
"""
Debug script to test environment variable loading and validation.
"""

import os
import sys

from dotenv import load_dotenv

# Add bot directory to path
sys.path.insert(0, "bot")


def test_env_loading():
    """Test environment variable loading."""
    print("🔍 Testing Environment Variable Loading")
    print("=" * 50)

    # Load .env file
    env_path = "bot/.env"
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path)

    # Check required variables
    required_vars = [
        "DISCORD_TOKEN",
        "API_KEY",
        "MYSQL_HOST",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DB",
        "TEST_GUILD_ID",
    ]

    print("\n📋 Required Variables Check:")
    print("-" * 30)
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ SET" if value else "❌ MISSING"
        print(f"{var}: {status}")
        if not value:
            all_present = False

    print(
        f"\n{'✅ All required variables present' if all_present else '❌ Missing required variables'}"
    )

    # Test the environment validator
    print("\n🔍 Testing Environment Validator")
    print("-" * 30)

    try:
        from bot.utils.environment_validator import EnvironmentValidator

        # Test the legacy validation
        errors = EnvironmentValidator._legacy_validate_all()

        if errors:
            print("❌ Validation Errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ No validation errors found")

    except Exception as e:
        print(f"❌ Error testing validator: {e}")


if __name__ == "__main__":
    test_env_loading()
