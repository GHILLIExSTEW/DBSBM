"""
Weather Command for DBSBM System

This module provides a Discord command to get weather information for game venues.
"""

import logging
from typing import Any, Dict, List, Optional

import discord
from discord import ButtonStyle, Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, View

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


def get_all_sport_categories() -> List[str]:
    """Get all available sport categories."""
    return [
        "Football",
        "Basketball",
        "Baseball",
        "Hockey",
        "Soccer",
        "UFC",
        "Tennis",
        "Golf",
        "Racing",
        "Darts",
        "Rugby",
        "Handball",
        "Volleyball",
    ]


def get_leagues_by_sport(sport: str) -> List[str]:
    """Get leagues available for a specific sport."""
    sport_leagues = {
        "Football": ["NFL", "CFL", "XFL", "NCAA"],
        "Basketball": ["NBA", "WNBA", "NCAA", "Euroleague"],
        "Baseball": ["MLB", "NPB", "KBO", "CPBL"],
        "Hockey": ["NHL", "KHL"],
        "Soccer": [
            "EPL",
            "LaLiga",
            "Bundesliga",
            "SerieA",
            "Ligue1",
            "MLS",
            "ChampionsLeague",
        ],
        "UFC": ["UFC"],
        "Tennis": ["ATP", "WTA"],
        "Golf": ["PGA", "LPGA"],
        "Racing": ["Formula1", "NASCAR", "IndyCar"],
        "Darts": ["PDC"],
        "Rugby": ["SixNations", "SuperRugby"],
        "Handball": ["EHF"],
        "Volleyball": ["FIVB"],
    }
    return sport_leagues.get(sport, [])


class ManualSearchModal(Modal):
    """Modal for manual city/state search."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        super().__init__(title="Manual Weather Search")
        self.parent_view = parent_view

        self.city_input = TextInput(
            label="City",
            placeholder="Enter city name (e.g., New York, Los Angeles)",
            required=True,
            max_length=100,
            custom_id="weather_city_input",
        )

        self.state_input = TextInput(
            label="State/Country",
            placeholder="Enter state or country (e.g., NY, CA, UK)",
            required=False,
            max_length=100,
            custom_id="weather_state_input",
        )

        self.weather_type_input = TextInput(
            label="Weather Type",
            placeholder="Enter 'current' or 'forecast' (default: current)",
            required=False,
            max_length=20,
            custom_id="weather_type_input",
        )

        self.add_item(self.city_input)
        self.add_item(self.state_input)
        self.add_item(self.weather_type_input)

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            city = self.city_input.value.strip()
            state = self.state_input.value.strip() if self.state_input.value else ""
            weather_type = (
                self.weather_type_input.value.strip().lower()
                if self.weather_type_input.value
                else "current"
            )

            location = f"{city}, {state}" if state else city
            weather_service = WeatherService()

            if weather_type == "forecast":
                weather_data = await weather_service.get_forecast_weather(
                    location, days=3
                )
                if weather_data:
                    weather_message = weather_service.format_forecast_message(
                        weather_data, location
                    )
                    # Regular message
                    await interaction.response.send_message(weather_message)
                else:
                    await interaction.response.send_message(
                        f"❌ Could not find forecast weather information for **{location}**. "
                        "Please check the spelling and try again.",
                        ephemeral=True,
                    )
            else:
                weather_data = await weather_service.get_current_weather(location)
                if weather_data:
                    weather_message = weather_service.format_weather_message(
                        weather_data, location
                    )
                    # Regular message
                    await interaction.response.send_message(weather_message)
                else:
                    await interaction.response.send_message(
                        f"❌ Could not find weather information for **{location}**. "
                        "Please check the spelling and try again.",
                        ephemeral=True,
                    )
        except Exception as e:
            logger.error(f"Error in manual search: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching weather information. Please try again later.",
                ephemeral=True,
            )


class ManualSearchButton(Button):
    """Button to trigger manual search modal."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        super().__init__(
            label="Manual Search",
            style=ButtonStyle.secondary,
            emoji="🔍",
            custom_id=f"weather_manual_search_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle manual search button click."""
        try:
            modal = ManualSearchModal(self.parent_view)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error showing manual search modal: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while opening the search form. Please try again.",
                ephemeral=True,
            )


