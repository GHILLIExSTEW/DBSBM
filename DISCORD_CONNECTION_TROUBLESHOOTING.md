# 🔧 Discord Connection Troubleshooting Guide

This guide helps you resolve Discord connection issues with your DBSBM bot on PebbleHost.

## 🚨 Common Error: "Discord connection failed after all attempts"

### **Step 1: Run Diagnostic Tools**

First, run the diagnostic tools I created to identify the specific issue:

```bash
# Run the diagnostic tool
python bot/discord_connection_diagnostic.py

# Run the fix tool
python bot/fix_discord_connection.py
```

### **Step 2: Check Environment Variables**

Ensure your `.env` file in the `bot/` directory contains:

```env
# Discord Bot Configuration
DISCORD_TOKEN=MTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database Configuration
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_mysql_database
MYSQL_PORT=3306

# API Configuration
API_KEY=your_api_sports_key

# Test Configuration
TEST_GUILD_ID=your_test_guild_id
```

### **Step 3: Verify Discord Token**

1. **Check Token Format**: Your Discord token should start with `MT` and be ~59 characters long
2. **Regenerate Token**: If unsure, regenerate your bot token in the Discord Developer Portal
3. **Check Token Permissions**: Ensure the token is for the correct bot application

### **Step 4: Enable Required Intents**

In the Discord Developer Portal, enable these intents for your bot:

- ✅ **Message Content Intent**
- ✅ **Server Members Intent** 
- ✅ **Presence Intent**

**How to enable intents:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Go to "Bot" section
4. Scroll down to "Privileged Gateway Intents"
5. Enable all three intents
6. Save changes

### **Step 5: Check Bot Permissions**

Ensure your bot has these permissions:
- Send Messages
- Read Message History
- Use Slash Commands
- Manage Messages (if needed)
- Add Reactions

### **Step 6: PebbleHost-Specific Checks**

#### **Check PebbleHost Logs**
1. Go to your PebbleHost dashboard
2. Check the console logs for additional error messages
3. Look for any resource limit warnings

#### **Check Resource Limits**
- Ensure your bot has sufficient RAM allocated
- Check if the container has proper network access
- Verify file permissions in the container

#### **Network Connectivity**
The bot needs to reach:
- `discord.com` (for API calls)
- `gateway.discord.gg` (for WebSocket connection)
- Your database server
- API-Sports servers

### **Step 7: Common Fixes**

#### **Fix 1: Increase Timeout Settings**
The bot already has 5-minute timeouts, but you can increase them if needed.

#### **Fix 2: Check Database Connection**
Ensure your MySQL database is accessible from the PebbleHost container.

#### **Fix 3: Verify API Keys**
Make sure your API-Sports key is valid and has sufficient quota.

#### **Fix 4: Restart the Bot**
After making any changes:
1. Stop the bot in PebbleHost
2. Wait 30 seconds
3. Start the bot again

### **Step 8: Advanced Troubleshooting**

#### **Check Bot Status**
Run this command to test your bot token:
```bash
curl -H "Authorization: Bot YOUR_TOKEN_HERE" https://discord.com/api/v10/users/@me
```

#### **Test Network Connectivity**
```bash
# Test Discord connectivity
curl -I https://discord.com

# Test Discord gateway
curl -I https://gateway.discord.gg
```

#### **Check Python Dependencies**
Ensure all required packages are installed:
```bash
pip install -r requirements.txt
```

### **Step 9: Error-Specific Solutions**

#### **"Invalid token" Error**
- Regenerate your bot token in Discord Developer Portal
- Ensure the token is copied correctly (no extra spaces)
- Check that the token starts with `MT`

#### **"Privileged intents required" Error**
- Enable the required intents in Discord Developer Portal
- Restart the bot after enabling intents

#### **"Connection timeout" Error**
- Check your internet connection
- Verify PebbleHost network settings
- Try increasing timeout values in the code

#### **"Login failure" Error**
- Verify the bot token is correct
- Check if the bot application exists in Discord Developer Portal
- Ensure the bot hasn't been deleted or disabled

### **Step 10: Prevention**

#### **Best Practices**
1. **Regular Token Rotation**: Regenerate tokens periodically
2. **Monitor Logs**: Check PebbleHost logs regularly
3. **Test Changes**: Test configuration changes in a development environment first
4. **Backup Configuration**: Keep backups of your `.env` file

#### **Monitoring**
- Set up alerts for bot disconnections
- Monitor PebbleHost resource usage
- Track API rate limits

### **Step 11: Getting Help**

If the issue persists:

1. **Run the diagnostic tools** and share the reports
2. **Check PebbleHost logs** for additional errors
3. **Verify all environment variables** are set correctly
4. **Test with a simple bot** to isolate the issue
5. **Contact support** with the diagnostic reports

### **Quick Checklist**

- [ ] Discord token is set and valid
- [ ] Required intents are enabled
- [ ] Bot has proper permissions
- [ ] Database connection is working
- [ ] API keys are valid
- [ ] PebbleHost resources are sufficient
- [ ] Network connectivity is good
- [ ] Bot has been restarted after changes

### **Emergency Fixes**

If the bot is completely down:

1. **Immediate Restart**: Restart the bot in PebbleHost
2. **Check Token**: Verify the Discord token is still valid
3. **Enable Intents**: Ensure all required intents are enabled
4. **Check Logs**: Review PebbleHost logs for errors
5. **Test Connectivity**: Run the diagnostic tools

---

**Remember**: Most Discord connection issues are related to token validity, intents configuration, or network connectivity. The diagnostic tools will help identify the specific cause. 