#!/bin/bash

# Stop Flask Application for Bluehost
# This script stops the Flask webapp gracefully

# Set the working directory to the script location
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "db_logs/flask.pid" ]; then
    FLASK_PID=$(cat db_logs/flask.pid)
    
    echo "$(date): Stopping Flask application with PID $FLASK_PID..." >> db_logs/startup.log
    
    # Kill the process gracefully
    if kill -0 $FLASK_PID 2>/dev/null; then
        kill $FLASK_PID
        echo "$(date): Flask application stopped successfully" >> db_logs/startup.log
        echo "Flask application stopped successfully"
    else
        echo "$(date): Flask application was not running" >> db_logs/startup.log
        echo "Flask application was not running"
    fi
    
    # Remove PID file
    rm -f db_logs/flask.pid
else
    echo "$(date): No PID file found, Flask application may not be running" >> db_logs/startup.log
    echo "No PID file found, Flask application may not be running"
fi 