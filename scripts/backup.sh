#!/bin/bash

# DBSBM Backup Script
# This script creates backups of the DBSBM system data

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="dbsbm_backup_${DATE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
}

# Create backup directory
create_backup_dir() {
    mkdir -p "${BACKUP_DIR}"
    log "Backup directory created: ${BACKUP_DIR}"
}

# Backup MySQL data
backup_mysql() {
    log "Starting MySQL backup..."

    if docker ps | grep -q "dbsbm-mysql"; then
        # Container is running, use mysqldump
        docker exec dbsbm-mysql mysqldump \
            -u root \
            -p"${MYSQL_ROOT_PASSWORD}" \
            --all-databases \
            --single-transaction \
            --routines \
            --triggers \
            > "${BACKUP_DIR}/mysql_${BACKUP_NAME}.sql"

        # Compress the backup
        gzip "${BACKUP_DIR}/mysql_${BACKUP_NAME}.sql"
        log "MySQL backup completed: mysql_${BACKUP_NAME}.sql.gz"
    else
        # Container is not running, backup volume directly
        if docker volume ls | grep -q "dbsbm_mysql_data"; then
            docker run --rm \
                -v dbsbm_mysql_data:/data \
                -v "$(pwd)/${BACKUP_DIR}:/backup" \
                alpine tar czf "/backup/mysql_volume_${BACKUP_NAME}.tar.gz" -C /data .
            log "MySQL volume backup completed: mysql_volume_${BACKUP_NAME}.tar.gz"
        else
            warning "MySQL container and volume not found"
        fi
    fi
}

# Backup Redis data
backup_redis() {
    log "Starting Redis backup..."

    if docker ps | grep -q "dbsbm-redis"; then
        # Container is running, use redis-cli
        docker exec dbsbm-redis redis-cli --rdb /data/dump.rdb
        docker cp dbsbm-redis:/data/dump.rdb "${BACKUP_DIR}/redis_${BACKUP_NAME}.rdb"
        log "Redis backup completed: redis_${BACKUP_NAME}.rdb"
    else
        # Container is not running, backup volume directly
        if docker volume ls | grep -q "dbsbm_redis_data"; then
            docker run --rm \
                -v dbsbm_redis_data:/data \
                -v "$(pwd)/${BACKUP_DIR}:/backup" \
                alpine tar czf "/backup/redis_volume_${BACKUP_NAME}.tar.gz" -C /data .
            log "Redis volume backup completed: redis_volume_${BACKUP_NAME}.tar.gz"
        else
            warning "Redis container and volume not found"
        fi
    fi
}

# Backup application data
backup_app_data() {
    log "Starting application data backup..."

    if [ -d "./data" ]; then
        tar czf "${BACKUP_DIR}/app_data_${BACKUP_NAME}.tar.gz" \
            --exclude='./data/cache' \
            --exclude='./data/temp' \
            ./data
        log "Application data backup completed: app_data_${BACKUP_NAME}.tar.gz"
    else
        warning "Application data directory not found"
    fi
}

# Backup logs
backup_logs() {
    log "Starting logs backup..."

    if [ -d "./logs" ]; then
        tar czf "${BACKUP_DIR}/logs_${BACKUP_NAME}.tar.gz" ./logs
        log "Logs backup completed: logs_${BACKUP_NAME}.tar.gz"
    else
        warning "Logs directory not found"
    fi
}

