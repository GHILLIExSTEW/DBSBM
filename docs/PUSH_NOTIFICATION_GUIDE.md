# 📱 Push Notification System Guide

## 🎯 **Overview**

The push notification system sends **standalone notifications** to all members with the member role. These notifications appear on their phones and devices as Discord push notifications, not just mentions in the channel.

## 🔧 **How It Works**

### **What Members See:**
- 📱 **Phone notifications** with the notification title and message
- 🔔 **Discord desktop notifications** 
- 📺 **Rich embeds** in the Discord channel with additional details
- ⚡ **Priority indicators** (low, normal, high, urgent)
- 📋 **Notification type badges** (community, bet, event, etc.)

### **Key Features:**
- ✅ **Standalone notifications** - Not just mentions, but actual push notifications
- ✅ **Cooldown system** - Prevents spam (configurable per notification type)
- ✅ **Priority levels** - Different urgency levels with different colors
- ✅ **Rich embeds** - Detailed notifications with fields and formatting
- ✅ **Analytics tracking** - Monitor notification effectiveness
- ✅ **Member role targeting** - Only sends to users with the member role

---

## 🚀 **Setup Instructions**

### **Step 1: Configure Member Role**

First, you need to set up which role will receive push notifications:

```sql
-- Update your guild settings with the member role ID
UPDATE guild_settings 
SET member_role = YOUR_MEMBER_ROLE_ID 
WHERE guild_id = YOUR_GUILD_ID;
```

**To find your member role ID:**
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on the member role → Copy ID
3. Use that ID in the SQL command above

### **Step 2: Test the System**

Use the `/notify` command to test:

```
/notify title:"Welcome to the Community!" message:"We're excited to have you here!" notification_type:community priority:normal
```

---

## 📋 **Available Commands**

### **1. `/notify` - Send Custom Notification**
```
/notify title:"Your Title" message:"Your message" notification_type:community priority:normal channel:#general
```

**Parameters:**
- **title** (required): Notification title
- **message** (required): Notification message  
- **notification_type** (optional): community, bet, alert, achievement, event, reminder, update, celebration
- **priority** (optional): low, normal, high, urgent
- **channel** (optional): Channel to send to (defaults to current channel)

### **2. `/notify_capper_bet` - Notify About New Capper Bet**
```
/notify_capper_bet capper_name:"John Doe" bet_details:"Lakers -5.5 @ -110" sport:football channel:#capper-bets
```

### **3. `/notify_event` - Notify About Community Event**
```
/notify_event event_name:"Meme Monday" event_description:"Share your best betting memes!" event_time:"Starting now!" channel:#main-chat
```

### **4. `/notification_stats` - View Statistics**
```
/notification_stats days:7
```

### **5. `/clear_notification_cooldowns` - Clear Cooldowns**
```
/clear_notification_cooldowns
```

---

## 🎯 **Notification Types & Use Cases**

### **Community Notifications**
```python
# General community updates
await push_service.send_push_notification(
    guild_id=guild_id,
    channel_id=channel_id,
    title="Community Update",
    message="New features are now available!",
    notification_type="community",
    priority="normal"
)
```

### **Bet Notifications**
```python
# New capper bets
await push_service.notify_new_capper_bet(
    guild_id=guild_id,
    channel_id=channel_id,
    capper_name="Pro Capper",
    bet_details="Warriors +3.5 @ -110",
    sport="basketball"
)
```

### **Event Notifications**
```python
# Community events
await push_service.notify_community_event(
    guild_id=guild_id,
    channel_id=channel_id,
    event_name="Trivia Tuesday",
    event_description="Test your sports knowledge!",
    event_time="Starting in 10 minutes!"
)
```

### **Achievement Notifications**
```python
# User achievements
await push_service.notify_achievement_unlocked(
    guild_id=guild_id,
    channel_id=channel_id,
    user_name="John Doe",
    achievement_name="Reaction Master",
    achievement_description="Reacted to 100 bets!"
)
```

