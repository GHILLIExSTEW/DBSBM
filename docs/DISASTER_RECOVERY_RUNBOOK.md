# DBSBM Disaster Recovery Runbook

This document provides step-by-step procedures for recovering the DBSBM system from various disaster scenarios.

## 🚨 Emergency Contacts

### Primary Contacts

- **System Administrator:** [Your Name] - [Phone] - [Email]
- **Database Administrator:** [DBA Name] - [Phone] - [Email]
- **Hosting Provider Support:** [Provider] - [Phone] - [Support Portal]

### Escalation Matrix

1. **Level 1:** System Administrator (0-2 hours)
2. **Level 2:** Database Administrator (2-4 hours)
3. **Level 3:** Hosting Provider Support (4+ hours)

## 📋 Pre-Recovery Checklist

Before starting any recovery procedure:

- [ ] Document the current incident details
- [ ] Take screenshots of error messages
- [ ] Note the time of failure
- [ ] Identify affected services
- [ ] Check system resources (CPU, memory, disk)
- [ ] Verify network connectivity
- [ ] Check recent changes or deployments

## 🔥 Critical Failure Scenarios

### Scenario 1: Complete System Failure

**Symptoms:**

- All services down
- No response from webapp
- Database connection failures
- Bot not responding to Discord

**Immediate Actions:**

1. **Assess the situation:**

   ```bash
   # Check if containers are running
   docker ps -a

   # Check system resources
   docker stats

   # Check logs
   docker-compose logs --tail=100
   ```

2. **Stop all services:**

   ```bash
   docker-compose down
   ```

3. **Check disk space:**

   ```bash
   df -h
   docker system df
   ```

4. **Restart services:**

   ```bash
   docker-compose up -d
   ```

5. **Verify recovery:**

   ```bash
   # Check health endpoints
   curl http://localhost:25594/health

   # Check database connection
   docker-compose exec dbsbm-bot python -c "import mysql.connector; print('DB OK')"

   # Check Redis connection
   docker-compose exec dbsbm-bot python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"
   ```

### Scenario 2: Database Corruption

**Symptoms:**

- Database connection errors
- Data inconsistency
- Application errors related to database queries

**Recovery Procedure:**

1. **Stop affected services:**

   ```bash
   docker-compose stop dbsbm-bot
   ```

2. **Backup current state:**

   ```bash
   ./scripts/backup.sh backup
   ```

3. **Check database integrity:**

   ```bash
   docker-compose exec mysql mysqlcheck -u root -p --all-databases
   ```

4. **If corruption detected, restore from backup:**

   ```bash
   # List available backups
   ./scripts/backup.sh list

   # Restore from specific backup
   ./scripts/backup.sh restore YYYYMMDD_HHMMSS
   ```

5. **Verify data integrity:**

   ```bash
   docker-compose exec dbsbm-bot python -c "
   import mysql.connector
   conn = mysql.connector.connect(
       host='mysql',
       user='dbsbm',
       password='${MYSQL_PASSWORD}',
       database='dbsbm'
   )
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM users')
   print(f'Users: {cursor.fetchone()[0]}')
   cursor.execute('SELECT COUNT(*) FROM bets')
   print(f'Bets: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```

6. **Restart services:**
   ```bash
   docker-compose up -d
   ```

### Scenario 3: Redis Cache Failure

**Symptoms:**

- Slow response times
- Cache-related errors
- Session data loss

**Recovery Procedure:**

1. **Check Redis status:**

   ```bash
   docker-compose exec redis redis-cli ping
   docker-compose exec redis redis-cli info memory
   ```

2. **If Redis is down, restart it:**

   ```bash
   docker-compose restart redis
   ```

3. **Clear cache if necessary:**

   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

4. **Verify Redis recovery:**
   ```bash
   docker-compose exec dbsbm-bot python -c "
   import redis
   r = redis.Redis(host='redis', port=6379, password='${REDIS_PASSWORD}')
   print(f'Redis ping: {r.ping()}')
   print(f'Redis info: {r.info()}')
   "
   ```

### Scenario 4: Discord Bot Failure

**Symptoms:**

- Bot not responding to commands
- Discord API errors
- Bot offline in Discord

**Recovery Procedure:**

