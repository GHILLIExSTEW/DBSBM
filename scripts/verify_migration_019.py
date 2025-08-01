#!/usr/bin/env python3
"""
Verification Script for Migration 019: Guild Customization Tables
This script verifies that the migration was executed successfully.
"""

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
            port=3306
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def verify_tables():
    """Verify that all expected tables exist."""
    connection = get_db_connection()
    if not connection:
        logger.error("Failed to connect to database")
        return False
    
    expected_tables = [
        'guild_customization',
        'guild_images', 
        'guild_page_templates'
    ]
    
    try:
        cursor = connection.cursor()
        
        # Check if tables exist
        for table in expected_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                logger.info(f"✓ Table '{table}' exists")
            else:
                logger.error(f"✗ Table '{table}' does not exist")
                return False
        
        # Check table structures
        logger.info("\nChecking table structures...")
        
        # Check guild_customization columns
        cursor.execute("DESCRIBE guild_customization")
        columns = cursor.fetchall()
        expected_columns = [
            'id', 'guild_id', 'page_title', 'page_description', 'welcome_message',
            'primary_color', 'secondary_color', 'accent_color', 'hero_image',
            'logo_image', 'background_image', 'about_section', 'features_section',
            'rules_section', 'discord_invite', 'website_url', 'twitter_url',
            'show_leaderboard', 'show_recent_bets', 'show_stats', 'public_access',
            'created_at', 'updated_at'
        ]
        
        actual_columns = [col[0] for col in columns]
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            logger.error(f"Missing columns in guild_customization: {missing_columns}")
            return False
        else:
            logger.info("✓ guild_customization table structure is correct")
        
        # Check guild_images columns
        cursor.execute("DESCRIBE guild_images")
        columns = cursor.fetchall()
        expected_columns = [
            'id', 'guild_id', 'image_type', 'filename', 'original_filename',
            'file_size', 'mime_type', 'alt_text', 'display_order', 'is_active',
            'uploaded_by', 'created_at'
        ]
        
        actual_columns = [col[0] for col in columns]
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            logger.error(f"Missing columns in guild_images: {missing_columns}")
            return False
        else:
            logger.info("✓ guild_images table structure is correct")
        
        # Check guild_page_templates columns
        cursor.execute("DESCRIBE guild_page_templates")
        columns = cursor.fetchall()
        expected_columns = [
            'id', 'template_name', 'template_description', 'template_config',
            'is_default', 'created_at'
        ]
        
        actual_columns = [col[0] for col in columns]
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            logger.error(f"Missing columns in guild_page_templates: {missing_columns}")
            return False
        else:
            logger.info("✓ guild_page_templates table structure is correct")
        
        # Check default templates
        cursor.execute("SELECT template_name, is_default FROM guild_page_templates")
        templates = cursor.fetchall()
        
        expected_templates = ['modern', 'classic', 'gaming']
        actual_templates = [template[0] for template in templates]
        
        missing_templates = set(expected_templates) - set(actual_templates)
        if missing_templates:
            logger.error(f"Missing default templates: {missing_templates}")
            return False
        else:
            logger.info("✓ Default templates are correctly inserted")
        
        # Check for default template
        cursor.execute("SELECT template_name FROM guild_page_templates WHERE is_default = TRUE")
        default_template = cursor.fetchone()
        if default_template and default_template[0] == 'modern':
            logger.info("✓ Modern template is set as default")
        else:
            logger.error("✗ Modern template is not set as default")
            return False
        
        logger.info("\n🎉 All verification checks passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main():
    """Main function."""
    logger.info("=" * 50)
    logger.info("Migration 019 Verification")
    logger.info("=" * 50)
    
    success = verify_tables()
    
    if success:
        logger.info("Verification completed successfully!")
        return 0
    else:
        logger.error("Verification failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 