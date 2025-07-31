"""UI components for parlay betting functionality."""

import logging
from typing import Any, Dict, List, Optional

import discord
from discord import ButtonStyle, Interaction, SelectOption, TextChannel
from discord.ui import Button, Select, View

from bot.data.game_utils import get_normalized_games_for_dropdown

from .constants import DEFAULT_LEGS_PER_PAGE, LINE_TYPES
from .utils import get_leagues_for_sport

logger = logging.getLogger(__name__)


class SportSelect(Select):
    """Sport selection dropdown."""

    def __init__(self, parent_view: "ParlayBetWorkflowView", sports: List[str]):
        options = [SelectOption(label=sport, value=sport) for sport in sports]
        super().__init__(
            placeholder="Select a sport...", options=options, custom_id="sport_select"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle sport selection."""
        self.parent_view.selected_sport = self.values[0]
        await self.parent_view.go_next(interaction)


class LeagueSelect(Select):
    """League selection dropdown with pagination."""

    def __init__(
        self,
        parent_view: "ParlayBetWorkflowView",
        leagues: List[str],
        page: int = 0,
        per_page: int = DEFAULT_LEGS_PER_PAGE,
    ):
        self.parent_view = parent_view
        self.all_leagues = leagues
        self.current_page = page
        self.per_page = per_page

        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_leagues = leagues[start_idx:end_idx]

        options = [SelectOption(label=league, value=league) for league in page_leagues]

        # Add navigation options if needed
        if page > 0:
            options.insert(0, SelectOption(label="← Previous", value="prev"))
        if end_idx < len(leagues):
            options.append(SelectOption(label="Next →", value="next"))

        super().__init__(
            placeholder=f"Select a league... (Page {page + 1})",
            options=options,
            custom_id="league_select",
        )

    async def callback(self, interaction: Interaction):
        """Handle league selection."""
        selected = self.values[0]

        if selected == "prev":
            await self.parent_view.update_league_page(
                interaction, self.current_page - 1
            )
        elif selected == "next":
            await self.parent_view.update_league_page(
                interaction, self.current_page + 1
            )
        else:
            self.parent_view.selected_league = selected
            await self.parent_view.go_next(interaction)


class LineTypeSelect(Select):
    """Line type selection dropdown."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        options = [
            SelectOption(label=line_type, value=line_type) for line_type in LINE_TYPES
        ]
        super().__init__(
            placeholder="Select line type...",
            options=options,
            custom_id="line_type_select",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle line type selection."""
        self.parent_view.selected_line_type = self.values[0]
        await self.parent_view.go_next(interaction)


class ParlayGameSelect(Select):
    """Game selection dropdown for parlay legs."""

    def __init__(self, parent_view: View, games: List[Dict]):
        self.parent_view = parent_view
        self.games = games

        options = []

        # Add manual entry as the first option
        options.append(
            SelectOption(
                label="📝 Manual Entry",
                value="manual",
                description="Enter game details manually",
            )
        )

        for game in games:
            home_team = game.get("home_team", "Unknown")
            away_team = game.get("away_team", "Unknown")
            game_time = game.get("game_time", "Unknown")

            label = f"{away_team} @ {home_team}"
            if game_time != "Unknown":
                label += f" ({game_time})"

            options.append(
                SelectOption(
                    label=label[:100],  # Discord limit
                    value=str(game.get("id", "")),
                    description=f"{home_team} vs {away_team}",
                )
            )

        super().__init__(
            placeholder="Select a game or Manual Entry...",
            options=options,
            custom_id="game_select",
        )

    async def callback(self, interaction: Interaction):
        """Handle game selection."""
        selected_value = self.values[0]

        if selected_value == "manual":
            # Handle manual entry
            self.parent_view.selected_game = {
                "id": "manual",
                "home_team": "Manual Entry",
                "away_team": "Manual Entry",
                "is_manual": True,
            }
            await self.parent_view.go_next(interaction)
            return

        selected_game = next(
            (game for game in self.games if str(game.get("id")) == selected_value),
            None,
        )

        if selected_game:
            self.parent_view.selected_game = selected_game
            await self.parent_view.go_next(interaction)
        else:
            await interaction.response.send_message(
                "Error: Selected game not found.", ephemeral=True
            )


class UnitsSelect(Select):
    """Units selection dropdown."""

    def __init__(self, parent_view: "ParlayBetWorkflowView", units_display_mode="auto"):
        self.parent_view = parent_view
        self.units_display_mode = units_display_mode

        # Generate units options based on display mode
        if units_display_mode == "auto":
            options = [
                SelectOption(label="0.5 units", value="0.5"),
                SelectOption(label="1 unit", value="1.0"),
                SelectOption(label="2 units", value="2.0"),
                SelectOption(label="3 units", value="3.0"),
                SelectOption(label="5 units", value="5.0"),
                SelectOption(label="10 units", value="10.0"),
            ]
        else:
            # Manual mode - more granular options
            options = [
                SelectOption(label=f"{i/2} units", value=str(i / 2))
                for i in range(1, 21)  # 0.5 to 10 units
            ]

        super().__init__(
            placeholder="Select units...", options=options, custom_id="units_select"
        )

    async def callback(self, interaction: Interaction):
        """Handle units selection."""
        units = float(self.values[0])
        await self.parent_view._handle_units_selection(interaction, units)


class ChannelSelect(Select):
    """Channel selection dropdown."""

    def __init__(
        self, parent_view: "ParlayBetWorkflowView", channels: List[TextChannel]
    ):
        self.parent_view = parent_view

        options = []
        for channel in channels:
            options.append(
                SelectOption(
                    label=f"#{channel.name}",
                    value=str(channel.id),
                    description=f"Channel: {channel.name}",
                )
            )

        super().__init__(
            placeholder="Select channel to post bet...",
            options=options,
            custom_id="channel_select",
        )

    async def callback(self, interaction: Interaction):
        """Handle channel selection."""
        channel_id = int(self.values[0])
        self.parent_view.selected_channel_id = channel_id
        await self.parent_view.go_next(interaction)


class TeamSelect(Select):
    """Team selection dropdown for game outcomes."""

    def __init__(self, parent_view: View, home_team: str, away_team: str):
        self.parent_view = parent_view

        options = [
            SelectOption(label=f"{away_team} (Away)", value=f"away_{away_team}"),
            SelectOption(label=f"{home_team} (Home)", value=f"home_{home_team}"),
        ]

        super().__init__(
            placeholder="Select team...", options=options, custom_id="team_select"
        )

    async def callback(self, interaction: Interaction):
        """Handle team selection."""
        selected = self.values[0]
        team_type, team_name = selected.split("_", 1)

        self.parent_view.selected_team = team_name
        self.parent_view.selected_team_type = team_type
        await self.parent_view.go_next(interaction)


# Button components
class ConfirmButton(Button):
    """Generic confirm button."""

    def __init__(self, parent_view: "ParlayBetWorkflowView", label: str = "Confirm"):
        super().__init__(
            label=label, style=ButtonStyle.green, custom_id="confirm_button"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle confirmation."""
        await self.parent_view.go_next(interaction)


class CancelButton(Button):
    """Cancel button."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            label="Cancel", style=ButtonStyle.red, custom_id="cancel_button"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle cancellation."""
        await interaction.response.send_message(
            "Parlay bet creation cancelled.", ephemeral=True
        )
        await self.parent_view.cleanup()


class AddAnotherLegButton(Button):
    """Button to add another leg to the parlay."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            label="Add Another Leg",
            style=ButtonStyle.primary,
            custom_id="add_leg_button",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle adding another leg."""
        # Reset to start of flow for new leg
        self.parent_view.current_step = "sport_selection"
        await self.parent_view.start_flow(interaction)


class FinalizeParlayButton(Button):
    """Button to finalize the parlay."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            label="Finalize Parlay",
            style=ButtonStyle.green,
            custom_id="finalize_parlay_button",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle parlay finalization."""
        # Proceed to odds and units selection
        await self.parent_view.go_next(interaction)


class FinalConfirmButton(Button):
    """Final confirmation button for submitting the bet."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            label="Submit Bet",
            style=ButtonStyle.green,
            custom_id="final_confirm_button",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        """Handle final confirmation."""
        await self.parent_view.submit_bet(interaction)