1. **Check bot logs:**

   ```bash
   docker-compose logs --tail=50 dbsbm-bot
   ```

2. **Verify Discord token:**

   ```bash
   docker-compose exec dbsbm-bot env | grep DISCORD
   ```

3. **Restart bot service:**

   ```bash
   docker-compose restart dbsbm-bot
   ```

4. **Check bot status:**

   ```bash
   docker-compose exec dbsbm-bot python -c "
   import discord
   import asyncio

   async def check_bot():
       try:
           bot = discord.Client()
           await bot.start('${DISCORD_TOKEN}')
       except Exception as e:
           print(f'Bot error: {e}')

   asyncio.run(check_bot())
   "
   ```

### Scenario 5: Webapp Failure

**Symptoms:**

- Health endpoint not responding
- Webapp errors in logs
- Port 25594 not accessible

**Recovery Procedure:**

1. **Check webapp status:**

   ```bash
   curl http://localhost:25594/health
   docker-compose logs --tail=50 dbsbm-bot
   ```

2. **Check port availability:**

   ```bash
   netstat -tlnp | grep 25594
   ```

3. **Restart webapp:**

   ```bash
   docker-compose restart dbsbm-bot
   ```

4. **Verify webapp recovery:**
   ```bash
   curl -f http://localhost:25594/health
   curl -f http://localhost:25594/
   ```

## 🔄 Data Recovery Procedures

### Database Recovery

**From Backup:**

```bash
# 1. Stop services
docker-compose down

# 2. Restore from backup
./scripts/backup.sh restore YYYYMMDD_HHMMSS

# 3. Start services
docker-compose up -d

# 4. Verify data
docker-compose exec dbsbm-bot python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='mysql',
    user='dbsbm',
    password='${MYSQL_PASSWORD}',
    database='dbsbm'
)
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
print(f'Recovered tables: {len(tables)}')
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'{table[0]}: {count} records')
conn.close()
"
```

**From SQL Dump:**

```bash
# 1. Copy SQL file to container
docker cp backup.sql dbsbm-mysql:/tmp/

# 2. Restore database
docker-compose exec mysql mysql -u root -p < backup.sql

# 3. Verify restoration
docker-compose exec mysql mysql -u root -p -e "USE dbsbm; SHOW TABLES;"
```

### Configuration Recovery

**Restore Configuration Files:**

```bash
# 1. Extract configuration backup
tar xzf config_YYYYMMDD_HHMMSS.tar.gz

# 2. Restart services to apply changes
docker-compose restart dbsbm-bot

# 3. Verify configuration
docker-compose exec dbsbm-bot python -c "
import os
print(f'Discord Token: {bool(os.getenv(\"DISCORD_TOKEN\"))}')
print(f'API Key: {bool(os.getenv(\"API_KEY\"))}')
print(f'Database Host: {os.getenv(\"MYSQL_HOST\")}')
"
```

## 🛠️ System Maintenance Recovery

### Disk Space Issues

**Symptoms:**

- Container startup failures
- Database errors
- Log rotation failures

**Recovery:**

```bash
# 1. Check disk usage
df -h
docker system df

# 2. Clean up Docker
docker system prune -f
docker volume prune -f

# 3. Clean up logs
find ./logs -name "*.log" -mtime +7 -delete

# 4. Clean up backups (keep last 3 days)
find ./backups -name "*.gz" -mtime +3 -delete

# 5. Restart services
docker-compose up -d
```

### Memory Issues

**Symptoms:**

- Container crashes
- Out of memory errors
- Slow performance

**Recovery:**

```bash
# 1. Check memory usage
free -h
docker stats --no-stream

# 2. Restart containers
docker-compose restart

# 3. Check for memory leaks
docker-compose logs dbsbm-bot | grep -i memory

# 4. Adjust memory limits if needed
# Edit docker-compose.yml and add:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## 📊 Post-Recovery Verification

### Health Check Checklist

After any recovery procedure, verify:

- [ ] **Webapp Health:** `curl http://localhost:25594/health`
- [ ] **Database Connection:** MySQL queries working
- [ ] **Redis Connection:** Cache operations working
- [ ] **Bot Status:** Bot online in Discord
- [ ] **Command Response:** Bot responds to test commands
- [ ] **Log Monitoring:** No critical errors in logs
- [ ] **Performance:** Response times within normal range

