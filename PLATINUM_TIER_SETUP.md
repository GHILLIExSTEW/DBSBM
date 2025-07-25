# 💎 Platinum Tier Setup Guide

## Overview

The Platinum tier is the highest subscription level for the Bet Embed Generator bot, offering advanced features for professional Discord communities. This guide covers the complete setup and implementation.

## 🎯 Platinum Tier Features

### Core Features
- **Webhook Integrations** (10 max) - Connect to external services including mobile apps
- **Real-Time Alerts** - Smart notifications for betting patterns and interventions
- **Data Export Tools** (50 max/month) - Export server data for analysis and reporting
- **Advanced Analytics** - Deep insights into betting patterns and user engagement
- **Direct API Access** - Query sports APIs directly for real-time data

### Enhanced Limits
- **5 Embed Channels** (vs 2 in Premium)
- **5 Command Channels** (vs 2 in Premium)
- **100 Active Bets** (vs unlimited in Premium, but higher limit)
- **Advanced Reporting** - More detailed analytics and reports

## 🗄️ Database Schema

### New Tables Created
1. **`platinum_features`** - Tracks enabled Platinum features
2. **`webhook_integrations`** - Manages webhook connections for mobile apps and external services
3. **`real_time_alerts`** - Configures smart notifications for betting patterns
4. **`data_exports`** - Tracks export requests for analysis and reporting
5. **`platinum_analytics`** - Usage tracking and betting pattern analytics
6. **API Access** - Direct querying of all sports APIs (no additional tables needed)

### Enhanced Tables
- **`guild_settings`** - Added Platinum-specific columns and limits
- **`subscriptions`** - Supports "platinum" plan type

## 🚀 Setup Instructions

### 1. Run Database Migration
```bash
cd scripts
python run_platinum_migration.py
```

### 2. Update Bot Configuration
The bot has been updated to include:
- Platinum service initialization
- Platinum commands loading
- Subscription level checking

### 3. Restart the Bot
```bash
# The bot will automatically load Platinum features
python main.py
```

## 📋 Available Commands

### Platinum Status
```
/platinum
```
- Check Platinum tier status
- View enabled features
- See usage analytics



### Webhook Integrations
```
/webhook <name> <url> <type>
```
- Create webhook connections for mobile apps and external services
- Types: bet_created, bet_resulted, user_activity, analytics, general
- Up to 10 webhooks per server
- Perfect for push notifications and external integrations

### Data Export
```
/export <type> <format>
```
- Export server data for analysis and reporting
- Types: bets, users, analytics, all
- Formats: csv, json, xlsx
- Up to 50 exports per month
- Perfect for Excel analysis, tax reporting, performance tracking, and third-party tools



### Analytics
```
/analytics
```
- View betting pattern analytics
- Track most active betting hours
- Monitor popular bet types and user engagement
- View feature usage statistics and performance metrics

### Direct API Access
```
/api_teams <sport> [league] [country] [season]
```
- Query teams from any supported sport API
- Filter by league, country, or season

```
/api_players <sport> [team] [league] [season] [search]
```
- Query players from any supported sport API
- Search by name, team, or league

```
/api_fixtures <sport> [league] [team] [season] [date]
```
- Query fixtures/matches from any supported sport API
- Filter by various criteria

```
/api_odds <sport> [fixture] [league] [season] [bookmaker]
```
- Query odds from any supported sport API
- Get real-time betting odds

```
/api_leagues <sport> [country] [season]
```
- Query leagues from any supported sport API
- Discover available competitions

```
/api_live <sport>
```
- Query live matches from any supported sport API
- Get real-time match data

## 🔧 Technical Implementation

### Services
- **`PlatinumService`** - Core service for webhooks, alerts, exports, and analytics
- **`SubscriptionService`** - Enhanced to support Platinum tier

### Commands
- **`PlatinumCog`** - Webhook, export, and analytics commands
- **`PlatinumAPICog`** - Direct API query commands for all sports
- Automatic permission checking
- Feature limit enforcement

