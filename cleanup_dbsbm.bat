@echo off
REM DBSBM Cleanup Script for Windows
REM This script provides easy cleanup options for the DBSBM project

echo.
echo ========================================
echo    DBSBM Cleanup Script
echo ========================================
echo.

:menu
echo Choose cleanup option:
echo.
echo 1. Dry run (show what would be deleted)
echo 2. Full cleanup (delete files)
echo 3. Quick cleanup (cache only)
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto dry_run
if "%choice%"=="2" goto full_cleanup
if "%choice%"=="3" goto quick_cleanup
if "%choice%"=="4" goto exit
echo Invalid choice. Please try again.
goto menu

:dry_run
echo.
echo Running dry run...
python cleanup_dbsbm.py --dry-run
echo.
pause
goto menu

:full_cleanup
echo.
echo WARNING: This will permanently delete files!
echo.
set /p confirm="Are you sure you want to proceed? (y/N): "
if /i "%confirm%"=="y" (
    echo Running full cleanup...
    python cleanup_dbsbm.py
) else (
    echo Cleanup cancelled.
)
echo.
pause
goto menu

:quick_cleanup
echo.
echo Running quick cleanup (cache only)...
echo.
echo Deleting cache directories...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist htmlcov rmdir /s /q htmlcov
if exist .coverage del .coverage
if exist bot\data\__pycache__ rmdir /s /q bot\data\__pycache__

echo.
echo Quick cleanup completed!
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0
