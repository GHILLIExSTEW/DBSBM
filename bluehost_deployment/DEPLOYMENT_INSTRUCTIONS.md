# Bluehost Deployment Instructions

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
