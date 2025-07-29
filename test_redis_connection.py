#!/usr/bin/env python3
"""
Test Redis connection with the provided credentials.
"""

import redis
import os


def test_redis_connection():
    """Test Redis connection with the provided credentials."""
    print("🔍 Testing Redis Connection...")

    # Set the environment variables for testing
    os.environ["REDIS_HOST"] = "redis-11437.c309.us-east-2-1.ec2.redns.redis-cloud.com"
    os.environ["REDIS_PORT"] = "11437"
    os.environ["REDIS_USERNAME"] = "default"
    # Replace with actual password
    os.environ["REDIS_PASSWORD"] = "REDIS_PASSWORD"
    os.environ["REDIS_DB"] = "0"

    try:
        # Create Redis connection
        r = redis.Redis(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            decode_responses=True,
            username=os.environ["REDIS_USERNAME"],
            password=os.environ["REDIS_PASSWORD"],
        )

        # Test connection
        print("✅ Connecting to Redis...")
        success = r.set('test_key', 'test_value')
        print(f"✅ Set operation: {success}")

        result = r.get('test_key')
        print(f"✅ Get operation: {result}")

        # Clean up
        r.delete('test_key')
        print("✅ Delete operation: success")

        print("🎉 Redis connection test successful!")
        return True

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


if __name__ == "__main__":
    test_redis_connection()
