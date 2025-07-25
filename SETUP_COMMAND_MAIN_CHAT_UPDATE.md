# Setup Command Main Chat Channel Update

## Problem
The `/setup` command was not asking for the main chat channel, which is needed for achievement notifications and community updates.

## Solution
Updated the setup command to include a "Main Chat Channel" step in the interactive setup process.

## Files Modified

### 1. Setup Steps (`bot/commands/admin.py`)
- **Added Main Chat Channel Step**: Added a new step to the `SETUP_STEPS` array
- **Position**: Added after "Admin Channel" and before "Admin Role" for logical flow
- **Configuration**:
  - **Name**: "Main Chat Channel"
  - **Type**: ChannelSelect (dropdown selection)
  - **Setting Key**: "main_chat_channel_id"
  - **Max Count**: 1 (only one main chat channel allowed)
  - **Free Count**: 1 (available for all tiers)
  - **Description**: "Channel for achievement notifications and community updates"

### 2. Database Operations (`bot/services/admin_service.py`)
- **Updated UPDATE Query**: Added `main_chat_channel_id = %s` to the UPDATE statement
- **Updated INSERT Query**: Added `main_chat_channel_id` to both column list and VALUES
- **Parameter Handling**: Added `settings.get("main_chat_channel_id")` to parameter lists

### 3. Data Processing (`bot/commands/admin.py`)
- **Updated finalize_setup()**: Added "main_chat_channel_id" to the list of single-value settings
- **Type Conversion**: Ensures the channel ID is converted from string to integer
- **Integration**: Seamlessly integrates with existing setup flow

## Setup Flow

### New Setup Process Order:
1. **Embed Channel** - For bet embeds and announcements
2. **Command Channel** - For bot commands
3. **Admin Channel** - For admin-only communications
4. **Main Chat Channel** - For achievement notifications and community updates ⭐ **NEW**
5. **Admin Role** - For admin permissions
6. **Authorized Role** - For authorized users
7. **Member Role** - For member permissions
8. **Bot Avatar URL** - For custom bot appearance (premium)
9. **Guild Background URL** - For custom backgrounds (premium)
10. **Default Parlay Image** - For parlay bet images (premium)
11. **Enable Live Game Updates** - For real-time updates
12. **Units Display Mode** - For bet display preferences

## User Experience

### During Setup:
- Users will see a dropdown of all text channels in their server
- They can select the channel where they want achievement notifications to appear
- The step is clearly labeled as "Main Chat Channel"
- Users can skip this step if needed (though not recommended)

### After Setup:
- Achievement notifications will be sent to the selected channel
- Community events will use this channel
- If no channel is selected, the system will fall back to channel name matching

## Benefits

1. **Centralized Notifications**: All achievement and community notifications go to one designated channel
2. **User Control**: Server admins can choose where these notifications appear
3. **Consistent Experience**: All community features use the same channel
4. **Easy Management**: Can be changed later through the setup command
5. **Graceful Fallbacks**: System works even if not configured

## Testing

### Verify Setup:
1. Run `/setup` command
2. Check that "Main Chat Channel" step appears in the correct order
3. Select a channel and complete setup
4. Verify the channel ID is saved in the database

### Test Notifications:
1. Trigger an achievement (react to bets, use community commands)
2. Verify notification appears in the selected main chat channel
3. Check logs for channel selection confirmation

## Database Schema

The `guild_settings` table now includes:
```sql
main_chat_channel_id BIGINT NULL COMMENT 'Channel for achievement notifications and community updates'
```

## Migration

For existing guilds that haven't run the new setup:
- The system will fall back to channel name matching ("Main_Chat", "main-chat", etc.)
- They can run `/setup` again to configure the main chat channel
- The setup script can also be used to automatically configure existing guilds

## Impact

- **New Guilds**: Will be prompted to select a main chat channel during setup
- **Existing Guilds**: Can run setup again to add main chat channel configuration
- **Achievement System**: Now properly directed to configured channels
- **Community Events**: Use the same channel for consistency
- **Admin Control**: Easy to manage notification destinations
