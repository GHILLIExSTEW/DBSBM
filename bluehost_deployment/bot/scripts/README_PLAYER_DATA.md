# Player Data Management Scripts

This directory contains scripts to fetch and manage player data for the enhanced player props feature.

## Overview

The enhanced player props system gets player data from multiple sources:
1. **Database Cache** (`player_search_cache` table) - Primary source
2. **Previous Bets** (`bets` table) - Fallback source
3. **Static Team Library** - Hardcoded popular players
4. **CSV File** (`players.csv`) - Bulk player data with images

## Scripts

### 1. `fetch_single_league.py` ⭐ **MAIN SCRIPT**

Fetches player data from API-Sports for any single league. This is the primary script for populating player data.

**Features:**
- Interactive menu to select which league to fetch
- Supports all major sports: Basketball, Baseball, American Football, Hockey, Football (Soccer)
- Fetches teams first, then players for each team
- Option to append to existing CSV or create new file
- Rate limiting to be respectful to API
- Immediate saving after each league

**Usage:**
```bash
cd bot/scripts
python fetch_single_league.py
```

**Supported Leagues:**
- **Basketball**: NBA
- **Baseball**: MLB
- **American Football**: NFL, NCAA
- **Hockey**: NHL
- **Football (Soccer)**: EPL, LaLiga, Bundesliga, SerieA, Ligue1, ChampionsLeague

**Requirements:**
- Valid API-Sports subscription
- API key will be prompted for when running the script

### 2. `update_player_search_cache.py`

Updates the database cache from the CSV file for fast player searches.

**Features:**
- Creates `player_search_cache` table if it doesn't exist
- Loads player data from `players.csv`
- Inserts players into database with proper indexing
- Provides statistics on cache population
- Batch processing for large datasets

**Usage:**
```bash
cd bot/scripts
python update_player_search_cache.py
```

**Requirements:**
- MySQL database connection
- `players.csv` file (created by fetch script)

## Workflow

### Initial Setup

1. **Fetch players for each league:**
   ```bash
   python fetch_single_league.py
   ```
   - Select league from menu
   - Choose whether to append or create new CSV
   - Repeat for each league you want

2. **Update database cache:**
   ```bash
   python update_player_search_cache.py
   ```

### Regular Updates

To keep player data fresh, run the scripts periodically:

```bash
# Weekly or monthly updates
python fetch_single_league.py  # Select leagues to update
python update_player_search_cache.py
```

## CSV File Structure

The `players.csv` file contains the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `strPlayer` | Player name | "LeBron James" |
| `strTeam` | Team name | "Los Angeles Lakers" |
| `strSport` | Sport type | "Basketball" |
| `strLeague` | League name | "NBA" |
| `strPosition` | Player position | "Forward" |
| `strCutouts` | Player photo URL | "https://..." |
| `strThumb` | Thumbnail photo URL | "https://..." |
| `strHeight` | Player height | "6'9\"" |
| `strWeight` | Player weight | "250 lbs" |
| `strNationality` | Player nationality | "USA" |
| `strBirthDate` | Birth date | "1984-12-30" |
| ... | Additional metadata fields | ... |

## Database Schema

The `player_search_cache` table structure:

```sql
CREATE TABLE player_search_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(255) NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    league VARCHAR(100) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    position VARCHAR(50),
    nationality VARCHAR(100),
    height VARCHAR(20),
    weight VARCHAR(20),
    birth_date VARCHAR(20),
    birth_location VARCHAR(255),
    photo_url VARCHAR(500),
    usage_count INT DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_player_name (player_name),
    INDEX idx_team_name (team_name),
    INDEX idx_league (league),
    INDEX idx_sport (sport),
    INDEX idx_usage (usage_count DESC, last_used DESC),
    INDEX idx_active (is_active)
);
```

## API Rate Limits

API-Sports has rate limits:
- **Free tier**: 100 requests/day
- **Basic tier**: 1,000 requests/day
- **Pro tier**: 10,000 requests/day

The scripts include 0.5-second delays between requests to be respectful.

## Troubleshooting

### Common Issues

1. **API key not provided:**
   ```
   ❌ API key is required
   ```
   Solution: Enter your API-Sports key when prompted.

2. **CSV file not found:**
   ```
   ❌ CSV file not found: /path/to/players.csv
   ```
   Solution: Run `fetch_single_league.py` first and select "No" when asked to append.

3. **Database connection error:**
   ```
   ❌ Error creating table: ...
   ```
   Solution: Check database credentials and connection.

4. **"This endpoint do not exist" error:**
   ```
   ❌ API Errors: {'endpoint': 'This endpoint do not exist.'}
   ```
   Solution: This means the API doesn't support player data for that sport/league. Try a different league.

### Recommended Order

For best results, fetch leagues in this order:
1. **Football (Soccer)** - Most reliable player data
2. **American Football** - Good player data
3. **Basketball** - Variable results
4. **Baseball** - May have API issues
5. **Hockey** - May have API issues

## File Structure

```
bot/scripts/
├── fetch_single_league.py          # Main player fetching script
├── update_player_search_cache.py   # Database cache updater
├── README_PLAYER_DATA.md           # This documentation
└── [other utility scripts...]
```
