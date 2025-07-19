# DBSBM API Reference

This document provides comprehensive API documentation for the DBSBM system utilities and services.

## Table of Contents

1. [Environment Validator](#environment-validator)
2. [Rate Limiter](#rate-limiter)
3. [Performance Monitor](#performance-monitor)
4. [Error Handler](#error-handler)
5. [Database Manager](#database-manager)
6. [Services](#services)

---

## Environment Validator

The environment validator ensures all required environment variables are properly configured.

### `EnvironmentValidator`

Main class for validating environment variables.

#### Methods

##### `validate_all() -> Tuple[bool, List[str]]`

Validates all environment variables and returns a tuple of (is_valid, list_of_errors).

```python
from utils.environment_validator import EnvironmentValidator

is_valid, errors = EnvironmentValidator.validate_all()
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

##### `get_config_summary() -> Dict[str, str]`

Returns a summary of current configuration (sensitive data is masked).

```python
config = EnvironmentValidator.get_config_summary()
print(f"Database host: {config['MYSQL_HOST']}")
print(f"API Key: {config['API_KEY']}")  # Shows "***" if set
```

##### `print_config_summary()`

Prints a formatted configuration summary to the logger.

```python
EnvironmentValidator.print_config_summary()
```

#### Required Environment Variables

- `DISCORD_TOKEN`: Discord bot token for authentication
- `API_KEY`: API-Sports key for sports data access
- `MYSQL_HOST`: MySQL database host address
- `MYSQL_USER`: MySQL database username
- `MYSQL_PASSWORD`: MySQL database password
- `MYSQL_DB`: MySQL database name
- `TEST_GUILD_ID`: Discord guild ID for testing

#### Optional Environment Variables

- `ODDS_API_KEY`: The Odds API key for additional odds data
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `API_TIMEOUT`: API request timeout in seconds (default: 30)
- `API_RETRY_ATTEMPTS`: Number of API retry attempts (default: 3)
- `API_RETRY_DELAY`: Delay between API retries in seconds (default: 5)
- `MYSQL_PORT`: MySQL database port (default: 3306)
- `MYSQL_POOL_MIN_SIZE`: Minimum MySQL connection pool size (default: 1)
- `MYSQL_POOL_MAX_SIZE`: Maximum MySQL connection pool size (default: 10)
- `REDIS_URL`: Redis connection URL for caching
- `CACHE_TTL`: Default cache TTL in seconds (default: 3600)

### `validate_environment() -> bool`

Main function to validate environment variables.

```python
from utils.environment_validator import validate_environment

if not validate_environment():
    print("Environment validation failed!")
    sys.exit(1)
```

---

## Rate Limiter

The rate limiter prevents abuse by limiting user actions.

### `RateLimiter`

Main class for rate limiting user actions.

#### Methods

##### `is_allowed(user_id: int, action: str) -> Tuple[bool, Optional[float]]`

Check if a user action is allowed. Returns (is_allowed, retry_after_seconds).

```python
from utils.rate_limiter import RateLimiter

limiter = RateLimiter()
is_allowed, retry_after = await limiter.is_allowed(123456789, "bet_placement")

if not is_allowed:
    print(f"Rate limited. Retry after {retry_after} seconds")
```

##### `get_user_stats(user_id: int) -> Dict[str, Dict]`

Get rate limit statistics for a specific user.

```python
stats = limiter.get_user_stats(123456789)
for action, info in stats.items():
    print(f"{action}: {info['current_requests']}/{info['max_requests']} requests")
```

##### `get_global_stats() -> Dict`

Get global rate limiter statistics.

```python
stats = limiter.get_global_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Rate limited: {stats['rate_limited_requests']}")
print(f"Rate limit percentage: {stats['rate_limit_percentage']:.1f}%")
```

##### `reset_user(user_id: int, action: Optional[str] = None)`

Reset rate limit for a specific user and action.

```python
# Reset all actions for user
limiter.reset_user(123456789)

# Reset specific action
limiter.reset_user(123456789, "bet_placement")
```

#### Default Rate Limits

- `bet_placement`: 5 requests per 60 seconds
- `stats_query`: 10 requests per 60 seconds
- `admin_command`: 3 requests per 60 seconds
- `image_generation`: 10 requests per 60 seconds
- `api_request`: 20 requests per 60 seconds
- `user_registration`: 1 request per 300 seconds (5 minutes)

### `rate_limit(action: str)`

Decorator for rate limiting functions.

```python
from utils.rate_limiter import rate_limit

@rate_limit("bet_placement")
async def place_bet(interaction):
    # Function implementation
    pass
```

### `RateLimitExceededError`

Exception raised when rate limit is exceeded.

```python
from utils.rate_limiter import RateLimitExceededError

try:
    await place_bet(interaction)
except RateLimitExceededError as e:
    print(f"Rate limit exceeded: {e}")
```

---

## Performance Monitor

The performance monitor tracks system metrics and health.

### `PerformanceMonitor`

Main class for performance monitoring.

#### Methods

##### `add_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None)`

Add a performance metric.

```python
from utils.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.add_metric("database_query_time", 0.5, {"table": "users"})
```

##### `record_response_time(operation: str, response_time: float)`

Record response time for an operation.

```python
monitor.record_response_time("database_query", 0.3)
monitor.record_response_time("api_call", 1.2)
```

##### `record_request(endpoint: str, success: bool = True)`

Record a request to an endpoint.

```python
monitor.record_request("/api/games", True)
monitor.record_request("/api/odds", False)
```

##### `add_health_check(name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None)`

Add a health check result.

```python
monitor.add_health_check("database_connection", "healthy", "Database is responding")
monitor.add_health_check("api_status", "warning", "API response time increased")
```

##### `check_system_health() -> Dict[str, Any]`

Check system health and return metrics.

```python
health = await monitor.check_system_health()
print(f"Status: {health['status']}")
print(f"CPU Usage: {health['metrics']['cpu_percent']}%")
print(f"Memory Usage: {health['metrics']['memory_percent']}%")
```

##### `get_metrics_summary(time_window: Optional[timedelta] = None) -> Dict[str, Any]`

Get a summary of metrics for a time window.

```python
from datetime import timedelta

# Last hour
summary = monitor.get_metrics_summary(timedelta(hours=1))

# Last 24 hours
summary = monitor.get_metrics_summary(timedelta(days=1))

for metric_name, stats in summary.items():
    print(f"{metric_name}: avg={stats['avg']:.2f}, count={stats['count']}")
```

##### `get_health_summary() -> Dict[str, Any]`

Get a summary of health checks.

```python
health_summary = monitor.get_health_summary()
print(f"Overall status: {health_summary['status']}")
for check in health_summary['checks']:
    print(f"{check['name']}: {check['status']} - {check['message']}")
```

##### `get_performance_summary() -> Dict[str, Any]`

Get a comprehensive performance summary.

```python
summary = monitor.get_performance_summary()
print(f"Uptime: {summary['uptime_seconds']} seconds")
print(f"Total requests: {sum(s['total_requests'] for s in summary['request_stats'].values())}")
```

##### `add_alert_callback(callback: Callable)`

Add a callback for alerts.

```python
def alert_callback(alert):
    print(f"Alert: {alert['type']} - {alert['message']}")

monitor.add_alert_callback(alert_callback)
```

##### `trigger_alert(alert_type: str, message: str, severity: str = "warning")`

Trigger an alert.

```python
await monitor.trigger_alert("high_cpu", "CPU usage above 90%", "critical")
```

##### `export_metrics(filepath: str)`

Export metrics to a JSON file.

```python
monitor.export_metrics("metrics_export.json")
```

### `monitor_performance(operation_name: str)`

Decorator for monitoring function performance.

```python
from utils.performance_monitor import monitor_performance

@monitor_performance("database_query")
async def get_user_data(user_id):
    # Function implementation
    pass

@monitor_performance("api_call")
def fetch_odds():
    # Function implementation
    pass
```

---

## Error Handler

The error handler provides custom exceptions and error tracking.

### Custom Exceptions

#### `DBSBMError`

Base exception for DBSBM.

```python
from utils.error_handler import DBSBMError

class CustomError(DBSBMError):
    pass
```

#### `DatabaseError`

Database-related errors.

```python
from utils.error_handler import DatabaseError

raise DatabaseError("Connection failed", user_id=123456789)
```

#### `APIError`

API-related errors.

```python
from utils.error_handler import APIError

raise APIError("API request failed", "sports_api", 500, user_id=123456789)
```

#### `RateLimitError`

Rate limiting errors.

```python
from utils.error_handler import RateLimitError

raise RateLimitError("Rate limit exceeded", retry_after=30.0)
```

#### `ValidationError`

Data validation errors.

```python
from utils.error_handler import ValidationError

raise ValidationError("Invalid user input")
```

#### `AuthenticationError`

Authentication and authorization errors.

```python
from utils.error_handler import AuthenticationError

raise AuthenticationError("Invalid token")
```

#### `ConfigurationError`

Configuration-related errors.

```python
from utils.error_handler import ConfigurationError

raise ConfigurationError("Missing required configuration")
```

#### `InsufficientUnitsError`

Insufficient units/balance errors.

```python
from utils.error_handler import InsufficientUnitsError

raise InsufficientUnitsError("Insufficient balance")
```

#### `BettingError`

Betting-related errors.

```python
from utils.error_handler import BettingError

raise BettingError("Bet placement failed")
```

#### `ImageGenerationError`

Image generation errors.

```python
from utils.error_handler import ImageGenerationError

raise ImageGenerationError("Failed to generate image")
```

### `ErrorHandler`

Main class for error handling and tracking.

#### Methods

##### `record_error(error: Exception, context: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None, guild_id: Optional[int] = None, command: Optional[str] = None, severity: str = "error")`

Record an error occurrence.

```python
from utils.error_handler import ErrorHandler

handler = ErrorHandler()

try:
    # Some operation
    pass
except Exception as e:
    handler.record_error(
        e, 
        context={"operation": "user_registration"}, 
        user_id=123456789,
        severity="warning"
    )
```

##### `handle_error(error: Exception, context: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None, guild_id: Optional[int] = None, command: Optional[str] = None) -> bool`

Handle an error with recovery strategies.

```python
recovered = await handler.handle_error(
    error,
    context={"command": "place_bet"},
    user_id=123456789,
    command="place_bet"
)

if not recovered:
    # Handle unrecovered error
    pass
```

##### `add_recovery_strategy(error_type: Type[Exception], strategy: Callable)`

Add a recovery strategy for a specific error type.

```python
async def database_recovery(error, context, user_id, guild_id, command):
    # Recovery logic
    return True  # Return True if recovered

handler.add_recovery_strategy(DatabaseError, database_recovery)
```

##### `get_error_summary(time_window: Optional[timedelta] = None) -> Dict[str, Any]`

Get a summary of errors for a time window.

```python
from datetime import timedelta

# Last hour
summary = handler.get_error_summary(timedelta(hours=1))

print(f"Total errors: {summary['total_errors']}")
for error_type, count in summary['error_types'].items():
    print(f"{error_type}: {count}")
```

##### `get_error_patterns() -> Dict[str, Dict[str, Any]]`

Get error pattern analysis.

```python
patterns = handler.get_error_patterns()
for pattern_key, pattern_data in patterns.items():
    print(f"{pattern_key}: {pattern_data['count']} occurrences")
```

##### `add_alert_callback(callback: Callable)`

Add a callback for error alerts.

```python
def error_alert_callback(alert):
    print(f"Error alert: {alert['message']}")

handler.add_alert_callback(error_alert_callback)
```

##### `clear_errors()`

Clear all stored errors.

```python
handler.clear_errors()
```

##### `export_errors(filepath: str)`

Export errors to a JSON file.

```python
handler.export_errors("errors_export.json")
```

### `handle_errors(context: Optional[Dict[str, Any]] = None)`

Decorator to handle errors in functions.

```python
from utils.error_handler import handle_errors

@handle_errors({"service": "user_service"})
async def create_user(interaction):
    # Function implementation
    pass

@handle_errors({"operation": "database_query"})
def query_database():
    # Function implementation
    pass
```

---

## Database Manager

The database manager handles MySQL connections and queries.

### `DatabaseManager`

Main class for database operations.

#### Methods

##### `connect() -> aiomysql.Pool`

Connect to the database and return a connection pool.

```python
from data.db_manager import DatabaseManager

db_manager = DatabaseManager()
pool = await db_manager.connect()
```

##### `execute(query: str, params: Optional[Tuple] = None) -> Tuple[int, Optional[int]]`

Execute a query and return (affected_rows, last_row_id).

```python
affected_rows, last_id = await db_manager.execute(
    "INSERT INTO users (user_id, username) VALUES (%s, %s)",
    (123456789, "testuser")
)
```

##### `fetch_one(query: str, params: Optional[Tuple] = None) -> Optional[Dict]`

Fetch a single row.

```python
user = await db_manager.fetch_one(
    "SELECT * FROM users WHERE user_id = %s",
    (123456789,)
)
```

##### `fetch_all(query: str, params: Optional[Tuple] = None) -> List[Dict]`

Fetch all rows.

```python
users = await db_manager.fetch_all("SELECT * FROM users")
```

##### `fetchval(query: str, params: Optional[Tuple] = None) -> Optional[Any]`

Fetch a single value.

```python
count = await db_manager.fetchval("SELECT COUNT(*) FROM users")
```

---

## Services

### BetService

Handles betting operations.

#### Methods

##### `start()`

Start the bet service.

```python
await bet_service.start()
```

##### `confirm_bet(user_id: int, bet_id: int, message_id: int) -> bool`

Confirm a bet.

```python
confirmed = await bet_service.confirm_bet(123456789, 12345, 67890)
```

##### `create_straight_bet(guild_id: int, user_id: int, league: str, bet_type: str, units: float, odds: float, team: str, opponent: str, line: str, api_game_id: str, channel_id: int) -> int`

Create a straight bet.

```python
bet_id = await bet_service.create_straight_bet(
    guild_id=123456789,
    user_id=987654321,
    league="NFL",
    bet_type="spread",
    units=2.0,
    odds=1.85,
    team="Patriots",
    opponent="Jets",
    line="-3.5",
    api_game_id="game_123",
    channel_id=111222333
)
```

##### `cleanup_expired_bets()`

Clean up expired bets.

```python
await bet_service.cleanup_expired_bets()
```

### UserService

Handles user operations.

#### Methods

##### `get_user(user_id: int) -> Optional[Dict]`

Get user information.

```python
user = await user_service.get_user(123456789)
```

##### `get_or_create_user(user_id: int, username: str) -> Dict`

Get or create a user.

```python
user = await user_service.get_or_create_user(123456789, "testuser")
```

##### `update_user_balance(user_id: int, amount: float, reason: str) -> Dict`

Update user balance.

```python
updated_user = await user_service.update_user_balance(
    123456789, 
    50.0, 
    "bet_win"
)
```

### AdminService

Handles administrative operations.

#### Methods

##### `start()`

Start the admin service.

```python
await admin_service.start()
```

##### `get_guild_subscription_level(guild_id: int) -> str`

Get guild subscription level.

```python
level = await admin_service.get_guild_subscription_level(123456789)
```

##### `check_guild_subscription(guild_id: int) -> bool`

Check if guild has active subscription.

```python
has_subscription = await admin_service.check_guild_subscription(123456789)
```

##### `setup_guild(guild_id: int, settings: Dict) -> bool`

Setup guild configuration.

```python
success = await admin_service.setup_guild(123456789, {
    "embed_channel_1": 111222333,
    "admin_role": 444555666,
    "min_units": 1.0,
    "max_units": 10.0
})
```

---

## Usage Examples

### Complete Setup Example

```python
import asyncio
from utils.environment_validator import validate_environment
from utils.rate_limiter import get_rate_limiter
from utils.performance_monitor import get_performance_monitor
from utils.error_handler import get_error_handler, initialize_default_recovery_strategies
from data.db_manager import DatabaseManager

async def setup_system():
    # Validate environment
    if not validate_environment():
        print("Environment validation failed!")
        return False
    
    # Initialize components
    rate_limiter = get_rate_limiter()
    performance_monitor = get_performance_monitor()
    error_handler = get_error_handler()
    initialize_default_recovery_strategies()
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.connect()
    
    print("System setup complete!")
    return True

# Run setup
asyncio.run(setup_system())
```

### Error Handling Example

```python
from utils.error_handler import handle_errors, DatabaseError

@handle_errors({"operation": "user_creation"})
async def create_user_with_error_handling(interaction):
    try:
        # Database operation
        user = await user_service.get_or_create_user(
            interaction.user.id, 
            interaction.user.name
        )
        return user
    except DatabaseError as e:
        # Handle database error specifically
        await interaction.response.send_message(
            "Database error occurred. Please try again later.",
            ephemeral=True
        )
        raise
```

### Performance Monitoring Example

```python
from utils.performance_monitor import monitor_performance

@monitor_performance("user_registration")
async def register_user(interaction):
    # Function implementation
    pass

# Monitor system health
async def check_health():
    monitor = get_performance_monitor()
    health = await monitor.check_system_health()
    
    if health['status'] == 'critical':
        await monitor.trigger_alert(
            "system_health", 
            health['message'], 
            "critical"
        )
```

### Rate Limiting Example

```python
from utils.rate_limiter import rate_limit, RateLimitExceededError

@rate_limit("bet_placement")
async def place_bet(interaction):
    # Bet placement logic
    pass

# Handle rate limit errors
async def handle_bet_command(interaction):
    try:
        await place_bet(interaction)
    except RateLimitExceededError as e:
        await interaction.response.send_message(
            f"Rate limit exceeded. {str(e)}",
            ephemeral=True
        )
```

---

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token
API_KEY=your_api_sports_key
MYSQL_HOST=localhost
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=betting_bot
TEST_GUILD_ID=your_test_guild_id

# Optional
ODDS_API_KEY=your_odds_api_key
LOG_LEVEL=INFO
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=5
MYSQL_PORT=3306
MYSQL_POOL_MIN_SIZE=1
MYSQL_POOL_MAX_SIZE=10
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
```

---

## Best Practices

1. **Always validate environment variables** before starting the application
2. **Use rate limiting** for user-facing operations to prevent abuse
3. **Monitor performance** for critical operations
4. **Handle errors gracefully** with appropriate recovery strategies
5. **Log errors with context** for better debugging
6. **Use custom exceptions** for domain-specific errors
7. **Monitor system health** regularly
8. **Export metrics and errors** for analysis
9. **Use connection pooling** for database operations
10. **Implement proper cleanup** for resources

---

## Troubleshooting

### Common Issues

1. **Environment validation fails**: Check that all required environment variables are set
2. **Database connection fails**: Verify MySQL credentials and network connectivity
3. **Rate limiting too aggressive**: Adjust rate limit configurations
4. **Performance issues**: Monitor system metrics and optimize slow operations
5. **Error handling not working**: Ensure error handlers are properly initialized

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Export Data for Analysis

```python
# Export metrics
monitor = get_performance_monitor()
monitor.export_metrics("debug_metrics.json")

# Export errors
handler = get_error_handler()
handler.export_errors("debug_errors.json")
``` 