"""
Bluehost Configuration for Bet Bot Manager Web Portal
This file contains all the necessary configuration for hosting on Bluehost.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Bluehost specific settings
BLUEHOST_CONFIG = {
    # Database settings for Bluehost MySQL
    'MYSQL_HOST': os.getenv('MYSQL_HOST', 'localhost'),
    'MYSQL_USER': os.getenv('MYSQL_USER', 'your_bluehost_username'),
    'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD', 'your_bluehost_password'),
    'MYSQL_DB': os.getenv('MYSQL_DB', 'your_bluehost_database'),
    'MYSQL_PORT': int(os.getenv('MYSQL_PORT', 3306)),
    
    # Web application settings
    'WEBAPP_PORT': int(os.getenv('WEBAPP_PORT', 25594)),
    'WEBAPP_HOST': os.getenv('WEBAPP_HOST', '0.0.0.0'),
    'FLASK_ENV': os.getenv('FLASK_ENV', 'production'),
    'FLASK_DEBUG': os.getenv('FLASK_DEBUG', '0').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-change-this-for-production'),
    
    # Logging settings
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'LOG_DIR': os.path.join(BASE_DIR, 'logs'),
    
    # Static and template directories
    'STATIC_FOLDER': os.path.join(BASE_DIR, 'bot', 'static'),
    'TEMPLATE_FOLDER': os.path.join(BASE_DIR, 'bot', 'templates'),
    
    # Cache settings
    'CACHE_DIR': os.path.join(BASE_DIR, 'data', 'cache'),
    'BACKUP_DIR': os.path.join(BASE_DIR, 'data', 'backups'),
    
    # API settings
    'API_KEY': os.getenv('API_KEY', ''),
    'API_SPORTS_KEY': os.getenv('API_SPORTS_KEY', ''),
    
    # Discord settings (if needed for web portal)
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN', ''),
    'TEST_GUILD_ID': os.getenv('TEST_GUILD_ID', ''),
}

# Bluehost specific paths
BLUEHOST_PATHS = {
    'public_html': '/home/your_username/public_html',
    'cgi_bin': '/home/your_username/public_html/cgi-bin',
    'logs': '/home/your_username/logs',
    'tmp': '/home/your_username/tmp',
}

# Database connection string for Bluehost
def get_database_url():
    """Get database connection URL for Bluehost."""
    return f"mysql://{BLUEHOST_CONFIG['MYSQL_USER']}:{BLUEHOST_CONFIG['MYSQL_PASSWORD']}@{BLUEHOST_CONFIG['MYSQL_HOST']}:{BLUEHOST_CONFIG['MYSQL_PORT']}/{BLUEHOST_CONFIG['MYSQL_DB']}"

# Bluehost specific requirements
BLUEHOST_REQUIREMENTS = [
    'Flask==2.3.3',
    'mysql-connector-python==8.1.0',
    'Werkzeug==2.3.7',
    'python-dotenv==1.0.0',
    'requests==2.31.0',
    'Pillow==10.0.1',
    'redis==5.0.1',
    'aiohttp==3.8.6',
    'discord.py==2.3.2',
    'asyncio-mqtt==0.16.1',
    'schedule==1.2.0',
    'pytz==2023.3',
    'python-dateutil==2.8.2',
    'urllib3==2.0.7',
    'certifi==2023.7.22',
    'charset-normalizer==3.2.0',
    'idna==3.4',
    'typing-extensions==4.7.1',
    'aiosignal==1.3.1',
    'async-timeout==4.0.3',
    'attrs==23.1.0',
    'frozenlist==1.4.0',
    'multidict==6.0.4',
    'yarl==1.9.2',
    'websockets==11.0.3',
    'aiofiles==23.2.1',
    'colorama==0.4.6',
    'packaging==23.1',
    'six==1.16.0',
    'click==8.1.7',
    'itsdangerous==2.1.2',
    'Jinja2==3.1.2',
    'MarkupSafe==2.1.3',
    'blinker==1.6.3',
]

# Bluehost deployment checklist
BLUEHOST_DEPLOYMENT_CHECKLIST = [
    "1. Upload all files to Bluehost via FTP or File Manager",
    "2. Set up MySQL database in Bluehost cPanel",
    "3. Configure environment variables in .htaccess or .env file",
    "4. Set proper file permissions (755 for directories, 644 for files)",
    "5. Install Python dependencies via SSH or cPanel",
    "6. Configure domain/subdomain to point to the application",
    "7. Set up SSL certificate if needed",
    "8. Test the application thoroughly",
    "9. Set up automated backups",
    "10. Monitor logs for any issues"
]

# Bluehost .htaccess configuration
HTACCESS_CONFIG = """
# Bluehost .htaccess configuration for Flask app
RewriteEngine On

# Handle Python CGI
AddHandler cgi-script .py

# Set Python path
SetEnv PYTHONPATH /home/your_username/public_html

# Redirect all requests to the Flask app
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /cgi-bin/webapp.py/$1 [L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# Cache static files
<FilesMatch "\\.(css|js|png|jpg|jpeg|gif|ico|webp)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 month"
</FilesMatch>
"""

# Bluehost environment variables template
ENV_TEMPLATE = """
# Bluehost Environment Variables
# Copy this to .env file in your Bluehost account

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_bluehost_username
MYSQL_PASSWORD=your_bluehost_password
MYSQL_DB=your_bluehost_database
MYSQL_PORT=3306

# Web Application
WEBAPP_PORT=25594
WEBAPP_HOST=0.0.0.0
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-change-this-for-production

# API Keys
API_KEY=your_api_key_here
API_SPORTS_KEY=your_api_sports_key_here

# Discord Bot (if needed)
DISCORD_TOKEN=your_discord_token_here
TEST_GUILD_ID=your_test_guild_id_here

# Logging
LOG_LEVEL=INFO
"""

def create_bluehost_setup():
    """Create Bluehost setup files."""
    # Create .htaccess file
    with open('.htaccess', 'w') as f:
        f.write(HTACCESS_CONFIG)
    
    # Create .env template
    with open('.env.template', 'w') as f:
        f.write(ENV_TEMPLATE)
    
    # Create requirements.txt for Bluehost
    with open('requirements_bluehost.txt', 'w') as f:
        f.write('\n'.join(BLUEHOST_REQUIREMENTS))
    
    print("Bluehost setup files created:")
    print("- .htaccess")
    print("- .env.template")
    print("- requirements_bluehost.txt")
    print("\nNext steps:")
    for step in BLUEHOST_DEPLOYMENT_CHECKLIST:
        print(step)

if __name__ == "__main__":
    create_bluehost_setup() 