### **Winning Streak Notifications**
```python
# Capper winning streaks
await push_service.notify_winning_streak(
    guild_id=guild_id,
    channel_id=channel_id,
    capper_name="Hot Capper",
    streak_count=5,
    total_profit="$250"
)
```

---

## ⚙️ **Cooldown System**

### **Default Cooldowns:**
- **Capper bets**: 2 minutes
- **Popular bets**: 10 minutes  
- **Community events**: 30 minutes
- **Achievements**: 5 minutes
- **Winning streaks**: 15 minutes
- **Daily reminders**: 60 minutes
- **Custom notifications**: 5 minutes

### **Managing Cooldowns:**
```python
# Clear all cooldowns for a guild
await push_service.clear_cooldowns(guild_id=123456789)

# Clear all cooldowns everywhere
await push_service.clear_cooldowns()
```

---

## 📊 **Analytics & Monitoring**

### **View Notification Statistics:**
```
/notification_stats days:7
```

**What you'll see:**
- Total notifications sent
- Breakdown by notification type
- Percentage distribution
- Time-based trends

### **Database Queries:**
```sql
-- Get notification stats for last 7 days
SELECT 
    notification_type,
    COUNT(*) as count,
    DATE(sent_at) as date
FROM push_notifications
WHERE guild_id = YOUR_GUILD_ID 
AND sent_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY notification_type, DATE(sent_at)
ORDER BY date DESC, count DESC;

-- Get most active notification types
SELECT 
    notification_type,
    COUNT(*) as total_sent
FROM push_notifications
WHERE guild_id = YOUR_GUILD_ID
GROUP BY notification_type
ORDER BY total_sent DESC;
```

---

## 🎨 **Notification Appearance**

