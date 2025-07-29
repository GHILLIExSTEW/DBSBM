#!/bin/bash

# DBSBM Cleanup Script for Unix/Linux
# This script provides easy cleanup options for the DBSBM project

echo
echo "========================================"
echo "   DBSBM Cleanup Script"
echo "========================================"
echo

show_menu() {
    echo "Choose cleanup option:"
    echo
    echo "1. Dry run (show what would be deleted)"
    echo "2. Full cleanup (delete files)"
    echo "3. Quick cleanup (cache only)"
    echo "4. Exit"
    echo
}

dry_run() {
    echo
    echo "Running dry run..."
    python3 cleanup_dbsbm.py --dry-run
    echo
    read -p "Press Enter to continue..."
}

full_cleanup() {
    echo
    echo "WARNING: This will permanently delete files!"
    echo
    read -p "Are you sure you want to proceed? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "Running full cleanup..."
        python3 cleanup_dbsbm.py
    else
        echo "Cleanup cancelled."
    fi
    echo
    read -p "Press Enter to continue..."
}

quick_cleanup() {
    echo
    echo "Running quick cleanup (cache only)..."
    echo
    echo "Deleting cache directories..."

    # Remove cache directories
    [ -d "__pycache__" ] && rm -rf __pycache__
    [ -d ".pytest_cache" ] && rm -rf .pytest_cache
    [ -d "htmlcov" ] && rm -rf htmlcov
    [ -f ".coverage" ] && rm .coverage
    [ -d "bot/data/__pycache__" ] && rm -rf bot/data/__pycache__

    echo
    echo "Quick cleanup completed!"
    echo
    read -p "Press Enter to continue..."
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            dry_run
            ;;
        2)
            full_cleanup
            ;;
        3)
            quick_cleanup
            ;;
        4)
            echo
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
