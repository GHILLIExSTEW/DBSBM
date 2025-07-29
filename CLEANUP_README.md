# DBSBM Cleanup Scripts

This directory contains cleanup scripts to safely remove unnecessary files from the DBSBM project and free up disk space.

## 📁 Files

- `cleanup_dbsbm.py` - Main Python cleanup script
- `cleanup_dbsbm.bat` - Windows batch script with menu
- `cleanup_dbsbm.sh` - Unix/Linux shell script with menu
- `CLEANUP_README.md` - This documentation

## 🚀 Quick Start

### Windows Users

```cmd
# Run the batch script
cleanup_dbsbm.bat

# Or run the Python script directly
python cleanup_dbsbm.py --dry-run
```

### Unix/Linux Users

```bash
# Make the script executable
chmod +x cleanup_dbsbm.sh

# Run the shell script
./cleanup_dbsbm.sh

# Or run the Python script directly
python3 cleanup_dbsbm.py --dry-run
```

## 🔧 Usage Options

### 1. Dry Run (Recommended First)

Shows what would be deleted without actually deleting anything:

```bash
python cleanup_dbsbm.py --dry-run
```

### 2. Full Cleanup

Removes all unnecessary files:

```bash
python cleanup_dbsbm.py
```

### 3. Quick Cleanup (Cache Only)

Only removes cache directories:

```bash
# Windows
cleanup_dbsbm.bat

# Unix/Linux
./cleanup_dbsbm.sh
```

Then select option 3.

## 🗑️ What Gets Cleaned Up

### High Priority (Safe to Delete)

- **Cache Directories**: `__pycache__/`, `.pytest_cache/`, `htmlcov/`
- **Empty Files**: `long_functions_report.txt`, corrupted files
- **Temporary Test Files**: `test_bot_startup.py`, `test_redis_timeout.py`, `debug_env_test.py`
- **Old Log Files**: Logs older than 7 days
- **Old Backup Files**: Backups older than 7 days
- **Old Cache Files**: Cache files older than 3 days

### Medium Priority (Consider for Deletion)

- **Duplicate Documentation**: Outdated audit reports and task lists
- **Migration Logs**: Old migration log files
- **Large Files**: Large images that can be regenerated

### Low Priority (Optional)

- **Virtual Environment**: `.venv310/` (can be recreated)
- **Coverage Reports**: `.coverage` file

## 📊 Expected Space Savings

| **Category**        | **Estimated Size** | **Files**                                    |
| ------------------- | ------------------ | -------------------------------------------- |
| **Cache Files**     | ~50MB              | `__pycache__/`, `.pytest_cache/`, `htmlcov/` |
| **Log Files**       | ~200MB             | Various log files                            |
| **Backup Files**    | ~17MB              | Old backup files                             |
| **Documentation**   | ~100KB             | Duplicate docs                               |
| **Test Files**      | ~50KB              | Temporary test files                         |
| **Total Estimated** | **~267MB**         | Significant cleanup                          |

## ⚠️ Safety Features

### What's Protected

- **Core Application**: `bot/` directory
- **Configuration**: `config/` directory
- **Documentation**: `docs/` directory
- **Database**: `migrations/` directory
- **Dependencies**: `requirements.txt`
- **Docker Files**: `Dockerfile`, `docker-compose.yml`
- **Version Control**: `.git/` directory

### Confirmation Prompts

- Large files require user confirmation
- Virtual environment deletion requires confirmation
- Full cleanup warns before proceeding

### Error Handling

- Graceful error handling for permission issues
- Continues cleanup even if individual files fail
- Detailed logging of all actions

## 🔍 Dry Run Output Example

```
2025-07-28 21:27:49,987 - INFO - 🚀 Starting DBSBM cleanup process...
2025-07-28 21:27:49,987 - INFO - 🔍 DRY RUN MODE - No files will be deleted
2025-07-28 21:27:49,988 - INFO - 🧹 Cleaning up cache directories...
2025-07-28 21:27:49,988 - INFO - [DRY RUN] DELETE DIRECTORY: __pycache__
2025-07-28 21:27:49,989 - INFO - [DRY RUN] DELETE DIRECTORY: .pytest_cache
2025-07-28 21:27:49,997 - INFO - [DRY RUN] DELETE DIRECTORY: htmlcov
2025-07-28 21:27:49,997 - INFO - 🗑️ Cleaning up empty files...
2025-07-28 21:27:49,998 - INFO - [DRY RUN] DELETE FILE: long_functions_report.txt
...
2025-07-28 21:27:50,390 - INFO - ✅ Cleanup process completed!
2025-07-28 21:27:50,390 - INFO - 📊 Cleanup Statistics:
2025-07-28 21:27:50,390 - INFO -   Files deleted: 0
2025-07-28 21:27:50,390 - INFO -   Directories deleted: 0
2025-07-28 21:27:50,390 - INFO -   Errors encountered: 0
```

## 🛠️ Advanced Usage

### Command Line Options

```bash
# Show help
python cleanup_dbsbm.py --help

# Dry run (safe)
python cleanup_dbsbm.py --dry-run

# Full cleanup
python cleanup_dbsbm.py

# Force mode (skip confirmations)
python cleanup_dbsbm.py --force
```

### Custom Cleanup

You can modify the script to add custom cleanup rules:

1. Edit `cleanup_dbsbm.py`
2. Add files to the appropriate lists:
   - `self.cache_dirs` - Cache directories
   - `self.empty_files` - Empty files
   - `self.temp_test_files` - Temporary test files
   - `self.duplicate_docs` - Duplicate documentation
   - `self.migration_logs` - Migration logs

## 🔄 After Cleanup

### Recreate Virtual Environment (if deleted)

```bash
# Windows
python -m venv .venv310
.venv310\Scripts\activate
pip install -r requirements.txt

# Unix/Linux
python3 -m venv .venv310
source .venv310/bin/activate
pip install -r requirements.txt
```

### Regenerate Cache Files

```bash
# Run tests to regenerate cache
python -m pytest bot/tests/ --tb=short

# Generate coverage report
python -m pytest --cov=bot --cov-report=html
```

## 🚨 Troubleshooting

### Permission Errors

```bash
# Windows: Run as Administrator
# Unix/Linux: Use sudo if needed
sudo python3 cleanup_dbsbm.py --dry-run
```

### Python Not Found

```bash
# Use python3 instead of python
python3 cleanup_dbsbm.py --dry-run
```

### Script Not Executable (Unix/Linux)

```bash
chmod +x cleanup_dbsbm.sh
./cleanup_dbsbm.sh
```

## 📝 Maintenance

### Regular Cleanup Schedule

- **Weekly**: Run quick cleanup (cache only)
- **Monthly**: Run full cleanup
- **Before Releases**: Run full cleanup to reduce repository size

### Monitoring Space Usage

```bash
# Check directory sizes
du -sh *

# Check specific directories
du -sh bot/data/cache/
du -sh logs/
du -sh bot/data/backups/
```

## 🤝 Contributing

To add new cleanup rules:

1. Identify files/directories to clean up
2. Add them to the appropriate list in `cleanup_dbsbm.py`
3. Test with `--dry-run` first
4. Update this documentation

## 📞 Support

If you encounter issues:

1. Run with `--dry-run` to see what would be deleted
2. Check the logs for error messages
3. Ensure you have proper permissions
4. Verify the script is in the correct directory

---

**Note**: Always run `--dry-run` first to see what will be deleted before running the actual cleanup!
