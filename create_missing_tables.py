#!/usr/bin/env python3
"""
Comprehensive script to create all missing tables that the bot needs.
This will create all the tables that are referenced in the bot but don't exist yet.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the bot directory to the path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))


async def create_missing_tables():
    """Create all missing tables that the bot needs."""

    try:
        # Import the bot's database manager
        from data.db_manager import DatabaseManager

        print("🔧 Initializing database connection...")
        db_manager = DatabaseManager()

        # List of all missing tables and their creation SQL
        missing_tables = [
            {
                "name": "user_analytics",
                "sql": """
                CREATE TABLE IF NOT EXISTS user_analytics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    event_data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_guild (user_id, guild_id),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_event_type (event_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "predictions",
                "sql": """
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id VARCHAR(50) PRIMARY KEY,
                    model_id VARCHAR(50) NOT NULL,
                    prediction_type VARCHAR(50) NOT NULL COMMENT 'bet_outcome, user_behavior, revenue_forecast, risk_assessment, churn_prediction, recommendation',
                    input_data JSON NOT NULL COMMENT 'Input data for prediction',
                    prediction_result JSON NOT NULL COMMENT 'Prediction output',
                    confidence_score DECIMAL(5,4) NOT NULL COMMENT 'Confidence score 0.0-1.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id BIGINT NULL,
                    guild_id BIGINT NULL,
                    INDEX idx_model_id (model_id),
                    INDEX idx_prediction_type (prediction_type),
                    INDEX idx_confidence_score (confidence_score),
                    INDEX idx_created_at (created_at),
                    INDEX idx_user_id (user_id),
                    INDEX idx_guild_id (guild_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "model_performance",
                "sql": """
                CREATE TABLE IF NOT EXISTS model_performance (
                    performance_id VARCHAR(50) PRIMARY KEY,
                    model_id VARCHAR(50) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(10,6) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dataset_size INT NOT NULL,
                    evaluation_type VARCHAR(50) NOT NULL COMMENT 'train, test, validation',
                    INDEX idx_model_id (model_id),
                    INDEX idx_metric_name (metric_name),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_evaluation_type (evaluation_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "feature_importance",
                "sql": """
                CREATE TABLE IF NOT EXISTS feature_importance (
                    feature_name VARCHAR(100) NOT NULL,
                    importance_score DECIMAL(10,6) NOT NULL,
                    rank INT NOT NULL,
                    model_id VARCHAR(50) NOT NULL,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (model_id, feature_name),
                    INDEX idx_model_id (model_id),
                    INDEX idx_importance_score (importance_score),
                    INDEX idx_rank (rank)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "unit_records",
                "sql": """
                CREATE TABLE IF NOT EXISTS unit_records (
                    record_id INT AUTO_INCREMENT PRIMARY KEY,
                    bet_serial BIGINT NOT NULL COMMENT 'FK to bets.bet_serial',
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    year INT NOT NULL COMMENT 'Year bet resolved',
                    month INT NOT NULL COMMENT 'Month bet resolved (1-12)',
                    units DECIMAL(15, 2) NOT NULL COMMENT 'Original stake',
                    odds DECIMAL(10, 2) NOT NULL COMMENT 'Original odds',
                    monthly_result_value DECIMAL(15, 2) NOT NULL COMMENT 'Net units won/lost for the bet',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp bet resolved',
                    INDEX idx_unit_records_guild_user_ym (guild_id, user_id, year, month),
                    INDEX idx_unit_records_year_month (year, month),
                    INDEX idx_unit_records_user_id (user_id),
                    INDEX idx_unit_records_guild_id (guild_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "platinum_features",
                "sql": """
                CREATE TABLE IF NOT EXISTS platinum_features (
                    feature_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "platinum_analytics",
                "sql": """
                CREATE TABLE IF NOT EXISTS platinum_analytics (
                    analytics_id VARCHAR(50) PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(15, 6) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_metric_name (metric_name),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "webhook_integrations",
                "sql": """
                CREATE TABLE IF NOT EXISTS webhook_integrations (
                    webhook_id VARCHAR(50) PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    webhook_url VARCHAR(500) NOT NULL,
                    webhook_type VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_webhook_type (webhook_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "real_time_alerts",
                "sql": """
                CREATE TABLE IF NOT EXISTS real_time_alerts (
                    alert_id VARCHAR(50) PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    alert_config JSON NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_alert_type (alert_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
            {
                "name": "data_exports",
                "sql": """
                CREATE TABLE IF NOT EXISTS data_exports (
                    export_id VARCHAR(50) PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    export_type VARCHAR(50) NOT NULL,
                    export_data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_export_type (export_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """,
            },
        ]

        created_tables = []

        for table_info in missing_tables:
            table_name = table_info["name"]
            create_sql = table_info["sql"]

            try:
                print(f"📝 Creating {table_name} table...")
                await db_manager.execute(create_sql)
                print(f"✅ {table_name} table created successfully!")
                created_tables.append(table_name)
            except Exception as e:
                print(f"⚠️  {table_name} table creation failed: {e}")
                # Continue with other tables even if one fails

        # Verify tables were created
        print("\n🔍 Verifying table creation...")
        for table_name in created_tables:
            try:
                verify_sql = f"SELECT COUNT(*) as count FROM {table_name};"
                result = await db_manager.fetch_one(verify_sql)
                if result is not None:
                    print(f"✅ {table_name} table verified successfully!")
                else:
                    print(f"⚠️  {table_name} table verification failed.")
            except Exception as e:
                print(f"⚠️  {table_name} table verification failed: {e}")

        print(f"\n🎉 Successfully created {len(created_tables)} missing tables!")
        print("💡 The bot should now work without missing table errors.")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(
            "💡 Make sure you're running this script from the project root directory."
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your database connection and try again.")


if __name__ == "__main__":
    print("🚀 Starting missing tables creation...")
    print("=" * 50)

    # Run the async function
    asyncio.run(create_missing_tables())

    print("=" * 50)
    print("🏁 Script completed!")
