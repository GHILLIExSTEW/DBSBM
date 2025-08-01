#!/usr/bin/env python3
"""
Migration Script for Guild Customization Tables (Migration 019)
This script executes the SQL migration to create guild customization tables.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create database connection using the project's database configuration."""
    try:
        connection = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            port=3306,
            autocommit=True
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def read_migration_file():
    """Read the migration SQL file."""
    # Get the script directory
    script_dir = Path(__file__).parent
    # Go up one level to the project root, then to migrations
    migration_file = script_dir.parent / "migrations" / "019_guild_customization_tables.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return None
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading migration file: {e}")
        return None

def execute_migration():
    """Execute the migration."""
    logger.info("Starting Migration 019: Guild Customization Tables")
    
    # Get database connection
    connection = get_db_connection()
    if not connection:
        logger.error("Failed to connect to database")
        return False
    
    # Read migration SQL
    sql_content = read_migration_file()
    if not sql_content:
        logger.error("Failed to read migration file")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        logger.info(f"Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            if statement:
                logger.info(f"Executing statement {i}/{len(statements)}")
                logger.debug(f"SQL: {statement[:100]}...")
                
                try:
                    cursor.execute(statement)
                    logger.info(f"Statement {i} executed successfully")
                except Error as e:
                    logger.error(f"Error executing statement {i}: {e}")
                    logger.error(f"Statement: {statement}")
                    return False
        
        logger.info("Migration 019 completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("Database connection closed")

def main():
    """Main function."""
    logger.info("=" * 50)
    logger.info("Guild Customization Migration Runner")
    logger.info("=" * 50)
    
    # Check if we're in the right directory
    if not Path("migrations").exists():
        logger.error("migrations directory not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Execute migration
    success = execute_migration()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 