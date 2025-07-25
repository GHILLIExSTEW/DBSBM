# Comprehensive API System

This document describes the new comprehensive API system that automatically discovers and fetches data for **ALL available leagues** from the API-Sports API.

## Overview

The comprehensive API system consists of three main components:

1. **League Discovery** (`bot/utils/league_discovery.py`) - Discovers all available leagues from the API
2. **Comprehensive Fetcher** (`bot/utils/comprehensive_fetcher.py`) - Fetches data for all discovered leagues
3. **Updated Main Fetcher** (`bot/fetcher.py`) - Uses the comprehensive system for hourly updates

## Features

- **Automatic League Discovery**: Discovers every single league available from API-Sports
- **Comprehensive Coverage**: Supports 25+ sports including football, basketball, baseball, hockey, MMA, Formula 1, and more
- **Hourly Updates**: Automatically fetches fresh data every hour for ALL leagues
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Error Handling**: Robust error handling for failed leagues
- **Statistics**: Detailed statistics on fetch operations

## Supported Sports

The system automatically discovers leagues for these sports:

- **Football (Soccer)**: EPL, La Liga, Bundesliga, Serie A, Champions League, etc.
- **Basketball**: NBA, WNBA, EuroLeague, etc.
- **Baseball**: MLB, NPB, KBO, etc.
- **Hockey**: NHL, KHL, etc.
- **American Football**: NFL, NCAA, CFL, etc.
- **Rugby**: Super Rugby, Six Nations, etc.
- **MMA**: UFC, Bellator, etc.
- **Formula 1**: F1 races and championships
- **Tennis**: ATP, WTA, Grand Slams, etc.
- **Golf**: PGA, LPGA, European Tour, etc.
- **Darts**: PDC, BDO, etc.
- **And many more**: Cricket, Boxing, Cycling, Esports, Futsal, Table Tennis, Badminton, Beach Volleyball, Field Hockey, Ice Hockey, Motorsport, Snooker, Squash, Water Polo, Winter Sports

## Setup Instructions

### 1. Initial League Discovery

Run the league discovery script to find all available leagues:

```bash
cd bot/scripts
python discover_all_leagues.py
```

This will:
- Discover all leagues from the API-Sports API
- Save the discovered leagues to `discovered_leagues.json`
- Update `bot/config/leagues.py` with the new LEAGUE_IDS configuration

### 2. Test the System

Test the comprehensive fetcher with a subset of leagues:

```bash
cd bot/scripts
python test_comprehensive_fetch.py
```

This will:
- Test league discovery
- Test fetching data for a subset of leagues
- Verify database operations
- Show detailed statistics

### 3. Start the System

The comprehensive system is automatically integrated into the main fetcher. Simply start the bot as usual:

```bash
python bot/fetcher.py
```

## How It Works

### League Discovery Process

1. **API Enumeration**: The system queries each sport's API endpoint to discover available leagues
2. **Data Collection**: For each league, it collects:
   - League ID
   - League name
   - Country information
   - Season data
   - Sport type
3. **Configuration Update**: Automatically updates the `LEAGUE_IDS` configuration

### Hourly Fetch Process

1. **League Discovery**: Discovers all available leagues (if not already cached)
2. **Data Fetching**: For each league:
   - Fetches games for today and tomorrow
   - Handles rate limiting automatically
   - Maps data to standard format
   - Saves to database
3. **Statistics**: Tracks successful/failed fetches and provides detailed reporting

### Error Handling

- **Rate Limiting**: Automatic retry with exponential backoff
- **Failed Leagues**: Tracks and reports failed leagues without stopping the entire process
- **API Errors**: Graceful handling of API errors and network issues
- **Database Errors**: Robust database error handling

## Configuration

### Environment Variables

Ensure these environment variables are set:

```env
API_KEY=your_api_sports_key
MYSQL_HOST=localhost
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database
MYSQL_PORT=3306
```

### Rate Limiting

The system respects API-Sports rate limits:
- 30 calls per minute per sport
- Automatic retry on rate limit exceeded
- Configurable delays between requests

## Monitoring and Statistics

### Log Files

- `league_discovery.log` - League discovery operations
- `comprehensive_fetch_test.log` - Test results
- `fetcher.log` - Main fetcher operations

### Statistics Available

The system provides detailed statistics:

```python
{
    "total_games": 1500,
    "unique_leagues": 45,
    "unique_sports": 12,
    "failed_leagues": ["Some League"],
    "successful_fetches": 44,
    "total_fetches": 45
}
```

## Performance Considerations

### Database Impact

- Clears `api_games` table before each hourly fetch
- Uses efficient batch operations
- Proper indexing recommended on `api_game_id`

### API Usage

- Respects rate limits automatically
- Efficient request batching
- Minimal redundant requests

### Memory Usage

- Streams data processing
- No large data structures in memory
- Efficient async operations

## Troubleshooting

### Common Issues

1. **No Leagues Discovered**
   - Check API key validity
   - Verify network connectivity
   - Check API-Sports service status

2. **High Failure Rate**
   - Check rate limiting configuration
   - Verify database connectivity
   - Review error logs

3. **Database Errors**
   - Verify database schema
   - Check connection pool settings
   - Review database permissions

### Debug Mode

Enable debug logging:

```python
logging.getLogger().setLevel(logging.DEBUG)
```

### Manual Testing

Test individual components:

```bash
# Test league discovery only
python -c "
import asyncio
from bot.utils.league_discovery import LeagueDiscovery
async def test():
    async with LeagueDiscovery() as d:
        leagues = await d.discover_all_leagues()
        print(f'Found {sum(len(l) for l in leagues.values())} leagues')
asyncio.run(test())
"
```

## Migration from Old System

The new system is backward compatible. The main changes:

1. **Automatic League Discovery**: No manual league configuration needed
2. **Comprehensive Coverage**: Fetches ALL available leagues
3. **Enhanced Error Handling**: Better failure recovery
4. **Detailed Statistics**: More comprehensive reporting

## Future Enhancements

- **Incremental Updates**: Only fetch changed data
- **League Filtering**: Allow selective league fetching
- **Advanced Caching**: Implement Redis caching
- **Web Dashboard**: Real-time monitoring interface
- **Alerting**: Notifications for failed fetches

## Support

For issues or questions:

1. Check the logs for detailed error information
2. Run the test script to verify functionality
3. Review the configuration and environment variables
4. Check API-Sports service status

---

**Note**: This system will fetch data for hundreds of leagues every hour. Ensure your API plan supports the expected request volume.
