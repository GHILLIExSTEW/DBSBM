#!/usr/bin/env python3
"""
Bluehost Deployment Script for Bet Bot Manager Web Portal
This script helps automate the deployment process to Bluehost.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from bluehost_config import create_bluehost_setup, BLUEHOST_CONFIG

def check_requirements():
    """Check if all required files exist."""
    required_files = [
        'webapp.py',
        'bot/templates/base.html',
        'bot/templates/landing.html',
        'bot/static/favicon.webp',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("All required files found")
    return True

def create_deployment_package():
    """Create a deployment package for Bluehost."""
    print("Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = "bluehost_deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Copy necessary files
    files_to_copy = [
        'webapp.py',
        'bot/',
        'config/',
        'data/',
        'static/',
        'templates/',
        'requirements.txt',
        'bluehost_config.py',
        '.htaccess',
        '.env.template'
    ]
    
    for item in files_to_copy:
        src = item
        dst = os.path.join(deploy_dir, item)
        
        if os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            print(f"   Copied {item}")
        else:
            print(f"   Skipped {item} (not found)")
    
    # Create deployment instructions
    instructions = """# Bluehost Deployment Instructions

## 1. Upload Files
Upload all files from this directory to your Bluehost public_html folder.

## 2. Database Setup
1. Go to Bluehost cPanel
2. Open MySQL Databases
3. Create a new database
4. Create a database user
5. Assign user to database with all privileges

## 3. Environment Configuration
1. Rename `.env.template` to `.env`
2. Edit `.env` with your actual database credentials
3. Update API keys and other settings

## 4. File Permissions
Set the following permissions:
- Directories: 755
- Files: 644
- Python files: 755

## 5. Python Setup
1. Access SSH terminal in Bluehost
2. Navigate to your public_html directory
3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## 6. Test the Application
1. Visit your domain
2. Check if the web portal loads
3. Test all functionality

## 7. Troubleshooting
- Check error logs in cPanel
- Verify database connection
- Ensure all environment variables are set
- Test Python CGI execution

## Support
If you encounter issues, check the logs in your Bluehost cPanel.
"""
    
    with open(os.path.join(deploy_dir, "DEPLOYMENT_INSTRUCTIONS.md"), 'w') as f:
        f.write(instructions)
    
    print(f"Deployment package created in '{deploy_dir}'")
    return deploy_dir

def create_bluehost_webapp():
    """Create a Bluehost-specific webapp file."""
    print("Creating Bluehost-specific webapp...")
    
    bluehost_webapp = """#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Bluehost
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

# Import and run the Flask app
from webapp import app

if __name__ == '__main__':
    app.run()
"""
    
    with open('bluehost_webapp.py', 'w') as f:
        f.write(bluehost_webapp)
    
    # Make it executable
    os.chmod('bluehost_webapp.py', 0o755)
    print("Created bluehost_webapp.py")

def create_cgi_script():
    """Create a CGI script for Bluehost."""
    print("Creating CGI script...")
    
    cgi_script = """#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Bluehost
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

# Import the Flask app
from webapp import app

# Create WSGI application
application = app

if __name__ == '__main__':
    app.run()
"""
    
    # Create cgi-bin directory if it doesn't exist
    os.makedirs('cgi-bin', exist_ok=True)
    
    with open('cgi-bin/webapp.py', 'w') as f:
        f.write(cgi_script)
    
    # Make it executable
    os.chmod('cgi-bin/webapp.py', 0o755)
    print("Created cgi-bin/webapp.py")

def validate_configuration():
    """Validate the Bluehost configuration."""
    print("Validating configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print(".env file not found. Please create one from .env.template")
        return False
    
    # Check database configuration
    required_env_vars = [
        'MYSQL_HOST',
        'MYSQL_USER', 
        'MYSQL_PASSWORD',
        'MYSQL_DB',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("Configuration validated")
    return True

def create_test_script():
    """Create a test script for Bluehost."""
    print("Creating test script...")
    
    test_script = """#!/usr/bin/env python3
import os
import sys
import mysql.connector
from mysql.connector import Error

def test_database_connection():
    \"\"\"Test database connection.\"\"\"
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        if connection.is_connected():
            print("Database connection successful")
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   MySQL Version: {version[0]}")
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"Database connection failed: {e}")
        return False

def test_flask_app():
    \"\"\"Test Flask app import.\"\"\"
    try:
        from webapp import app
        print("Flask app import successful")
        return True
    except Exception as e:
        print(f"Flask app import failed: {e}")
        return False

def test_templates():
    \"\"\"Test template loading.\"\"\"
    try:
        from flask import render_template_string
        template = "Hello {{ name }}!"
        result = render_template_string(template, name="World")
        if result == "Hello World!":
            print("Template rendering successful")
            return True
        else:
            print("Template rendering failed")
            return False
    except Exception as e:
        print(f"Template rendering failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Bluehost tests...")
    print()
    
    db_success = test_database_connection()
    flask_success = test_flask_app()
    template_success = test_templates()
    
    print()
    if all([db_success, flask_success, template_success]):
        print("All tests passed! Your Bluehost setup is ready.")
    else:
        print("Some tests failed. Please check your configuration.")
"""
    
    with open('test_bluehost.py', 'w') as f:
        f.write(test_script)
    
    print("Created test_bluehost.py")

def main():
    """Main deployment function."""
    print("Bluehost Deployment Script")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("Deployment failed due to missing files")
        sys.exit(1)
    
    # Create Bluehost setup files
    create_bluehost_setup()
    
    # Create Bluehost-specific files
    create_bluehost_webapp()
    create_cgi_script()
    create_test_script()
    
    # Create deployment package
    deploy_dir = create_deployment_package()
    
    # Validate configuration
    validate_configuration()
    
    print("\nBluehost deployment preparation complete!")
    print(f"Deployment package: {deploy_dir}")
    print("\nNext steps:")
    print("1. Upload files to Bluehost")
    print("2. Set up MySQL database")
    print("3. Configure environment variables")
    print("4. Test the application")
    print("\nSee DEPLOYMENT_INSTRUCTIONS.md for detailed steps")

if __name__ == "__main__":
    main() 