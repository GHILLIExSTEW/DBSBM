#!/usr/bin/env python3
import os
import sys
import mysql.connector
from mysql.connector import Error

def test_database_connection():
    """Test database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        if connection.is_connected():
            print("Database connection successful")
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   MySQL Version: {version[0]}")
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"Database connection failed: {e}")
        return False

def test_flask_app():
    """Test Flask app import."""
    try:
        from webapp import app
        print("Flask app import successful")
        return True
    except Exception as e:
        print(f"Flask app import failed: {e}")
        return False

def test_templates():
    """Test template loading."""
    try:
        from flask import render_template_string
        template = "Hello {{ name }}!"
        result = render_template_string(template, name="World")
        if result == "Hello World!":
            print("Template rendering successful")
            return True
        else:
            print("Template rendering failed")
            return False
    except Exception as e:
        print(f"Template rendering failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Bluehost tests...")
    print()
    
    db_success = test_database_connection()
    flask_success = test_flask_app()
    template_success = test_templates()
    
    print()
    if all([db_success, flask_success, template_success]):
        print("All tests passed! Your Bluehost setup is ready.")
    else:
        print("Some tests failed. Please check your configuration.")
