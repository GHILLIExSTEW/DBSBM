"""
Enhanced Player Prop Modal for Parlays
Provides improved player search, prop type selection, and validation for parlay legs.

VERSION: 1.1.0 - Fixed PlayerPropSearchView attribute error
"""

import logging

import discord
from bot.config.prop_templates import (
    get_prop_groups_for_league,
    get_prop_templates_for_league,
    validate_prop_value,
)
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Modal, Select, TextInput, View
from bot.services.player_search_service import PlayerSearchResult, PlayerSearchService

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
        logger.info(f"[PARLAY ENHANCED MODAL] Modal submitted for user {interaction.user.id}")
        try:
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

            # Add the leg to the parlay using the view's add_leg method
            if hasattr(self.view_ref, "add_leg"):
                await self.view_ref.add_leg(interaction, bet_data)
            else:
                logger.error("View reference missing add_leg method")
                await interaction.followup.send(
                    "❌ Error: Could not add leg to parlay", ephemeral=True
                )
            
            # Properly close the modal
            await interaction.response.defer()

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
            logger.info(f"[PARLAY ENHANCED MODAL] Searching for player: {player_name} in league: {self.league}")
            search_results = await self.player_search_service.search_players(
                player_name, self.league, limit=1, min_confidence=70.0
            )

            if not search_results:
                logger.warning(f"[PARLAY ENHANCED MODAL] No players found for: {player_name}")
                return {
                    "valid": False,
                    "error": f'Player "{player_name}" not found. Try a different search term.',
                }

            selected_player = search_results[0]
            logger.info(f"[PARLAY ENHANCED MODAL] Selected player: {selected_player.player_name} from {selected_player.team_name}")

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
                    "player_name": selected_player.player_name,
                    "player_id": None,  # PlayerSearchResult doesn't have player_id
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
        logger.info(f"[PARLAY ENHANCED MODAL] Storing bet data: {bet_data.get('player_name', 'unknown')} - {bet_data.get('line', 'unknown')}")
        if not self.view_ref:
            return

        # Store in current leg construction details with proper parlay format
        self.view_ref.current_leg_construction_details.update(
            {
                "line_type": "player_prop",  # Use line_type for consistency
                "bet_type": "player_prop",  # Add bet_type for image generation
                "player_name": bet_data["player_name"],
                "player_id": bet_data["player_id"],
                "team": bet_data["team_name"],  # Use 'team' for consistency
                "home_team_name": bet_data["team_name"],
                "away_team_name": bet_data["player_name"],  # For player image display
                "selected_team": bet_data["team_name"],
                "prop_type": bet_data["prop_type"],
                "line_value": bet_data["line_value"],
                "bet_direction": bet_data["bet_direction"],
                "line": bet_data["line"],
                "odds": bet_data["odds"],
                "odds_str": bet_data["odds_str"],
                "league": bet_data["league"],
                # Add additional fields for complete data
                "sport": self.view_ref.current_leg_construction_details.get("sport", ""),
                "is_manual": self.view_ref.current_leg_construction_details.get("is_manual", False),
            }
        )

    async def _generate_preview_image(self, bet_data: dict):
        """Generate preview image for the parlay leg."""
        try:
            from bot.utils.parlay_bet_image_generator import ParlayBetImageGenerator

            generator = ParlayBetImageGenerator(
                guild_id=self.view_ref.original_interaction.guild_id
            )

            # Prepare leg data for preview
            leg_data = {
                "bet_type": "player_prop",
                "line_type": "player_prop",
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
            logger.info(f"[PARLAY PLAYER SEARCH] Starting search for league: {self.league}")
            
            # Get popular players for this league (like the working player props)
            search_results = await self.player_search_service.get_popular_players(
                self.league, limit=100
            )

            logger.info(f"[PARLAY PLAYER SEARCH] Found {len(search_results) if search_results else 0} players")

            if not search_results:
                await interaction.response.send_message(
                    f"No players found for {self.league}. Please try a different league.",
                    ephemeral=True,
                )
                return

            # Create player selection options
            options = []
            for player in search_results[:25]:  # Limit to 25 for Discord
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
                try:
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
                        self.selected_player = selected_player  # Store for later use
                        await self._show_prop_type_selection(interaction, selected_player)
                    else:
                        await interaction.response.send_message(
                            "Error: Selected player not found.", ephemeral=True
                        )
                except Exception as e:
                    logger.error(f"Error in player callback: {e}")
                    await interaction.response.send_message(
                        "❌ Error selecting player. Please try again.",
                        ephemeral=True,
                    )

            player_select.callback = player_callback

            # Create new view with player selection
            view = View(timeout=300)
            view.add_item(player_select)
            view.add_item(Button(label="Cancel", style=ButtonStyle.secondary))

            logger.info(f"[PARLAY PLAYER SEARCH] Showing player selection view")
            await interaction.response.edit_message(
                content=f"**Select a player for Leg {self.leg_number}:**", view=view
            )

        except Exception as e:
            logger.error(f"Error in player search: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error searching for players. Please try again.",
                    ephemeral=True,
                )
            except:
                # If response already sent, try to follow up
                try:
                    await interaction.followup.send(
                        "❌ Error searching for players. Please try again.",
                        ephemeral=True,
                    )
                except:
                    logger.error("Could not send error message to user")

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

                # Create the bet data directly from the selected player and prop
                bet_data = {
                    "player_name": self.selected_player.player_name,
                    "player_id": None,  # PlayerSearchResult doesn't have player_id
                    "team_name": self.selected_player.team_name,
                    "prop_type": selected_prop_type,
                    "line_value": 0.0,  # Will be set by user
                    "bet_direction": "over",  # Default
                    "odds": 0.0,  # Will be set by user
                    "league": self.league,
                    "line": "Over 0.0",  # Will be updated
                    "odds_str": "0",
                }

                # Show a modal to get the line value, bet direction, and odds
                from discord.ui import Modal, TextInput
                
                class QuickPlayerPropModal(Modal, title=f"Leg {self.leg_number} - {selected_prop_type.title()}"):
                    def __init__(self, parent_view, bet_data):
                        super().__init__()
                        self.parent_view = parent_view
                        self.bet_data = bet_data
                        
                        self.line_value_input = TextInput(
                            label="Line Value",
                            placeholder="e.g., 25.5",
                            required=True,
                            max_length=10
                        )
                        self.bet_direction_input = TextInput(
                            label="Over/Under",
                            placeholder="Type 'over' or 'under'",
                            required=True,
                            max_length=10
                        )
                        self.odds_input = TextInput(
                            label="Odds",
                            placeholder="e.g., -110",
                            required=True,
                            max_length=10
                        )
                        
                        self.add_item(self.line_value_input)
                        self.add_item(self.bet_direction_input)
                        self.add_item(self.odds_input)
                    
                    async def on_submit(self, interaction: Interaction):
                        try:
                            # Validate inputs
                            line_value = float(self.line_value_input.value.strip())
                            bet_direction = self.bet_direction_input.value.strip().lower()
                            odds = float(self.odds_input.value.strip())
                            
                            if bet_direction not in ["over", "under"]:
                                await interaction.response.send_message(
                                    "❌ Bet direction must be 'over' or 'under'", 
                                    ephemeral=True
                                )
                                return
                            
                            # Update bet data
                            self.bet_data.update({
                                "line_value": line_value,
                                "bet_direction": bet_direction,
                                "odds": odds,
                                "line": f"{bet_direction.title()} {line_value}",
                                "odds_str": str(odds),
                            })
                            
                            # Store in parent view (parlay workflow)
                            if hasattr(self.parent_view, 'parent_view') and self.parent_view.parent_view:
                                self.parent_view.parent_view.current_leg_construction_details.update({
                                    "line_type": "player_prop",
                                    "bet_type": "player_prop",
                                    "player_name": self.bet_data["player_name"],
                                    "player_id": self.bet_data["player_id"],
                                    "team": self.bet_data["team_name"],
                                    "home_team_name": self.bet_data["team_name"],
                                    "away_team_name": self.bet_data["player_name"],
                                    "selected_team": self.bet_data["team_name"],
                                    "prop_type": self.bet_data["prop_type"],
                                    "line_value": self.bet_data["line_value"],
                                    "bet_direction": self.bet_data["bet_direction"],
                                    "line": self.bet_data["line"],
                                    "odds": self.bet_data["odds"],
                                    "odds_str": self.bet_data["odds_str"],
                                    "league": self.bet_data["league"],
                                })
                            
                            # Add the leg to the parlay
                            if hasattr(self.parent_view, 'parent_view') and self.parent_view.parent_view:
                                await self.parent_view.parent_view.add_leg(interaction, self.bet_data)
                            
                            await interaction.response.defer()
                            
                        except ValueError:
                            await interaction.response.send_message(
                                "❌ Invalid input. Please enter valid numbers.", 
                                ephemeral=True
                            )
                        except Exception as e:
                            logger.error(f"Error in QuickPlayerPropModal: {e}")
                            await interaction.response.send_message(
                                "❌ An error occurred. Please try again.", 
                                ephemeral=True
                            )
                
                # Show the quick modal
                quick_modal = QuickPlayerPropModal(self, bet_data)
                await interaction.response.send_modal(quick_modal)

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
