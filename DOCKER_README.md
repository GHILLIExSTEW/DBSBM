# DBSBM Docker Containerization

This document explains how to use Docker for running the DBSBM betting bot system in both development and production environments.

## 🐳 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for containers

### Environment Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables:**
   ```bash
   # Required variables
   DISCORD_TOKEN=your_discord_bot_token
   API_KEY=your_api_key
   API_SPORTS_KEY=your_api_sports_key
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_ROOT_PASSWORD=your_mysql_root_password
   REDIS_PASSWORD=your_redis_password

   # Optional variables
   TEST_GUILD_ID=your_test_guild_id
   MYSQL_USER=dbsbm
   MYSQL_DB=dbsbm
   ```

## 🚀 Production Deployment

### Using Docker Compose

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f dbsbm-bot
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

4. **Rebuild and restart:**
   ```bash
   docker-compose up -d --build
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t dbsbm-bot .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name dbsbm-bot \
     --env-file .env \
     -p 25594:25594 \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/data:/app/data \
     dbsbm-bot
   ```

## 🔧 Development Environment

### Using Development Docker Compose

1. **Start development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Access development tools:**
   - **Adminer (Database GUI):** http://localhost:8080
   - **Redis Commander:** http://localhost:8081
   - **Webapp:** http://localhost:25594
   - **Debug Port:** localhost:5678

3. **View development logs:**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f dbsbm-bot-dev
   ```

### Development Features

- **Live code reloading:** Source code is mounted as a volume
- **Debug mode:** Python debugger available on port 5678
- **Development databases:** Separate databases for development
- **GUI tools:** Adminer and Redis Commander for database management

## 📊 Monitoring and Health Checks

### Health Check Endpoints

- **Bot Health:** `http://localhost:25594/health`
- **Nginx Health:** `http://localhost/health` (production)

### Container Health Checks

All containers include health checks:
- **Bot:** Checks webapp health endpoint
- **MySQL:** Pings database server
- **Redis:** Tests Redis connectivity

### Monitoring Commands

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Check health status
docker-compose exec dbsbm-bot python -c "import requests; print(requests.get('http://localhost:25594/health').json())"
```

## 🔒 Security Considerations

### Production Security

1. **SSL/TLS:** Configure SSL certificates in `nginx.conf`
2. **Secrets:** Use Docker secrets or external secret management
3. **Network:** Use custom networks for service isolation
4. **User:** Container runs as non-root user (dbsbm)

### Environment Variables

**Never commit sensitive data to version control:**
- Use `.env` files (not tracked in git)
- Use Docker secrets for production
- Use external secret management services

## 📁 Volume Management

### Persistent Data

The following directories are mounted as volumes:

- **`./logs`** → `/app/logs` (Application logs)
- **`./data`** → `/app/data` (Application data)
- **`./bot/static`** → `/app/bot/static` (Static files)

### Database Volumes

- **`mysql_data`** → MySQL data persistence
- **`redis_data`** → Redis data persistence

### Backup Volumes

```bash
# Backup MySQL data
docker run --rm -v dbsbm_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz -C /data .

# Backup Redis data
docker run --rm -v dbsbm_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

## 🔄 Load Balancing (Production)

### Nginx Configuration

The `nginx.conf` includes:
- **Load balancing** with least connections
- **Rate limiting** for API and webapp endpoints
- **SSL termination** with security headers
- **Gzip compression** for better performance

### Scaling

To scale the bot service:

1. **Add more bot instances in nginx.conf:**
   ```nginx
   upstream dbsbm_backend {
       least_conn;
       server dbsbm-bot:25594 max_fails=3 fail_timeout=30s;
       server dbsbm-bot-2:25594 max_fails=3 fail_timeout=30s;
       server dbsbm-bot-3:25594 max_fails=3 fail_timeout=30s;
   }
   ```

2. **Scale with Docker Compose:**
   ```bash
   docker-compose up -d --scale dbsbm-bot=3
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check logs
   docker-compose logs dbsbm-bot

   # Check environment variables
   docker-compose exec dbsbm-bot env
   ```

2. **Database connection issues:**
   ```bash
   # Check MySQL container
   docker-compose logs mysql

   # Test database connection
   docker-compose exec dbsbm-bot python -c "import mysql.connector; print('DB OK')"
   ```

3. **Redis connection issues:**
   ```bash
   # Check Redis container
   docker-compose logs redis

   # Test Redis connection
   docker-compose exec dbsbm-bot python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"
   ```

### Debug Mode

For development debugging:

1. **Start in debug mode:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Attach debugger:**
   - Use VS Code with Python extension
   - Connect to `localhost:5678`
   - Set breakpoints in your code

### Performance Issues

1. **Check resource usage:**
   ```bash
   docker stats
   ```

2. **Optimize container resources:**
   ```yaml
   # In docker-compose.yml
   services:
     dbsbm-bot:
       deploy:
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
   ```

## 📋 Maintenance

### Regular Tasks

1. **Update images:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Clean up unused resources:**
   ```bash
   docker system prune -f
   ```

3. **Backup data:**
   ```bash
   # Create backup script
   ./scripts/backup.sh
   ```

### Log Rotation

Logs are automatically rotated by the application. For Docker logs:

```bash
# Configure log rotation in daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 🚀 Deployment Checklist

### Pre-deployment

- [ ] Environment variables configured
- [ ] SSL certificates ready (production)
- [ ] Database migrations tested
- [ ] Health checks configured
- [ ] Monitoring set up

### Post-deployment

- [ ] Health checks passing
- [ ] Logs showing no errors
- [ ] Database connections working
- [ ] Redis connections working
- [ ] Webapp responding
- [ ] Bot commands working

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [MySQL Docker Image](https://hub.docker.com/_/mysql)
- [Redis Docker Image](https://hub.docker.com/_/redis)
