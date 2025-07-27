@echo off
echo ============================================
echo DATABASE SETUP FOR BETTING BOT
echo ============================================
echo.

echo Starting database setup...
echo.

echo Step 1: Creating core tables...
mysql -u %MYSQL_USER% -p%MYSQL_PASSWORD% -h %MYSQL_HOST% -P %MYSQL_PORT% %MYSQL_DB% < database_setup_part1_core.sql
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create core tables
    pause
    exit /b 1
)
echo ✓ Core tables created successfully
echo.

echo Step 2: Creating guild settings tables...
mysql -u %MYSQL_USER% -p%MYSQL_PASSWORD% -h %MYSQL_HOST% -P %MYSQL_PORT% %MYSQL_DB% < database_setup_part2_guild_settings.sql
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create guild settings tables
    pause
    exit /b 1
)
echo ✓ Guild settings tables created successfully
echo.

echo Step 3: Creating ML tables...
mysql -u %MYSQL_USER% -p%MYSQL_PASSWORD% -h %MYSQL_HOST% -P %MYSQL_PORT% %MYSQL_DB% < database_setup_part3_ml_tables.sql
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create ML tables
    pause
    exit /b 1
)
echo ✓ ML tables created successfully
echo.

echo ============================================
echo DATABASE SETUP COMPLETED SUCCESSFULLY!
echo ============================================
echo.
echo The bot should now work without the ml_models error.
echo.
pause
