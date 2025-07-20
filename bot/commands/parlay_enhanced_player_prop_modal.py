"""
Enhanced Player Prop Modal for Parlays
Provides improved player search, prop type selection, and validation for parlay legs.

VERSION: 1.1.0 - Fixed PlayerPropSearchView attribute error
"""

import logging

import discord
from config.prop_templates import (
    get_prop_groups_for_league,
    get_prop_templates_for_league,
    validate_prop_value,
)
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Modal, Select, TextInput, View
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

        # Set modal title with league-specific terminology
        title = self._get_league_specific_title(league, leg_number)
        super().__init__(title=title)

        # Setup UI components
        self._setup_ui_components()

    def _get_league_specific_title(self, league: str, leg_number: int) -> str:
        """Get league-specific modal title."""
        league_titles = {
            "Formula-1": f"🏎️ Leg {leg_number} - Driver Prop",
            "PGA": f"⛳ Leg {leg_number} - Golfer Prop",
            "LPGA": f"⛳ Leg {leg_number} - Golfer Prop",
            "EuropeanTour": f"⛳ Leg {leg_number} - Golfer Prop",
            "LIVGolf": f"⛳ Leg {leg_number} - Golfer Prop",
            "ATP": f"🎾 Leg {leg_number} - Player Prop",
            "WTA": f"🎾 Leg {leg_number} - Player Prop",
            "Tennis": f"🎾 Leg {leg_number} - Player Prop",
            "MMA": f"🥊 Leg {leg_number} - Fighter Prop",
            "Bellator": f"🥊 Leg {leg_number} - Fighter Prop",
            "PDC": f"🎯 Leg {leg_number} - Darts Player Prop",
            "BDO": f"🎯 Leg {leg_number} - Darts Player Prop",
            "WDF": f"🎯 Leg {leg_number} - Darts Player Prop",
            "NBA": f"🏀 Leg {leg_number} - Player Prop",
            "WNBA": f"🏀 Leg {leg_number} - Player Prop",
            "NFL": f"🏈 Leg {leg_number} - Player Prop",
            "MLB": f"⚾ Leg {leg_number} - Player Prop",
            "NHL": f"🏒 Leg {leg_number} - Player Prop",
            "Soccer": f"⚽ Leg {leg_number} - Player Prop",
            "EPL": f"⚽ Leg {leg_number} - Player Prop",
            "LaLiga": f"⚽ Leg {leg_number} - Player Prop",
            "Bundesliga": f"⚽ Leg {leg_number} - Player Prop",
            "SerieA": f"⚽ Leg {leg_number} - Player Prop",
            "Ligue1": f"⚽ Leg {leg_number} - Player Prop",
            "ChampionsLeague": f"⚽ Leg {leg_number} - Player Prop",
            "EuropaLeague": f"⚽ Leg {leg_number} - Player Prop",
            "WorldCup": f"⚽ Leg {leg_number} - Player Prop",
        }
        return league_titles.get(league, f"🏀 Leg {leg_number} - Player Prop")

    def _get_participant_label(self, league: str) -> str:
        """Get league-specific participant label."""
        labels = {
            "Formula-1": "Driver",
            "PGA": "Golfer",
            "LPGA": "Golfer",
            "EuropeanTour": "Golfer",
            "LIVGolf": "Golfer",
            "ATP": "Player",
            "WTA": "Player",
            "Tennis": "Player",
            "MMA": "Fighter",
            "Bellator": "Fighter",
            "PDC": "Darts Player",
            "BDO": "Darts Player",
            "WDF": "Darts Player",
            "NBA": "Player",
            "WNBA": "Player",
            "NFL": "Player",
            "MLB": "Player",
            "NHL": "Player",
            "Soccer": "Player",
            "EPL": "Player",
            "LaLiga": "Player",
            "Bundesliga": "Player",
            "SerieA": "Player",
            "Ligue1": "Player",
            "ChampionsLeague": "Player",
            "EuropaLeague": "Player",
            "WorldCup": "Player",
        }
        return labels.get(league, "Player")

    def _get_participant_placeholder(self, league: str) -> str:
        """Get league-specific participant placeholder."""
        placeholders = {
            "Formula-1": "Search for driver (e.g., Max Verstappen, Lewis Hamilton)",
            "PGA": "Search for golfer (e.g., Scottie Scheffler, Rory McIlroy)",
            "LPGA": "Search for golfer (e.g., Nelly Korda, Lydia Ko)",
            "EuropeanTour": "Search for golfer (e.g., Jon Rahm, Viktor Hovland)",
            "LIVGolf": "Search for golfer (e.g., Dustin Johnson, Phil Mickelson)",
            "ATP": "Search for player (e.g., Novak Djokovic, Rafael Nadal)",
            "WTA": "Search for player (e.g., Iga Swiatek, Aryna Sabalenka)",
            "Tennis": "Search for player (e.g., Novak Djokovic, Iga Swiatek)",
            "MMA": "Search for fighter (e.g., Jon Jones, Francis Ngannou)",
            "Bellator": "Search for fighter (e.g., Patricio Pitbull, Cris Cyborg)",
            "PDC": "Search for darts player (e.g., Michael van Gerwen, Peter Wright)",
            "BDO": "Search for darts player (e.g., Michael van Gerwen, Peter Wright)",
            "WDF": "Search for darts player (e.g., Michael van Gerwen, Peter Wright)",
            "NBA": "Search for player (e.g., LeBron James, Stephen Curry)",
            "WNBA": "Search for player (e.g., Breanna Stewart, A'ja Wilson)",
            "NFL": "Search for player (e.g., Patrick Mahomes, Josh Allen)",
            "MLB": "Search for player (e.g., Aaron Judge, Shohei Ohtani)",
            "NHL": "Search for player (e.g., Connor McDavid, Nathan MacKinnon)",
            "Soccer": "Search for player (e.g., Lionel Messi, Cristiano Ronaldo)",
            "EPL": "Search for player (e.g., Erling Haaland, Mohamed Salah)",
            "LaLiga": "Search for player (e.g., Vinicius Jr, Robert Lewandowski)",
            "Bundesliga": "Search for player (e.g., Harry Kane, Jamal Musiala)",
            "SerieA": "Search for player (e.g., Lautaro Martinez, Victor Osimhen)",
            "Ligue1": "Search for player (e.g., Kylian Mbappé, Jonathan David)",
            "ChampionsLeague": "Search for player (e.g., Erling Haaland, Kylian Mbappé)",
            "EuropaLeague": "Search for player (e.g., Romelu Lukaku, Tammy Abraham)",
            "WorldCup": "Search for player (e.g., Lionel Messi, Kylian Mbappé)",
        }
        return placeholders.get(league, "Search for player (e.g., Player Name)")

    def _setup_ui_components(self):
        """Setup the UI components for the modal."""
        # Get league-specific labels
        participant_label = self._get_participant_label(self.league)
        participant_placeholder = self._get_participant_placeholder(self.league)

        # Player search input
        self.player_search = TextInput(
            label=f"Search {participant_label}",
            placeholder=participant_placeholder,
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
        self.view_ref.current_leg_construction_details.update(
            {
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
            }
        )

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
                        label=f"{player.player_name} ({player.team_name})",
                        value=player.player_name,
                        description=f"{player.team_name} - {player.confidence:.0f}% match",
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
                selected_player_name = player_select.values[0]
                selected_player = next(
                    (
                        p
                        for p in search_results
                        if p.player_name == selected_player_name
                    ),
                    None,
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
                content=f"**Select a player for Leg {self.leg_number}:**", view=view
            )

        except Exception as e:
            logger.error(f"Error in player search: {e}")
            await interaction.response.send_message(
                "❌ Error searching for players. Please try again.",
                ephemeral=True,
            )

    async def _show_prop_type_selection(
        self, interaction: Interaction, player: PlayerSearchResult
    ):
        """Show prop type selection after player is chosen."""
        try:
            # Get prop templates and groups for this league
            prop_templates = get_prop_templates_for_league(self.league)
            prop_groups = get_prop_groups_for_league(self.league)

            if not prop_templates:
                await interaction.response.send_message(
                    f"No prop types available for {self.league}.", ephemeral=True
                )
                return

            # Store selected player for later use
            self.selected_player = player
            self.prop_templates = prop_templates

            # Create category options
            category_options = []
            for category_name, prop_types in prop_groups.items():
                # Count props in this category
                prop_count = len(prop_types)
                category_options.append(
                    SelectOption(
                        label=f"{category_name} ({prop_count} props)",
                        value=category_name,
                        description=f"Select from {prop_count} {category_name.lower()} props",
                    )
                )

            # Create category selection dropdown
            category_select = Select(
                placeholder="Select a category...",
                options=category_options,
                min_values=1,
                max_values=1,
            )

            async def category_callback(interaction: Interaction):
                selected_category = category_select.values[0]
                await self._show_props_for_category(interaction, selected_category)

            category_select.callback = category_callback

            # Create new view with category selection
            view = View(timeout=300)
            view.add_item(category_select)
            view.add_item(Button(label="Back", style=ButtonStyle.secondary))

            await interaction.response.edit_message(
                content=f"**Select category for {player.player_name}:**\n"
                f"Choose a stat category to see available props:",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing prop type selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing prop types. Please try again.", ephemeral=True
            )

    async def _show_props_for_category(
        self, interaction: Interaction, category_name: str
    ):
        """Show prop types for a specific category."""
        try:
            # Get prop types for this category
            prop_groups = get_prop_groups_for_league(self.league)
            category_props = prop_groups.get(category_name, [])
            
            if not category_props:
                await interaction.response.send_message(
                    f"No props found in {category_name} category.", ephemeral=True
                )
                return

            # Create prop options for this category
            prop_options = []
            for prop_type in category_props:
                template = self.prop_templates.get(prop_type)
                if template:
                    # Format the range nicely
                    range_text = f"{template.min_value}-{template.max_value} {template.unit}"
                    if template.min_value == 0.0:
                        range_text = f"0-{template.max_value} {template.unit}"
                    
                    # Limit description to 100 characters (Discord limit)
                    if len(range_text) > 100:
                        range_text = range_text[:97] + "..."
                    
                    # Limit label to 100 characters (Discord limit)
                    label = template.label[:100]
                    
                    prop_options.append(
                        SelectOption(
                            label=label,
                            value=prop_type,
                            description=range_text,
                        )
                    )

            # Create prop selection dropdown
            prop_select = Select(
                placeholder=f"Select {category_name.lower()} prop...",
                options=prop_options,
                min_values=1,
                max_values=1,
            )

            async def prop_callback(interaction: Interaction):
                selected_prop_type = prop_select.values[0]

                # Show the enhanced modal with pre-filled data
                modal = ParlayEnhancedPlayerPropModal(
                    self.bot, self.db_manager, self.league, self.leg_number
                )

                # Pre-fill player name
                modal.player_search.default = self.selected_player.player_name

                await interaction.response.send_modal(modal)

            prop_select.callback = prop_callback

            # Create new view with prop selection
            view = View(timeout=300)
            view.add_item(prop_select)
            view.add_item(Button(label="Back to Categories", style=ButtonStyle.secondary))

            await interaction.response.edit_message(
                content=f"**{category_name} Props for {self.selected_player.player_name}:**\n"
                f"Choose the specific stat you want to bet on:",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing props for category: {e}")
            await interaction.response.send_message(
                "❌ Error showing props for category. Please try again.", ephemeral=True
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
