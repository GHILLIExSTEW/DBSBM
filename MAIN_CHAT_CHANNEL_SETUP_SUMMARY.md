# Main Chat Channel Setup for Achievement Notifications

## Problem
Achievement notifications were being sent to hardcoded channel names like "general-chat" or falling back to the first text channel, instead of using a dedicated "Main_Chat" channel.

## Solution
Added a `main_chat_channel_id` column to the `guild_settings` table and updated all achievement notification systems to use this configured channel.

## Files Modified

### 1. Database Migration (`migrations/011_add_main_chat_channel.sql`)
- **Added Column**: `main_chat_channel_id BIGINT NULL` to `guild_settings` table
- **Added Index**: For performance optimization
- **Added Comment**: Documents the purpose of the column

### 2. Achievement Notifications (`bot/services/community_analytics.py`)
- **Updated `notify_achievement()` method**:
  - First tries to use `main_chat_channel_id` from guild settings
  - Falls back to "main-chat" channel name
  - Falls back to "general-chat" channel name
  - Final fallback to first text channel
  - Added comprehensive logging for debugging

### 3. Community Events (`bot/services/community_events.py`)
- **Updated `start_daily_event()` method**:
  - Uses `main_chat_channel_id` from guild settings
  - Falls back to channel names in order of preference
  - Enhanced logging for channel selection

- **Updated `start_weekly_event()` method**:
  - Uses `main_chat_channel_id` from guild settings
  - Falls back to channel names in order of preference
  - Enhanced logging for channel selection

### 4. Setup Script (`scripts/set_main_chat_channels.py`)
- **Automated Setup**: Finds "Main_Chat" channels in all guilds
- **Database Update**: Sets `main_chat_channel_id` for existing guilds
- **Alternative Names**: Tries "main-chat", "main_chat", "general-chat", "general"
- **Comprehensive Logging**: Reports success/failure for each guild

## Channel Priority Order

1. **Configured Channel**: `main_chat_channel_id` from guild settings
2. **Main_Chat**: Channel named "Main_Chat"
3. **Alternative Names**: "main-chat", "main_chat", "general-chat", "general"
4. **Fallback**: First available text channel

## Usage

### For New Guilds
The `main_chat_channel_id` will be set when guilds are configured through the admin interface.

### For Existing Guilds
Run the setup script to automatically configure existing guilds:

```bash
python scripts/set_main_chat_channels.py
```

### Manual Configuration
Admins can manually set the main chat channel through the guild settings interface or directly in the database:

```sql
UPDATE guild_settings
SET main_chat_channel_id = [CHANNEL_ID]
WHERE guild_id = [GUILD_ID];
```

## Benefits

1. **Centralized Notifications**: All achievement notifications go to the designated main chat channel
2. **Flexible Configuration**: Each guild can specify their preferred notification channel
3. **Graceful Fallbacks**: System works even if main chat channel isn't configured
4. **Easy Management**: Simple to change notification channel through guild settings
5. **Consistent Experience**: All community events and achievements use the same channel

## Testing

### Verify Configuration
Check that the main chat channel is properly set:

```sql
SELECT guild_id, main_chat_channel_id
FROM guild_settings
WHERE main_chat_channel_id IS NOT NULL;
```

### Test Achievement Notifications
1. Trigger an achievement (e.g., react to bets, use community commands)
2. Verify notification appears in the Main_Chat channel
3. Check logs for channel selection messages

### Test Community Events
1. Wait for daily/weekly events to trigger
2. Verify events appear in the Main_Chat channel
3. Check logs for event channel selection

## Impact

- **Achievement Notifications**: Now properly sent to Main_Chat channel
- **Community Events**: Daily and weekly events use Main_Chat channel
- **Consistent Experience**: All community notifications centralized
- **Better Organization**: Clear separation between different types of channels
- **Admin Control**: Easy to configure and change notification channels
