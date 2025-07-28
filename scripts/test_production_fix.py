#!/usr/bin/env python3
"""
Test script to simulate production environment and test the lenient validation fix.
"""

import os
import sys
from dotenv import load_dotenv


def test_production_fix():
    """Test the production environment fix."""
    print("🔍 Testing Production Environment Fix")
    print("=" * 50)

    # Load environment variables
    load_dotenv('bot/.env')

    # Simulate production environment
    os.environ['HOSTNAME'] = 'container-123'
    os.environ['FLASK_ENV'] = 'production'

    print("✅ Environment variables loaded")
    print("✅ Production environment simulated")

    # Test the environment validator
    try:
        sys.path.insert(0, 'bot')
        from utils.environment_validator import validate_environment

        print("\n🔧 Testing Environment Validator in Production Mode:")
        result = validate_environment()
        print(f"✅ Environment validation result: {result}")

        if result:
            print("🎉 SUCCESS: Environment validation passed!")
            return True
        else:
            print("❌ FAILED: Environment validation still failed")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_production_fix()
    sys.exit(0 if success else 1)