### Verification Commands

```bash
# Comprehensive health check
echo "=== Health Check ==="
echo "1. Webapp Health:"
curl -s http://localhost:25594/health | jq .

echo "2. Database Status:"
docker-compose exec dbsbm-bot python -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='mysql',
        user='dbsbm',
        password='${MYSQL_PASSWORD}',
        database='dbsbm'
    )
    print('✓ Database connection OK')
    conn.close()
except Exception as e:
    print(f'✗ Database error: {e}')
"

echo "3. Redis Status:"
docker-compose exec dbsbm-bot python -c "
import redis
try:
    r = redis.Redis(host='redis', password='${REDIS_PASSWORD}')
    print(f'✓ Redis ping: {r.ping()}')
except Exception as e:
    print(f'✗ Redis error: {e}')
"

echo "4. Container Status:"
docker-compose ps

echo "5. Recent Logs:"
docker-compose logs --tail=10 dbsbm-bot
```

## 📝 Incident Documentation

### Post-Incident Report Template

**Incident Details:**

- **Date/Time:** [Date and time of incident]
- **Duration:** [How long the incident lasted]
- **Severity:** [Critical/High/Medium/Low]
- **Affected Services:** [List of affected services]

**Root Cause Analysis:**

- **What happened:** [Description of the incident]
- **Why it happened:** [Root cause analysis]
- **How it was detected:** [How the issue was identified]

**Recovery Actions:**

- **Immediate actions:** [Steps taken to resolve]
- **Recovery time:** [Time to full recovery]
- **Data loss:** [Any data that was lost]

**Lessons Learned:**

- **What worked well:** [Positive aspects of the response]
- **What could be improved:** [Areas for improvement]
- **Prevention measures:** [Steps to prevent recurrence]

**Follow-up Actions:**

- [ ] Update monitoring alerts
- [ ] Review backup procedures
- [ ] Update runbook if needed
- [ ] Schedule post-mortem meeting
- [ ] Implement preventive measures

## 🔧 Preventive Measures

### Regular Maintenance Tasks

**Daily:**

- [ ] Check system health endpoints
- [ ] Monitor log files for errors
- [ ] Verify backup completion

**Weekly:**

- [ ] Review system performance metrics
- [ ] Test backup restoration procedures
- [ ] Update security patches

**Monthly:**

- [ ] Full disaster recovery drill
- [ ] Review and update runbook
- [ ] Capacity planning review

### Monitoring Setup

**Essential Alerts:**

- Container health status
- Database connection failures
- Redis connection failures
- Disk space usage > 80%
- Memory usage > 80%
- Bot offline status
- Webapp health check failures

**Alert Configuration:**

```bash
# Example monitoring script
#!/bin/bash
# health_monitor.sh

# Check webapp health
if ! curl -f http://localhost:25594/health > /dev/null 2>&1; then
    echo "ALERT: Webapp health check failed"
    # Send alert notification
fi

# Check database
if ! docker-compose exec -T dbsbm-bot python -c "import mysql.connector" 2>/dev/null; then
    echo "ALERT: Database connection failed"
    # Send alert notification
fi

# Check Redis
if ! docker-compose exec -T dbsbm-bot python -c "import redis; r=redis.Redis(host='redis'); r.ping()" 2>/dev/null; then
    echo "ALERT: Redis connection failed"
    # Send alert notification
fi
```

## 📞 Emergency Procedures

### Immediate Response Protocol

1. **Assess the situation** (5 minutes)
2. **Implement immediate workarounds** (15 minutes)
3. **Begin recovery procedures** (30 minutes)
4. **Notify stakeholders** (1 hour)
5. **Document incident** (ongoing)

### Communication Plan

**Internal Communication:**

- Immediate notification to system administrator
- Status updates every 30 minutes during incident
- Post-incident report within 24 hours

**External Communication:**

- Discord server announcements if bot is affected
- Hosting provider support ticket if needed
- User notifications if data loss occurs

---

**Last Updated:** [Date]
**Next Review:** [Date + 3 months]
**Version:** 1.0
