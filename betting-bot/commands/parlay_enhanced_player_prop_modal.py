"""
Enhanced Player Prop Modal for Parlays
Provides improved player search, prop type selection, and validation for parlay legs.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any

import discord
from config.prop_templates import (
    get_prop_groups_for_league,
    get_prop_templates_for_league,
    validate_prop_value,
)
from discord import app_commands, Interaction, SelectOption
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, View, Button
from discord import ButtonStyle
from services.player_search_service import PlayerSearchResult, PlayerSearchService

logger = logging.getLogger(__name__)


class ParlayEnhancedPlayerPropModal(Modal):
    """Enhanced modal for player prop betting in parlays with search and validation."""

    def __init__(
        self,
        bot,
        db_manager,
        league: str,
        leg_number: int = 1,
        view_custom_id_suffix: str = "",
        bet_details_from_view: dict = None,
    ):
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.leg_number = leg_number
        self.view_custom_id_suffix = view_custom_id_suffix
        self.view_ref = None
        self.bet_details_from_view = bet_details_from_view or {}
        
        # Initialize services
        self.player_search_service = PlayerSearchService(db_manager)
        
        # Get prop templates for this league
        self.prop_templates = get_prop_templates_for_league(league)
        self.prop_groups = get_prop_groups_for_league(league)
        
        # Set modal title
        title = f"Parlay Leg {leg_number} - Player Prop"
        super().__init__(title=title)
        
        # Setup UI components
        self._setup_ui_components()

    def _setup_ui_components(self):
        """Setup the UI components for the modal."""
        # Player search input
        self.player_search = TextInput(
            label="Search Player",
            placeholder="Type player name to search (e.g., LeBron James)",
            required=True,
            max_length=100,
            custom_id=f"parlay_player_search_{self.view_custom_id_suffix}",
            default=self.bet_details_from_view.get("player_name", ""),
        )

        # Prop type selection
        prop_types = list(self.prop_templates.keys())
        prop_placeholder = f"Available: {', '.join(prop_types[:5])}..."
        self.prop_type = TextInput(
            label="Prop Type",
            placeholder=prop_placeholder,
            required=True,
            max_length=50,
            custom_id=f"parlay_prop_type_{self.view_custom_id_suffix}",
            default=self.bet_details_from_view.get("prop_type", ""),
        )

        # Line value input
        self.line_value = TextInput(
            label="Line Value",
            placeholder="Enter the over/under line (e.g., 25.5)",
            required=True,
            max_length=10,
            custom_id=f"parlay_line_value_{self.view_custom_id_suffix}",
            default=self.bet_details_from_view.get("line_value", ""),
        )

        # Bet direction
        self.bet_direction = TextInput(
            label="Over/Under",
            placeholder="Type 'over' or 'under'",
            required=True,
            max_length=10,
            custom_id=f"parlay_bet_direction_{self.view_custom_id_suffix}",
            default=self.bet_details_from_view.get("bet_direction", ""),
        )

        # Leg odds (for parlay)
        self.leg_odds = TextInput(
            label="Leg Odds",
            placeholder="e.g., -110",
            required=True,
            max_length=10,
            custom_id=f"parlay_leg_odds_{self.view_custom_id_suffix}",
            default=self.bet_details_from_view.get("odds", ""),
        )

        # Add components to modal
        self.add_item(self.player_search)
        self.add_item(self.prop_type)
        self.add_item(self.line_value)
        self.add_item(self.bet_direction)
        self.add_item(self.leg_odds)

    async def on_submit(self, interaction: Interaction):
        """Handle modal submission with validation."""
        try:
            # Set skip increment flag so go_next does not double-increment
            if self.view_ref:
                self.view_ref._skip_increment = True

            # Validate and process inputs
            validation_result = await self._validate_inputs()

            if not validation_result["valid"]:
                await interaction.response.send_message(
                    f"❌ **Validation Error:** {validation_result['error']}",
                    ephemeral=True,
                )
                return

            # Store validated data in view reference
            bet_data = validation_result["bet_data"]
            self._store_bet_data(bet_data)

            # Generate preview image
            await self._generate_preview_image(bet_data)

            # Advance workflow
            if hasattr(self.view_ref, "current_step"):
                self.view_ref.current_step += 1
                logger.info(
                    f"[PARLAY ENHANCED MODAL] Advancing to step {self.view_ref.current_step}"
                )
                await self.view_ref.go_next(interaction)
            else:
                logger.error("View reference missing current_step attribute")
                await interaction.response.send_message(
                    "Error: Could not advance workflow", ephemeral=True
                )

        except Exception as e:
            logger.exception(f"Error in ParlayEnhancedPlayerPropModal on_submit: {e}")
            await interaction.response.send_message(
                "❌ **An error occurred.** Please try again.", ephemeral=True
            )

    async def _validate_inputs(self) -> dict:
        """Validate all modal inputs."""
        try:
            # Validate player search
            player_name = self.player_search.value.strip()
            if len(player_name) < 2:
                return {
                    "valid": False,
                    "error": "Player name must be at least 2 characters long.",
                }

            # Search for player
            search_results = await self.player_search_service.search_players(
                player_name, self.league, limit=1, min_confidence=70.0
            )

            if not search_results:
                return {
                    "valid": False,
                    "error": f'Player "{player_name}" not found. Try a different search term.',
                }

            selected_player = search_results[0]

            # Validate prop type
            prop_type = self.prop_type.value.strip().lower()
            if prop_type not in self.prop_templates:
                available_types = ", ".join(list(self.prop_templates.keys())[:10])
                return {
                    "valid": False,
                    "error": f"Invalid prop type. Available types: {available_types}",
                }

            # Validate line value
            try:
                line_value = float(self.line_value.value.strip())
                if not validate_prop_value(self.league, prop_type, line_value):
                    template = self.prop_templates[prop_type]
                    return {
                        "valid": False,
                        "error": f"Line value must be between {template.min_value} and {template.max_value} {template.unit}.",
                    }
            except ValueError:
                return {"valid": False, "error": "Line value must be a valid number."}

            # Validate bet direction
            bet_direction = self.bet_direction.value.strip().lower()
            if bet_direction not in ["over", "under"]:
                return {
                    "valid": False,
                    "error": 'Bet direction must be "over" or "under".',
                }

            # Validate leg odds
            try:
                odds = float(self.leg_odds.value.strip())
                if odds == 0:
                    return {"valid": False, "error": "Odds cannot be zero."}
            except ValueError:
                return {"valid": False, "error": "Odds must be a valid number."}

            # All validations passed
            return {
                "valid": True,
                "bet_data": {
                    "player_name": selected_player.name,
                    "player_id": selected_player.player_id,
                    "team_name": selected_player.team_name,
                    "prop_type": prop_type,
                    "line_value": line_value,
                    "bet_direction": bet_direction,
                    "odds": odds,
                    "league": self.league,
                    "line": f"{bet_direction.title()} {line_value}",
                    "odds_str": str(odds),
                },
            }

        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            return {"valid": False, "error": "An error occurred during validation."}

    def _store_bet_data(self, bet_data: dict):
        """Store the validated bet data in the view reference."""
        if not self.view_ref:
            return

        # Store in current leg construction details
        self.view_ref.current_leg_construction_details.update({
            "player_name": bet_data["player_name"],
            "player_id": bet_data["player_id"],
            "team_name": bet_data["team_name"],
            "prop_type": bet_data["prop_type"],
            "line_value": bet_data["line_value"],
            "bet_direction": bet_data["bet_direction"],
            "odds": bet_data["odds"],
            "odds_str": bet_data["odds_str"],
            "line": bet_data["line"],
            "league": bet_data["league"],
            "bet_type": "player_prop",
            "home_team_name": bet_data["team_name"],
            "away_team_name": bet_data["player_name"],  # For player image display
            "selected_team": bet_data["team_name"],
        })

    async def _generate_preview_image(self, bet_data: dict):
        """Generate preview image for the parlay leg."""
        try:
            from utils.parlay_bet_image_generator import ParlayBetImageGenerator

            generator = ParlayBetImageGenerator(
                guild_id=self.view_ref.original_interaction.guild_id
            )

            # Prepare leg data for preview
            leg_data = {
                "bet_type": "player_prop",
                "league": bet_data["league"],
                "home_team": bet_data["team_name"],
                "away_team": bet_data["player_name"],
                "selected_team": bet_data["team_name"],
                "line": bet_data["line"],
                "odds": bet_data["odds"],
                "player_name": bet_data["player_name"],
                "prop_type": bet_data["prop_type"],
            }

            # Generate preview with just this leg
            preview_legs = [leg_data]
            image_bytes = generator.generate_image(
                legs=preview_legs,
                output_path=None,
                total_odds=bet_data["odds"],  # Use leg odds for preview
                units=1.0,
                bet_id="PREVIEW",
                bet_datetime=None,
                finalized=False,
                units_display_mode="auto",
                display_as_risk=False,
            )

            if image_bytes:
                self.view_ref.preview_image_bytes = image_bytes
            else:
                self.view_ref.preview_image_bytes = None

        except Exception as e:
            logger.error(f"Error generating parlay preview image: {e}")
            self.view_ref.preview_image_bytes = None


class ParlayPlayerSearchView(View):
    """View for player search in parlay player props."""
    
    def __init__(self, bot, db_manager, league: str, leg_number: int = 1):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.leg_number = leg_number
        self.player_search_service = PlayerSearchService(db_manager)
        self.search_results = []

    @discord.ui.button(label="Search Players", style=ButtonStyle.primary)
    async def search_players(self, interaction: Interaction, button: discord.ui.Button):
        """Search for players based on input."""
        try:
            # This would be triggered by a text input or search field
            # For now, we'll show available players
            search_results = await self.player_search_service.get_popular_players(
                self.league, limit=10
            )
            
            if not search_results:
                await interaction.response.send_message(
                    f"No players found for {self.league}. Please try a different league.",
                    ephemeral=True,
                )
                return

            # Create player selection options
            options = []
            for player in search_results:
                options.append(
                    SelectOption(
                        label=f"{player.name} ({player.team_name})",
                        value=player.player_id,
                        description=f"{player.team_name} - {player.position or 'N/A'}"
                    )
                )

            # Create player selection dropdown
            player_select = Select(
                placeholder="Select a player...",
                options=options,
                min_values=1,
                max_values=1,
            )

            async def player_callback(interaction: Interaction):
                selected_player_id = player_select.values[0]
                selected_player = next(
                    (p for p in search_results if p.player_id == selected_player_id),
                    None
                )
                
                if selected_player:
                    # Store selected player and show prop type selection
                    await self._show_prop_type_selection(interaction, selected_player)
                else:
                    await interaction.response.send_message(
                        "Error: Selected player not found.", ephemeral=True
                    )

            player_select.callback = player_callback
            
            # Create new view with player selection
            view = View(timeout=300)
            view.add_item(player_select)
            view.add_item(Button(label="Cancel", style=ButtonStyle.secondary))
            
            await interaction.response.edit_message(
                content=f"**Select a player for Leg {self.leg_number}:**",
                view=view
            )

        except Exception as e:
            logger.error(f"Error in player search: {e}")
            await interaction.response.send_message(
                "❌ Error searching for players. Please try again.", ephemeral=True,
            )

    async def _show_prop_type_selection(self, interaction: Interaction, player: PlayerSearchResult):
        """Show prop type selection after player is chosen."""
        try:
            # Get prop templates for this league
            prop_templates = get_prop_templates_for_league(self.league)
            
            if not prop_templates:
                await interaction.response.send_message(
                    f"No prop types available for {self.league}.", ephemeral=True
                )
                return

            # Create prop type options
            options = []
            for prop_type, template in prop_templates.items():
                options.append(
                    SelectOption(
                        label=prop_type.title(),
                        value=prop_type,
                        description=f"{template.min_value}-{template.max_value} {template.unit}"
                    )
                )

            # Create prop type selection dropdown
            prop_select = Select(
                placeholder="Select prop type...",
                options=options,
                min_values=1,
                max_values=1,
            )

            async def prop_callback(interaction: Interaction):
                selected_prop_type = prop_select.values[0]
                
                # Show the enhanced modal with pre-filled data
                modal = ParlayEnhancedPlayerPropModal(
                    self.bot,
                    self.db_manager,
                    self.league,
                    self.leg_number
                )
                
                # Pre-fill player name
                modal.player_search.default = player.name
                
                await interaction.response.send_modal(modal)

            prop_select.callback = prop_callback
            
            # Create new view with prop type selection
            view = View(timeout=300)
            view.add_item(prop_select)
            view.add_item(Button(label="Back", style=ButtonStyle.secondary))
            
            await interaction.response.edit_message(
                content=f"**Select prop type for {player.name}:**",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing prop type selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing prop types. Please try again.", ephemeral=True
            )


async def setup_parlay_enhanced_player_prop(
    bot, db_manager, league: str, leg_number: int = 1
):
    """Setup enhanced player prop functionality for parlays."""
    try:
        # Create the search view
        view = ParlayPlayerSearchView(bot, db_manager, league, leg_number)
        
        # Return the view for use in parlay workflow
        return view
        
    except Exception as e:
        logger.error(f"Error setting up parlay enhanced player prop: {e}")
        return None 