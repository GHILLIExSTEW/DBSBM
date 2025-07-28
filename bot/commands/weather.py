"""
Weather Command for DBSBM System

This module provides a Discord command to get weather information for game venues.
"""

import logging
from typing import Dict, List, Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from bot.services.weather_service import WeatherService

# Import GameService with fallback for missing API_KEY
GAME_SERVICE_AVAILABLE = False
GameService = None

try:
    from bot.services.game_service import GameService

    GAME_SERVICE_AVAILABLE = True
except (ValueError, ImportError):
    # GameService requires API_KEY, so we'll handle this gracefully
    GAME_SERVICE_AVAILABLE = False
    GameService = None

logger = logging.getLogger(__name__)


class WeatherCog(commands.Cog):
    """Cog for weather-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.weather_service = WeatherService()
        # Handle case where game_service might not be available
        self.game_service = getattr(bot, "game_service", None)

    @app_commands.command(
        name="weather",
        description="Get weather information for games in a specific sport and league",
    )
    @app_commands.describe(
        sport="The sport type (e.g., football, basketball, baseball, hockey)",
        league="The league name (e.g., NFL, NBA, MLB, NHL, EPL)",
    )
    async def weather_command(self, interaction: Interaction, sport: str, league: str):
        """Get weather information for games in a specific sport and league."""
        try:
            # Defer the response since weather API calls can take time
            await interaction.response.defer(thinking=True)

            # Normalize sport and league names
            sport = sport.lower().strip()
            league = league.upper().strip()

            # Get upcoming games for the specified sport and league
            games = await self._get_upcoming_games(sport, league)

            if not games:
                await interaction.followup.send(
                    f"❌ No upcoming games found for {sport.title()} - {league}.\n"
                    f"Please check the sport and league names and try again."
                )
                return

            # Get weather for each game venue
            weather_messages = []
            for game in games[:5]:  # Limit to 5 games to avoid spam
                venue_name = game.get("venue")
                home_team = game.get("home_team_name", "Unknown")
                away_team = game.get("away_team_name", "Unknown")
                start_time = game.get("start_time", "Unknown")

                if venue_name:
                    weather_data = await self.weather_service.get_weather_for_venue(
                        venue_name
                    )
                    if weather_data:
                        weather_message = self.weather_service.format_weather_message(
                            weather_data, venue_name
                        )

                        # Add game info to the weather message
                        game_info = f"\n\n🏈 **Game:** {away_team} @ {home_team}"
                        game_info += f"\n🕐 **Start Time:** {start_time}"

                        weather_messages.append(weather_message + game_info)
                    else:
                        # Fallback message if weather data unavailable
                        fallback_msg = (
                            f"🌤️ **Weather for {venue_name}**\n\n"
                            f"❌ Weather data unavailable for this venue.\n\n"
                            f"🏈 **Game:** {away_team} @ {home_team}\n"
                            f"🕐 **Start Time:** {start_time}"
                        )
                        weather_messages.append(fallback_msg)
                else:
                    # No venue information
                    no_venue_msg = (
                        f"🌤️ **Weather Information**\n\n"
                        f"❌ No venue information available for this game.\n\n"
                        f"🏈 **Game:** {away_team} @ {home_team}\n"
                        f"🕐 **Start Time:** {start_time}"
                    )
                    weather_messages.append(no_venue_msg)

            # Send the weather information
            if weather_messages:
                # Combine messages if there are multiple games
                if len(weather_messages) == 1:
                    await interaction.followup.send(weather_messages[0])
                else:
                    # Send multiple messages for multiple games
                    combined_message = (
                        f"🌤️ **Weather for {sport.title()} - {league} Games**\n\n"
                    )
                    combined_message += "\n\n---\n\n".join(weather_messages)

                    # Split if message is too long
                    if len(combined_message) > 2000:
                        for i, message in enumerate(weather_messages, 1):
                            await interaction.followup.send(f"**Game {i}:**\n{message}")
                    else:
                        await interaction.followup.send(combined_message)
            else:
                await interaction.followup.send(
                    f"❌ No weather information available for {sport.title()} - {league} games."
                )

        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching weather information. Please try again later."
            )

    async def _get_upcoming_games(self, sport: str, league: str) -> List[Dict]:
        """Get upcoming games for the specified sport and league."""
        try:
            # Check if game service is available
            if not hasattr(self.bot, "game_service") or not self.game_service:
                logger.error("Game service not available")
                return []

            # Map sport names to API sport keys
            sport_mapping = {
                "football": "football",
                "soccer": "football",
                "basketball": "basketball",
                "baseball": "baseball",
                "hockey": "hockey",
                "ice hockey": "hockey",
                "ufc": "ufc",
                "mma": "ufc",
            }

            api_sport = sport_mapping.get(sport, sport)

            # Get games from the database
            games = await self.game_service.get_upcoming_games_by_league(
                sport=api_sport, league_name=league, limit=10  # Get next 10 games
            )

            return games

        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []

    @weather_command.error
    async def weather_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for the weather command."""
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.followup.send(
                "❌ An error occurred while processing the weather command. "
                "Please check your input and try again."
            )
        else:
            await interaction.followup.send(
                "❌ An unexpected error occurred. Please try again later."
            )


async def setup(bot: commands.Bot):
    """Set up the weather cog."""
    await bot.add_cog(WeatherCog(bot))
