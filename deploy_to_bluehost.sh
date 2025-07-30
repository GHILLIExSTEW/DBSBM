#!/bin/bash

# Deploy Flask Application to Bluehost
# This script helps prepare and deploy the application

echo "=== Bluehost Flask Application Deployment ==="
echo ""

# Check if we're in the right directory
if [ ! -f "webapp.py" ]; then
    echo "Error: webapp.py not found. Please run this script from the project root."
    exit 1
fi

echo "1. Setting file permissions..."
chmod +x start_flask.sh
chmod +x stop_flask.sh
chmod +x restart_flask.sh
chmod +x check_status.sh

echo "2. Creating necessary directories..."
mkdir -p db_logs
mkdir -p bot/static
mkdir -p bot/templates

echo "3. Checking required files..."
REQUIRED_FILES=("webapp.py" "start_flask.sh" "stop_flask.sh" "restart_flask.sh" "check_status.sh" "requirements_webapp.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ Missing: $file"
    fi
done

echo ""
echo "4. Checking Python dependencies..."
if command -v python3 &> /dev/null; then
    echo "✓ Python3 found: $(python3 --version)"
else
    echo "✗ Python3 not found"
fi

if command -v pip3 &> /dev/null; then
    echo "✓ pip3 found"
else
    echo "✗ pip3 not found"
fi

echo ""
echo "5. Environment check..."
if [ -f ".env" ]; then
    echo "✓ .env file found"
else
    echo "✗ .env file not found - you'll need to create this"
    echo "   Required variables:"
    echo "   - FLASK_APP=webapp.py"
    echo "   - FLASK_ENV=production"
    echo "   - WEBAPP_PORT=25594"
    echo "   - MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB"
    echo "   - SECRET_KEY, API_KEY"
fi

echo ""
echo "=== Deployment Instructions ==="
echo ""
echo "1. Upload these files to your Bluehost directory:"
echo "   - webapp.py"
echo "   - start_flask.sh"
echo "   - stop_flask.sh"
echo "   - restart_flask.sh"
echo "   - check_status.sh"
echo "   - requirements_webapp.txt"
echo "   - bot/ (entire directory)"
echo "   - .env (with your configuration)"
echo ""
echo "2. SSH into your Bluehost server and run:"
echo "   cd /home4/kudnlmmy/public_html/website_2121475b/"
echo "   chmod +x *.sh"
echo "   pip3 install -r requirements_webapp.txt"
echo ""
echo "3. Test the application:"
echo "   ./start_flask.sh"
echo "   ./check_status.sh"
echo ""
echo "4. Configure cron job in Bluehost cPanel:"
echo "   - Go to Cron Jobs"
echo "   - Add: 0 0 1 1 0 /home4/kudnlmmy/public_html/website_2121475b/start_flask.sh"
echo ""
echo "5. Monitor the application:"
echo "   ./check_status.sh"
echo "   tail -f db_logs/flask_output.log"
echo ""
echo "=== Files to Upload ==="
echo "Essential files:"
ls -la webapp.py start_flask.sh stop_flask.sh restart_flask.sh check_status.sh requirements_webapp.txt 2>/dev/null || echo "Some files missing"
echo ""
echo "Bot directory:"
ls -la bot/ 2>/dev/null || echo "Bot directory not found" 