# Bet Bot Manager - Bluehost Deployment Guide

This guide will help you deploy the Bet Bot Manager web portal to Bluehost hosting.

## 🚀 Quick Start

1. **Run the deployment script:**
   ```bash
   python deploy_bluehost.py
   ```

2. **Upload files to Bluehost**
3. **Set up MySQL database**
4. **Configure environment variables**
5. **Test the application**

## 📋 Prerequisites

- Bluehost hosting account
- Python 3.7+ support (available on Bluehost)
- MySQL database access
- FTP access or File Manager access

## 🛠️ Step-by-Step Deployment

### Step 1: Prepare Your Local Environment

1. **Clone or download the project files**
2. **Run the deployment script:**
   ```bash
   python deploy_bluehost.py
   ```
   This will create:
   - `bluehost_deployment/` directory with all necessary files
   - `.htaccess` file for Bluehost
   - `.env.template` for environment variables
   - `requirements_bluehost.txt` for Python dependencies

### Step 2: Set Up Bluehost Database

1. **Log into Bluehost cPanel**
2. **Navigate to MySQL Databases**
3. **Create a new database:**
   - Database name: `your_username_dbsbm`
   - Note down the database name
4. **Create a database user:**
   - Username: `your_username_dbsbm_user`
   - Password: Create a strong password
   - Note down the username and password
5. **Assign user to database:**
   - Select your user and database
   - Grant ALL PRIVILEGES
   - Click "Add"

### Step 3: Upload Files to Bluehost

#### Option A: Using File Manager
1. **Open Bluehost File Manager**
2. **Navigate to `public_html`**
3. **Upload all files from `bluehost_deployment/` directory**
4. **Set file permissions:**
   - Directories: 755
   - Files: 644
   - Python files: 755

#### Option B: Using FTP
1. **Connect via FTP client**
2. **Upload to `public_html` directory**
3. **Set permissions as above**

### Step 4: Configure Environment Variables

1. **Rename `.env.template` to `.env`**
2. **Edit `.env` file with your actual credentials:**
   ```env
   # Database Configuration
   MYSQL_HOST=localhost
   MYSQL_USER=your_username_dbsbm_user
   MYSQL_PASSWORD=your_database_password
   MYSQL_DB=your_username_dbsbm
   MYSQL_PORT=3306
   
   # Web Application
   WEBAPP_PORT=25594
   WEBAPP_HOST=0.0.0.0
   FLASK_ENV=production
   FLASK_DEBUG=0
   SECRET_KEY=your-secret-key-change-this-for-production
   
   # API Keys (if you have them)
   API_KEY=your_api_key_here
   API_SPORTS_KEY=your_api_sports_key_here
   
   # Logging
   LOG_LEVEL=INFO
   ```

### Step 5: Install Python Dependencies

1. **Access SSH terminal in Bluehost**
2. **Navigate to your public_html directory:**
   ```bash
   cd public_html
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements_bluehost.txt
   ```

### Step 6: Test the Application

1. **Run the test script:**
   ```bash
   python test_bluehost.py
   ```
2. **Visit your domain in a web browser**
3. **Check if the web portal loads correctly**

## 🔧 Configuration Details

### File Structure
```
public_html/
├── webapp.py                 # Main Flask application
├── bluehost_webapp.py        # Bluehost-specific entry point
├── cgi-bin/
│   └── webapp.py            # CGI script for Bluehost
├── bot/
│   ├── templates/           # HTML templates
│   └── static/             # Static files (CSS, JS, images)
├── config/                  # Configuration files
├── data/                    # Data files
├── .htaccess               # Apache configuration
├── .env                    # Environment variables
└── requirements_bluehost.txt # Python dependencies
```

