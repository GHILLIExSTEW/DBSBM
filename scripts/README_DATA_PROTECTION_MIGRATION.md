# Data Protection Migration Scripts

This directory contains scripts to run the data protection migration (`013_data_protection_tables.sql`) for the DBSBM system.

## Overview

The data protection migration creates the necessary database tables and infrastructure for:

- Data encryption at rest and in transit
- Data anonymization and pseudonymization
- Data retention and deletion policies
- Privacy impact assessment tools
- GDPR compliance automation

## Files

- `run_data_protection_migration.py` - Main Python migration script
- `run_data_protection_migration.bat` - Windows batch script
- `run_data_protection_migration.sh` - Unix/Linux shell script
- `README_DATA_PROTECTION_MIGRATION.md` - This documentation

## Prerequisites

1. **Python 3.7+** installed and in PATH
2. **MySQL database** running and accessible
3. **Environment variables** configured (see `.env` file)
4. **DBSBM project** properly set up

## Database Configuration

Ensure your `.env` file contains the following database configuration:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database_name
```

## Running the Migration

### Option 1: Windows (Recommended for Windows users)

1. Open Command Prompt or PowerShell
2. Navigate to the DBSBM root directory
3. Run the batch script:

```cmd
scripts\run_data_protection_migration.bat
```

### Option 2: Unix/Linux/macOS

1. Open Terminal
2. Navigate to the DBSBM root directory
3. Make the script executable (if not already):
   ```bash
   chmod +x scripts/run_data_protection_migration.sh
   ```
4. Run the shell script:
   ```bash
   ./scripts/run_data_protection_migration.sh
   ```

### Option 3: Direct Python Execution

1. Open Terminal/Command Prompt
2. Navigate to the DBSBM root directory
3. Run the Python script directly:

```bash
# Unix/Linux/macOS
python3 scripts/run_data_protection_migration.py

# Windows
python scripts/run_data_protection_migration.py
```

## What the Migration Does

The migration script will:

1. **Validate** the migration file exists and is readable
2. **Check** if the migration has already been run
3. **Execute** the SQL migration file
4. **Verify** all tables were created successfully
5. **Log** the results and any errors

### Tables Created

The migration creates the following tables:

- `encryption_metadata` - Stores encryption metadata for data protection
- `anonymized_data` - Stores anonymized data for privacy protection
- `pseudonymized_data` - Stores pseudonymized data for reversible privacy protection
- `retention_policies` - Defines data retention policies for compliance
- `privacy_assessments` - Stores privacy impact assessments for GDPR compliance
- `data_items` - Stores data items for retention management
- `data_archives` - Stores archived data before deletion
- `encryption_keys` - Stores encryption keys for data protection
- `data_protection_audit_log` - Audit log for data protection activities

### Default Data Inserted

The migration also inserts:

- **Default retention policies** for different data types
- **Placeholder encryption keys** for immediate use

## Migration Status

The script will check the current migration status and:

- **Skip** if already completed
- **Run** if not yet executed
- **Report** partial completion if some tables exist

## Logging

The migration script creates detailed logs:

- **Console output** - Real-time progress and results
- **Log file** - `migration_013_data_protection.log` in the current directory

## Error Handling

The script includes comprehensive error handling:

- **File validation** - Ensures migration file exists and is readable
- **Database connection** - Validates database connectivity
- **SQL execution** - Handles individual statement failures
- **Verification** - Confirms all tables were created
- **Rollback** - Logs errors for manual intervention if needed

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Check your `.env` file configuration
   - Ensure MySQL is running
   - Verify database credentials

2. **Migration File Not Found**

   - Ensure you're in the DBSBM root directory
   - Check that `migrations/013_data_protection_tables.sql` exists

3. **Permission Denied**

   - On Unix/Linux: `chmod +x scripts/run_data_protection_migration.sh`
   - On Windows: Run as Administrator if needed

4. **Python Not Found**
   - Install Python 3.7+ from python.org
   - Ensure Python is in your system PATH

### Manual Verification

To manually verify the migration:

```sql
-- Check if tables exist
SHOW TABLES LIKE '%encryption%';
SHOW TABLES LIKE '%anonymized%';
SHOW TABLES LIKE '%retention%';
SHOW TABLES LIKE '%privacy%';

-- Check default data
SELECT COUNT(*) FROM retention_policies;
SELECT COUNT(*) FROM encryption_keys;
```

## Rollback

If you need to rollback the migration:

```sql
-- Drop all data protection tables
DROP TABLE IF EXISTS data_protection_audit_log;
DROP TABLE IF EXISTS encryption_keys;
DROP TABLE IF EXISTS data_archives;
DROP TABLE IF EXISTS data_items;
DROP TABLE IF EXISTS privacy_assessments;
DROP TABLE IF EXISTS retention_policies;
DROP TABLE IF EXISTS pseudonymized_data;
DROP TABLE IF EXISTS anonymized_data;
DROP TABLE IF EXISTS encryption_metadata;
```

## Security Considerations

- The migration creates encryption infrastructure
- Default encryption keys are placeholders - replace with production keys
- Audit logging is enabled for compliance
- Retention policies are conservative by default

## Support

For issues with the migration:

1. Check the log file: `migration_013_data_protection.log`
2. Verify database connectivity
3. Review the error messages in the console output
4. Check the troubleshooting section above

## Next Steps

After successful migration:

1. **Test the DataProtectionService** - Run the test suite
2. **Configure production keys** - Replace placeholder encryption keys
3. **Review retention policies** - Adjust based on your needs
4. **Enable data protection features** - Integrate with your application
