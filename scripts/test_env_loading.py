
#!/usr/bin/env python3
"""
Test script to debug environment variable loading.
"""

import os
import sys
from dotenv import load_dotenv


def test_env_loading():
    """Test environment variable loading."""
    print("🔍 Testing Environment Variable Loading")
    print("=" * 50)

    # Check current directory
    print(f"Current Directory: {os.getcwd()}")

    # Check if .env file exists in bot directory
    bot_env_path = os.path.join("bot", ".env")
    print(f"Bot .env path: {bot_env_path}")
    print(f"Bot .env exists: {os.path.exists(bot_env_path)}")

    # Check if .env file exists in root directory
    root_env_path = ".env"
    print(f"Root .env path: {root_env_path}")
    print(f"Root .env exists: {os.path.exists(root_env_path)}")

    # Try to load from bot directory
    if os.path.exists(bot_env_path):
        print(f"\n📁 Loading from bot directory: {bot_env_path}")
        load_dotenv(dotenv_path=bot_env_path)

        # Check required variables
        required_vars = [
            "DISCORD_TOKEN", "API_KEY", "MYSQL_HOST", "MYSQL_USER",
            "MYSQL_PASSWORD", "MYSQL_DB", "TEST_GUILD_ID"
        ]

        print("\n📋 Environment Variables After Loading:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                    print(f"  ✅ {var}: *** (masked)")
                else:
                    print(f"  ✅ {var}: {value}")
            else:
                print(f"  ❌ {var}: NOT SET")

    # Also try loading from root directory
    if os.path.exists(root_env_path):
        print(f"\n📁 Loading from root directory: {root_env_path}")
        load_dotenv(dotenv_path=root_env_path)

        print("\n📋 Environment Variables After Root Loading:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if "PASSWORD" in var or "TOKEN" in var or "KEY" in var:
                    print(f"  ✅ {var}: *** (masked)")
                else:
                    print(f"  ✅ {var}: {value}")
            else:
                print(f"  ❌ {var}: NOT SET")

    # Check if we can read the .env file content
    if os.path.exists(bot_env_path):
        print(f"\n📄 .env file content (first 10 lines):")
        try:
            with open(bot_env_path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):
                    if line.strip() and not line.startswith('#'):
                        # Mask sensitive values
                        if any(keyword in line.lower() for keyword in ['password', 'token', 'key']):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                print(f"  {i+1}: {parts[0]}=***")
                            else:
                                print(f"  {i+1}: {line.strip()}")
                        else:
                            print(f"  {i+1}: {line.strip()}")
                if len(lines) > 10:
                    print(f"  ... and {len(lines) - 10} more lines")
        except Exception as e:
            print(f"  ❌ Error reading .env file: {e}")

    # Test the same logic as main.py
    print(f"\n🔧 Testing main.py logic:")
    BASE_DIR = os.path.dirname(os.path.abspath("bot/main.py"))
    DOTENV_PATH = os.path.join(BASE_DIR, ".env")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DOTENV_PATH: {DOTENV_PATH}")
    print(f"DOTENV_PATH exists: {os.path.exists(DOTENV_PATH)}")

    if os.path.exists(DOTENV_PATH):
        print("✅ .env file found at expected location")
        load_dotenv(dotenv_path=DOTENV_PATH)
        print("✅ Environment variables loaded")
    else:
        print("❌ .env file not found at expected location")
        PARENT_DOTENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
        print(f"Trying parent path: {PARENT_DOTENV_PATH}")
        if os.path.exists(PARENT_DOTENV_PATH):
            print("✅ .env file found in parent directory")
            load_dotenv(dotenv_path=PARENT_DOTENV_PATH)
            print("✅ Environment variables loaded from parent")
        else:
            print("❌ .env file not found in either location")


def main():
    """Main test function."""
    test_env_loading()

    print("\n" + "=" * 50)
    print("💡 If variables are still not loading, check:")
    print("1. File permissions on .env file")
    print("2. File encoding (should be UTF-8)")
    print("3. No extra spaces or quotes in .env values")
    print("4. Correct variable names (case-sensitive)")
    print("5. No hidden characters in the file")


if __name__ == "__main__":
    main()
