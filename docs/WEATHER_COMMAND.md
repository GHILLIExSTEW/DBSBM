# Weather Command Documentation

## Overview

The `/weather` command provides real-time weather information for game venues in the DBSBM system. It uses the WeatherAPI.com service to fetch current weather conditions for stadiums and arenas where games are being played.

## Features

- **Real-time Weather Data**: Get current temperature, conditions, wind, humidity, and precipitation
- **Venue-specific Information**: Weather data is fetched for specific stadium/arena locations
- **Multi-sport Support**: Works with football, basketball, baseball, hockey, and other sports
- **League Filtering**: Get weather for games in specific leagues (NFL, NBA, MLB, NHL, EPL, etc.)
- **Fallback Support**: If venue-specific weather isn't available, falls back to city-level data

## Usage

### Command Syntax

```
/weather sport:<sport_type> league:<league_name>
```

### Parameters

- **sport**: The sport type (e.g., football, basketball, baseball, hockey)
- **league**: The league name (e.g., NFL, NBA, MLB, NHL, EPL)

### Examples

```
/weather sport:football league:NFL
/weather sport:basketball league:NBA
/weather sport:baseball league:MLB
/weather sport:hockey league:NHL
/weather sport:football league:EPL
```

## Weather Information Provided

The command returns the following weather information for each game venue:

- **Temperature**: Current temperature in both Celsius and Fahrenheit
- **Feels Like**: Apparent temperature considering wind and humidity
- **Conditions**: Current weather conditions (sunny, cloudy, rain, etc.)
- **Wind**: Wind speed and direction
- **Humidity**: Relative humidity percentage
- **Precipitation**: Current precipitation amount (if any)
- **Location**: Venue name and location details
- **Last Updated**: Timestamp of when weather data was last updated

## Technical Implementation

### Weather Service (`bot/services/weather_service.py`)

The weather functionality is implemented through a dedicated service that:

- Integrates with WeatherAPI.com API
- Handles API authentication and rate limiting
- Formats weather data for Discord display
- Provides fallback mechanisms for unavailable data
- Includes error handling and logging

### Weather Command (`bot/commands/weather.py`)

The Discord command implementation:

- Uses Discord.py slash commands
- Integrates with the existing game service
- Provides user-friendly error messages
- Limits results to prevent spam (max 5 games)
- Handles message length limits

### Configuration

The weather feature requires:

1. **WeatherAPI.com API Key**: Set as `WEATHER_API_KEY` in your `.env` file
2. **Centralized Configuration**: The API key is managed through the centralized settings system
3. **Database Integration**: Uses existing game data to find venues

## Error Handling

The command includes comprehensive error handling:

- **API Key Missing**: Graceful fallback with helpful error message
- **No Games Found**: Clear message indicating no upcoming games
- **Weather Data Unavailable**: Fallback message for venues without weather data
- **Network Issues**: Timeout handling and retry logic
- **Invalid Input**: User-friendly validation messages

## Rate Limiting

The weather service includes built-in rate limiting:

- API calls are limited to prevent excessive usage
- Timeout settings prevent hanging requests
- Error handling for API quota exceeded scenarios

## Future Enhancements

Potential improvements for the weather command:

1. **Forecast Support**: Add multi-day weather forecasts
2. **Game-time Weather**: Show weather at specific game start times
3. **Weather Alerts**: Include severe weather warnings
4. **Historical Weather**: Compare current conditions to historical averages
5. **Weather Impact**: Show how weather might affect game conditions

## Troubleshooting

### Common Issues

1. **"Weather API key not configured"**

   - Ensure `WEATHER_API_KEY` is set in your `.env` file
   - Verify the API key is valid and active

2. **"No upcoming games found"**

   - Check that the sport and league names are correct
   - Ensure there are upcoming games in the database
   - Verify the game sync process is running

3. **"Weather data unavailable"**
   - Some venues may not have precise weather data
   - The system will fall back to city-level data
   - This is normal for some international venues

### Debugging

Enable debug logging to troubleshoot issues:

```python
# In your logging configuration
logging.getLogger('bot.services.weather_service').setLevel(logging.DEBUG)
logging.getLogger('bot.commands.weather').setLevel(logging.DEBUG)
```

## API Integration

The weather command integrates with:

- **WeatherAPI.com**: For real-time weather data
- **Database**: For game and venue information
- **Discord API**: For command interface
- **Centralized Settings**: For configuration management

## Security Considerations

- API keys are stored securely using Pydantic's SecretStr
- Weather data is cached to minimize API calls
- User input is validated and sanitized
- Error messages don't expose sensitive information
