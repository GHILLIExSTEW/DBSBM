#!/bin/bash

# Migration 019: Guild Customization Tables
# This script runs the migration to create guild customization tables

echo "=================================================="
echo "Guild Customization Migration Runner"
echo "=================================================="

# Check if we're in the right directory
if [ ! -d "migrations" ]; then
    echo "ERROR: migrations directory not found. Please run this script from the project root."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed or not in PATH"
    exit 1
fi

# Check if mysql-connector is installed
python3 -c "import mysql.connector" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: mysql-connector-python is not installed"
    echo "Please install it with: pip install mysql-connector-python"
    exit 1
fi

# Run the migration
echo "Starting migration..."
python3 scripts/run_migration_019.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "Migration completed successfully!"
    exit 0
else
    echo "Migration failed!"
    exit 1
fi 