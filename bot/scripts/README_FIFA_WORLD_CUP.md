# FIFA World Cup Data Fetch Scripts

This directory contains scripts to fetch FIFA World Cup data including teams, logos, and other information from the API-Sports API.

## Files

- `fetch_fifa_world_cup_data.py` - Main script to fetch FIFA World Cup data
- `run_fifa_world_cup_fetch.py` - Runner script with error handling and requirements checking
- `README_FIFA_WORLD_CUP.md` - This documentation file

## Prerequisites

1. **API Key**: You need a valid API-Sports API key. You can either:
   - Set it in your `.env` file: `API_KEY=your_api_key_here`
   - Or the script will prompt you to enter it when you run it

2. **Python Dependencies**: Make sure you have the required packages installed:
   ```bash
   pip install aiohttp asyncio
   ```

3. **Directory Structure**: Ensure the betting-bot directory structure is intact:
   ```
   betting-bot/
   ├── config/
   ├── utils/
   ├── static/
   ├── data/
   └── scripts/
   ```

## Usage

### Option 1: Using the Runner Script (Recommended)

The runner script provides better error handling and requirements checking:

```bash
cd betting-bot
python scripts/run_fifa_world_cup_fetch.py
```

### Option 2: Running the Main Script Directly

```bash
cd betting-bot
python scripts/fetch_fifa_world_cup_data.py
```

## What the Script Does

The FIFA World Cup data fetch script performs the following operations:

1. **Fetches League Information**: Gets FIFA World Cup league details
2. **Downloads League Logo**: Saves the FIFA World Cup logo
3. **Fetches Teams**: Gets all participating teams for 2026 and 2022 World Cups
4. **Downloads Team Logos**: Downloads and saves team logos
5. **Fetches Seasons**: Gets available World Cup seasons
6. **Fetches Standings**: Gets current standings for 2026 World Cup
7. **Fetches Fixtures**: Gets fixtures for 2026 World Cup

## Output Files

After running the script, you'll find the following files:

### Data Files (in `betting-bot/data/`)
- `fifa_world_cup_league.json` - League information
- `fifa_world_cup_seasons.json` - Available seasons
- `fifa_world_cup_teams_2026.csv` - Teams for 2026 World Cup (CSV format)
- `fifa_world_cup_teams_2026.json` - Teams for 2026 World Cup (JSON format)
- `fifa_world_cup_teams_2022.csv` - Teams for 2022 World Cup (CSV format)
- `fifa_world_cup_teams_2022.json` - Teams for 2022 World Cup (JSON format)
- `fifa_world_cup_standings_2026.json` - Standings for 2026 World Cup
- `fifa_world_cup_fixtures_2026.json` - Fixtures for 2026 World Cup

### Logo Files
- **League Logo**: `betting-bot/static/logos/leagues/SOCCER/worldcup.png`
- **Team Logos**: `betting-bot/static/logos/teams/SOCCER/WORLDCUP/[team_name].png`

### Log Files
- `betting-bot/logs/fifa_world_cup_fetch.log` - Main fetch script logs
- `betting-bot/logs/fifa_world_cup_runner.log` - Runner script logs

## FIFA World Cup Configuration

The script is configured for FIFA World Cup with:
- **League ID**: 15
- **Sport**: football
- **League Key**: WorldCup
- **Name**: FIFA World Cup

## Team Name Normalization

The script uses team name normalization to ensure consistent logo matching. Team names are normalized using the mappings in `betting-bot/utils/league_dictionaries/soccer.py`.

## Error Handling

The script includes comprehensive error handling:
- API rate limiting (waits 60 seconds if rate limited)
- Network timeouts and retries
- Invalid logo URL handling
- Missing data handling
- File system error handling

## Rate Limiting

The script respects API rate limits:
- 0.5 second delay between logo downloads
- 60 second wait if rate limited
- Proper session management

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   WARNING: API_KEY not found in environment variables
   ```
   **Solution**: The script will prompt you to enter your API key. You can also set it in the `.env` file

2. **Import Errors**
   ```
   ❌ Failed to import FIFA World Cup fetch script
   ```
   **Solution**: Ensure you're running from the `betting-bot` directory

3. **Directory Not Found**
   ```
   ❌ Required directory not found
   ```
   **Solution**: Ensure the betting-bot directory structure is intact

4. **API Errors**
   ```
   API returned errors: [error details]
   ```
   **Solution**: Check your API key validity and quota

### Log Files

Check the log files for detailed error information:
- `betting-bot/logs/fifa_world_cup_fetch.log`
- `betting-bot/logs/fifa_world_cup_runner.log`

## Integration with Betting Bot

The fetched data integrates with the betting bot system:

1. **Team Logos**: Used in betting slips and game displays
2. **Team Names**: Normalized for consistent matching
3. **League Data**: Used for game fetching and display
4. **Standings**: Available for standings displays

## Updating Data

To update FIFA World Cup data, simply run the script again. The script will:
- Skip existing logos (won't re-download)
- Update data files with latest information
- Add new teams if they qualify

## Support

If you encounter issues:
1. Check the log files for detailed error messages
2. Verify your API key is valid and has sufficient quota
3. Ensure all required directories and files exist
4. Check your internet connection for logo downloads
