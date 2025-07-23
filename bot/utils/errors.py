# betting-bot/utils/errors.py

"""Custom error classes for the betting bot."""


class BettingBotError(Exception):
    """Base error class for betting bot errors."""


class AdminServiceError(BettingBotError):
    """Raised when there is an error in the admin service."""


class BetServiceError(BettingBotError):
    """Raised when there is an error in the bet service."""


class AnalyticsServiceError(BettingBotError):
    """Raised when there is an error in the analytics service."""


class ValidationError(BettingBotError):
    """Raised when there is a validation error."""


class ServiceError(Exception):
    """Base class for all service-related errors."""


# Added UserServiceError
class UserServiceError(ServiceError):
    """Raised when there's an error in the user service."""


class GameServiceError(ServiceError):
    """Raised when there's an error in the game service."""


class DataSyncError(ServiceError):
    """Raised when there's an error in data synchronization."""


# Consider renaming this if it's specific to db_manager or make it more generic
class DatabaseError(Exception):
    """Raised when there's an error in database operations."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthorizationError(Exception):
    """Raised when authorization fails."""


class RateLimitError(Exception):
    """Raised when rate limits are exceeded."""


class APIError(Exception):
    """Raised when there's an error in external API calls."""


class CacheError(Exception):
    """Raised when there's an error in cache operations."""


class ConfigurationError(Exception):
    """Raised when there's an error in configuration."""





class PaymentError(Exception):
    """Raised when there's an error in payment operations."""


class VoiceError(Exception):
    """Raised when there's an error in voice operations."""


class GameNotFoundError(GameServiceError):  # Changed inheritance to GameServiceError
    """Exception raised when a game is not found."""


class InsufficientUnitsError(BetServiceError):  # Changed inheritance to BetServiceError
    """Exception raised when a user has insufficient units."""


class InvalidBetTypeError(ValidationError):
    """Exception raised for invalid bet types."""


class InvalidOddsError(ValidationError):
    """Exception raised for invalid odds."""


class InvalidUnitsError(ValidationError):
    """Exception raised for invalid units."""


class GameDataError(GameServiceError):
    """Exception raised for game data errors."""


class LeagueNotFoundError(GameServiceError):
    """Exception raised when a league is not found."""


class ScheduleError(GameServiceError):
    """Exception raised for schedule-related errors."""


class StatsGenerationError(AnalyticsServiceError):
    """Exception raised for errors during stats generation."""


class DataProcessingError(AnalyticsServiceError):
    """Exception raised for errors during data processing."""


class VisualizationError(AnalyticsServiceError):
    """Exception raised for errors during data visualization."""
