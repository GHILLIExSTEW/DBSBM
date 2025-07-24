# DBSBM Cleanup Quick Reference Guide

## 🚀 Quick Start

### 1. Run the Automated Cleanup Script
```bash
# First, run in dry-run mode to see what will be cleaned
python scripts/system_cleanup.py --dry-run

# If the output looks good, run the actual cleanup
python scripts/system_cleanup.py

# Customize backup retention and cache size limits
python scripts/system_cleanup.py --backup-count 5 --cache-size-limit 2048
```

### 2. Manual Cleanup Tasks

#### High Priority (Do First)
- [ ] **Delete broken files**: `platinum.py.broken`, `platinum_api.py.broken`
- [ ] **Delete empty files**: `add_capper.py`
- [ ] **Remove empty directories**: `TEMP/`, `PEM/`

#### Medium Priority (Do Next)
- [ ] **Review duplicate documentation**: Consolidate strategy documents
- [ ] **Clean up deprecated code**: Remove or implement TODO comments
- [ ] **Optimize imports**: Standardize import patterns

#### Low Priority (Do Later)
- [ ] **Image optimization**: Convert PNG to WebP
- [ ] **Database migration**: Move CSV data to database
- [ ] **Performance tuning**: Optimize startup times

## 📋 Detailed Instructions

### Phase 1: Critical Cleanup (Week 1)

#### 1.1 Remove Broken Files
```bash
# These files are already handled by the cleanup script
# Manual removal if needed:
rm bot/commands/platinum.py.broken
rm bot/commands/platinum_api.py.broken
```

#### 1.2 Remove Empty Files
```bash
# Remove empty add_capper.py
rm bot/commands/add_capper.py
```

#### 1.3 Remove Empty Directories
```bash
# Remove empty directories
rmdir TEMP/
rmdir PEM/
```

### Phase 2: Data Cleanup (Week 2-3)

#### 2.1 Backup Management
```bash
# Keep only 3 most recent backups
# The cleanup script handles this automatically
python scripts/system_cleanup.py --backup-count 3
```

#### 2.2 Cache Cleanup
```bash
# Remove small cache files (< 1KB)
python scripts/system_cleanup.py --cache-size-limit 1024
```

#### 2.3 Documentation Consolidation
```bash
# Manually review and consolidate these files:
# - COMMUNITY_ENGAGEMENT_STRATEGIES.md
# - COMMUNITY_ENGAGEMENT_STRATEGIES_REVISED.md
# - COMMUNITY_ENGAGEMENT_STRATEGIES_UPDATED.md

# Keep only the most recent version
rm COMMUNITY_ENGAGEMENT_STRATEGIES.md
rm COMMUNITY_ENGAGEMENT_STRATEGIES_REVISED.md
# Keep: COMMUNITY_ENGAGEMENT_STRATEGIES_UPDATED.md
```

### Phase 3: Code Quality (Week 3-4)

#### 3.1 Remove Deprecated Code
```python
# In bot/services/game_service.py, remove:
async def fetch_and_save_daily_games(self):
    """Fetch and save daily games for all leagues (deprecated; use fetcher.py)."""
    # ... remove this entire method
```

#### 3.2 Implement TODO Comments
```python
# In bot/utils/voice_channel_updater.py, implement:
# TODO: Replace this with your actual reinitialization logic
# Replace with actual implementation or remove if not needed
```

#### 3.3 Standardize Imports
```python
# In main.py and other files, standardize to:
from bot.utils.some_module import some_function
# Instead of fallback imports
```

### Phase 4: Performance Optimization (Month 1-2)

#### 4.1 Image Optimization
```bash
# Convert PNG to WebP for smaller file sizes
# Use tools like ImageMagick or Pillow
for file in bot/static/logos/**/*.png; do
    convert "$file" "${file%.png}.webp"
done
```

#### 4.2 Database Migration
```sql
-- Move CSV data to database tables
-- Create tables for players.csv data
-- Import data from CSV to database
-- Remove large CSV files
```

## 🔍 Verification Steps

### After Each Phase
1. **Run tests**: `python -m pytest bot/tests/`
2. **Check functionality**: Verify bot starts and works correctly
3. **Monitor performance**: Check startup times and memory usage
4. **Review logs**: Ensure no errors in bot logs

### Success Metrics
- [ ] **Storage saved**: Target 50MB+ reduction
- [ ] **Files removed**: Target 100+ files cleaned
- [ ] **Tests passing**: Maintain 100% pass rate
- [ ] **Performance**: 10% faster startup time

## ⚠️ Important Notes

### Before Running Cleanup
1. **Backup your system**: Create a full backup before cleanup
2. **Test in development**: Run cleanup on a copy first
3. **Review dry-run output**: Always run with `--dry-run` first
4. **Check dependencies**: Ensure no files are referenced elsewhere

### Safety Measures
- The cleanup script has a `--dry-run` mode
- Files are not permanently deleted (use trash/recycle bin)
- Test suite should catch any broken functionality
- Monitor logs for any issues

### Rollback Plan
If something goes wrong:
1. **Restore from backup**
2. **Check git history** for recent changes
3. **Review cleanup logs** to identify issues
4. **Fix any broken imports** or references

## 📊 Progress Tracking

### Checklist Template
```
Phase 1 - Critical Cleanup:
□ Broken files removed
□ Empty files removed  
□ Empty directories removed
□ Tests still pass

Phase 2 - Data Cleanup:
□ Backup files cleaned
□ Cache files optimized
□ Documentation consolidated
□ Storage saved: ___ MB

Phase 3 - Code Quality:
□ Deprecated code removed
□ TODO comments addressed
□ Imports standardized
□ Code quality improved

Phase 4 - Performance:
□ Images optimized
□ Database migrated
□ Performance improved
□ Startup time: ___ seconds
```

## 🆘 Troubleshooting

### Common Issues
1. **Import errors**: Check for broken import references
2. **Missing files**: Verify files aren't referenced elsewhere
3. **Test failures**: Review what was removed
4. **Performance issues**: Check for missing dependencies

### Getting Help
1. **Check logs**: Review cleanup script output
2. **Review changes**: Use git diff to see what changed
3. **Test incrementally**: Run cleanup in smaller batches
4. **Ask for help**: If unsure, get assistance before proceeding

---

**Last Updated**: December 19, 2024  
**Next Review**: January 19, 2025 