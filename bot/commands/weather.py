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

        self.add_item(self.city_input)
        self.add_item(self.state_input)

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            city = self.city_input.value.strip()
            state = self.state_input.value.strip() if self.state_input.value else ""

            # Combine city and state for location
            location = f"{city}, {state}" if state else city

            # Get weather service
            weather_service = WeatherService()

            # Get weather for the location
            weather_data = await weather_service.get_current_weather(location)

            if weather_data:
                # Format the weather message
                weather_message = weather_service.format_weather_message(
                    weather_data, location
                )
                await interaction.response.send_message(weather_message, ephemeral=True)
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


class SportSelect(Select):
    """Sport category selection dropdown."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        self.parent_view = parent_view
        sports = get_all_sport_categories()
        options = [SelectOption(label=sport, value=sport) for sport in sports]
        super().__init__(
            placeholder="Select Sport Category...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"weather_sport_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        self.parent_view.weather_details["sport"] = value
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class LeagueSelect(Select):
    """League selection dropdown."""

    def __init__(self, parent_view: "WeatherWorkflowView", leagues: List[str]):
        self.parent_view = parent_view
        options = [SelectOption(label=league, value=league) for league in leagues]
        super().__init__(
            placeholder="Select League...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"weather_league_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        self.parent_view.weather_details["league"] = value
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class GameSelect(Select):
    """Game selection dropdown."""

    def __init__(self, parent_view: "WeatherWorkflowView", games: List[Dict]):
        self.parent_view = parent_view
        options = []

        for game in games[:25]:  # Limit to 25 games (Discord limit)
            home_team = game.get("home_team", "Unknown")
            away_team = game.get("away_team", "Unknown")
            game_time = game.get("game_time", "Unknown")

            # Format the label to fit Discord's 100 character limit
            label = f"{home_team} vs {away_team}"
            if len(label) > 100:
                label = f"{home_team[:45]} vs {away_team[:45]}"

            value = str(game.get("id", ""))
            description = (
                f"Game Time: {game_time}" if game_time != "Unknown" else "Time TBD"
            )

            options.append(
                SelectOption(
                    label=label,
                    value=value,
                    description=description[:100],  # Discord description limit
                )
            )

        super().__init__(
            placeholder="Select Game...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"weather_game_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        selected_game_id = self.values[0]
        self.parent_view.weather_details["game_id"] = selected_game_id

        # Find the selected game
        selected_game = None
        for game in self.parent_view.games:
            if str(game.get("id", "")) == selected_game_id:
                selected_game = game
                break

        if selected_game:
            self.parent_view.weather_details["selected_game"] = selected_game
            self.disabled = True
            await interaction.response.defer()
            await self.parent_view.show_weather_info(interaction)
        else:
            await interaction.response.send_message(
                "❌ Selected game not found. Please try again.", ephemeral=True
            )


class CancelButton(Button):
    """Cancel button for the workflow."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        super().__init__(
            label="Cancel",
            style=ButtonStyle.danger,
            custom_id=f"weather_cancel_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "❌ Weather lookup cancelled.", ephemeral=True
        )
        self.parent_view.stop()


