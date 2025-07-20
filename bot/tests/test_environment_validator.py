"""
Tests for the environment validator utility.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from bot.utils.environment_validator import EnvironmentValidator, validate_environment


class TestEnvironmentValidator:
    """Test cases for EnvironmentValidator class."""

    def test_validate_all_success(self):
        """Test successful validation with all required variables set."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
            },
        ):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is True
            assert len(errors) == 0

    def test_validate_all_missing_required(self):
        """Test validation failure with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is False
            assert len(errors) > 0
            assert any("DISCORD_TOKEN" in error for error in errors)
            assert any("API_KEY" in error for error in errors)

    def test_optional_vars_defaults(self):
        """Test that optional variables get default values."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
            },
            clear=True,
        ):
            EnvironmentValidator.validate_all()
            assert os.getenv("LOG_LEVEL") == "INFO"
            assert os.getenv("API_TIMEOUT") == "30"
            assert os.getenv("MYSQL_PORT") == "3306"

    def test_invalid_log_level(self):
        """Test validation with invalid log level."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
                "LOG_LEVEL": "INVALID_LEVEL",
            },
        ):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is False
            assert any("Invalid LOG_LEVEL" in error for error in errors)

    def test_invalid_numeric_values(self):
        """Test validation with invalid numeric values."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
                "API_TIMEOUT": "invalid_number",
            },
        ):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is False
            assert any("Invalid API_TIMEOUT" in error for error in errors)

    def test_invalid_guild_id(self):
        """Test validation with invalid guild ID."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "invalid_id",
            },
        ):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is False
            assert any("Invalid TEST_GUILD_ID" in error for error in errors)

    def test_mysql_pool_size_validation(self):
        """Test MySQL pool size validation."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
                "MYSQL_POOL_MIN_SIZE": "10",
                "MYSQL_POOL_MAX_SIZE": "5",
            },
        ):
            is_valid, errors = EnvironmentValidator.validate_all()
            assert is_valid is False
            assert any("MYSQL_POOL_MIN_SIZE" in error for error in errors)

    def test_get_config_summary(self):
        """Test configuration summary generation."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test_token",
                "API_KEY": "test_api_key",
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "test_user",
                "MYSQL_PASSWORD": "test_password",
                "MYSQL_DB": "test_db",
                "TEST_GUILD_ID": "123456789",
            },
        ):
            config = EnvironmentValidator.get_config_summary()

            # Check that sensitive data is masked
            assert config["DISCORD_TOKEN"] == "***"
            assert config["API_KEY"] == "***"
            assert config["MYSQL_PASSWORD"] == "***"

            # Check that non-sensitive data is visible
            assert config["MYSQL_HOST"] == "localhost"
            assert config["MYSQL_USER"] == "test_user"
            assert config["MYSQL_DB"] == "test_db"
            assert config["TEST_GUILD_ID"] == "123456789"


class TestValidateEnvironment:
    """Test cases for the main validate_environment function."""

    @patch("utils.environment_validator.EnvironmentValidator.validate_all")
    def test_validate_environment_success(self, mock_validate):
        """Test successful environment validation."""
        mock_validate.return_value = (True, [])

        with patch(
            "utils.environment_validator.EnvironmentValidator.print_config_summary"
        ):
            result = validate_environment()
            assert result is True

    @patch("utils.environment_validator.EnvironmentValidator.validate_all")
    def test_validate_environment_failure(self, mock_validate):
        """Test failed environment validation."""
        mock_validate.return_value = (False, ["Missing DISCORD_TOKEN"])

        result = validate_environment()
        assert result is False

    @patch("utils.environment_validator.EnvironmentValidator.validate_all")
    def test_validate_environment_exception(self, mock_validate):
        """Test environment validation with exception."""
        mock_validate.side_effect = Exception("Test exception")

        result = validate_environment()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
