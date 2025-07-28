#!/usr/bin/env python3
"""
Advanced AI Migration Runner
Runs the advanced AI tables migration for Phase 4 Task 4.1
"""


from bot.data.db_manager import DatabaseManager
import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import after setting up the path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_016_advanced_ai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_advanced_ai_migration():
    """Run the advanced AI migration."""
    db_manager = DatabaseManager()

    try:
        logger.info("Starting Advanced AI migration...")

        # Connect to database
        await db_manager.connect()
        logger.info("Connected to database")

        # Read migration file
        migration_file = Path(__file__).parent.parent / \
            "migrations" / "016_advanced_ai_tables.sql"

        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        logger.info(f"Read migration file: {migration_file}")

        # Split SQL into individual statements
        statements = [stmt.strip()
                      for stmt in migration_sql.split(';') if stmt.strip()]

        logger.info(f"Found {len(statements)} SQL statements to execute")

        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    await db_manager.execute(statement)
                    logger.info(f"Successfully executed statement {i}")
                except Exception as e:
                    logger.error(f"Failed to execute statement {i}: {e}")
                    logger.error(f"Statement: {statement[:100]}...")
                    return False

        # Verify tables were created
        logger.info("Verifying tables were created...")
        tables_to_check = [
            'advanced_ai_models',
            'ai_predictions',
            'nlp_results',
            'computer_vision_results',
            'reinforcement_learning_states',
            'model_training_jobs',
            'ai_model_metrics',
            'ai_model_versions',
            'ai_model_ab_tests'
        ]

        for table in tables_to_check:
            try:
                result = await db_manager.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                count = result['count'] if result else 0
                logger.info(f"Table {table}: {count} records")
            except Exception as e:
                logger.error(f"Failed to verify table {table}: {e}")
                return False

        logger.info("Advanced AI migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    success = asyncio.run(run_advanced_ai_migration())
    sys.exit(0 if success else 1)
