# DBSBM Deployment Guide

This guide provides comprehensive instructions for deploying the DBSBM (Discord Betting Sports Bot Management) system in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Bot Configuration](#bot-configuration)
5. [Deployment Options](#deployment-options)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

---

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **MySQL**: 8.0 or higher
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB, Recommended 50GB+
- **Network**: Stable internet connection for API calls

### Required Accounts & APIs

1. **Discord Developer Account**
   - Create a Discord application
   - Generate bot token
   - Set up OAuth2 scopes

2. **API-Sports Account**
   - Register at [api-sports.io](https://api-sports.io)
   - Get API key for sports data

3. **The Odds API** (Optional)
   - Register at [the-odds-api.com](https://the-odds-api.com)
   - Get API key for additional odds data

4. **MySQL Database**
   - Local or cloud database instance
   - Database user with appropriate permissions

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DBSBM
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install additional development dependencies
pip install pytest pytest-asyncio black flake8 mypy
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
TEST_GUILD_ID=your_test_guild_id_here

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_database_user
MYSQL_PASSWORD=your_secure_database_password
MYSQL_DB=betting_bot
MYSQL_PORT=3306
MYSQL_POOL_MIN_SIZE=1
MYSQL_POOL_MAX_SIZE=10

# API Configuration
API_KEY=your_api_sports_key_here
ODDS_API_KEY=your_odds_api_key_here
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=5

# Logging Configuration
LOG_LEVEL=INFO

# Cache Configuration
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Optional: Scheduler Mode
SCHEDULER_MODE=false
```

### 5. Validate Environment

```bash
# Test environment validation
python -m bot.utils.environment_validator

# Expected output:
# ✅ All environment variables validated successfully
# 📋 Environment Configuration Summary:
# ==================================================
# 🔐 Required Variables:
#   ✅ DISCORD_TOKEN: ***
#   ✅ API_KEY: ***
#   ...
```

---

## Database Setup

### 1. MySQL Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

#### CentOS/RHEL
```bash
sudo yum install mysql-server
sudo systemctl start mysqld
sudo mysql_secure_installation
```

#### Windows
Download and install MySQL from [mysql.com](https://mysql.com)

#### macOS
```bash
brew install mysql
brew services start mysql
```

### 2. Create Database and User

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE betting_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'betting_bot_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON betting_bot.* TO 'betting_bot_user'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### 3. Initialize Database Schema

```bash
# Run database initialization
python init_mysql_db.py

# Or manually run the schema
mysql -u betting_bot_user -p betting_bot < bot/migrations/all_schema.sql
```

### 4. Verify Database Connection

```bash
# Test database connection
python -c "
import asyncio
from bot.data.db_manager import DatabaseManager

async def test_db():
    db = DatabaseManager()
    try:
        await db.connect()
        print('✅ Database connection successful')
        await db.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"
```

---

## Bot Configuration

### 1. Discord Bot Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your application (e.g., "DBSBM Bot")

2. **Create Bot**
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the bot token to your `.env` file

3. **Configure Bot Permissions**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions:
     - Send Messages
     - Use Slash Commands
     - Attach Files
     - Embed Links
     - Read Message History
     - Add Reactions

4. **Invite Bot to Server**
   - Use the generated OAuth2 URL
   - Select your server
   - Authorize the bot

### 2. Bot Permissions Setup

The bot requires the following Discord permissions:

```yaml
Bot Permissions:
  - Send Messages
  - Use Slash Commands
  - Attach Files
  - Embed Links
  - Read Message History
  - Add Reactions
  - Manage Messages (for bet confirmations)
  - View Channels
  - Send Messages in Threads

User Permissions:
  - Use Slash Commands
  - Send Messages
  - Add Reactions
```

### 3. Test Bot Connection

```bash
# Test bot startup
python bot/main.py

# Expected output:
# ✅ All environment variables validated successfully
# 📋 Environment Configuration Summary:
# ✅ Rate limiter initialized
# ✅ Performance monitor initialized
# ✅ Error handler initialized
# Database connection established
# Bot setup_hook completed successfully
# Logged in as DBSBM Bot (123456789)
# ------ Bot is Ready ------
```

---

## Deployment Options

### 1. Local Development

```bash
# Start bot in development mode
python bot/main.py

# Run tests
pytest bot/tests/

# Run linting
black bot/
flake8 bot/
mypy bot/
```

### 2. Production Deployment

#### Using systemd (Linux)

1. **Create Service File**

```bash
sudo nano /etc/systemd/system/dbsbm-bot.service
```

```ini
[Unit]
Description=DBSBM Discord Bot
After=network.target mysql.service

[Service]
Type=simple
User=dbsbm
WorkingDirectory=/opt/dbsbm
Environment=PATH=/opt/dbsbm/venv/bin
ExecStart=/opt/dbsbm/venv/bin/python bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Enable and Start Service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable dbsbm-bot

# Start service
sudo systemctl start dbsbm-bot

# Check status
sudo systemctl status dbsbm-bot

# View logs
sudo journalctl -u dbsbm-bot -f
```

#### Using Docker

1. **Create Dockerfile**

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 dbsbm && chown -R dbsbm:dbsbm /app
USER dbsbm

# Run the bot
CMD ["python", "bot/main.py"]
```

2. **Create docker-compose.yml**

```yaml
version: '3.8'

services:
  dbsbm-bot:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - API_KEY=${API_KEY}
      - MYSQL_HOST=mysql
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DB=${MYSQL_DB}
      - TEST_GUILD_ID=${TEST_GUILD_ID}
    depends_on:
      - mysql
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DB}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./bot/migrations:/docker-entrypoint-initdb.d
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  mysql_data:
```

3. **Deploy with Docker Compose**

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f dbsbm-bot

# Stop services
docker-compose down
```

#### Using Cloud Platforms

##### Heroku

1. **Create Procfile**

```
worker: python bot/main.py
```

2. **Deploy to Heroku**

```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-dbsbm-bot

# Add MySQL addon
heroku addons:create jawsdb:kitefin

# Set environment variables
heroku config:set DISCORD_TOKEN=your_token
heroku config:set API_KEY=your_api_key
# ... set other variables

# Deploy
git push heroku main

# Start worker
heroku ps:scale worker=1
```

##### AWS EC2

1. **Launch EC2 Instance**
   - Choose Ubuntu 20.04 LTS
   - t3.medium or larger
   - Configure security groups for SSH and MySQL

2. **Install Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx

# Clone repository
git clone <repository-url>
cd DBSBM

# Setup as described in Environment Setup section
```

3. **Configure Nginx (Optional)**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring & Maintenance

### 1. Log Management

```bash
# View bot logs
tail -f logs/bot.log

# View error logs
grep "ERROR" logs/bot.log

# View performance logs
grep "performance" logs/bot.log
```

### 2. Database Maintenance

```sql
-- Check database size
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'betting_bot'
GROUP BY table_schema;

-- Clean up old data
DELETE FROM bets WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
DELETE FROM user_stats WHERE updated_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### 3. Performance Monitoring

```python
# Check system performance
from bot.utils.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
summary = monitor.get_performance_summary()
print(f"Uptime: {summary['uptime_seconds']} seconds")
print(f"System health: {summary['health_summary']['status']}")
```

### 4. Error Monitoring

```python
# Check error patterns
from bot.utils.error_handler import get_error_handler

handler = get_error_handler()
patterns = handler.get_error_patterns()
for pattern, data in patterns.items():
    print(f"{pattern}: {data['count']} occurrences")
```

### 5. Automated Maintenance Scripts

Create maintenance scripts:

```bash
#!/bin/bash
# maintenance.sh

# Backup database
mysqldump -u betting_bot_user -p betting_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Restart bot if needed
sudo systemctl restart dbsbm-bot

# Check system resources
df -h
free -h
```

### 6. Health Checks

```python
# health_check.py
import asyncio
import requests
from bot.utils.performance_monitor import get_performance_monitor
from bot.utils.error_handler import get_error_handler

async def health_check():
    monitor = get_performance_monitor()
    handler = get_error_handler()
    
    # Check system health
    health = await monitor.check_system_health()
    
    # Check error rates
    error_summary = handler.get_error_summary()
    
    # Send alert if issues detected
    if health['status'] == 'critical' or error_summary['total_errors'] > 10:
        # Send notification
        pass
    
    return health['status'] == 'healthy'

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## Troubleshooting

### Common Issues

#### 1. Bot Won't Start

**Symptoms**: Bot fails to start or crashes immediately

**Solutions**:
```bash
# Check environment variables
python -m bot.utils.environment_validator

# Check database connection
python -c "import asyncio; from bot.data.db_manager import DatabaseManager; asyncio.run(DatabaseManager().connect())"

# Check Discord token
curl -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/v10/users/@me
```

#### 2. Database Connection Issues

**Symptoms**: Database connection errors

**Solutions**:
```bash
# Check MySQL service
sudo systemctl status mysql

# Check MySQL connection
mysql -u betting_bot_user -p -h localhost

# Check firewall
sudo ufw status
```

#### 3. Rate Limiting Issues

**Symptoms**: API calls failing due to rate limits

**Solutions**:
```python
# Check rate limiter stats
from bot.utils.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
stats = limiter.get_global_stats()
print(f"Rate limit percentage: {stats['rate_limit_percentage']}%")
```

#### 4. Memory Issues

**Symptoms**: High memory usage, bot crashes

**Solutions**:
```bash
# Check memory usage
free -h
ps aux | grep python

# Restart bot
sudo systemctl restart dbsbm-bot

# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 5. Permission Issues

**Symptoms**: File permission errors

**Solutions**:
```bash
# Fix file permissions
sudo chown -R dbsbm:dbsbm /opt/dbsbm
sudo chmod -R 755 /opt/dbsbm

# Check bot user
sudo -u dbsbm python bot/main.py
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
# Set debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Or set in .env
LOG_LEVEL=DEBUG
```

### Performance Issues

```python
# Monitor performance
from bot.utils.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
summary = monitor.get_performance_summary()

# Check slow operations
for operation, stats in summary['response_times'].items():
    if stats['avg'] > 1.0:  # Operations taking more than 1 second
        print(f"Slow operation: {operation} - avg: {stats['avg']:.2f}s")
```

---

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate API keys regularly
- Use environment-specific configurations

### 2. Database Security

```sql
-- Create dedicated user with minimal privileges
CREATE USER 'betting_bot_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON betting_bot.* TO 'betting_bot_user'@'localhost';
REVOKE ALL PRIVILEGES ON *.* FROM 'betting_bot_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Network Security

```bash
# Configure firewall
sudo ufw allow ssh
sudo ufw allow 3306/tcp  # MySQL
sudo ufw enable

# Use VPN for remote access
# Implement IP whitelisting
```

### 4. Bot Security

- Use bot tokens with minimal required permissions
- Implement rate limiting for all user actions
- Validate all user inputs
- Log security events
- Monitor for suspicious activity

### 5. Data Protection

```python
# Sanitize user inputs
import re

def sanitize_input(input_str):
    # Remove potentially dangerous characters
    return re.sub(r'[<>"\']', '', input_str)

# Encrypt sensitive data
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data):
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(data.encode())
```

### 6. Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Database backup
mysqldump -u betting_bot_user -p betting_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env bot/config/

# Upload to cloud storage
# aws s3 cp backup_*.sql s3://your-backup-bucket/
# gsutil cp backup_*.sql gs://your-backup-bucket/
```

---

## Scaling Considerations

### 1. Horizontal Scaling

For high-traffic scenarios:

- Use load balancers
- Implement Redis for session management
- Use read replicas for database
- Implement microservices architecture

### 2. Vertical Scaling

- Increase server resources
- Optimize database queries
- Implement caching strategies
- Use CDN for static assets

### 3. Monitoring at Scale

```python
# Implement distributed monitoring
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Export metrics
start_http_server(8000)
```

---

## Support and Resources

### Documentation
- [API Reference](API_REFERENCE.md)
- [System Architecture](COMPREHENSIVE_API_SYSTEM.md)
- [Security Guide](SECURITY.md)

### Community
- Discord Server: [Link to community server]
- GitHub Issues: [Repository issues page]
- Wiki: [Project wiki]

### Monitoring Tools
- Grafana for metrics visualization
- Prometheus for metrics collection
- ELK Stack for log analysis
- Sentry for error tracking

---

## Conclusion

This deployment guide covers the essential steps to deploy and maintain the DBSBM system. Follow the security best practices and monitor the system regularly to ensure optimal performance and reliability.

For additional support, refer to the documentation or contact the development team. 