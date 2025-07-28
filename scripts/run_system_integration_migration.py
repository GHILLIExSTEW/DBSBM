#!/usr/bin/env python3
"""
System Integration Migration Runner
Runs the system integration tables migration for Phase 4 Task 4.3
"""

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
from bot.data.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_018_system_integration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_system_integration_migration():
    """Run the system integration migration."""
    db_manager = DatabaseManager()

    try:
        logger.info("Starting System Integration migration...")

        # Connect to database
        await db_manager.connect()
        logger.info("Connected to database")

        # Read migration file
        migration_file = Path(__file__).parent.parent / \
            "migrations" / "018_system_integration_tables.sql"

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
            'service_instances',
            'service_registry',
            'api_gateways',
            'load_balancers',
            'circuit_breakers',
            'deployment_configs',
            'service_metrics',
            'deployment_history',
            'service_mesh_config',
            'distributed_tracing'
        ]

        for table in tables_to_check:
            try:
                result = await db_manager.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                count = result['count'] if result else 0
                logger.info(f"Table {table}: {count} records")
            except Exception as e:
                logger.error(f"Failed to verify table {table}: {e}")
                return False

        # Verify default data was inserted
        logger.info("Verifying default data was inserted...")
        default_data_checks = [
            ("service_registry", "SELECT COUNT(*) as count FROM service_registry WHERE service_id LIKE '%_default'"),
            ("api_gateways", "SELECT COUNT(*) as count FROM api_gateways WHERE gateway_id = 'gateway_main'"),
            ("load_balancers", "SELECT COUNT(*) as count FROM load_balancers WHERE balancer_id LIKE 'lb_%'"),
            ("circuit_breakers", "SELECT COUNT(*) as count FROM circuit_breakers WHERE breaker_id LIKE 'cb_%'"),
            ("deployment_configs", "SELECT COUNT(*) as count FROM deployment_configs WHERE deployment_id LIKE 'deploy_%'"),
            ("service_mesh_config", "SELECT COUNT(*) as count FROM service_mesh_config WHERE mesh_id LIKE 'mesh_%'")
        ]

        for table_name, query in default_data_checks:
            try:
                result = await db_manager.fetch_one(query)
                count = result['count'] if result else 0
                logger.info(f"Default data in {table_name}: {count} records")
            except Exception as e:
                logger.error(f"Failed to verify default data in {table_name}: {e}")
                return False

        logger.info("System Integration migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    success = asyncio.run(run_system_integration_migration())
    sys.exit(0 if success else 1)
