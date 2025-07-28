"""
Weather Command for DBSBM System

This module provides a Discord command to get weather information for game venues.
"""

import logging
from typing import Any, Dict, List, Optional

import discord
from discord import ButtonStyle, Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Button, Select, View

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

        for game in games:
            home_team = game.get("home_team_name", "Unknown")
            away_team = game.get("away_team_name", "Unknown")
            start_time = game.get("start_time", "Unknown")
            venue = game.get("venue", "Unknown Venue")

            label = f"{away_team} @ {home_team}"
            if len(label) > 100:
                label = label[:97] + "..."

            description = f"{start_time} - {venue}"
            if len(description) > 100:
                description = description[:97] + "..."

            options.append(
                SelectOption(
                    label=label, value=str(game.get("id", "")), description=description
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
        game_id = self.values[0]
        # Find the selected game
        selected_game = None
        for game in self.parent_view.games:
            if str(game.get("id", "")) == game_id:
                selected_game = game
                break

        if selected_game:
            self.parent_view.weather_details["game"] = selected_game
            self.disabled = True
            await interaction.response.defer()
            await self.parent_view.go_next(interaction)
        else:
            await interaction.response.send_message(
                "❌ Error: Selected game not found. Please try again.", ephemeral=True
            )


class CancelButton(Button):
    """Cancel button for the weather workflow."""

    def __init__(self, parent_view: "WeatherWorkflowView"):
        super().__init__(label="Cancel", style=ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "❌ Weather lookup cancelled.", ephemeral=True
        )
        self.parent_view.stop()


class WeatherWorkflowView(View):
    """Workflow view for weather lookup with dropdowns."""

    def __init__(self, original_interaction: Interaction, bot: commands.Bot):
        super().__init__(timeout=1800)  # 30 minutes timeout
        self.original_interaction = original_interaction
        self.bot = bot
        self.current_step = 0
        self.weather_details: Dict[str, Any] = {}
        self.games: List[Dict] = []
        self.weather_service = WeatherService()
        self.game_service = getattr(bot, "game_service", None)

    async def start_flow(self, interaction: Interaction):
        """Start the weather workflow."""
        try:
            self.current_step = 0
            await self.go_next(interaction)
        except Exception as e:
            logger.error(f"Error starting weather workflow: {e}")
            await interaction.followup.send(
                "❌ Error starting weather workflow. Please try again.", ephemeral=True
            )

    async def go_next(self, interaction: Interaction):
        """Advance to the next step in the weather workflow."""
        self.current_step += 1
        logger.info(f"[WEATHER WORKFLOW] Step {self.current_step}")

        if self.current_step == 1:
            # Step 1: Sport category selection
            self.clear_items()
            self.add_item(SportSelect(self))
            self.add_item(CancelButton(self))
            await self.edit_message(content=self.get_content(), view=self)
            return

        elif self.current_step == 2:
            # Step 2: League selection
            sport = self.weather_details.get("sport")
            leagues = get_leagues_by_sport(sport)
            self.clear_items()
            self.add_item(LeagueSelect(self, leagues))
            self.add_item(CancelButton(self))
            await self.edit_message(content=self.get_content(), view=self)
            return

        elif self.current_step == 3:
            # Step 3: Game selection
            sport = self.weather_details.get("sport")
            league = self.weather_details.get("league")

            # Get games from database
            games = await self._get_upcoming_games(sport, league)

            if not games:
                await interaction.followup.send(
                    f"❌ No upcoming games found for {sport} - {league}.\n"
                    f"Please try a different sport or league.",
                    ephemeral=True,
                )
                return

            self.games = games
            self.clear_items()
            self.add_item(GameSelect(self, games))
            self.add_item(CancelButton(self))
            await self.edit_message(content=self.get_content(), view=self)
            return

        elif self.current_step == 4:
            # Step 4: Show weather information
            await self.show_weather_info(interaction)
            return

    async def _get_upcoming_games(self, sport: str, league: str) -> List[Dict]:
        """Get upcoming games for the specified sport and league."""
        try:
            if not self.game_service:
                logger.error("Game service not available")
                return []

            # Map sport names to API sport keys
            sport_mapping = {
                "Football": "football",
                "Basketball": "basketball",
                "Baseball": "baseball",
                "Hockey": "hockey",
                "Soccer": "football",
                "UFC": "ufc",
                "Tennis": "tennis",
                "Golf": "golf",
                "Racing": "racing",
                "Darts": "darts",
                "Rugby": "rugby",
                "Handball": "handball",
                "Volleyball": "volleyball",
            }

            api_sport = sport_mapping.get(sport, sport.lower())

            # Get games from the database
            games = await self.game_service.get_upcoming_games_by_league(
                sport=api_sport, league_name=league, limit=25  # Get next 25 games
            )

            return games

        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []

    async def show_weather_info(self, interaction: Interaction):
        """Display weather information for the selected game."""
        try:
            game = self.weather_details.get("game")
            if not game:
                await interaction.followup.send(
                    "❌ Error: No game selected. Please try again.", ephemeral=True
                )
                return

            venue_name = game.get("venue")
            home_team = game.get("home_team_name", "Unknown")
            away_team = game.get("away_team_name", "Unknown")
            start_time = game.get("start_time", "Unknown")

            if not venue_name:
                await interaction.followup.send(
                    f"🌤️ **Weather Information**\n\n"
                    f"❌ No venue information available for this game.\n\n"
                    f"🏈 **Game:** {away_team} @ {home_team}\n"
                    f"🕐 **Start Time:** {start_time}",
                    ephemeral=True,
                )
                return

            # Get weather data
            weather_data = await self.weather_service.get_weather_for_venue(venue_name)

            if weather_data:
                weather_message = self.weather_service.format_weather_message(
                    weather_data, venue_name
                )

                # Add game info to the weather message
                game_info = f"\n\n🏈 **Game:** {away_team} @ {home_team}"
                game_info += f"\n🕐 **Start Time:** {start_time}"

                full_message = weather_message + game_info
                await interaction.followup.send(full_message, ephemeral=True)
            else:
                # Fallback message if weather data unavailable
                fallback_msg = (
                    f"🌤️ **Weather for {venue_name}**\n\n"
                    f"❌ Weather data unavailable for this venue.\n\n"
                    f"🏈 **Game:** {away_team} @ {home_team}\n"
                    f"🕐 **Start Time:** {start_time}"
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
            return "🌤️ **Weather Lookup**\n\nPlease select a sport category:"
        elif self.current_step == 2:
            sport = self.weather_details.get("sport", "Unknown")
            return (
                f"🌤️ **Weather Lookup**\n\nSport: **{sport}**\n\nPlease select a league:"
            )
        elif self.current_step == 3:
            sport = self.weather_details.get("sport", "Unknown")
            league = self.weather_details.get("league", "Unknown")
            return f"🌤️ **Weather Lookup**\n\nSport: **{sport}**\nLeague: **{league}**\n\nPlease select a game:"
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
        description="Get weather information for game venues with easy dropdown selection",
    )
    async def weather_command(self, interaction: Interaction):
        """Get weather information for game venues using dropdown selection."""
        try:
            # Check if weather service is available
            if not GAME_SERVICE_AVAILABLE:
                await interaction.response.send_message(
                    "❌ Weather service is currently unavailable. Please try again later.",
                    ephemeral=True,
                )
                return

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
