"""Modal components for parlay betting functionality."""

import logging
from typing import Any, Dict, Optional

import discord
from discord import Interaction, TextInput, TextStyle
from discord.ui import Button, Modal, View

from .utils import validate_bet_details

logger = logging.getLogger(__name__)


class BetDetailsModal(Modal):
    """Modal for entering bet details."""

    def __init__(
        self,
        line_type: str,
        is_manual: bool = False,
        leg_number: int = 1,
        view_custom_id_suffix: str = "",
        bet_details_from_view: dict = None,
    ):
        self.line_type = line_type
        self.is_manual = is_manual
        self.leg_number = leg_number
        self.view_custom_id_suffix = view_custom_id_suffix
        self.bet_details_from_view = bet_details_from_view or {}

        title = f"Leg {leg_number} Details - {line_type}"
        if is_manual:
            title += " (Manual Entry)"

        super().__init__(title=title)

        # Create text inputs based on line type
        self._create_text_inputs()

    def _create_text_inputs(self):
        """Create appropriate text inputs based on line type."""
        if self.line_type == "Moneyline":
            self.selection = TextInput(
                label="Team Selection",
                placeholder="Enter team name (e.g., Lakers, Celtics)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., +150, -110)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Spread":
            self.selection = TextInput(
                label="Team Selection",
                placeholder="Enter team name and spread (e.g., Lakers -5.5)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., -110)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Total":
            self.selection = TextInput(
                label="Total Selection",
                placeholder="Enter over/under and line (e.g., Over 220.5)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., -110)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Player Props":
            self.selection = TextInput(
                label="Player Prop Selection",
                placeholder="Enter player and prop (e.g., LeBron James Over 25.5 points)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., -110)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Team Props":
            self.selection = TextInput(
                label="Team Prop Selection",
                placeholder="Enter team and prop (e.g., Lakers Over 110.5 points)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., -110)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Futures":
            self.selection = TextInput(
                label="Futures Selection",
                placeholder="Enter futures bet (e.g., Lakers to win NBA Championship)",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., +500)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        elif self.line_type == "Live Betting":
            self.selection = TextInput(
                label="Live Bet Selection",
                placeholder="Enter live bet selection",
                style=TextStyle.short,
                required=True,
                max_length=100,
                value=self.bet_details_from_view.get("selection", ""),
            )
            self.odds = TextInput(
                label="Odds",
                placeholder="Enter odds (e.g., +150)",
                style=TextStyle.short,
                required=True,
                max_length=10,
                value=self.bet_details_from_view.get("odds", ""),
            )

        # Add notes field for all types
        self.notes = TextInput(
            label="Notes (Optional)",
            placeholder="Add any additional notes about this bet",
            style=TextStyle.paragraph,
            required=False,
            max_length=500,
            value=self.bet_details_from_view.get("notes", ""),
        )

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            # Extract data from inputs
            leg_details = {
                "line_type": self.line_type,
                "selection": self.selection.value.strip(),
                "odds": self.odds.value.strip(),
                "notes": self.notes.value.strip() if self.notes.value else "",
                "is_manual": self.is_manual,
                "leg_number": self.leg_number,
            }

            # Validate the bet details
            if not validate_bet_details(leg_details):
                await interaction.response.send_message(
                    "❌ Invalid bet details. Please check your input and try again.",
                    ephemeral=True,
                )
                return

            # Store the leg details in the parent view
            if hasattr(interaction.data, "custom_id"):
                # This is a complex workflow - we need to find the parent view
                # For now, we'll store it in a way that the parent can access
                interaction.leg_details = leg_details

                await interaction.response.send_message(
                    f"✅ Leg {self.leg_number} details saved successfully!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ Error: Could not save bet details.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in BetDetailsModal.on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while saving bet details.", ephemeral=True
            )


class TotalOddsModal(Modal):
    """Modal for entering total parlay odds."""

    def __init__(self, view_custom_id_suffix: str):
        self.view_custom_id_suffix = view_custom_id_suffix

        super().__init__(title="Enter Total Parlay Odds")

        self.total_odds = TextInput(
            label="Total Odds",
            placeholder="Enter the total parlay odds (e.g., +500, -110)",
            style=TextStyle.short,
            required=True,
            max_length=10,
        )

        self.notes = TextInput(
            label="Parlay Notes (Optional)",
            placeholder="Add any notes about this parlay",
            style=TextStyle.paragraph,
            required=False,
            max_length=500,
        )

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            total_odds = self.total_odds.value.strip()
            notes = self.notes.value.strip() if self.notes.value else ""

            # Validate odds format
            try:
                odds_value = float(total_odds.replace("+", "").replace("-", ""))
                if odds_value < -1000 or odds_value > 10000:
                    await interaction.response.send_message(
                        "❌ Odds out of reasonable range. Please enter valid odds.",
                        ephemeral=True,
                    )
                    return
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid odds format. Please enter valid odds (e.g., +500, -110).",
                    ephemeral=True,
                )
                return

            # Store the total odds
            interaction.total_odds = float(total_odds)
            interaction.parlay_notes = notes

            await interaction.response.send_message(
                f"✅ Total odds set to {total_odds}", ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in TotalOddsModal.on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while saving total odds.", ephemeral=True
            )


class OddsModal(Modal):
    """Modal for entering odds for a specific leg."""

    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        self.parent_view = parent_view

        super().__init__(title="Enter Odds")

        self.odds = TextInput(
            label="Odds",
            placeholder="Enter odds (e.g., +150, -110)",
            style=TextStyle.short,
            required=True,
            max_length=10,
        )

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            odds_value = self.odds.value.strip()

            # Validate odds format
            try:
                odds_float = float(odds_value.replace("+", "").replace("-", ""))
                if odds_float < -1000 or odds_float > 10000:
                    await interaction.response.send_message(
                        "❌ Odds out of reasonable range. Please enter valid odds.",
                        ephemeral=True,
                    )
                    return
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid odds format. Please enter valid odds (e.g., +150, -110).",
                    ephemeral=True,
                )
                return

            # Store the odds in the parent view
            self.parent_view.current_leg_odds = float(odds_value)

            await interaction.response.send_message(
                f"✅ Odds set to {odds_value}", ephemeral=True
            )

            # Continue to next step
            await self.parent_view.go_next(interaction)

        except Exception as e:
            logger.error(f"Error in OddsModal.on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while saving odds.", ephemeral=True
            )


class ManualEntryModalButton(Button):
    """Button to open manual entry modal."""

    def __init__(self, modal):
        super().__init__(
            label="Manual Entry",
            style=discord.ButtonStyle.secondary,
            custom_id="manual_entry_button",
        )
        self.modal = modal

    async def callback(self, interaction: Interaction):
        """Handle manual entry button click."""
        await interaction.response.send_modal(self.modal)
