#!/usr/bin/env python3
"""
Simple environment test that bypasses complex validation.
"""

import os
import sys
from dotenv import load_dotenv


def simple_test():
    """Simple environment test."""
    print("🔍 Simple Environment Test")
    print("=" * 50)

    # Load environment variables
    env_path = "/home/container/bot/.env"
    if os.path.exists(env_path):
        print(f"✅ Found .env file at: {env_path}")
        load_dotenv(dotenv_path=env_path)
        print("✅ Environment variables loaded")
    else:
        print(f"❌ .env file not found at: {env_path}")
        return False

    # Simple check - just verify variables exist
    required_vars = [
        "DISCORD_TOKEN", "API_KEY", "MYSQL_HOST", "MYSQL_USER",
        "MYSQL_PASSWORD", "MYSQL_DB", "TEST_GUILD_ID"
    ]

    print("\n📋 Simple Variable Check:")
    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                print(f"  ✅ {var}: *** (set)")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            all_good = False

    if all_good:
        print("\n✅ SIMPLE TEST PASSED - All variables are set!")
        return True
    else:
        print("\n❌ SIMPLE TEST FAILED - Some variables are missing!")
        return False


if __name__ == "__main__":
    success = simple_test()
    sys.exit(0 if success else 1)
