# Manual Flask Process Kill Commands

If your Flask app is still running after killing it in terminal, use these commands:

## 1. Find All Python Processes
```bash
ps aux | grep python3
```

## 2. Find Flask-Specific Processes
```bash
ps aux | grep -i flask
```

## 3. Find Processes Using Port 25594
```bash
netstat -tulpn | grep :25594
```

## 4. Kill All Python Processes (NUCLEAR OPTION)
```bash
pkill -9 python3
```

## 5. Kill Specific Process by PID
If you see a process with PID 12345:
```bash
kill -9 12345
```

## 6. Kill All Processes on Port 25594
```bash
fuser -k 25594/tcp
```

## 7. Kill Flask Processes by Name
```bash
pkill -f flask
pkill -f webapp.py
```

## 8. Check What's Still Running
```bash
# Check Python processes
ps aux | grep python3

# Check port usage
netstat -tulpn | grep :25594

# Check Flask processes
ps aux | grep -i flask
```

## 9. Clean Up PID File
```bash
rm -f db_logs/flask.pid
```

## 10. Complete Kill Sequence
Run these commands in order:
```bash
# Kill all Python processes
pkill -9 python3

# Kill anything on port 25594
fuser -k 25594/tcp

# Clean up PID file
rm -f db_logs/flask.pid

# Verify everything is killed
ps aux | grep python3
netstat -tulpn | grep :25594
```

## 11. Restart Flask After Killing
```bash
./start_flask.sh
```

## Troubleshooting

### If processes won't die:
1. Try `kill -9` instead of `kill`
2. Use `sudo` if you have permission issues
3. Check if it's running as a different user
4. Look for processes in different terminals/sessions

### If port is still in use:
1. Use `fuser -k 25594/tcp` to force kill
2. Check if another service is using the port
3. Wait a few seconds and try again

### If you see "Permission denied":
1. Use `sudo` before the command
2. Check if you own the process
3. Contact your system administrator 