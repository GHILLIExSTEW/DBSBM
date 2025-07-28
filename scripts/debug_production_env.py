#!/usr/bin/env python3
"""
Simple debug script for production environment.
Run this in production to see what's happening with environment validation.
"""

import os
import sys
from dotenv import load_dotenv

def debug_production():
    """Debug production environment issues."""
    print("🔍 Production Environment Debug")
    print("=" * 50)

    # Load environment variables
    env_path = "/home/container/bot/.env"
    if os.path.exists(env_path):
        print(f"✅ Found .env file at: {env_path}")
        load_dotenv(dotenv_path=env_path)
        print("✅ Environment variables loaded")
    else:
        print(f"❌ .env file not found at: {env_path}")
        return

    # Check required variables
    required_vars = [
        "DISCORD_TOKEN", "API_KEY", "MYSQL_HOST", "MYSQL_USER",
        "MYSQL_PASSWORD", "MYSQL_DB", "TEST_GUILD_ID"
    ]

    print("\n📋 Environment Variables Status:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                print(f"  ✅ {var}: *** (set)")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing variables: {missing_vars}")
    else:
        print(f"\n✅ All required variables are set!")

    # Test the environment validator
    print("\n🔧 Testing Environment Validator:")
    try:
        # Import and test the validator
        sys.path.insert(0, '/home/container/bot')
        from utils.environment_validator import validate_environment

        print("✅ Environment validator imported successfully")

        # Test the validation
        result = validate_environment()
        print(f"✅ Environment validation result: {result}")

    except Exception as e:
        print(f"❌ Error testing environment validator: {e}")
        import traceback
        traceback.print_exc()

    # Test database connection
    print("\n🔧 Testing Database Connection:")
    try:
        import aiomysql
        import asyncio

        async def test_db():
            try:
                conn = await aiomysql.connect(
                    host=os.getenv("MYSQL_HOST"),
                    port=int(os.getenv("MYSQL_PORT", 3306)),
                    user=os.getenv("MYSQL_USER"),
                    password=os.getenv("MYSQL_PASSWORD"),
                    db=os.getenv("MYSQL_DB"),
                    autocommit=True
                )
                print("✅ Database connection successful")
                await conn.ensure_closed()
                return True
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False

        # Run the test
        result = asyncio.run(test_db())
        print(f"Database test result: {result}")

    except Exception as e:
        print(f"❌ Error testing database: {e}")

    # Test Discord token
    print("\n🔧 Testing Discord Token:")
    try:
        import discord

        token = os.getenv("DISCORD_TOKEN")
        if token:
            print("✅ Discord token is set")
            # Don't actually connect, just check if it's a valid format
            if token.startswith("MT") and len(token) > 50:
                print("✅ Discord token format looks valid")
            else:
                print("⚠️  Discord token format may be invalid")
        else:
            print("❌ Discord token is not set")

    except Exception as e:
        print(f"❌ Error testing Discord token: {e}")

    # Test API key
    print("\n🔧 Testing API Key:")
    api_key = os.getenv("API_KEY")
    if api_key:
        print("✅ API key is set")
        if len(api_key) > 10:
            print("✅ API key format looks valid")
        else:
            print("⚠️  API key may be too short")
    else:
        print("❌ API key is not set")

    print("\n" + "=" * 50)
    print("💡 If all variables are set but validation still fails,")
    print("the issue might be in the validation logic itself.")
    print("Check the logs for more specific error messages.")

if __name__ == "__main__":
    debug_production()