### Database
- Comprehensive migration script
- Proper indexing for performance
- Foreign key constraints for data integrity

## 💰 Pricing

**Platinum Tier: $99.99/month**

### Value Proposition
- **Mobile Integration** - Push notifications for bet results via webhooks
- **Smart Monitoring** - Real-time alerts for betting patterns and interventions
- **Data Analysis** - Export tools for Excel analysis, tax reporting, and performance tracking
- **Advanced Analytics** - Deep insights into betting patterns and user engagement
- **Direct API Access** - Query all sports APIs directly for real-time data
- **External Tools** - Integration with third-party analytics platforms

## 🔒 Security & Permissions

### Access Control
- All Platinum commands require Administrator permissions
- Automatic subscription level checking
- Feature limit enforcement
- Secure webhook handling

### Data Protection
- Encrypted webhook URLs
- Secure data export handling
- User permission validation
- Audit logging for all actions

## 📊 Monitoring & Analytics

### Usage Tracking
- Betting pattern analytics
- Most active betting hours tracking
- Popular bet types analysis
- User engagement patterns
- Export request tracking
- Webhook notification logs

### Performance Monitoring
- Database query optimization
- Rate limiting for API calls
- Error tracking and reporting
- Service health monitoring

## 🛠️ Troubleshooting

### Common Issues

1. **"Platinum tier required" error**
   - Ensure server has Platinum subscription
   - Check subscription status with `/platinum`

2. **"Limit reached" errors**
   - Check current usage with `/analytics`
   - Delete unused items to free up space

3. **Webhook failures**
   - Verify webhook URL is valid
   - Check webhook permissions
   - Ensure Discord webhook is active

4. **Export failures**
   - Check export limits (50 per month)
   - Verify data format compatibility
   - Ensure sufficient storage space

### Support
- Use `/platinum` to check feature status
- Contact support for technical issues
- Check logs for detailed error information

## 🔄 Migration from Premium

### Automatic Features
- Existing Premium features remain active
- Webhook, alert, export, and analytics features are automatically enabled
- No data loss during upgrade

### Manual Steps
- Update subscription level in database
- Enable Platinum features for guild
- Configure webhooks for mobile apps and external services
- Set up real-time alerts for betting patterns

## 📈 Future Enhancements

### Planned Features
- **Enhanced Mobile Integration** - Direct mobile app APIs
- **Advanced Betting Analytics** - Machine learning insights
- **Automated Reporting** - Scheduled export and analysis
- **Third-party Integrations** - Pre-built connections to popular tools
- **Real-time Dashboard** - Live betting analytics dashboard

### Performance Improvements
- Caching for frequently accessed data
- Optimized database queries
- Background processing for heavy operations
- Real-time data synchronization

## 📝 Configuration Examples

### Webhook Integration Example
```
/webhook mobile_notifications https://discord.com/api/webhooks/... bet_resulted
```

### Real-Time Alert Example
```
Alert: "Notify when any bet over 50 units is placed"
```

### Data Export Example
```
/export bets csv  # For Excel analysis and tax reporting
```

### API Query Examples
```
/api_teams football league:39  # Get Premier League teams
/api_players basketball team:14  # Get Lakers players
/api_fixtures football date:2024-01-15  # Get today's matches
/api_odds football fixture:123456  # Get odds for specific match
/api_live basketball  # Get all live basketball games
```

## 🎉 Success Metrics

### Key Performance Indicators
- **Webhook Usage** - % of users with mobile app integrations
- **Alert Effectiveness** - Reduction in betting pattern issues
- **Export Frequency** - Data analysis and reporting usage
- **Analytics Engagement** - User interaction with betting insights
- **Revenue Impact** - Additional revenue from Platinum tier

### Monitoring Dashboard
- Real-time betting pattern analytics
- Webhook delivery success rates
- Export request tracking
- Alert effectiveness monitoring
- User engagement with analytics

---

**Platinum Tier is now ready for production use!** 🚀

For technical support or questions, please refer to the documentation or contact the development team.