class WeatherTypeSelect(Select):
    """Select for weather type (current vs forecast)."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        options = [
            SelectOption(
                label="Current Weather",
                description="Get current weather conditions",
                value="current",
                emoji="🌤️",
            ),
            SelectOption(
                label="Weather Forecast",
                description="Get 3-day weather forecast",
                value="forecast",
                emoji="📅",
            ),
        ]
        super().__init__(
            placeholder="Select weather type...",
            options=options,
            custom_id=f"weather_type_select_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle weather type selection."""
        try:
            self.parent_view.selected_weather_type = self.values[0]
            await self.parent_view.go_next(interaction)
        except Exception as e:
            logger.error(f"Error in weather type selection: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True,
            )


class SportSelect(Select):
    """Select for sport categories."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        sports = get_all_sport_categories()
        options = [SelectOption(label=sport, value=sport) for sport in sports]
        super().__init__(
            placeholder="Select a sport...",
            options=options,
            custom_id=f"weather_sport_select_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle sport selection."""
        try:
            self.parent_view.selected_sport = self.values[0]
            await self.parent_view.go_next(interaction)
        except Exception as e:
            logger.error(f"Error in sport selection: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True,
            )


class LeagueSelect(Select):
    """Select for leagues within a sport."""

    def __init__(self, parent_view: "WeatherWorkflowView", leagues: List[str]):
        options = [SelectOption(label=league, value=league) for league in leagues]
        super().__init__(
            placeholder="Select a league...",
            options=options,
            custom_id=f"weather_league_select_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle league selection."""
        try:
            self.parent_view.selected_league = self.values[0]
            await self.parent_view.go_next(interaction)
        except Exception as e:
            logger.error(f"Error in league selection: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True,
            )


class GameSelect(Select):
    """Select for games within a league."""

    def __init__(self, parent_view: "WeatherWorkflowView", games: List[Dict]):
        options = []
        for game in games[:25]:  # Limit to 25 games
            home_team = game.get("home_team", "Unknown")
            away_team = game.get("away_team", "Unknown")
            start_time = game.get("start_time", "Unknown")

            # Format the option label
            label = f"{home_team} vs {away_team}"
            if start_time and start_time != "Unknown":
                try:
                    # Try to format the date
                    from datetime import datetime

                    if isinstance(start_time, str):
                        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        date_str = dt.strftime("%m/%d %H:%M")
                        label += f" ({date_str})"
                except:
                    pass

            options.append(SelectOption(label=label, value=str(game.get("id", ""))))

        super().__init__(
            placeholder="Select a game...",
            options=options,
            custom_id=f"weather_game_select_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view
        self.games = games

    async def callback(self, interaction: Interaction):
        """Handle game selection."""
        try:
            game_id = self.values[0]
            selected_game = next(
                (game for game in self.games if str(game.get("id", "")) == game_id),
                None,
            )

            if selected_game:
                self.parent_view.selected_game = selected_game
                await self.parent_view.show_weather_info(interaction)
            else:
                await interaction.response.send_message(
                    "❌ Selected game not found. Please try again.",
                    ephemeral=True,
                )
        except Exception as e:
            logger.error(f"Error in game selection: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True,
            )


class CancelButton(Button):
    """Button to cancel the weather workflow."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        super().__init__(
            label="Cancel",
            style=ButtonStyle.danger,
            emoji="❌",
            custom_id=f"weather_cancel_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle cancel button click."""
        try:
            await interaction.response.send_message(
                "Weather search cancelled.", ephemeral=True
            )
            self.parent_view.stop()
        except Exception as e:
            logger.error(f"Error in cancel button: {e}")


class WeatherWorkflowView(View):
    """View for managing the weather workflow."""

    def __init__(self, original_interaction: Interaction, bot: commands.Bot):
        super().__init__(timeout=300)  # 5 minute timeout
        self.original_interaction = original_interaction
        self.bot = bot
        self.selected_sport = None
        self.selected_league = None
        self.selected_game = None
        self.selected_weather_type = "current"  # Default to current weather
        self.current_step = 0

        # Add manual search button to all steps
        self.add_item(ManualSearchButton(self))
        self.add_item(CancelButton(self))

    async def start_flow(self, interaction: Interaction):
        """Start the weather workflow."""
        try:
            # First step: Select weather type
            weather_type_select = WeatherTypeSelect(self)
            view = View(timeout=300)
            view.add_item(weather_type_select)
            view.add_item(ManualSearchButton(self))
            view.add_item(CancelButton(self))

            content = "🌤️ **Weather Information**\n\nPlease select the type of weather information you'd like to get:"
            await interaction.response.send_message(content, view=view, ephemeral=True)
            self.current_step = 0

        except Exception as e:
            logger.error(f"Error starting weather flow: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the weather search. Please try again.",
                ephemeral=True,
            )

    async def go_next(self, interaction: Interaction):
        """Progress to the next step in the workflow."""
        try:
            if self.current_step == 0:  # Weather type selected, now select sport
                sport_select = SportSelect(self)
                view = View(timeout=300)
                view.add_item(sport_select)
                view.add_item(ManualSearchButton(self))
                view.add_item(CancelButton(self))

                content = f"🏈 **Sport Selection**\n\nYou selected: **{self.selected_weather_type.title()} Weather**\n\nNow select a sport category:"
                await self.edit_message(content, view)
                self.current_step = 1

            elif self.current_step == 1:  # Sport selected, now select league
                leagues = get_leagues_by_sport(self.selected_sport)
                if not leagues:
                    await interaction.response.send_message(
                        f"❌ No leagues found for {self.selected_sport}. Please try another sport.",
                        ephemeral=True,
                    )
                    return

                league_select = LeagueSelect(self, leagues)
                view = View(timeout=300)
                view.add_item(league_select)
                view.add_item(ManualSearchButton(self))
                view.add_item(CancelButton(self))

                content = f"🏆 **League Selection**\n\nSport: **{self.selected_sport}**\nWeather Type: **{self.selected_weather_type.title()}**\n\nSelect a league:"
                await self.edit_message(content, view)
                self.current_step = 2

            elif self.current_step == 2:  # League selected, now select game
                games = await self._get_upcoming_games(
                    self.selected_sport, self.selected_league
                )
                if not games:
                    await interaction.response.send_message(
                        f"❌ No upcoming games found for {self.selected_league}. Please try another league or use Manual Search.",
                        ephemeral=True,
                    )
                    return

                game_select = GameSelect(self, games)
                view = View(timeout=300)
                view.add_item(game_select)
                view.add_item(ManualSearchButton(self))
                view.add_item(CancelButton(self))

                content = f"🎮 **Game Selection**\n\nSport: **{self.selected_sport}**\nLeague: **{self.selected_league}**\nWeather Type: **{self.selected_weather_type.title()}**\n\nSelect a game:"
                await self.edit_message(content, view)
                self.current_step = 3

        except Exception as e:
            logger.error(f"Error in weather workflow: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True,
            )

    async def _get_upcoming_games(self, sport: str, league: str) -> List[Dict]:
        """Get upcoming games for a sport and league."""
        try:
            if not GAME_SERVICE_AVAILABLE:
                logger.warning("GameService not available, returning empty games list")
                return []

            game_service = getattr(self.bot, "game_service", None)
            if not game_service:
                logger.warning("Game service not found on bot instance")
                return []

            # Map sport names to API keys
            sport_mapping = {
                "Football": "americanfootball",
                "Basketball": "basketball",
                "Baseball": "baseball",
                "Hockey": "icehockey",
                "Soccer": "football",
                "UFC": "mma",
                "Tennis": "tennis",
                "Golf": "golf",
                "Racing": "motorsport",
                "Darts": "darts",
                "Rugby": "rugby",
                "Handball": "handball",
                "Volleyball": "volleyball",
            }

            api_sport = sport_mapping.get(sport, sport.lower())

            # Get games from the service
            games = await game_service.get_upcoming_games_by_league(league, limit=25)

            # Filter games by sport if needed
            if games:
                # Add sport information to games
                for game in games:
                    game["sport"] = sport
                    game["league"] = league

            return games

        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []

    async def show_weather_info(self, interaction: Interaction):
        """Show weather information for the selected game."""
        try:
            if not self.selected_game:
                await interaction.response.send_message(
                    "❌ No game selected. Please try again.",
                    ephemeral=True,
                )
                return

            weather_service = WeatherService()

            # Extract venue information from the game
            venue_name = self.selected_game.get("venue", "")
            home_team = self.selected_game.get("home_team", "")
            away_team = self.selected_game.get("away_team", "")

            # Try to get weather for the venue
            if venue_name:
                location = venue_name
            elif home_team:
                # Try to use home team's city as fallback
                location = home_team
            else:
                await interaction.response.send_message(
                    "❌ Could not determine venue location for this game. Please use Manual Search instead.",
                    ephemeral=True,
                )
                return

            # Get weather based on selected type
            if self.selected_weather_type == "forecast":
                weather_data = await weather_service.get_forecast_weather(
                    location, days=3
                )
                if weather_data:
                    weather_message = weather_service.format_forecast_message(
                        weather_data, location
                    )
                    # Regular message
                    await interaction.response.send_message(weather_message)
                else:
                    await interaction.response.send_message(
                        f"❌ Could not find forecast weather information for **{location}**. "
                        "Please try using Manual Search with a specific city name.",
                        ephemeral=True,
                    )
            else:
                weather_data = await weather_service.get_current_weather(location)
                if weather_data:
                    weather_message = weather_service.format_weather_message(
                        weather_data, location
                    )
                    # Regular message
                    await interaction.response.send_message(weather_message)
                else:
                    await interaction.response.send_message(
                        f"❌ Could not find weather information for **{location}**. "
                        "Please try using Manual Search with a specific city name.",
                        ephemeral=True,
                    )

        except Exception as e:
            logger.error(f"Error showing weather info: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching weather information. Please try again.",
                ephemeral=True,
            )

    async def edit_message(self, content: str, view: View):
        """Edit the current message."""
        try:
            await self.original_interaction.edit_original_response(
                content=content, view=view
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")

    def get_content(self) -> str:
        """Get the current content based on the step."""
        if self.current_step == 0:
            return "🌤️ **Weather Information**\n\nPlease select the type of weather information you'd like to get:"
        elif self.current_step == 1:
            return f"🏈 **Sport Selection**\n\nYou selected: **{self.selected_weather_type.title()} Weather**\n\nNow select a sport category:"
        elif self.current_step == 2:
            return f"🏆 **League Selection**\n\nSport: **{self.selected_sport}**\nWeather Type: **{self.selected_weather_type.title()}**\n\nSelect a league:"
        elif self.current_step == 3:
            return f"🎮 **Game Selection**\n\nSport: **{self.selected_sport}**\nLeague: **{self.selected_league}**\nWeather Type: **{self.selected_weather_type.title()}**\n\nSelect a game:"
        else:
            return "Weather search in progress..."

    def stop(self):
        """Stop the workflow."""
        super().stop()


class WeatherCog(commands.Cog):
    """Cog for weather-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="weather",
        description="Get weather information for game venues with easy dropdown selection or manual search",
    )
    async def weather_command(self, interaction: Interaction):
        """Weather command with dropdown workflow."""
        try:
            view = WeatherWorkflowView(interaction, self.bot)
            await view.start_flow(interaction)

        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the weather search. Please try again.",
                ephemeral=True,
            )

    @weather_command.error
    async def weather_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors in the weather command."""
        logger.error(f"Weather command error: {error}")
        await interaction.response.send_message(
            "❌ An error occurred with the weather command. Please try again later.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    """Set up the weather cog."""
    await bot.add_cog(WeatherCog(bot))