class WeatherWorkflowView(View):
    """View for managing the weather workflow."""

    def __init__(self, original_interaction: Interaction, bot: commands.Bot):
        super().__init__(timeout=300)  # 5 minute timeout
        self.original_interaction = original_interaction
        self.bot = bot
        self.current_step = 1
        self.weather_details = {}
        self.games = []

        # Add components
        self.add_item(SportSelect(self))
        self.add_item(ManualSearchButton(self))
        self.add_item(CancelButton(self))

    async def start_flow(self, interaction: Interaction):
        """Start the weather workflow."""
        try:
            content = self.get_content()
            await interaction.response.send_message(content, view=self, ephemeral=True)
        except Exception as e:
            logger.error(f"Error starting weather flow: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the weather lookup. Please try again.",
                ephemeral=True,
            )

    async def go_next(self, interaction: Interaction):
        """Progress to the next step in the workflow."""
        try:
            if self.current_step == 1:
                # Step 1: Sport selected, show leagues
                sport = self.weather_details.get("sport")
                leagues = get_leagues_by_sport(sport)

                if not leagues:
                    await interaction.followup.send(
                        f"❌ No leagues found for {sport}. Please try a different sport.",
                        ephemeral=True,
                    )
                    return

                # Clear previous components and add new ones
                self.clear_items()
                self.add_item(LeagueSelect(self, leagues))
                self.add_item(ManualSearchButton(self))
                self.add_item(CancelButton(self))

                self.current_step = 2
                content = self.get_content()
                await self.edit_message(content, self)

            elif self.current_step == 2:
                # Step 2: League selected, show games
                sport = self.weather_details.get("sport")
                league = self.weather_details.get("league")

                # Get upcoming games
                self.games = await self._get_upcoming_games(sport, league)

                if not self.games:
                    await interaction.followup.send(
                        f"❌ No upcoming games found for {sport} - {league}. "
                        "Please try a different league or use Manual Search.",
                        ephemeral=True,
                    )
                    return

                # Clear previous components and add new ones
                self.clear_items()
                self.add_item(GameSelect(self, self.games))
                self.add_item(ManualSearchButton(self))
                self.add_item(CancelButton(self))

                self.current_step = 3
                content = self.get_content()
                await self.edit_message(content, self)

        except Exception as e:
            logger.error(f"Error in go_next: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your selection. Please try again.",
                ephemeral=True,
            )

    async def _get_upcoming_games(self, sport: str, league: str) -> List[Dict]:
        """Get upcoming games for the selected sport and league."""
        try:
            if not GAME_SERVICE_AVAILABLE or not GameService:
                return []

            # Map sport names to API keys
            sport_mapping = {
                "Football": "american-football",
                "Basketball": "basketball",
                "Baseball": "baseball",
                "Hockey": "ice-hockey",
                "Soccer": "football",
                "UFC": "mma",
                "Tennis": "tennis",
                "Golf": "golf",
                "Racing": "formula-1",
                "Darts": "darts",
                "Rugby": "rugby",
                "Handball": "handball",
                "Volleyball": "volleyball",
            }

            api_sport = sport_mapping.get(sport, sport.lower())

            # Get games from the database
            game_service = getattr(self.bot, "game_service", None)
            if game_service and hasattr(game_service, "get_upcoming_games_by_league"):
                games = await game_service.get_upcoming_games_by_league(
                    league, limit=25
                )
                return games or []

            return []

        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []

    async def show_weather_info(self, interaction: Interaction):
        """Show weather information for the selected game."""
        try:
            selected_game = self.weather_details.get("selected_game")
            if not selected_game:
                await interaction.followup.send(
                    "❌ No game selected. Please try again.", ephemeral=True
                )
                return

            # Get venue information
            venue = selected_game.get("venue", "")
            home_team = selected_game.get("home_team", "")
            away_team = selected_game.get("away_team", "")
            game_time = selected_game.get("game_time", "")

            # Try to get weather for the venue
            weather_service = WeatherService()
            weather_data = None

            if venue:
                weather_data = await weather_service.get_weather_for_venue(venue)

            # If no venue or weather data, try using home team location
            if not weather_data and home_team:
                # You could implement team location mapping here
                weather_data = await weather_service.get_current_weather(home_team)

            if weather_data:
                # Format weather message
                weather_message = weather_service.format_weather_message(
                    weather_data, venue or home_team
                )

                # Add game information
                game_info = (
                    f"🏈 **Game Information**\n"
                    f"**{home_team}** vs **{away_team}**\n"
                    f"🕐 **Start Time:** {game_time}\n\n"
                )

                full_message = game_info + weather_message
                await interaction.followup.send(full_message, ephemeral=True)
            else:
                # Fallback message
                fallback_msg = (
                    f"🏈 **Game Information**\n"
                    f"**{home_team}** vs **{away_team}**\n"
                    f"🕐 **Start Time:** {game_time}\n\n"
                    f"❌ Weather information not available for this venue. "
                    f"Try using Manual Search for the specific location."
                )
                await interaction.followup.send(fallback_msg, ephemeral=True)

        except Exception as e:
            logger.error(f"Error showing weather info: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching weather information. Please try again later.",
                ephemeral=True,
            )

    async def edit_message(self, content: str, view: View):
        """Edit the original message with new content and view."""
        try:
            if self.original_interaction.response.is_done():
                await self.original_interaction.edit_original_response(
                    content=content, view=view
                )
            else:
                await self.original_interaction.response.send_message(
                    content=content, view=view, ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error editing message: {e}")

    def get_content(self) -> str:
        """Get content for the current step."""
        if self.current_step == 1:
            return "🌤️ **Weather Lookup**\n\nPlease select a sport category or use Manual Search:"
        elif self.current_step == 2:
            sport = self.weather_details.get("sport", "Unknown")
            return f"🌤️ **Weather Lookup**\n\nSport: **{sport}**\n\nPlease select a league or use Manual Search:"
        elif self.current_step == 3:
            sport = self.weather_details.get("sport", "Unknown")
            league = self.weather_details.get("league", "Unknown")
            return f"🌤️ **Weather Lookup**\n\nSport: **{sport}**\nLeague: **{league}**\n\nPlease select a game or use Manual Search:"
        else:
            return "🌤️ **Weather Lookup**\n\nProcessing..."

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
        """Get weather information for game venues using dropdown selection or manual search."""
        try:
            # Create and start the weather workflow
            view = WeatherWorkflowView(interaction, self.bot)
            await view.start_flow(interaction)

        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the weather command. Please try again later.",
                ephemeral=True,
            )

    @weather_command.error
    async def weather_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for the weather command."""
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.followup.send(
                "❌ An error occurred while processing the weather command. "
                "Please check your input and try again.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ An unexpected error occurred. Please try again later.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """Set up the weather cog."""
    await bot.add_cog(WeatherCog(bot))
