# DBSBM API Documentation

## Overview

The DBSBM (Discord Betting Sports Bot Management) system provides a comprehensive API for managing sports betting through Discord. This documentation covers all major endpoints, services, and utilities.

## Table of Contents

1. [Services](#services)
2. [Commands](#commands)
3. [Utilities](#utilities)
4. [Database Schema](#database-schema)
5. [Configuration](#configuration)

## Services

### BetService

Handles all betting-related operations.

#### Methods

##### `create_straight_bet(guild_id: int, user_id: int, game_id: str, selection: str, odds: float, units: float, description: str) -> Dict`

Creates a new straight bet.

**Parameters:**
- `guild_id`: Discord guild ID
- `user_id`: Discord user ID
- `game_id`: Unique game identifier
- `selection`: Bet selection (home/away/draw)
- `odds`: Decimal odds
- `units`: Number of units wagered
- `description`: Bet description

**Returns:**
```json
{
    "bet_id": "unique_bet_id",
    "status": "created",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

##### `get_user_bets(guild_id: int, user_id: int, limit: int = 50) -> List[Dict]`

Retrieves user's betting history.

**Parameters:**
- `guild_id`: Discord guild ID
- `user_id`: Discord user ID
- `limit`: Maximum number of bets to return

**Returns:**
```json
[
    {
        "bet_id": "bet_123",
        "game_id": "game_456",
        "selection": "home",
        "odds": 1.85,
        "units": 2.0,
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z"
    }
]
```

### UserService

Manages user profiles and statistics.

#### Methods

##### `get_user_stats(guild_id: int, user_id: int) -> Dict`

Retrieves user statistics.

**Returns:**
```json
{
    "user_id": 123456789,
    "display_name": "User Name",
    "image_path": "/static/users/123456789.png",
    "banner_color": "#00ff00",
    "bet_won": 100.0,
    "bet_loss": 50.0,
    "bet_push": 10.0,
    "net_units": 40.0,
    "win_rate": 66.7,
    "roi": 26.7
}
```

##### `update_user_profile(guild_id: int, user_id: int, display_name: str = None, image_path: str = None, banner_color: str = None) -> Dict`

Updates user profile information.

### AnalyticsService

Provides analytics and statistics.

#### Methods

##### `get_guild_stats(guild_id: int) -> Dict`

Retrieves guild-wide statistics.

**Returns:**
```json
{
    "total_bets": 150,
    "total_cappers": 25,
    "total_units": 500.0,
    "net_units": 75.5,
    "wins": 85,
    "losses": 60,
    "pushes": 5,
    "leaderboard": [
        {
            "username": "User1",
            "net_units": 25.5,
            "win_rate": 70.0
        }
    ]
}
```

##### `get_top_cappers(guild_id: int, limit: int = 10) -> List[Dict]`

Retrieves top performing cappers.

## Commands

### Straight Betting

#### `/bet straight`

Initiates the straight betting workflow.

**Options:**
- `league`: Sports league selection
- `sport`: Sport type selection
- `game`: Game selection
- `bet_type`: Type of bet (spread, moneyline, total)

### Statistics

#### `/stats [user]`

Displays betting statistics.

**Options:**
- `user`: Optional user mention for individual stats
- `server`: Show server-wide statistics

### Admin Commands

#### `/admin setup`

Sets up the bot for a new guild.

#### `/admin add_capper <user>`

Adds a user as a capper.

#### `/admin remove_user <user>`

Removes a user from the guild.

## Utilities

### Image Generators

#### `GameLineImageGenerator`

Generates game line images for betting displays.

**Methods:**
- `generate_game_line_image(game_data: Dict) -> Image.Image`
- `draw_teams_section(draw: ImageDraw, game_data: Dict, position: Tuple)`

#### `StatsImageGenerator`

Generates statistics images.

**Methods:**
- `generate_capper_stats_image(stats: Dict, username: str, profile_image_url: str = None) -> Image.Image`
- `generate_guild_stats_image(stats: Dict) -> Image.Image`

### Asset Management

#### `AssetLoader`

Manages loading of team and league logos.

**Methods:**
- `load_team_logo(team_name: str, sport: str) -> Optional[Image.Image]`
- `load_league_logo(league_code: str) -> Optional[Image.Image]`

#### `ImageOptimizer`

Optimizes images for performance.

**Methods:**
- `optimize_image(image_path: str) -> str`
- `batch_optimize(directory: str) -> Dict`
- `create_thumbnail(image_path: str, size: Tuple[int, int]) -> str`

### Caching

#### `CacheManager`

Manages data caching for performance.

**Methods:**
- `set(key: str, value: Any, ttl: int = 3600) -> bool`
- `get(key: str) -> Optional[Any]`
- `delete(key: str) -> bool`
- `clear() -> bool`

**Decorator:**
```python
@cached(ttl=3600, key_prefix="api")
async def expensive_function():
    # Function implementation
    pass
```

## Database Schema

### Tables

#### `cappers`
```sql
CREATE TABLE cappers (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    display_name VARCHAR(255),
    image_path VARCHAR(500),
    banner_color VARCHAR(7),
    bet_won DECIMAL(10,2) DEFAULT 0,
    bet_loss DECIMAL(10,2) DEFAULT 0,
    bet_push DECIMAL(10,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);
```

#### `bets`
```sql
CREATE TABLE bets (
    bet_id VARCHAR(50) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    bet_type ENUM('straight', 'parlay', 'prop') NOT NULL,
    selection VARCHAR(50) NOT NULL,
    odds DECIMAL(5,2) NOT NULL,
    units DECIMAL(5,2) NOT NULL,
    description TEXT,
    status ENUM('pending', 'won', 'lost', 'push') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### `games`
```sql
CREATE TABLE games (
    game_id VARCHAR(100) PRIMARY KEY,
    sport VARCHAR(50) NOT NULL,
    league VARCHAR(50) NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    game_time DATETIME NOT NULL,
    status ENUM('scheduled', 'live', 'finished') DEFAULT 'scheduled',
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables

#### Required
- `DISCORD_TOKEN`: Discord bot token
- `API_KEY`: Sports API key
- `MYSQL_HOST`: MySQL host address
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_DB`: MySQL database name
- `TEST_GUILD_ID`: Test guild ID for development

#### Optional
- `ODDS_API_KEY`: The Odds API key for live odds
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `WEB_SERVER_URL`: Web server URL for image serving

### Configuration Files

#### `pyproject.toml`
Project configuration including:
- Build system requirements
- Code formatting (Black)
- Import sorting (isort)
- Testing configuration (pytest)
- Coverage settings

#### `.pre-commit-config.yaml`
Pre-commit hooks for code quality:
- Code formatting
- Import sorting
- Linting (flake8)
- Type checking (mypy)

## Error Handling

### Common Error Codes

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Missing or invalid API key
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

### Error Response Format
```json
{
    "error": {
        "code": 400,
        "message": "Invalid parameters",
        "details": "Missing required field: user_id"
    }
}
```

## Rate Limiting

- API calls are limited to 100 requests per minute per guild
- Image generation is limited to 10 requests per minute per user
- Database queries are cached for 5 minutes by default

## Best Practices

### Performance
1. Use caching for frequently accessed data
2. Optimize images before serving
3. Implement pagination for large datasets
4. Use async/await for I/O operations

### Security
1. Validate all user inputs
2. Use parameterized queries to prevent SQL injection
3. Implement proper authentication and authorization
4. Sanitize file uploads

### Code Quality
1. Follow PEP 8 style guidelines
2. Write comprehensive unit tests
3. Use type hints for all functions
4. Document all public APIs

## Support

For technical support or questions about the API, please refer to:
- [GitHub Issues](https://github.com/your-repo/issues)
- [Documentation](https://docs.your-domain.com)
- [Discord Server](https://discord.gg/your-server) 