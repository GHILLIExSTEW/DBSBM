# DBSBM Project Structure

This document outlines the organized structure of the DBSBM (Discord Betting Sports Bot Management) project.

## 📁 **Root Directory Structure**

```
DBSBM/
├── 📁 bot/                    # Main bot application
├── 📁 docs/                   # Documentation
├── 📁 scripts/                # Utility scripts
├── 📁 tests/                  # Test files
├── 📁 migrations/             # Database migrations
├── 📁 data/                   # Data files and cache
├── 📁 logs/                   # Log files
├── 📁 config/                 # Configuration files
├── 📁 audit_reports/          # Audit reports and analysis
├── 📁 PEM/                    # SSL certificates (if any)
├── 📄 README.md               # Project overview
├── 📄 LICENSE                 # License information
├── 📄 requirements.txt        # Python dependencies
├── 📄 .gitignore              # Git ignore rules
├── 📄 CONTRIBUTING.md         # Contribution guidelines
└── 📄 PROJECT_STRUCTURE.md    # This file
```

---

## 📁 **bot/ - Main Bot Application**

The core Discord bot application containing all the main functionality.

```
bot/
├── 📁 api/                    # API integrations
│   ├── __init__.py
│   └── sports_api.py          # Sports data API
├── 📁 commands/               # Discord slash commands
│   ├── __init__.py
│   ├── add_capper.py
│   ├── add_user.py
│   ├── admin_commands.py
│   ├── bet_commands.py
│   ├── game_commands.py
│   ├── parlay_commands.py
│   ├── player_prop_commands.py
│   ├── setup_commands.py
│   ├── stats_commands.py
│   └── ... (other command files)
├── 📁 config/                 # Configuration management
│   ├── __init__.py
│   ├── api_settings.py
│   ├── asset_paths.py
│   ├── database_mysql.py
│   └── ... (other config files)
├── 📁 data/                   # Database and data management
│   ├── __init__.py
│   ├── db_manager.py          # Database connection manager
│   ├── cache/                 # API response cache
│   ├── teams/                 # Team data files
│   └── ... (other data files)
├── 📁 services/               # Business logic services
│   ├── __init__.py
│   ├── admin_service.py
│   ├── analytics_service.py
│   ├── bet_service.py
│   ├── data_sync_service.py
│   ├── game_service.py
│   ├── live_game_channel_service.py
│   ├── user_service.py
│   ├── voice_service.py
│   └── ... (other service files)
├── 📁 static/                 # Static assets
│   ├── cache/                 # Optimized assets
│   ├── favicon.ico
│   ├── guilds/                # Guild-specific assets
│   ├── logos/                 # Team and league logos
│   └── ... (other static files)
├── 📁 templates/              # Web templates
│   ├── base.html
│   ├── guild_home.html
│   ├── guild_public.html
│   └── ... (other template files)
├── 📁 utils/                  # Utility functions
│   ├── __init__.py
│   ├── environment_validator.py    # Environment validation
│   ├── rate_limiter.py             # Rate limiting system
│   ├── performance_monitor.py      # Performance monitoring
│   ├── error_handler.py            # Error handling system
│   ├── api_sports.py               # API utilities
│   ├── asset_loader.py             # Asset loading utilities
│   ├── game_line_image_generator.py
│   ├── parlay_image_generator.py
│   ├── player_prop_image_generator.py
│   ├── league_dictionaries/        # League-specific data
│   └── ... (other utility files)
├── 📁 tests/                  # Test files
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_environment_validator.py
│   ├── test_services.py
│   ├── test_rate_limiter.py
│   ├── test_performance_monitor.py
│   └── ... (other test files)
├── 📁 cogs/                   # Discord.py cogs
│   └── __init__.py
├── 📁 assets/                 # Bot assets
│   ├── fonts/                 # Font files
│   └── ... (other asset files)
├── 📁 migrations/             # Database migrations
│   └── all_schema.sql
├── 📁 logs/                   # Bot-specific logs
├── 📁 docs/                   # Bot-specific documentation
├── 📁 scripts/                # Bot-specific scripts
├── __init__.py
├── main.py                    # Main bot entry point
└── webapp.py                  # Web application entry point
```

---

## 📁 **docs/ - Documentation**

Comprehensive documentation for the project.

```
docs/
├── 📄 API_DOCUMENTATION.md        # API documentation
├── 📄 COMPREHENSIVE_API_SYSTEM.md # System architecture
├── 📄 PRODUCTION_DEPLOYMENT.md    # Deployment guide
├── 📄 API_REFERENCE.md            # Complete API reference
├── 📄 DEPLOYMENT_GUIDE.md         # Deployment instructions
├── 📄 ENHANCED_PLAYER_PROPS.md    # Player props documentation
├── 📄 PARLAY_WORKFLOW_GUIDE.md    # Parlay workflow guide
└── 📄 ENHANCED_PLAYER_PROPS_SETUP.md # Player props setup
```

---

## 📁 **scripts/ - Utility Scripts**

Scripts for development, deployment, and maintenance.

```
scripts/
├── 📄 setup_development.py        # Development environment setup
├── 📄 init_mysql_db.py            # Database initialization
├── 📄 fetcher.py                  # Data fetching script
├── 📄 fetcher_main.py             # Main fetcher entry point
├── 📄 debug_*.py                  # Debug scripts
├── 📄 check_*.py                  # Health check scripts
├── 📄 clean_*.py                  # Cleanup scripts
├── 📄 fix_*.py                    # Fix scripts
├── 📄 verify_*.py                 # Verification scripts
├── 📄 validate_*.py               # Validation scripts
├── 📄 create_placeholder_logos.py # Logo creation script
├── 📄 download_league_logos.py    # Logo download script
└── ... (other utility scripts)
```

