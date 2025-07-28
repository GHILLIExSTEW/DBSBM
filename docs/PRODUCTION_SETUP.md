# DBSBM Production Environment Setup Guide

## 🚀 Quick Start

### 1. Environment Variables Setup

Create a `.env` file in the `/home/container/bot/` directory with the following variables:

```bash
# Required Variables - MUST BE SET
DISCORD_TOKEN=your_actual_discord_bot_token
API_KEY=your_actual_api_sports_key
MYSQL_HOST=your_mysql_host_address
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_mysql_database_name
TEST_GUILD_ID=your_discord_guild_id

# Optional Variables (recommended)
REDIS_URL=your_redis_url_here
LOG_LEVEL=INFO
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=5
MYSQL_PORT=3306
MYSQL_POOL_MIN_SIZE=1
MYSQL_POOL_MAX_SIZE=10
CACHE_TTL=3600

# Production Settings
SCHEDULER_MODE=false
FLASK_ENV=production
```

### 2. Required Services

#### Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select existing one
3. Go to "Bot" section
4. Copy the token and set as `DISCORD_TOKEN`

#### API-Sports Key

1. Go to [API-Sports](https://www.api-sports.io/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Set as `API_KEY`

#### MySQL Database

1. Set up a MySQL database (local or cloud)
2. Create a database for DBSBM
3. Create a user with appropriate permissions
4. Set the connection details in environment variables

#### Discord Guild ID

1. Enable Developer Mode in Discord
2. Right-click on your server
3. Copy the server ID
4. Set as `TEST_GUILD_ID`

### 3. Validation Commands

Run these commands to validate your setup:

```bash
# Check environment variables
python scripts/diagnose_env.py

# Set up environment (if needed)
python scripts/setup_env.py
```

### 4. Troubleshooting

#### Common Issues:

**Environment validation failed**

- Check that all 7 required variables are set
- Ensure no placeholder values (like "your_token_here")
- Verify file permissions on .env file

**Database connection failed**

- Verify MySQL server is running
- Check host, port, username, and password
- Ensure database exists and user has permissions

**Discord bot not connecting**

- Verify bot token is correct
- Check that bot has proper permissions
- Ensure bot is invited to the server

**API calls failing**

- Verify API key is valid
- Check API rate limits
- Ensure API service is accessible

### 5. Production Checklist

- [ ] All 7 required environment variables set
- [ ] No placeholder values in .env file
- [ ] Database connection working
- [ ] Redis connection working (if using)
- [ ] Discord bot token valid
- [ ] API key valid and has permissions
- [ ] Bot invited to Discord server
- [ ] File permissions correct
- [ ] Application restarted after changes

### 6. Monitoring

Check the logs for:

- Environment validation status
- Database connection status
- API connection status
- Discord bot connection status
- Any error messages

### 7. Support

If you continue to have issues:

1. Run the diagnostic tool: `python scripts/diagnose_env.py`
2. Check the logs for specific error messages
3. Verify all services are accessible from the production environment
4. Ensure all credentials are correct and up-to-date

## 🔧 Advanced Configuration

### Database Setup

```sql
-- Create database
CREATE DATABASE dbsbm;

-- Create user
CREATE USER 'dbsbm_user'@'%' IDENTIFIED BY 'your_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON dbsbm.* TO 'dbsbm_user'@'%';
FLUSH PRIVILEGES;
```

### Redis Setup (Optional)

```bash
# If using Redis Cloud or similar
REDIS_URL=redis://username:password@host:port/db
```

### Discord Bot Permissions

Required permissions:

- Send Messages
- Read Message History
- Use Slash Commands
- Manage Channels (if using live game channels)
- Attach Files (for image generation)

## 📝 Environment Variable Reference

| Variable            | Required | Description                | Example                           |
| ------------------- | -------- | -------------------------- | --------------------------------- |
| DISCORD_TOKEN       | ✅       | Discord bot token          | `your_discord_bot_token_here`     |
| API_KEY             | ✅       | API-Sports key             | `your_api_sports_key_here`        |
| MYSQL_HOST          | ✅       | MySQL host address         | `localhost` or `your-db-host.com` |
| MYSQL_USER          | ✅       | MySQL username             | `dbsbm_user`                      |
| MYSQL_PASSWORD      | ✅       | MySQL password             | `your_secure_password`            |
| MYSQL_DB            | ✅       | MySQL database name        | `dbsbm`                           |
| TEST_GUILD_ID       | ✅       | Discord guild ID           | `1234567890123456789`             |
| REDIS_URL           | ❌       | Redis connection URL       | `redis://localhost:6379/0`        |
| LOG_LEVEL           | ❌       | Logging level              | `INFO`                            |
| API_TIMEOUT         | ❌       | API timeout in seconds     | `30`                              |
| API_RETRY_ATTEMPTS  | ❌       | API retry attempts         | `3`                               |
| API_RETRY_DELAY     | ❌       | API retry delay in seconds | `5`                               |
| MYSQL_PORT          | ❌       | MySQL port                 | `3306`                            |
| MYSQL_POOL_MIN_SIZE | ❌       | MySQL pool min size        | `1`                               |
| MYSQL_POOL_MAX_SIZE | ❌       | MySQL pool max size        | `10`                              |
| CACHE_TTL           | ❌       | Cache TTL in seconds       | `3600`                            |
| SCHEDULER_MODE      | ❌       | Scheduler mode             | `false`                           |
| FLASK_ENV           | ❌       | Flask environment          | `production`                      |
