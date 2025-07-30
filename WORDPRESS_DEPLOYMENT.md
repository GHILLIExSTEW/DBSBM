# WordPress + Flask Integration Deployment Instructions

## Step 1: Set Up WordPress on Bluehost

1. **Install WordPress:**
   - Log into Bluehost cPanel
   - Go to "Website" → "Install WordPress"
   - Follow the installation wizard
   - Choose a theme (recommend a modern, responsive theme)

2. **Install Required Plugins:**
   - Go to WordPress Admin → Plugins → Add New
   - Install and activate:
     - Advanced Custom Fields
     - Custom Post Types UI
     - WP REST API

## Step 2: Deploy Flask API

1. **Upload Flask API files:**
   - Upload `api_endpoints.py` to your Bluehost account
   - Create a subdomain (e.g., `app.yourdomain.com`) or use a subdirectory
   - Set up Python environment on Bluehost

2. **Configure environment variables:**
   ```bash
   # Create .env file
   MYSQL_HOST=localhost
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DB=your_database
   API_PORT=5000
   FLASK_DEBUG=0
   ```

3. **Install Python dependencies:**
   ```bash
   pip install flask flask-cors mysql-connector-python
   ```

4. **Test the API:**
   ```bash
   python api_endpoints.py
   ```
   Visit: `http://app.yourdomain.com:5000/api/health`

## Step 3: Install WordPress Plugin

1. **Upload the plugin:**
   - Zip the `betbot-wordpress-plugin` folder
   - Go to WordPress Admin → Plugins → Add New → Upload Plugin
   - Upload and activate the plugin

2. **Configure the plugin:**
   - Go to Settings → Bet Bot Manager
   - Set the API URL (e.g., `http://app.yourdomain.com:5000`)
   - Save settings

## Step 4: Create WordPress Pages

1. **Create Live Scores Page:**
   - Go to Pages → Add New
   - Title: "Live Scores"
   - Template: "Live Scores" (if using custom templates)
   - Or use shortcode: `[live_scores]`

2. **Create Guild Dashboard Page:**
   - Go to Pages → Add New
   - Title: "Guild Dashboard"
   - Template: "Guild Dashboard" (if using custom templates)
   - Or use shortcode: `[guild_stats]`

## Step 5: Upload Custom Templates (Optional)

1. **Upload page templates:**
   - Upload `wordpress_templates/page-live-scores.php` to your theme directory
   - Upload `wordpress_templates/page-guild-dashboard.php` to your theme directory
   - These will appear as template options when creating pages

## Step 6: Test the Integration

1. **Test API endpoints:**
   - Visit: `http://app.yourdomain.com:5000/api/guilds`
   - Visit: `http://app.yourdomain.com:5000/api/live-scores`

2. **Test WordPress pages:**
   - Visit your live scores page
   - Visit your guild dashboard page
   - Check browser console for any errors

## Troubleshooting

### Common Issues:

1. **API not accessible from WordPress:**
   - Check CORS settings in Flask API
   - Verify API URL in WordPress settings
   - Check firewall/security settings

2. **Database connection errors:**
   - Verify MySQL credentials in .env file
   - Check if database exists and has correct tables
   - Test database connection manually

3. **WordPress pages not loading data:**
   - Check browser console for JavaScript errors
   - Verify API endpoints are working
   - Check WordPress plugin settings

### Debug Steps:

1. **Test API directly:**
   ```bash
   curl http://app.yourdomain.com:5000/api/health
   ```

2. **Check WordPress debug log:**
   - Enable WP_DEBUG in wp-config.php
   - Check error logs in wp-content/debug.log

3. **Test database connection:**
   ```python
   import mysql.connector
   connection = mysql.connector.connect(
       host='localhost',
       user='your_username',
       password='your_password',
       database='your_database'
   )
   print("Database connected successfully!")
   ```

## Next Steps

1. **Customize the design** to match your WordPress theme
2. **Add more API endpoints** as needed
3. **Implement caching** for better performance
4. **Add authentication** if required
5. **Set up monitoring** and logging

## Support

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Verify API endpoints are accessible
3. Test database connectivity
4. Review WordPress error logs
