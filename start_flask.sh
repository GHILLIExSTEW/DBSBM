#!/bin/bash

# Start Flask Application for Bluehost
# This script starts the Flask webapp and keeps it running

# Set the working directory to the script location
cd "$(dirname "$0")"

# Set environment variables for Bluehost
export FLASK_APP=webapp.py
export FLASK_ENV=production
export FLASK_DEBUG=0

# Create logs directory if it doesn't exist
mkdir -p db_logs

# Start the Flask application
echo "$(date): Starting Flask application..." >> db_logs/startup.log

# Use nohup to keep the process running and redirect output
nohup python3 webapp.py > db_logs/flask_output.log 2>&1 &

# Get the process ID
FLASK_PID=$!
echo $FLASK_PID > db_logs/flask.pid

echo "$(date): Flask application started with PID $FLASK_PID" >> db_logs/startup.log
echo "Flask application is running with PID: $FLASK_PID"
echo "Logs are being written to: db_logs/flask_output.log" 