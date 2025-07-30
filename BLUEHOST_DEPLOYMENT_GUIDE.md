# Bluehost Flask Application Deployment Guide

## Overview
This guide covers deploying your Flask betting bot webapp on Bluehost using cron jobs to keep it running.

## Current Setup
Your cron job is configured to run daily at midnight:
- **Schedule**: `0 0 1 1 0` (Daily at midnight)
- **Command**: `/home4/kudnlmmy/public_html/website_2121475b/start_flask.sh`

## Files Created
1. `start_flask.sh` - Starts the Flask application
2. `stop_flask.sh` - Stops the Flask application gracefully
3. `restart_flask.sh` - Restarts the Flask application

## Deployment Steps

### 1. Upload Files to Bluehost
Upload these files to your Bluehost directory:
- `webapp.py` - Main Flask application
- `start_flask.sh` - Start script
- `stop_flask.sh` - Stop script
- `restart_flask.sh` - Restart script
- `requirements_webapp.txt` - Python dependencies
- All bot/ directories and files

### 2. Set File Permissions
```bash
chmod +x start_flask.sh
chmod +x stop_flask.sh
chmod +x restart_flask.sh
```

### 3. Install Python Dependencies
```bash
pip3 install -r requirements_webapp.txt
```

### 4. Configure Environment Variables
Create a `.env` file in your Bluehost directory:
```env
FLASK_APP=webapp.py
FLASK_ENV=production
FLASK_DEBUG=0
WEBAPP_PORT=25594
MYSQL_HOST=localhost
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DB=your_db_name
MYSQL_PORT=3306
SECRET_KEY=your-secret-key
API_KEY=your-api-sports-key
```

### 5. Test the Application
```bash
# Test start script
./start_flask.sh

# Check if it's running
ps aux | grep python3

# Check logs
tail -f db_logs/flask_output.log
```

### 6. Configure Cron Job
In Bluehost cPanel:
1. Go to "Cron Jobs"
2. Add new cron job:
   - **Common Settings**: Daily
   - **Command**: `/home4/kudnlmmy/public_html/website_2121475b/start_flask.sh`

## Monitoring and Maintenance

### Check Application Status
```bash
# Check if Flask is running
ps aux | grep python3

# Check logs
tail -f db_logs/flask_output.log
tail -f db_logs/startup.log
```

### Restart Application
```bash
./restart_flask.sh
```

### Stop Application
```bash
./stop_flask.sh
```

## Troubleshooting

### Common Issues

1. **Application not starting**
   - Check Python3 is installed: `python3 --version`
   - Check dependencies: `pip3 list`
   - Check logs: `tail -f db_logs/flask_output.log`

2. **Port already in use**
   - Check what's using the port: `netstat -tulpn | grep 25594`
   - Kill existing process: `kill -9 <PID>`

3. **Database connection issues**
   - Verify MySQL credentials in `.env`
   - Test connection: `mysql -u user -p database`

4. **Permission issues**
   - Ensure scripts are executable: `chmod +x *.sh`
   - Check directory permissions: `ls -la`

### Log Files
- `db_logs/flask_output.log` - Flask application output
- `db_logs/startup.log` - Start/stop script logs
- `db_logs/webapp_daily.log` - Daily application logs

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **File Permissions**: Ensure sensitive files are not world-readable
3. **Database**: Use strong passwords and limit database user permissions
4. **HTTPS**: Configure SSL certificate for production

## Performance Optimization

1. **Database**: Use connection pooling for MySQL
2. **Caching**: Implement Redis for session storage
3. **Static Files**: Serve static files through a CDN
4. **Monitoring**: Set up application monitoring

## Backup Strategy

1. **Database**: Regular MySQL backups
2. **Code**: Version control with Git
3. **Logs**: Rotate log files to prevent disk space issues
4. **Configuration**: Backup `.env` and configuration files

## Support

For issues with:
- **Bluehost**: Contact Bluehost support
- **Application**: Check logs and error messages
- **Database**: Verify MySQL connection and permissions
- **Cron Jobs**: Test manually before relying on automation 