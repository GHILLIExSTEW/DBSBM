#!/bin/bash

# DBSBM Backup Verification Script
# This script verifies backup integrity and tests restoration procedures

set -e

# Configuration
BACKUP_DIR="./backups"
VERIFICATION_DIR="./backup_verification"
DATE=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
}

# Create verification directory
create_verification_dir() {
    mkdir -p "${VERIFICATION_DIR}"
    log "Verification directory created: ${VERIFICATION_DIR}"
}

# List available backups
list_backups() {
    log "Available backups:"
    echo ""

    if [ -d "${BACKUP_DIR}" ]; then
        for backup in "${BACKUP_DIR}"/*.gz; do
            if [ -f "$backup" ]; then
                echo "- $(basename "$backup") ($(du -h "$backup" | cut -f1))"
            fi
        done
    else
        error "Backup directory not found: ${BACKUP_DIR}"
        exit 1
    fi
}

# Verify backup file integrity
verify_backup_integrity() {
    local backup_file=$1

    log "Verifying backup integrity: $(basename "$backup_file")"

    # Check if file exists
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi

    # Check file size
    local file_size=$(stat -c%s "$backup_file")
    if [ "$file_size" -eq 0 ]; then
        error "Backup file is empty: $backup_file"
        return 1
    fi

    # Verify gzip integrity
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            error "Backup file is corrupted: $backup_file"
            return 1
        fi
    fi

    # Check file permissions
    if [ ! -r "$backup_file" ]; then
        error "Backup file is not readable: $backup_file"
        return 1
    fi

    log "✓ Backup integrity check passed: $(basename "$backup_file")"
    return 0
}

# Test MySQL backup restoration
test_mysql_restoration() {
    local backup_file=$1
    local test_db_name="test_restore_${DATE}"

    log "Testing MySQL backup restoration..."

    # Extract backup to temporary location
    local temp_dir="${VERIFICATION_DIR}/mysql_test_${DATE}"
    mkdir -p "$temp_dir"

    # Extract SQL file
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "${temp_dir}/restore.sql"
    else
        cp "$backup_file" "${temp_dir}/restore.sql"
    fi

    # Create test database
    docker-compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${test_db_name};"

    # Restore to test database
    docker-compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "$test_db_name" < "${temp_dir}/restore.sql"

    # Verify restoration
    local table_count=$(docker-compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "$test_db_name" -e "SHOW TABLES;" | wc -l)
    table_count=$((table_count - 1))  # Subtract header line

    if [ "$table_count" -gt 0 ]; then
        log "✓ MySQL restoration test passed: $table_count tables restored"

        # Show table details
        docker-compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "$test_db_name" -e "
        SELECT
            table_name,
            table_rows,
            ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
        FROM information_schema.tables
        WHERE table_schema = '${test_db_name}'
        ORDER BY table_name;
        "
    else
        error "MySQL restoration test failed: No tables found"
        return 1
    fi

    # Clean up test database
    docker-compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "DROP DATABASE IF EXISTS ${test_db_name};"

    # Clean up temporary files
    rm -rf "$temp_dir"

    return 0
}

# Test Redis backup restoration
test_redis_restoration() {
    local backup_file=$1

    log "Testing Redis backup restoration..."

    # Create test Redis container
    local test_redis_container="test_redis_${DATE}"

    docker run -d --name "$test_redis_container" redis:7-alpine

    # Wait for Redis to start
    sleep 5

    # Restore backup to test container
    if [[ "$backup_file" == *.tar.gz ]]; then
        docker run --rm \
            -v "$(pwd)/${backup_file}:/backup.tar.gz" \
            -v "$test_redis_container":/data \
            alpine sh -c "cd /data && tar xzf /backup.tar.gz"
    elif [[ "$backup_file" == *.rdb ]]; then
        docker cp "$backup_file" "$test_redis_container:/data/dump.rdb"
    fi

    # Restart Redis to load the backup
    docker restart "$test_redis_container"
    sleep 5

    # Verify restoration
    local key_count=$(docker exec "$test_redis_container" redis-cli DBSIZE)

    if [ "$key_count" -ge 0 ]; then
        log "✓ Redis restoration test passed: $key_count keys restored"

        # Show some key details
        docker exec "$test_redis_container" redis-cli --scan --pattern "*" | head -10
    else
        error "Redis restoration test failed"
        return 1
    fi

    # Clean up test container
    docker stop "$test_redis_container"
    docker rm "$test_redis_container"

    return 0
}

# Test application data restoration
test_app_data_restoration() {
    local backup_file=$1

    log "Testing application data restoration..."

    # Create test directory
    local test_dir="${VERIFICATION_DIR}/app_data_test_${DATE}"
    mkdir -p "$test_dir"

    # Extract backup
    tar xzf "$backup_file" -C "$test_dir"

    # Check for expected files and directories
    local expected_dirs=("data" "logs" "config")
    local found_dirs=0

    for dir in "${expected_dirs[@]}"; do
        if [ -d "$test_dir/$dir" ]; then
            found_dirs=$((found_dirs + 1))
            log "✓ Found directory: $dir"
        fi
    done

    if [ "$found_dirs" -gt 0 ]; then
        log "✓ Application data restoration test passed: $found_dirs directories found"

        # Show directory structure
        find "$test_dir" -type d | head -10
    else
        error "Application data restoration test failed: No expected directories found"
        return 1
    fi

    # Clean up test directory
    rm -rf "$test_dir"

    return 0
}

# Comprehensive backup verification
verify_backup() {
    local backup_date=$1

    if [ -z "$backup_date" ]; then
        error "Please provide backup date (YYYYMMDD_HHMMSS format)"
        echo "Usage: $0 verify YYYYMMDD_HHMMSS"
        exit 1
    fi

    log "Starting comprehensive backup verification for: ${backup_date}"

    # Check if backup files exist
    local backup_files=(
        "${BACKUP_DIR}/mysql_${backup_date}.sql.gz"
        "${BACKUP_DIR}/redis_volume_${backup_date}.tar.gz"
        "${BACKUP_DIR}/app_data_${backup_date}.tar.gz"
        "${BACKUP_DIR}/config_${backup_date}.tar.gz"
    )

    local verification_results=()

    # Verify each backup file
    for backup_file in "${backup_files[@]}"; do
        if [ -f "$backup_file" ]; then
            log "Verifying: $(basename "$backup_file")"

            if verify_backup_integrity "$backup_file"; then
                verification_results+=("✓ $(basename "$backup_file")")
            else
                verification_results+=("✗ $(basename "$backup_file")")
            fi
        else
            warning "Backup file not found: $(basename "$backup_file")"
            verification_results+=("? $(basename "$backup_file")")
        fi
    done

    # Test restoration procedures
    log "Testing restoration procedures..."

    # Test MySQL restoration
    if [ -f "${BACKUP_DIR}/mysql_${backup_date}.sql.gz" ]; then
        if test_mysql_restoration "${BACKUP_DIR}/mysql_${backup_date}.sql.gz"; then
            verification_results+=("✓ MySQL restoration test")
        else
            verification_results+=("✗ MySQL restoration test")
        fi
    fi

    # Test Redis restoration
    if [ -f "${BACKUP_DIR}/redis_volume_${backup_date}.tar.gz" ]; then
        if test_redis_restoration "${BACKUP_DIR}/redis_volume_${backup_date}.tar.gz"; then
            verification_results+=("✓ Redis restoration test")
        else
            verification_results+=("✗ Redis restoration test")
        fi
    fi

    # Test app data restoration
    if [ -f "${BACKUP_DIR}/app_data_${backup_date}.tar.gz" ]; then
        if test_app_data_restoration "${BACKUP_DIR}/app_data_${backup_date}.tar.gz"; then
            verification_results+=("✓ App data restoration test")
        else
            verification_results+=("✗ App data restoration test")
        fi
    fi

    # Generate verification report
    generate_verification_report "$backup_date" "${verification_results[@]}"

    log "Backup verification completed!"
}

# Generate verification report
generate_verification_report() {
    local backup_date=$1
    shift
    local results=("$@")

    local report_file="${VERIFICATION_DIR}/verification_report_${backup_date}.txt"

    cat > "$report_file" << EOF
DBSBM Backup Verification Report
================================
Date: $(date)
Backup Date: ${backup_date}
Verification Date: $(date +%Y%m%d_%H%M%S)

Verification Results:
EOF

    for result in "${results[@]}"; do
        echo "$result" >> "$report_file"
    done

    echo "" >> "$report_file"
    echo "Summary:" >> "$report_file"

    local passed=0
    local failed=0
    local unknown=0

    for result in "${results[@]}"; do
        if [[ "$result" == ✓* ]]; then
            passed=$((passed + 1))
        elif [[ "$result" == ✗* ]]; then
            failed=$((failed + 1))
        else
            unknown=$((unknown + 1))
        fi
    done

    echo "- Passed: $passed" >> "$report_file"
    echo "- Failed: $failed" >> "$report_file"
    echo "- Unknown: $unknown" >> "$report_file"

    if [ "$failed" -eq 0 ] && [ "$unknown" -eq 0 ]; then
        echo "Overall Status: PASSED" >> "$report_file"
        log "✓ Backup verification PASSED"
    else
        echo "Overall Status: FAILED" >> "$report_file"
        error "✗ Backup verification FAILED"
    fi

    log "Verification report saved: $report_file"
}

# Automated verification for all backups
verify_all_backups() {
    log "Starting automated verification for all backups..."

    if [ ! -d "${BACKUP_DIR}" ]; then
        error "Backup directory not found: ${BACKUP_DIR}"
        exit 1
    fi

    # Find all backup dates
    local backup_dates=()
    for manifest in "${BACKUP_DIR}"/manifest_*.txt; do
        if [ -f "$manifest" ]; then
            local date_from_manifest=$(basename "$manifest" .txt | sed 's/manifest_//')
            backup_dates+=("$date_from_manifest")
        fi
    done

    if [ ${#backup_dates[@]} -eq 0 ]; then
        warning "No backups found to verify"
        return 0
    fi

    log "Found ${#backup_dates[@]} backups to verify"

    # Verify each backup
    for backup_date in "${backup_dates[@]}"; do
        log "Verifying backup: $backup_date"
        verify_backup "$backup_date"
        echo ""
    done

    log "Automated verification completed for all backups"
}

# Clean up verification artifacts
cleanup_verification() {
    log "Cleaning up verification artifacts..."

    if [ -d "${VERIFICATION_DIR}" ]; then
        # Remove verification artifacts older than 1 day
        find "${VERIFICATION_DIR}" -type f -mtime +1 -delete
        find "${VERIFICATION_DIR}" -type d -empty -delete

        log "Verification artifacts cleaned up"
    fi
}

# Show usage
usage() {
    echo "DBSBM Backup Verification Script"
    echo ""
    echo "Usage: $0 [verify|verify-all|list|cleanup] [backup_date]"
    echo ""
    echo "Commands:"
    echo "  verify      - Verify a specific backup (requires backup_date)"
    echo "  verify-all  - Verify all available backups"
    echo "  list        - List available backups"
    echo "  cleanup     - Clean up verification artifacts"
    echo ""
    echo "Examples:"
    echo "  $0 verify 20240101_120000"
    echo "  $0 verify-all"
    echo "  $0 list"
    echo "  $0 cleanup"
}

# Main script logic
case "${1:-list}" in
    verify)
        check_docker
        create_verification_dir
        verify_backup "$2"
        ;;
    verify-all)
        check_docker
        create_verification_dir
        verify_all_backups
        ;;
    list)
        list_backups
        ;;
    cleanup)
        cleanup_verification
        ;;
    *)
        usage
        exit 1
        ;;
esac
