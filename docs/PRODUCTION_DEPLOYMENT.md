# Production Deployment Guide

## Overview

This guide covers deploying the DBSBM betting bot to production with high availability, monitoring, and scalability.

## Prerequisites

### Infrastructure Requirements
- **Server**: Minimum 4GB RAM, 2 CPU cores, 50GB storage
- **Database**: MySQL 8.0+ with connection pooling
- **Redis**: Redis 6.0+ for caching and session storage
- **CDN**: CloudFlare or similar for static asset delivery
- **Monitoring**: Prometheus + Grafana or similar

### Software Requirements
- Python 3.8+
- Docker (optional but recommended)
- Nginx (for reverse proxy)
- Supervisor or systemd (for process management)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/betting-bot/logs \
    /app/betting-bot/data/cache \
    /app/betting-bot/static/cache/optimized \
    /app/betting-bot/data/metrics

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start the application
CMD ["python", "betting-bot/main.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  betting-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - API_KEY=${API_KEY}
      - MYSQL_HOST=mysql
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DB=${MYSQL_DB}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - mysql
      - redis
    volumes:
      - ./data:/app/betting-bot/data
      - ./logs:/app/betting-bot/logs
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DB}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "3306:3306"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - betting-bot
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
```

### Option 2: Traditional Server Deployment

#### Systemd Service
```ini
[Unit]
Description=DBSBM Betting Bot
After=network.target mysql.service redis.service

[Service]
Type=simple
User=betting-bot
WorkingDirectory=/opt/betting-bot
Environment=PATH=/opt/betting-bot/venv/bin
ExecStart=/opt/betting-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
```nginx
upstream betting_bot {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Static assets
    location /static/ {
        alias /opt/betting-bot/betting-bot/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://betting_bot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://betting_bot;
        access_log off;
    }
}
```

## Environment Configuration

### Production Environment Variables
```bash
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token
TEST_GUILD_ID=your_test_guild_id

# Database
MYSQL_HOST=localhost
MYSQL_USER=betting_bot
MYSQL_PASSWORD=secure_password
MYSQL_DB=betting_bot_prod

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
API_KEY=your_sports_api_key
ODDS_API_KEY=your_odds_api_key

# Web Server
WEB_SERVER_URL=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/betting-bot/bot.log

# Performance
MAX_WORKERS=4
CACHE_TTL=3600
IMAGE_OPTIMIZATION=true

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Database Setup

### Production Database Configuration
```sql
-- Create production database
CREATE DATABASE betting_bot_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create dedicated user
CREATE USER 'betting_bot'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON betting_bot_prod.* TO 'betting_bot'@'localhost';
FLUSH PRIVILEGES;

-- Optimize MySQL settings
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 67108864; -- 64MB
```

### Database Migration
```bash
# Run migrations
python betting-bot/scripts/optimize_database.py

# Create indexes
mysql -u betting_bot -p betting_bot_prod < migrations/create_indexes.sql
```

## Monitoring Setup

### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'betting-bot'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Grafana Dashboard
Import the provided Grafana dashboard configuration for monitoring:
- System metrics (CPU, memory, disk)
- Application metrics (request rates, error rates)
- Database performance
- Cache hit rates

## Security Considerations

### SSL/TLS Configuration
```bash
# Generate SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem
```

### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 3306/tcp  # MySQL (if external)
ufw allow 6379/tcp  # Redis (if external)
ufw enable
```

### File Permissions
```bash
# Set proper file permissions
chown -R betting-bot:betting-bot /opt/betting-bot
chmod 755 /opt/betting-bot
chmod 600 /opt/betting-bot/.env
```

## Performance Optimization

### Image Optimization
```bash
# Optimize all images
python -c "
from betting-bot.utils.image_optimizer import ImageOptimizer
optimizer = ImageOptimizer()
results = optimizer.batch_optimize('betting-bot/static/')
print(f'Optimized {results[\"optimized\"]} images, saved {results[\"saved_space\"]} bytes')
"
```

### Cache Warming
```bash
# Warm up caches
python -c "
import asyncio
from betting-bot.utils.cache_manager import cache_manager
from betting-bot.services.analytics_service import AnalyticsService

async def warm_cache():
    analytics = AnalyticsService()
    # Pre-load frequently accessed data
    await analytics.get_guild_stats(123456789)
    await analytics.get_top_cappers(123456789, limit=10)

asyncio.run(warm_cache())
"
```

## Backup Strategy

### Database Backups
```bash
#!/bin/bash
# Daily database backup
mysqldump -u betting_bot -p betting_bot_prod > \
    /backups/db_$(date +%Y%m%d_%H%M%S).sql

# Keep backups for 30 days
find /backups -name "db_*.sql" -mtime +30 -delete
```

### File Backups
```bash
#!/bin/bash
# Backup important files
tar -czf /backups/files_$(date +%Y%m%d_%H%M%S).tar.gz \
    /opt/betting-bot/betting-bot/data \
    /opt/betting-bot/betting-bot/static \
    /opt/betting-bot/.env
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (HAProxy, Nginx)
- Implement session sharing via Redis
- Use database read replicas
- Implement CDN for static assets

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Implement connection pooling
- Use Redis for caching

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
ps aux | grep python
free -h

# Restart service if needed
sudo systemctl restart betting-bot
```

#### Database Connection Issues
```bash
# Check MySQL status
sudo systemctl status mysql

# Check connection pool
mysql -u betting_bot -p -e "SHOW PROCESSLIST;"
```

#### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping
```

### Log Analysis
```bash
# Monitor logs in real-time
tail -f /var/log/betting-bot/bot.log

# Search for errors
grep -i error /var/log/betting-bot/bot.log

# Check recent activity
tail -n 100 /var/log/betting-bot/bot.log
```

## Maintenance

### Regular Maintenance Tasks
```bash
# Daily
- Check system metrics
- Monitor error logs
- Verify backups

# Weekly
- Update dependencies
- Optimize database
- Clean up old files

# Monthly
- Security updates
- Performance review
- Capacity planning
```

### Update Process
```bash
# 1. Backup current version
cp -r /opt/betting-bot /opt/betting-bot.backup

# 2. Pull latest code
cd /opt/betting-bot
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt

# 4. Run migrations
python betting-bot/scripts/optimize_database.py

# 5. Restart service
sudo systemctl restart betting-bot

# 6. Verify deployment
curl http://localhost:8000/health
```

## Support

For production support:
- Monitor system metrics continuously
- Set up alerting for critical issues
- Maintain regular backups
- Keep documentation updated
- Test disaster recovery procedures

---

*This guide provides a comprehensive approach to deploying DBSBM in production with enterprise-grade reliability and performance.*
