# Database Setup Script for Betting Bot
# PowerShell version with better error handling

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DATABASE SETUP FOR BETTING BOT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if MySQL is available
try {
    $mysqlVersion = mysql --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ MySQL client found: $mysqlVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ MySQL client not found. Please install MySQL client." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ MySQL client not found. Please install MySQL client." -ForegroundColor Red
    exit 1
}

# Get database credentials
Write-Host "Enter your database credentials:" -ForegroundColor Yellow
$MYSQL_HOST = Read-Host "MySQL Host (e.g., localhost)"
$MYSQL_PORT = Read-Host "MySQL Port (default: 3306)"
if ([string]::IsNullOrEmpty($MYSQL_PORT)) { $MYSQL_PORT = "3306" }
$MYSQL_USER = Read-Host "MySQL Username"
$MYSQL_PASSWORD = Read-Host "MySQL Password" -AsSecureString
$MYSQL_DB = Read-Host "Database Name"

# Convert secure string to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MYSQL_PASSWORD)
$MYSQL_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

Write-Host ""
Write-Host "Testing database connection..." -ForegroundColor Yellow

# Test connection
$testCmd = "mysql -u `"$MYSQL_USER`" -p`"$MYSQL_PASSWORD`" -h `"$MYSQL_HOST`" -P `"$MYSQL_PORT`" `"$MYSQL_DB`" -e `"SELECT 'Connection successful!' as status;`" 2>&1"
$testResult = Invoke-Expression $testCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database connection successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Database connection failed!" -ForegroundColor Red
    Write-Host "Error: $testResult" -ForegroundColor Red
    Write-Host "Please check your credentials and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting database setup..." -ForegroundColor Yellow

# Function to run SQL file
function Run-SQLFile {
    param(
        [string]$FileName,
        [string]$Description
    )

    Write-Host "Step: $Description" -ForegroundColor Cyan
    $sqlCmd = "mysql -u `"$MYSQL_USER`" -p`"$MYSQL_PASSWORD`" -h `"$MYSQL_HOST`" -P `"$MYSQL_PORT`" `"$MYSQL_DB`" < `"$FileName`" 2>&1"
    $result = Invoke-Expression $sqlCmd

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $Description completed successfully!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ $Description failed!" -ForegroundColor Red
        Write-Host "Error: $result" -ForegroundColor Red
        return $false
    }
}

# Run setup steps
$success = $true

# Step 1: Quick fix for ml_models
if (Test-Path "quick_fix_ml_models.sql") {
    $success = Run-SQLFile "quick_fix_ml_models.sql" "Creating ml_models table (quick fix)"
    if (-not $success) { exit 1 }
} else {
    Write-Host "✗ quick_fix_ml_models.sql not found!" -ForegroundColor Red
    exit 1
}

# Step 2: Core tables
if (Test-Path "database_setup_part1_core.sql") {
    $success = Run-SQLFile "database_setup_part1_core.sql" "Creating core tables"
    if (-not $success) { exit 1 }
} else {
    Write-Host "✗ database_setup_part1_core.sql not found!" -ForegroundColor Red
    exit 1
}

# Step 3: Guild settings
if (Test-Path "database_setup_part2_guild_settings.sql") {
    $success = Run-SQLFile "database_setup_part2_guild_settings.sql" "Creating guild settings tables"
    if (-not $success) { exit 1 }
} else {
    Write-Host "✗ database_setup_part2_guild_settings.sql not found!" -ForegroundColor Red
    exit 1
}

# Step 4: ML tables
if (Test-Path "database_setup_part3_ml_tables.sql") {
    $success = Run-SQLFile "database_setup_part3_ml_tables.sql" "Creating ML tables"
    if (-not $success) { exit 1 }
} else {
    Write-Host "✗ database_setup_part3_ml_tables.sql not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "DATABASE SETUP COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "The bot should now work without the ml_models error." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"
