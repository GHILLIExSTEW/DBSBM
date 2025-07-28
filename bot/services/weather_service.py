"""
Weather Service for DBSBM System

This module provides weather information for game venues using WeatherAPI.com.
"""

import logging
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from config.settings import get_settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from WeatherAPI.com."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://api.weatherapi.com/v1"
        self.api_key = self.settings.api.weather_key.get_secret_value(
        ) if self.settings.api.weather_key else None
        self.timeout = self.settings.api.timeout

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
                "aqi": "no"  # Disable air quality to save API calls
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
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

    async def get_forecast_weather(self, location: str, days: int = 1) -> Optional[Dict]:
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
                "aqi": "no"
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
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
                    "localtime": location.get("localtime", "")
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
                    "last_updated": current.get("last_updated", "")
                }
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

                formatted_forecast.append({
                    "date": day.get("date", ""),
                    "temp": {
                        "max_c": day_data.get("maxtemp_c", 0),
                        "max_f": day_data.get("maxtemp_f", 0),
                        "min_c": day_data.get("mintemp_c", 0),
                        "min_f": day_data.get("mintemp_f", 0),
                        "avg_c": day_data.get("avgtemp_c", 0),
                        "avg_f": day_data.get("avgtemp_f", 0)
                    },
                    "condition": {
                        "text": condition.get("text", "Unknown"),
                        "icon": condition.get("icon", "")
                    },
                    "wind": {
                        "max_mph": day_data.get("maxwind_mph", 0),
                        "max_kph": day_data.get("maxwind_kph", 0)
                    },
                    "precipitation": {
                        "total_mm": day_data.get("totalprecip_mm", 0),
                        "total_in": day_data.get("totalprecip_in", 0),
                        "chance_of_rain": day_data.get("daily_chance_of_rain", 0),
                        "chance_of_snow": day_data.get("daily_chance_of_snow", 0)
                    },
                    "astro": {
                        "sunrise": astro.get("sunrise", ""),
                        "sunset": astro.get("sunset", ""),
                        "moonrise": astro.get("moonrise", ""),
                        "moonset": astro.get("moonset", "")
                    }
                })

            return {
                "location": {
                    "name": location.get("name", "Unknown"),
                    "region": location.get("region", ""),
                    "country": location.get("country", ""),
                    "lat": location.get("lat", 0),
                    "lon": location.get("lon", 0)
                },
                "forecast": formatted_forecast
            }
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return {}

    async def get_weather_for_venue(self, venue_name: str, city: str = None) -> Optional[Dict]:
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
            message += f"\n🕐 **Last updated:** {current.get('last_updated', 'Unknown')}"

            return message

        except Exception as e:
            logger.error(f"Error formatting weather message: {e}")
            return "❌ Error formatting weather data."

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
