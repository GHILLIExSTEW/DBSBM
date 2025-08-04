"""
Weather Service for DBSBM System

This module provides weather information for game venues using WeatherAPI.com.
"""

import logging
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime, timedelta

# Import centralized configuration with fallback
try:
    from config.settings import get_settings
except ImportError:
    # Fallback - try to import from parent directory
    import sys
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add multiple possible paths for different execution contexts
    possible_paths = [
        os.path.dirname(os.path.dirname(current_dir)),  # From bot/services/
        os.path.dirname(current_dir),  # From services/
    ]
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from config.settings import get_settings
    except ImportError:
        # Final fallback - create mock function for testing
        def get_settings():
            return None


logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from WeatherAPI.com."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://api.weatherapi.com/v1"

        # Handle case where settings might be None
        if self.settings and hasattr(self.settings, "api"):
            self.api_key = (
                self.settings.api.weather_key.get_secret_value()
                if self.settings.api.weather_key
                else None
            )
            self.timeout = self.settings.api.timeout
        else:
            # Fallback to environment variables
            import os

            self.api_key = os.getenv("WEATHER_API_KEY")
            self.timeout = int(os.getenv("API_TIMEOUT", "30"))

    async def get_current_weather(self, location: str) -> Optional[Dict]:
        """
        Get current weather for a location.

        Args:
            location: City name, coordinates, or venue name

        Returns:
            Weather data dictionary or None if error
        """
        if not self.api_key:
            logger.error("Weather API key not configured")
            return None

        try:
            url = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "no",  # Disable air quality to save API calls
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_weather_data(data)
                    else:
                        error_data = await response.json()
                        logger.error(f"Weather API error: {error_data}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return None

    async def get_forecast_weather(
        self, location: str, days: int = 1
    ) -> Optional[Dict]:
        """
        Get weather forecast for a location.

        Args:
            location: City name, coordinates, or venue name
            days: Number of days to forecast (1-14)

        Returns:
            Forecast data dictionary or None if error
        """
        if not self.api_key:
            logger.error("Weather API key not configured")
            return None

        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": min(days, 14),  # API limit is 14 days
                "aqi": "no",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_forecast_data(data)
                    else:
                        error_data = await response.json()
                        logger.error(f"Weather API error: {error_data}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching forecast for {location}: {e}")
            return None

    def _format_weather_data(self, data: Dict) -> Dict:
        """Format weather API response into a clean dictionary."""
        try:
            location = data.get("location", {})
            current = data.get("current", {})
            condition = current.get("condition", {})

            return {
                "location": {
                    "name": location.get("name", "Unknown"),
                    "region": location.get("region", ""),
                    "country": location.get("country", ""),
                    "lat": location.get("lat", 0),
                    "lon": location.get("lon", 0),
                    "localtime": location.get("localtime", ""),
                },
                "current": {
                    "temp_c": current.get("temp_c", 0),
                    "temp_f": current.get("temp_f", 0),
                    "feelslike_c": current.get("feelslike_c", 0),
                    "feelslike_f": current.get("feelslike_f", 0),
                    "condition": condition.get("text", "Unknown"),
                    "condition_icon": condition.get("icon", ""),
                    "wind_mph": current.get("wind_mph", 0),
                    "wind_kph": current.get("wind_kph", 0),
                    "wind_dir": current.get("wind_dir", ""),
                    "pressure_mb": current.get("pressure_mb", 0),
                    "precip_mm": current.get("precip_mm", 0),
                    "humidity": current.get("humidity", 0),
                    "cloud": current.get("cloud", 0),
                    "vis_km": current.get("vis_km", 0),
                    "uv": current.get("uv", 0),
                    "last_updated": current.get("last_updated", ""),
                },
            }
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return {}

    def _format_forecast_data(self, data: Dict) -> Dict:
        """Format forecast API response into a clean dictionary."""
        try:
            location = data.get("location", {})
            forecast = data.get("forecast", {})
            forecastday = forecast.get("forecastday", [])

            formatted_forecast = []
            for day in forecastday:
                day_data = day.get("day", {})
                astro = day.get("astro", {})
                condition = day_data.get("condition", {})

                formatted_forecast.append(
                    {
                        "date": day.get("date", ""),
                        "temp": {
                            "max_c": day_data.get("maxtemp_c", 0),
                            "max_f": day_data.get("maxtemp_f", 0),
                            "min_c": day_data.get("mintemp_c", 0),
                            "min_f": day_data.get("mintemp_f", 0),
                            "avg_c": day_data.get("avgtemp_c", 0),
                            "avg_f": day_data.get("avgtemp_f", 0),
                        },
                        "condition": {
                            "text": condition.get("text", "Unknown"),
                            "icon": condition.get("icon", ""),
                        },
                        "wind": {
                            "max_mph": day_data.get("maxwind_mph", 0),
                            "max_kph": day_data.get("maxwind_kph", 0),
                        },
                        "precipitation": {
                            "total_mm": day_data.get("totalprecip_mm", 0),
                            "total_in": day_data.get("totalprecip_in", 0),
                            "chance_of_rain": day_data.get("daily_chance_of_rain", 0),
                            "chance_of_snow": day_data.get("daily_chance_of_snow", 0),
                        },
                        "humidity": day_data.get("avghumidity", 0),
                        "astro": {
                            "sunrise": astro.get("sunrise", ""),
                            "sunset": astro.get("sunset", ""),
                            "moonrise": astro.get("moonrise", ""),
                            "moonset": astro.get("moonset", ""),
                        },
                    }
                )

            return {
                "location": {
                    "name": location.get("name", "Unknown"),
                    "region": location.get("region", ""),
                    "country": location.get("country", ""),
                    "lat": location.get("lat", 0),
                    "lon": location.get("lon", 0),
                },
                "forecast": formatted_forecast,
            }
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return {}

    async def get_weather_for_venue(
        self, venue_name: str, city: str = None
    ) -> Optional[Dict]:
        """
        Get weather for a specific venue.

        Args:
            venue_name: Name of the venue/stadium
            city: City name (optional, used as fallback)

        Returns:
            Weather data for the venue
        """
        # Try venue name first, then city as fallback
        location = venue_name
        if city and venue_name != city:
            location = f"{venue_name}, {city}"

        weather_data = await self.get_current_weather(location)
        if not weather_data:
            # Fallback to city only
            if city and venue_name != city:
                weather_data = await self.get_current_weather(city)

        return weather_data

    def format_weather_message(self, weather_data: Dict, venue_name: str = None) -> str:
        """Format weather data into a readable Discord message."""
        if not weather_data:
            return "❌ Unable to fetch weather data."

        try:
            location = weather_data.get("location", {})
            current = weather_data.get("current", {})

            location_name = location.get("name", "Unknown Location")
            if venue_name and venue_name not in location_name:
                location_name = f"{venue_name} ({location_name})"

            temp_c = current.get("temp_c", 0)
            temp_f = current.get("temp_f", 0)
            feelslike_c = current.get("feelslike_c", 0)
            feelslike_f = current.get("feelslike_f", 0)
            condition = current.get("condition", "Unknown")
            wind_mph = current.get("wind_mph", 0)
            wind_dir = current.get("wind_dir", "")
            humidity = current.get("humidity", 0)
            precip_mm = current.get("precip_mm", 0)

            # Create weather emoji based on condition
            weather_emoji = self._get_weather_emoji(condition)

            message = f"🌤️ **Weather for {location_name}**\n\n"
            message += f"{weather_emoji} **{condition}**\n"
            message += f"🌡️ **Temperature:** {temp_c}°C ({temp_f}°F)\n"

            if feelslike_c != temp_c:
                message += f"🌡️ **Feels like:** {feelslike_c}°C ({feelslike_f}°F)\n"

            if wind_mph > 0:
                message += f"💨 **Wind:** {wind_mph} mph {wind_dir}\n"

            message += f"💧 **Humidity:** {humidity}%\n"

            if precip_mm > 0:
                message += f"🌧️ **Precipitation:** {precip_mm} mm\n"

            message += f"\n📍 **Location:** {location.get('region', '')}, {location.get('country', '')}"
            message += (
                f"\n🕐 **Last updated:** {current.get('last_updated', 'Unknown')}"
            )

            return message

        except Exception as e:
            logger.error(f"Error formatting weather message: {e}")
            return "❌ Error formatting weather data."

    def format_forecast_message(
        self, weather_data: Dict, venue_name: str = None
    ) -> str:
        """Format forecast weather data into a readable Discord message."""
        if not weather_data:
            return "❌ Unable to fetch forecast data."

        try:
            location = weather_data.get("location", {})
            forecast = weather_data.get("forecast", [])

            location_name = location.get("name", "Unknown Location")
            if venue_name and venue_name not in location_name:
                location_name = f"{venue_name} ({location_name})"

            message = f"📅 **3-Day Forecast for {location_name}**\n\n"
            message += f"📍 **Location:** {location.get('region', '')}, {location.get('country', '')}\n\n"

            # Handle both list format (from _format_forecast_data) and dict format (from API)
            forecast_days = []
            if isinstance(forecast, list):
                forecast_days = forecast[:3]  # Limit to 3 days
            elif isinstance(forecast, dict):
                forecast_days = forecast.get("forecastday", [])[:3]  # Limit to 3 days

            for i, day in enumerate(forecast_days):
                # Handle different data structures
                if isinstance(day, dict):
                    if "date" in day and "temp" in day:
                        # Formatted structure from _format_forecast_data
                        date = day.get("date", "Unknown")
                        condition = day.get("condition", {}).get("text", "Unknown")
                        temp_data = day.get("temp", {})
                        max_temp_c = temp_data.get("max_c", 0)
                        max_temp_f = temp_data.get("max_f", 0)
                        min_temp_c = temp_data.get("min_c", 0)
                        min_temp_f = temp_data.get("min_f", 0)
                        wind_data = day.get("wind", {})
                        max_wind_mph = wind_data.get("max_mph", 0)
                        precip_data = day.get("precipitation", {})
                        total_precip_mm = precip_data.get("total_mm", 0)
                        avg_humidity = day.get("humidity", 0)
                    else:
                        # Raw API structure
                        date = day.get("date", "Unknown")
                        day_info = day.get("day", {})
                        condition = day_info.get("condition", {}).get("text", "Unknown")
                        max_temp_c = day_info.get("maxtemp_c", 0)
                        max_temp_f = day_info.get("maxtemp_f", 0)
                        min_temp_c = day_info.get("mintemp_c", 0)
                        min_temp_f = day_info.get("mintemp_f", 0)
                        avg_humidity = day_info.get("avghumidity", 0)
                        total_precip_mm = day_info.get("totalprecip_mm", 0)
                        max_wind_mph = day_info.get("maxwind_mph", 0)
                else:
                    continue

                # Format date
                try:
                    from datetime import datetime

                    dt = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = dt.strftime("%A, %B %d")
                except:
                    formatted_date = date

                # Get weather emoji
                weather_emoji = self._get_weather_emoji(condition)

                message += f"**{formatted_date}**\n"
                message += f"{weather_emoji} **{condition}**\n"
                message += f"🌡️ **High:** {max_temp_c}°C ({max_temp_f}°F) | **Low:** {min_temp_c}°C ({min_temp_f}°F)\n"

                if avg_humidity > 0:
                    message += f"💧 **Humidity:** {avg_humidity}%\n"

                if total_precip_mm > 0:
                    message += f"🌧️ **Precipitation:** {total_precip_mm} mm\n"

                if max_wind_mph > 0:
                    message += f"💨 **Max Wind:** {max_wind_mph} mph\n"

                message += "\n"

            return message

        except Exception as e:
            logger.error(f"Error formatting forecast message: {e}")
            return "❌ Error formatting forecast data."

    def _get_weather_emoji(self, condition: str) -> str:
        """Get appropriate emoji for weather condition."""
        condition_lower = condition.lower()

        if any(word in condition_lower for word in ["sunny", "clear"]):
            return "☀️"
        elif any(word in condition_lower for word in ["cloudy", "overcast"]):
            return "☁️"
        elif any(word in condition_lower for word in ["rain", "drizzle", "shower"]):
            return "🌧️"
        elif any(word in condition_lower for word in ["snow", "sleet"]):
            return "❄️"
        elif any(word in condition_lower for word in ["thunder", "storm"]):
            return "⛈️"
        elif any(word in condition_lower for word in ["fog", "mist"]):
            return "🌫️"
        else:
            return "🌤️"