### Database Schema
The application expects the following MySQL tables:
- `guilds` - Discord guild information
- `games` - Game data and scores
- `teams` - Team information
- `leagues` - League information
- `bets` - Betting data
- `users` - User information

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `MYSQL_HOST` | Database host | Yes |
| `MYSQL_USER` | Database username | Yes |
| `MYSQL_PASSWORD` | Database password | Yes |
| `MYSQL_DB` | Database name | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `API_KEY` | External API key | No |
| `API_SPORTS_KEY` | Sports API key | No |

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
- **Check:** Database credentials in `.env` file
- **Verify:** Database and user exist in Bluehost cPanel
- **Test:** Run `python test_bluehost.py`

#### 2. Flask App Not Loading
- **Check:** Python dependencies are installed
- **Verify:** File permissions (755 for Python files)
- **Test:** Import Flask in Python console

#### 3. Templates Not Found
- **Check:** `bot/templates/` directory exists
- **Verify:** Template files are uploaded
- **Test:** Flask template rendering

#### 4. Static Files Not Loading
- **Check:** `bot/static/` directory exists
- **Verify:** File permissions (644 for static files)
- **Test:** Direct URL access to static files

#### 5. 500 Internal Server Error
- **Check:** Bluehost error logs in cPanel
- **Verify:** Python CGI is enabled
- **Test:** Simple Python script execution

### Error Logs
- **Bluehost Error Logs:** cPanel → Error Logs
- **Application Logs:** `logs/` directory
- **Python Errors:** Check `.htaccess` configuration

### Performance Optimization

1. **Enable Caching:**
   - Configure Redis if available
   - Use file-based caching as fallback

2. **Optimize Images:**
   - Compress team logos and images
   - Use WebP format where possible

3. **Database Optimization:**
   - Add indexes to frequently queried columns
   - Use connection pooling

4. **CDN Setup:**
   - Configure Cloudflare or similar CDN
   - Cache static assets

## 🔒 Security Considerations

1. **Environment Variables:**
   - Never commit `.env` file to version control
   - Use strong, unique passwords
   - Rotate API keys regularly

2. **File Permissions:**
   - Set proper permissions (755 for dirs, 644 for files)
   - Restrict access to sensitive files

3. **Database Security:**
   - Use strong database passwords
   - Limit database user privileges
   - Enable SSL connections if available

4. **HTTPS:**
   - Enable SSL certificate in Bluehost
   - Force HTTPS redirects

## 📊 Monitoring

### Health Checks
- **Database:** Monitor connection status
- **Application:** Check response times
- **Errors:** Monitor error logs

### Logs
- **Access Logs:** Track user visits
- **Error Logs:** Monitor application errors
- **Performance Logs:** Track response times

## 🔄 Updates and Maintenance

### Regular Maintenance
1. **Backup Database:** Weekly automated backups
2. **Update Dependencies:** Monthly security updates
3. **Monitor Logs:** Daily error log review
4. **Performance Check:** Weekly performance monitoring

### Deployment Updates
1. **Backup Current Version**
2. **Upload New Files**
3. **Update Dependencies**
4. **Test Application**
5. **Monitor for Issues**

## 📞 Support

### Bluehost Support
- **Technical Issues:** Bluehost support team
- **Database Issues:** MySQL support in cPanel
- **File Permissions:** File Manager or FTP

### Application Support
- **Code Issues:** Check error logs
- **Configuration:** Review `.env` file
- **Performance:** Monitor resource usage

## 🎯 Success Metrics

After deployment, verify:
- ✅ Web portal loads without errors
- ✅ Database connections work
- ✅ Live scores display correctly
- ✅ Guild pages function properly
- ✅ Static assets load quickly
- ✅ Mobile responsiveness works
- ✅ SSL certificate is active

## 📝 Notes

- **Python Version:** Bluehost supports Python 3.7+
- **Memory Limits:** Be aware of Bluehost memory limits
- **CPU Usage:** Monitor for high CPU usage
- **Storage:** Keep logs and cache under control
- **Bandwidth:** Monitor monthly bandwidth usage

---

**Need Help?** Check the error logs in your Bluehost cPanel or run `python test_bluehost.py` to diagnose issues. 