# Backup configuration
backup_config() {
    log "Starting configuration backup..."

    tar czf "${BACKUP_DIR}/config_${BACKUP_NAME}.tar.gz" \
        --exclude='.env' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        ./bot/config \
        ./config \
        ./*.yml \
        ./*.yaml \
        ./*.json \
        ./*.ini
    log "Configuration backup completed: config_${BACKUP_NAME}.tar.gz"
}

# Create backup manifest
create_manifest() {
    log "Creating backup manifest..."

    cat > "${BACKUP_DIR}/manifest_${BACKUP_NAME}.txt" << EOF
DBSBM Backup Manifest
=====================
Date: $(date)
Backup Name: ${BACKUP_NAME}
Host: $(hostname)
User: $(whoami)

Files included in this backup:
EOF

    # List all backup files
    for file in "${BACKUP_DIR}"/*"${BACKUP_NAME}"*; do
        if [ -f "$file" ]; then
            echo "- $(basename "$file") ($(du -h "$file" | cut -f1))" >> "${BACKUP_DIR}/manifest_${BACKUP_NAME}.txt"
        fi
    done

    echo "" >> "${BACKUP_DIR}/manifest_${BACKUP_NAME}.txt"
    echo "Total backup size: $(du -sh "${BACKUP_DIR}"/*"${BACKUP_NAME}"* | tail -1 | cut -f1)" >> "${BACKUP_DIR}/manifest_${BACKUP_NAME}.txt"

    log "Backup manifest created: manifest_${BACKUP_NAME}.txt"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last 7 days)..."

    find "${BACKUP_DIR}" -name "*.gz" -mtime +7 -delete
    find "${BACKUP_DIR}" -name "*.rdb" -mtime +7 -delete
    find "${BACKUP_DIR}" -name "*.sql" -mtime +7 -delete
    find "${BACKUP_DIR}" -name "manifest_*.txt" -mtime +7 -delete

    log "Old backups cleaned up"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    local failed=0

    for file in "${BACKUP_DIR}"/*"${BACKUP_NAME}"*; do
        if [ -f "$file" ]; then
            if [[ "$file" == *.gz ]]; then
                if ! gzip -t "$file" 2>/dev/null; then
                    error "Backup file is corrupted: $(basename "$file")"
                    failed=1
                fi
            fi
        fi
    done

    if [ $failed -eq 0 ]; then
        log "Backup integrity verification passed"
    else
        error "Backup integrity verification failed"
        exit 1
    fi
}

# Main backup function
main_backup() {
    log "Starting DBSBM backup process..."

    check_docker
    create_backup_dir

    # Run all backup functions
    backup_mysql
    backup_redis
    backup_app_data
    backup_logs
    backup_config

    create_manifest
    verify_backup
    cleanup_old_backups

    log "Backup process completed successfully!"
    log "Backup location: ${BACKUP_DIR}"

    # Show backup summary
    echo ""
    echo "=== Backup Summary ==="
    ls -lh "${BACKUP_DIR}"/*"${BACKUP_NAME}"*
    echo ""
    echo "Total backup size: $(du -sh "${BACKUP_DIR}"/*"${BACKUP_NAME}"* | tail -1 | cut -f1)"
}

# Restore function
restore_backup() {
    local backup_date=$1

    if [ -z "$backup_date" ]; then
        error "Please provide backup date (YYYYMMDD_HHMMSS format)"
        echo "Usage: $0 restore YYYYMMDD_HHMMSS"
        exit 1
    fi

    log "Starting restore from backup: ${backup_date}"

    # Check if backup files exist
    local backup_files=(
        "mysql_${backup_date}.sql.gz"
        "redis_volume_${backup_date}.tar.gz"
        "app_data_${backup_date}.tar.gz"
        "config_${backup_date}.tar.gz"
    )

    for file in "${backup_files[@]}"; do
        if [ ! -f "${BACKUP_DIR}/${file}" ]; then
            warning "Backup file not found: ${file}"
        fi
    done

    # Stop services before restore
    log "Stopping DBSBM services..."
    docker-compose down

    # Restore MySQL
    if [ -f "${BACKUP_DIR}/mysql_${backup_date}.sql.gz" ]; then
        log "Restoring MySQL data..."
        gunzip -c "${BACKUP_DIR}/mysql_${backup_date}.sql.gz" | docker exec -i dbsbm-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}"
    fi

    # Restore Redis
    if [ -f "${BACKUP_DIR}/redis_volume_${backup_date}.tar.gz" ]; then
        log "Restoring Redis data..."
        docker run --rm \
            -v dbsbm_redis_data:/data \
            -v "$(pwd)/${BACKUP_DIR}:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/redis_volume_${backup_date}.tar.gz"
    fi

    # Restore app data
    if [ -f "${BACKUP_DIR}/app_data_${backup_date}.tar.gz" ]; then
        log "Restoring application data..."
        tar xzf "${BACKUP_DIR}/app_data_${backup_date}.tar.gz"
    fi

    # Restore config
    if [ -f "${BACKUP_DIR}/config_${backup_date}.tar.gz" ]; then
        log "Restoring configuration..."
        tar xzf "${BACKUP_DIR}/config_${backup_date}.tar.gz"
    fi

    # Start services
    log "Starting DBSBM services..."
    docker-compose up -d

    log "Restore completed successfully!"
}

# Show usage
usage() {
    echo "DBSBM Backup Script"
    echo ""
    echo "Usage: $0 [backup|restore|list] [backup_date]"
    echo ""
    echo "Commands:"
    echo "  backup   - Create a new backup"
    echo "  restore  - Restore from a backup (requires backup_date)"
    echo "  list     - List available backups"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore 20240101_120000"
    echo "  $0 list"
}

# List backups
list_backups() {
    log "Available backups:"
    echo ""

    if [ -d "${BACKUP_DIR}" ]; then
        for manifest in "${BACKUP_DIR}"/manifest_*.txt; do
            if [ -f "$manifest" ]; then
                echo "=== $(basename "$manifest" .txt) ==="
                cat "$manifest"
                echo ""
            fi
        done
    else
        echo "No backups found"
    fi
}

# Main script logic
case "${1:-backup}" in
    backup)
        main_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    list)
        list_backups
        ;;
    *)
        usage
        exit 1
        ;;
esac
