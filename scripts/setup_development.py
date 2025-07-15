#!/usr/bin/env python3
"""
Development setup script for DBSBM.
This script sets up the development environment with all necessary tools.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command: str, description: str) -> bool:
    """Run a command and log the result."""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


def setup_pre_commit() -> bool:
    """Set up pre-commit hooks."""
    logger.info("Setting up pre-commit hooks...")
    
    # Install pre-commit
    if not run_command("pip install pre-commit", "Installing pre-commit"):
        return False
    
    # Install pre-commit hooks
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        return False
    
    return True


def setup_code_formatting() -> bool:
    """Set up code formatting tools."""
    logger.info("Setting up code formatting...")
    
    # Install formatting tools
    tools = [
        ("pip install black isort flake8 mypy", "Installing code quality tools"),
    ]
    
    for command, description in tools:
        if not run_command(command, description):
            return False
    
    return True


def setup_testing() -> bool:
    """Set up testing environment."""
    logger.info("Setting up testing environment...")
    
    # Create tests directory if it doesn't exist
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    
    # Install testing dependencies
    if not run_command("pip install pytest pytest-asyncio pytest-cov", "Installing testing dependencies"):
        return False
    
    return True


def setup_directories() -> bool:
    """Create necessary directories."""
    logger.info("Creating necessary directories...")
    
    directories = [
        "betting-bot/logs",
        "betting-bot/data/cache",
        "betting-bot/static/cache/optimized",
        "docs",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")
    
    return True


def run_initial_tests() -> bool:
    """Run initial tests to verify setup."""
    logger.info("Running initial tests...")
    
    # Run pytest to check if everything is working
    if not run_command("python -m pytest tests/ -v", "Running initial tests"):
        logger.warning("⚠️  Initial tests failed, but setup continues...")
        return True  # Don't fail setup if tests fail initially
    
    return True


def format_code() -> bool:
    """Format existing code."""
    logger.info("Formatting existing code...")
    
    # Format Python files
    if not run_command("black betting-bot/", "Formatting Python code with Black"):
        return False
    
    # Sort imports
    if not run_command("isort betting-bot/", "Sorting imports with isort"):
        return False
    
    return True


def create_git_hooks() -> bool:
    """Create additional git hooks for development."""
    logger.info("Creating development git hooks...")
    
    hooks_dir = Path(".git/hooks")
    hooks_dir.mkdir(exist_ok=True)
    
    # Create pre-push hook
    pre_push_hook = hooks_dir / "pre-push"
    pre_push_content = """#!/bin/bash
echo "Running pre-push checks..."
python -m pytest tests/ --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Push aborted."
    exit 1
fi
echo "Pre-push checks passed."
"""
    
    with open(pre_push_hook, 'w') as f:
        f.write(pre_push_content)
    
    # Make executable
    os.chmod(pre_push_hook, 0o755)
    logger.info("✅ Created pre-push git hook")
    
    return True


def main():
    """Main setup function."""
    logger.info("🚀 Starting DBSBM development setup...")
    logger.info("=" * 50)
    
    setup_steps = [
        ("Creating directories", setup_directories),
        ("Setting up code formatting", setup_code_formatting),
        ("Setting up pre-commit hooks", setup_pre_commit),
        ("Setting up testing environment", setup_testing),
        ("Formatting existing code", format_code),
        ("Creating git hooks", create_git_hooks),
        ("Running initial tests", run_initial_tests),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        logger.info(f"\n📋 {step_name}...")
        if not step_function():
            failed_steps.append(step_name)
    
    logger.info("\n" + "=" * 50)
    logger.info("🏁 SETUP COMPLETE")
    logger.info("=" * 50)
    
    if failed_steps:
        logger.error(f"❌ The following steps failed: {', '.join(failed_steps)}")
        logger.error("Please review the errors above and try again.")
        return False
    else:
        logger.info("✅ All setup steps completed successfully!")
        logger.info("\n🎉 Your development environment is ready!")
        logger.info("\nNext steps:")
        logger.info("1. Configure your .env file with your Discord bot token")
        logger.info("2. Set up your database connection")
        logger.info("3. Run 'python -m pytest' to run all tests")
        logger.info("4. Run 'pre-commit run --all-files' to check code quality")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 