### **Priority Colors:**
- 🔴 **Urgent**: Red (#ff0000)
- 🟠 **High**: Orange (#ffa500)  
- 🟢 **Normal**: Green (#00ff00)
- ⚪ **Low**: Gray (#808080)

### **Type Icons:**
- 👥 **Community**: Community updates
- 🎯 **Bet**: Betting-related notifications
- 🚨 **Alert**: Important alerts
- 🏆 **Achievement**: User achievements
- 🎉 **Event**: Community events
- ⏰ **Reminder**: Daily reminders
- 📢 **Update**: System updates
- 🎊 **Celebration**: Celebrations

### **Rich Embed Features:**
- 📋 **Type badge**: Shows notification category
- ⚡ **Priority badge**: Shows urgency level
- 📅 **Timestamp**: When notification was sent
- 🔗 **Footer**: "Tap to view details"
- 📊 **Custom fields**: Additional information

---

## 🔧 **Integration Examples**

### **Automatic Capper Bet Notifications:**
```python
# In your bet posting service
async def post_capper_bet(self, bet_data):
    # Post the bet normally
    await self.post_bet_to_channel(bet_data)
    
    # Send push notification
    if hasattr(self.bot, 'push_notification_service'):
        await self.bot.push_notification_service.notify_new_capper_bet(
            guild_id=bet_data['guild_id'],
            channel_id=bet_data['channel_id'],
            capper_name=bet_data['capper_name'],
            bet_details=bet_data['bet_details'],
            sport=bet_data['sport']
        )
```

### **Popular Bet Alerts:**
```python
# When a bet gets many reactions
async def check_popular_bet(self, bet_id, reaction_count):
    if reaction_count >= 10:  # Threshold for "popular"
        if hasattr(self.bot, 'push_notification_service'):
            await self.bot.push_notification_service.notify_popular_bet(
                guild_id=guild_id,
                channel_id=channel_id,
                bet_details=bet_details,
                reaction_count=reaction_count
            )
```

### **Daily Community Events:**
```python
# Scheduled daily events
async def daily_community_event(self):
    events = {
        "monday": ("Meme Monday", "Share your best betting memes!"),
        "tuesday": ("Trivia Tuesday", "Test your sports knowledge!"),
        "wednesday": ("Prediction Wednesday", "Make your predictions!"),
        # ... etc
    }
    
    today = datetime.now().strftime("%A").lower()
    if today in events:
        event_name, event_desc = events[today]
        await self.bot.push_notification_service.notify_community_event(
            guild_id=guild_id,
            channel_id=channel_id,
            event_name=event_name,
            event_description=event_desc,
            event_time="Starting now!"
        )
```

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. Notifications not sending**
- ✅ Check if member role is configured
- ✅ Verify member role ID is correct
- ✅ Ensure bot has permissions in the channel
- ✅ Check if cooldown is active

#### **2. Members not receiving notifications**
- ✅ Verify members have the member role
- ✅ Check Discord notification settings
- ✅ Ensure members haven't muted the channel
- ✅ Verify Discord app notifications are enabled

#### **3. Service not available**
- ✅ Check bot logs for initialization errors
- ✅ Verify database migration was run
- ✅ Restart the bot to reinitialize service

### **Debug Commands:**
```python
# Check if service is available
if hasattr(bot, 'push_notification_service'):
    print("Push notification service is available")
else:
    print("Push notification service not available")

# Check member role configuration
member_role = await bot.push_notification_service.get_member_role_id(guild_id)
if member_role:
    print(f"Member role ID: {member_role}")
else:
    print("No member role configured")
```

---

## 📈 **Best Practices**

### **1. Notification Frequency**
- 🎯 **Don't spam**: Use cooldowns appropriately
- 📊 **Monitor engagement**: Check notification stats regularly
- ⏰ **Time notifications**: Send during active hours
- 🎨 **Vary content**: Mix different notification types

### **2. Content Quality**
- 📝 **Clear titles**: Make titles descriptive and engaging
- 💬 **Concise messages**: Keep messages under 200 characters
- 🎯 **Relevant content**: Only notify about important things
- 🎨 **Use rich embeds**: Include additional context

### **3. Member Experience**
- 🔔 **Respect preferences**: Don't overwhelm members
- 📱 **Mobile-friendly**: Consider mobile notification limits
- 🎯 **Targeted content**: Send relevant notifications
- 📊 **Track feedback**: Monitor member reactions

---

## 🎉 **Success Metrics**

### **Key Performance Indicators:**
- 📱 **Notification open rate**: How many members tap notifications
- ⏰ **Response time**: How quickly members engage after notification
- 📊 **Engagement increase**: Higher activity after notifications
- 🎯 **Member retention**: Members staying active longer
- 📈 **Community growth**: New member acquisition

### **Target Goals:**
- 🎯 **70% notification open rate**
- ⏰ **5-minute average response time**
- 📊 **50% increase in engagement**
- 🎯 **80% member retention**
- 📈 **20% community growth**

---

## 🔮 **Future Enhancements**

### **Planned Features:**
- 📱 **Mobile app integration**: Direct mobile push notifications
- 🎯 **Smart targeting**: AI-powered notification timing
- 📊 **Advanced analytics**: Detailed engagement tracking
- 🎨 **Custom themes**: Server-specific notification styling
- 🔔 **Member preferences**: Let members choose notification types

### **Integration Opportunities:**
- 📱 **Mobile apps**: Direct push to mobile devices
- 📧 **Email integration**: Email notifications for important events
- 🔔 **SMS notifications**: Critical alerts via SMS
- 📊 **Analytics platforms**: Integration with external analytics
- 🤖 **Chatbots**: Automated notification responses

---

## 📞 **Support**

### **Getting Help:**
- 📚 **Check this guide**: Most issues are covered here
- 🔍 **Review logs**: Check bot logs for error messages
- 📊 **Monitor stats**: Use `/notification_stats` to check system health
- 🆘 **Contact support**: For technical issues beyond this guide

### **Useful Commands:**
```
/notification_stats days:7          # Check system health
/clear_notification_cooldowns       # Reset cooldowns if needed
/notify title:"Test" message:"Test" # Test the system
```

---

**🎉 You're now ready to use the push notification system! Start with a simple test notification and gradually build up your notification strategy.** 