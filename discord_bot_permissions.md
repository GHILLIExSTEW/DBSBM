# Discord Bot Permissions for Bet Tracking AI

## Required Permissions

### Server Management
- **Manage Server** - Required for server-wide settings and configurations
- **Manage Roles** - Needed to create and manage custom roles for betting features
- **Manage Channels** - Required to create and organize betting channels
- **Manage Webhooks** - Needed for automated notifications and score updates
- **Manage Emojis and Stickers** - For custom betting-related emojis and reactions

### Channel Permissions
- **View Channels** - Required to see all channels in the server
- **Send Messages** - Essential for posting betting plays and updates
- **Send Messages in Threads** - For organized betting discussions
- **Use Slash Commands** - For interactive betting commands
- **Add Reactions** - For voting on plays and reactions to results
- **Use External Emojis** - For sports team emojis and betting symbols
- **Use External Stickers** - For custom betting stickers
- **Attach Files** - For uploading betting reports and analytics
- **Embed Links** - For linking to live scores and analytics
- **Read Message History** - To track betting history and performance
- **Mention Everyone** - For important betting alerts and announcements
- **Use Application Commands** - For slash commands and bot interactions

### Member Management
- **View Server Insights** - To analyze server activity and member engagement
- **Manage Nicknames** - For custom member titles based on betting performance
- **Kick Members** - For moderation of betting-related violations
- **Ban Members** - For serious violations in betting communities
- **Create Instant Invite** - For generating invite links for new members
- **Change Nickname** - For updating member nicknames with betting stats

### Communication
- **Send TTS Messages** - For voice announcements of important betting updates
- **Use Voice Activity** - For voice channel betting discussions
- **Connect** - To join voice channels for live betting discussions
- **Speak** - To provide voice updates during live games
- **Use VAD** - For voice activity detection in betting channels
- **Priority Speaker** - To ensure betting announcements are heard
- **Request to Speak** - For requesting to speak in stage channels

### Advanced Features
- **Administrator** - For full server management capabilities
- **View Audit Log** - To track betting-related actions and changes
- **View Server Insights** - To analyze betting community engagement
- **Manage Events** - For scheduling betting events and game watches
- **Moderate Members** - For managing betting community behavior

## Permission Categories by Feature

### Live Score Updates
- Send Messages
- Embed Links
- Attach Files
- Use External Emojis
- Mention Everyone (for important updates)

### Betting Play Management
- Send Messages
- Add Reactions
- Read Message History
- Manage Messages (to edit/correct plays)
- Use Slash Commands

### Performance Tracking
- View Channels
- Read Message History
- Send Messages (for performance reports)
- Embed Links (for analytics dashboards)
- Attach Files (for detailed reports)

### Community Management
- Manage Roles
- Manage Nicknames
- Kick Members
- Ban Members
- Moderate Members

### Automated Notifications
- Send Messages
- Embed Links
- Mention Everyone
- Use External Emojis
- Manage Webhooks

### Voice Features
- Connect
- Speak
- Use Voice Activity
- Priority Speaker
- Request to Speak

## Permission Setup Instructions

### Step 1: Bot Role Setup
1. Create a dedicated role for the bot called "Bet Tracking AI"
2. Assign all required permissions to this role
3. Place the bot role above other roles that need to be managed

### Step 2: Channel-Specific Permissions
1. **Betting Plays Channel**
   - Send Messages: ✅
   - Embed Links: ✅
   - Add Reactions: ✅
   - Read Message History: ✅
   - Use Slash Commands: ✅

2. **Live Scores Channel**
   - Send Messages: ✅
   - Embed Links: ✅
   - Mention Everyone: ✅
   - Use External Emojis: ✅

3. **Performance Reports Channel**
   - Send Messages: ✅
   - Embed Links: ✅
   - Attach Files: ✅
   - Read Message History: ✅

4. **Voice Channels**
   - Connect: ✅
   - Speak: ✅
   - Use Voice Activity: ✅
   - Priority Speaker: ✅

### Step 3: Server-Wide Permissions
1. **Server Management**
   - Manage Server: ✅
   - Manage Roles: ✅
   - Manage Channels: ✅
   - Manage Webhooks: ✅

2. **Member Management**
   - View Server Insights: ✅
   - Manage Nicknames: ✅
   - Kick Members: ✅
   - Ban Members: ✅

## Security Considerations

### Minimal Permissions Approach
For enhanced security, consider using only these essential permissions:
- View Channels
- Send Messages
- Embed Links
- Add Reactions
- Read Message History
- Use Slash Commands
- Manage Webhooks

### Advanced Permissions (Optional)
These permissions can be added as needed:
- Manage Roles
- Manage Channels
- Kick Members
- Ban Members
- Administrator

## Troubleshooting Common Permission Issues

### Bot Can't Send Messages
- Check if the bot has "Send Messages" permission
- Verify the bot role is above the target channel
- Ensure the channel allows bot messages

### Bot Can't Use Slash Commands
- Verify "Use Application Commands" permission
- Check if slash commands are enabled in server settings
- Ensure the bot has proper OAuth2 scopes

### Bot Can't Manage Roles
- Confirm "Manage Roles" permission is granted
- Ensure the bot role is above roles it needs to manage
- Check server owner permissions

### Bot Can't Access Voice Channels
- Verify "Connect" and "Speak" permissions
- Check if voice channels allow bot access
- Ensure bot role has proper voice permissions

## OAuth2 Scopes Required

### Bot Scopes
- `bot` - Basic bot functionality
- `applications.commands` - Slash commands

### Bot Permissions
- `Send Messages`
- `Embed Links`
- `Attach Files`
- `Read Message History`
- `Add Reactions`
- `Use Slash Commands`
- `Manage Messages`
- `Manage Roles`
- `Manage Channels`
- `Manage Webhooks`
- `Connect`
- `Speak`
- `Use Voice Activity`
- `Priority Speaker`
- `View Server Insights`
- `Manage Nicknames`
- `Kick Members`
- `Ban Members`
- `Moderate Members`

## Invite URL Format
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot%20applications.commands
```

Replace `YOUR_BOT_ID` with your actual bot client ID.

## Permission Summary
The bot needs comprehensive permissions to provide full functionality for:
- Automated betting play management
- Live score updates and notifications
- Performance tracking and analytics
- Community management and moderation
- Voice channel integration
- Advanced server management features

All permissions are designed to enhance the betting community experience while maintaining security and proper Discord etiquette. 