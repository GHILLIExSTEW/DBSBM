#!/usr/bin/env python3
"""
Quick script to create the ml_models table using the bot's database connection.
This bypasses phpMyAdmin and uses the same connection the bot uses.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the bot directory to the path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))


async def create_ml_models_table():
    """Create the ml_models table using the bot's database connection."""

    try:
        # Import the bot's database manager
        from data.db_manager import DatabaseManager

        print("🔧 Initializing database connection...")
        db_manager = DatabaseManager()

        # Create the ml_models table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ml_models (
            model_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            model_type VARCHAR(50) NOT NULL,
            version VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'inactive',
            model_path VARCHAR(500),
            config JSON NOT NULL,
            features JSON NOT NULL,
            target_variable VARCHAR(100) NOT NULL,
            performance_metrics JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            trained_at TIMESTAMP NULL,
            deployed_at TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        print("📝 Creating ml_models table...")
        await db_manager.execute(create_table_sql)
        print("✅ ml_models table created successfully!")

        # Insert default model
        insert_model_sql = """
        INSERT IGNORE INTO ml_models (model_id, name, description, model_type, version, status, config, features, target_variable) VALUES
        ('default_model', 'Default Model', 'Default placeholder model', 'classification', '1.0.0', 'inactive',
         '{"algorithm": "placeholder"}',
         '["placeholder"]',
         'placeholder');
        """

        print("📝 Inserting default model...")
        await db_manager.execute(insert_model_sql)
        print("✅ Default model inserted successfully!")

        # Verify the table exists
        verify_sql = "SELECT COUNT(*) as count FROM ml_models;"
        result = await db_manager.fetch_one(verify_sql)

        if result and result["count"] > 0:
            print(
                f"✅ Verification successful! Found {result['count']} model(s) in ml_models table."
            )
            print("\n🎉 The ml_models error should now be resolved!")
            print("💡 Try restarting your bot now.")
        else:
            print("⚠️  Table created but verification failed. Please check manually.")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(
            "💡 Make sure you're running this script from the project root directory."
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your database connection and try again.")


if __name__ == "__main__":
    print("🚀 Starting ml_models table creation...")
    print("=" * 50)

    # Run the async function
    asyncio.run(create_ml_models_table())

    print("=" * 50)
    print("🏁 Script completed!")