---

## 📁 **tests/ - Test Files**

Test files for the entire project.

```
tests/
├── 📄 conftest.py                 # Test configuration
├── 📄 test_dynamic_title.py       # Dynamic title tests
└── ... (other test files)
```

---

## 📁 **migrations/ - Database Migrations**

Database schema and migration files.

```
migrations/
├── 📄 all_schema.sql              # Complete database schema
└── 📄 sync_cappers_stats.sql      # Cappers stats sync
```

---

## 📁 **data/ - Data Files**

Data files, cache, and external data.

```
data/
├── 📄 datagolf_players_by_name.json # Golf player data
├── 📁 cache/                        # API response cache
└── ... (other data files)
```

---

## 📁 **logs/ - Log Files**

Application logs and debugging information.

```
logs/
├── 📄 download_logos.log           # Logo download logs
├── 📄 bot.log                      # Bot application logs
└── ... (other log files)
```

---

## 📁 **config/ - Configuration Files**

Configuration and setup files.

```
config/
├── 📄 .pre-commit-config.yaml      # Pre-commit hooks
├── 📄 mypy.ini                     # MyPy configuration
├── 📄 setup.py                     # Setup configuration
├── 📄 pyproject.toml               # Project configuration
└── ... (other config files)
```

---

## 📁 **audit_reports/ - Audit Reports**

Reports from system audits and analysis.

```
audit_reports/
├── 📄 COMPREHENSIVE_SYSTEM_AUDIT_REPORT.md
├── 📄 SECURITY_AUDIT_DETAILED.md
├── 📄 PERFORMANCE_SCALABILITY_AUDIT.md
├── 📄 SYSTEM_AUDIT_STATS.md
├── 📄 CLEANUP_SUMMARY.md
└── 📄 IMPROVEMENTS_IMPLEMENTED.md
```

---

## 📁 **PEM/ - SSL Certificates**

SSL certificates and security files (if any).

```
PEM/
└── ... (SSL certificate files)
```

---

## 🔧 **Key Files**

### **Root Level Files**
- `README.md` - Project overview and getting started guide
- `LICENSE` - Project license information
- `requirements.txt` - Python package dependencies
- `.gitignore` - Git ignore patterns
- `CONTRIBUTING.md` - Contribution guidelines

### **Bot Entry Points**
- `bot/main.py` - Main Discord bot application
- `bot/webapp.py` - Web application for bot management

### **Configuration**
- `config/pyproject.toml` - Project metadata and build configuration
- `config/.pre-commit-config.yaml` - Pre-commit hooks for code quality
- `config/mypy.ini` - Type checking configuration

### **Database**
- `migrations/all_schema.sql` - Complete database schema
- `scripts/init_mysql_db.py` - Database initialization script

---

## 🎯 **Organization Principles**

### **1. Separation of Concerns**
- **bot/**: Core application logic
- **docs/**: All documentation
- **scripts/**: Utility and maintenance scripts
- **tests/**: Test files
- **config/**: Configuration files

### **2. Modular Structure**
- Each major component has its own directory
- Clear separation between application code and utilities
- Logical grouping of related functionality

### **3. Scalability**
- Easy to add new commands, services, or utilities
- Clear patterns for organizing new code
- Consistent naming conventions

### **4. Maintainability**
- Clear file organization
- Comprehensive documentation
- Proper test structure
- Configuration management

---

## 📋 **File Naming Conventions**

### **Python Files**
- Use snake_case for file names
- Use descriptive names that indicate purpose
- Group related functionality in modules

### **Directories**
- Use lowercase with underscores for multi-word directories
- Use descriptive names that indicate contents

### **Configuration Files**
- Use descriptive names with appropriate extensions
- Group related configurations together

### **Documentation**
- Use descriptive names in Title Case
- Include file type in name (e.g., `API_REFERENCE.md`)

---

## 🚀 **Adding New Files**

### **New Commands**
- Add to `bot/commands/` directory
- Follow existing naming patterns
- Include proper imports and error handling

### **New Services**
- Add to `bot/services/` directory
- Follow service pattern with proper initialization
- Include error handling and logging

### **New Utilities**
- Add to `bot/utils/` directory
- Include comprehensive documentation
- Add corresponding tests

### **New Scripts**
- Add to `scripts/` directory
- Include proper error handling
- Add documentation if needed

### **New Tests**
- Add to appropriate test directory
- Follow existing test patterns
- Include comprehensive coverage

---

## 🔍 **Finding Files**

### **Quick Reference**
- **Bot Code**: `bot/` directory
- **Commands**: `bot/commands/`
- **Services**: `bot/services/`
- **Utilities**: `bot/utils/`
- **Configuration**: `config/`
- **Documentation**: `docs/`
- **Scripts**: `scripts/`
- **Tests**: `bot/tests/` and `tests/`

### **Search Patterns**
- Use IDE search functionality
- Check appropriate directories based on file type
- Follow naming conventions for consistency

---

This organized structure provides a clean, maintainable, and scalable foundation for the DBSBM project. All files are logically grouped and easy to locate, making development and maintenance efficient and straightforward. 