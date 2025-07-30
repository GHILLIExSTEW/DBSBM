#!/bin/bash

# Restart Flask Application for Bluehost
# This script stops and then starts the Flask webapp

# Set the working directory to the script location
cd "$(dirname "$0")"

echo "$(date): Restarting Flask application..." >> db_logs/startup.log
echo "Restarting Flask application..."

# Stop the application first
./stop_flask.sh

# Wait a moment for the process to fully stop
sleep 2

# Start the application
./start_flask.sh

echo "$(date): Flask application restart completed" >> db_logs/startup.log
echo "Flask application restart completed" 