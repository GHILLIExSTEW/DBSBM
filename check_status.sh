#!/bin/bash

# Check Flask Application Status for Bluehost
# This script checks if the Flask app is running and shows status info

# Set the working directory to the script location
cd "$(dirname "$0")"

echo "=== Flask Application Status Check ==="
echo "Timestamp: $(date)"
echo ""

# Check if PID file exists
if [ -f "db_logs/flask.pid" ]; then
    FLASK_PID=$(cat db_logs/flask.pid)
    echo "PID File: Found (PID: $FLASK_PID)"
    
    # Check if process is actually running
    if kill -0 $FLASK_PID 2>/dev/null; then
        echo "Status: RUNNING"
        echo "Process Info:"
        ps -p $FLASK_PID -o pid,ppid,cmd,etime,pcpu,pmem
    else
        echo "Status: PID FILE EXISTS BUT PROCESS NOT RUNNING"
        echo "Cleaning up stale PID file..."
        rm -f db_logs/flask.pid
    fi
else
    echo "PID File: Not found"
    echo "Status: NOT RUNNING"
fi

echo ""
echo "=== Port Check ==="
PORT=25594
if netstat -tulpn 2>/dev/null | grep ":$PORT " > /dev/null; then
    echo "Port $PORT: IN USE"
    netstat -tulpn 2>/dev/null | grep ":$PORT "
else
    echo "Port $PORT: AVAILABLE"
fi

echo ""
echo "=== Recent Logs ==="
if [ -f "db_logs/flask_output.log" ]; then
    echo "Last 5 lines of Flask output:"
    tail -5 db_logs/flask_output.log
else
    echo "No Flask output log found"
fi

echo ""
echo "=== Startup Logs ==="
if [ -f "db_logs/startup.log" ]; then
    echo "Last 5 lines of startup log:"
    tail -5 db_logs/startup.log
else
    echo "No startup log found"
fi

echo ""
echo "=== Disk Usage ==="
echo "Log directory size:"
du -sh db_logs/ 2>/dev/null || echo "db_logs directory not found"

echo ""
echo "=== Python Processes ==="
echo "All Python processes:"
ps aux | grep python3 | grep -v grep || echo "No Python processes found" 