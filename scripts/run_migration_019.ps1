# Migration 019: Guild Customization Tables
# This script runs the migration to create guild customization tables

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Guild Customization Migration Runner" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "migrations")) {
    Write-Host "ERROR: migrations directory not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if mysql-connector is installed
try {
    python -c "import mysql.connector" 2>$null
    Write-Host "mysql-connector-python is installed" -ForegroundColor Green
} catch {
    Write-Host "ERROR: mysql-connector-python is not installed" -ForegroundColor Red
    Write-Host "Please install it with: pip install mysql-connector-python" -ForegroundColor Yellow
    exit 1
}

# Run the migration
Write-Host "Starting migration..." -ForegroundColor Yellow
python scripts/run_migration_019.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "Migration completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Migration failed!" -ForegroundColor Red
    exit 1
} 