"""
Enhanced Player Prop Modal
Provides improved player search, prop type selection, and validation.

VERSION: 1.1.0 - Fixed PlayerPropSearchView attribute error
"""

import logging

import discord
from config.prop_templates import (
    get_prop_groups_for_league,
    get_prop_templates_for_league,
    validate_prop_value,
)
from services.player_search_service import PlayerSearchService

logger = logging.getLogger(__name__)


class EnhancedPlayerPropModal(discord.ui.Modal, title="Player Prop Bet"):
    """Enhanced modal for player prop betting with search and validation."""

    def __init__(self, bot, db_manager, league: str, game_id: str, team_name: str):
        super().__init__()
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.team_name = team_name
        self.player_search_service = PlayerSearchService(db_manager)

        # Get prop templates for this league
        self.prop_templates = get_prop_templates_for_league(league)
        self.prop_groups = get_prop_groups_for_league(league)

        # Set league-specific title
        self.title = self._get_league_specific_title(league)

        # Initialize UI components
        self._setup_ui_components()

    def _get_league_specific_title(self, league: str) -> str:
        """Get league-specific modal title."""
        league_titles = {
            "Formula-1": "🏎️ Driver Prop Bet",
            "PGA": "⛳ Golfer Prop Bet",
            "LPGA": "⛳ Golfer Prop Bet",
            "EuropeanTour": "⛳ Golfer Prop Bet",
            "LIVGolf": "⛳ Golfer Prop Bet",
            "ATP": "🎾 Player Prop Bet",
            "WTA": "🎾 Player Prop Bet",
            "Tennis": "🎾 Player Prop Bet",
            "MMA": "🥊 Fighter Prop Bet",
            "Bellator": "🥊 Fighter Prop Bet",
            "PDC": "🎯 Darts Player Prop Bet",
            "BDO": "🎯 Darts Player Prop Bet",
            "WDF": "🎯 Darts Player Prop Bet",
            "NBA": "🏀 Player Prop Bet",
            "WNBA": "🏀 Player Prop Bet",
            "NFL": "🏈 Player Prop Bet",
            "MLB": "⚾ Player Prop Bet",
            "NHL": "🏒 Player Prop Bet",
            "Soccer": "⚽ Player Prop Bet",
            "EPL": "⚽ Player Prop Bet",
            "LaLiga": "⚽ Player Prop Bet",
            "Bundesliga": "⚽ Player Prop Bet",
            "SerieA": "⚽ Player Prop Bet",
            "Ligue1": "⚽ Player Prop Bet",
            "ChampionsLeague": "⚽ Player Prop Bet",
            "EuropaLeague": "⚽ Player Prop Bet",
            "WorldCup": "⚽ Player Prop Bet",
        }
        return league_titles.get(league, "🏀 Player Prop Bet")

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
        self.player_search = discord.ui.TextInput(
            label=f"Search {participant_label}",
            placeholder=participant_placeholder,
            style=discord.TextStyle.short,
            required=True,
            max_length=100,
        )

        # Prop type selection
        prop_types = list(self.prop_templates.keys())
        self.prop_type = discord.ui.TextInput(
            label="Prop Type",
            placeholder=f"Available: {', '.join(prop_types[:5])}...",
            style=discord.TextStyle.short,
            required=True,
            max_length=50,
        )

        # Line value input
        self.line_value = discord.ui.TextInput(
            label="Line Value",
            placeholder="Enter the over/under line (e.g., 25.5)",
            style=discord.TextStyle.short,
            required=True,
            max_length=10,
        )

        # Bet direction
        self.bet_direction = discord.ui.TextInput(
            label="Over/Under",
            placeholder="Type 'over' or 'under'",
            style=discord.TextStyle.short,
            required=True,
            max_length=10,
        )

        # Odds input
        self.odds = discord.ui.TextInput(
            label="Odds",
            placeholder="Enter odds (e.g., -110, +150, 2.5)",
            style=discord.TextStyle.short,
            required=True,
            max_length=10,
        )

        # Add components to modal
        self.add_item(self.player_search)
        self.add_item(self.prop_type)
        self.add_item(self.line_value)
        self.add_item(self.bet_direction)
        self.add_item(self.odds)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission with validation."""
        try:
            # Validate and process inputs
            validation_result = await self._validate_inputs()

            if not validation_result["valid"]:
                await interaction.response.send_message(
                    f"❌ **Validation Error:** {validation_result['error']}",
                    ephemeral=True,
                )
                return

            # Create the bet
            bet_data = validation_result["bet_data"]
            success = await self._create_player_prop_bet(interaction, bet_data)

            if success:
                # Show units selection screen
                await self._show_units_selection(interaction, bet_data)
            else:
                await interaction.response.send_message(
                    "❌ **Error creating bet.** Please try again.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in player prop modal submission: {e}")
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

            # Validate odds
            odds_input = self.odds.value.strip()
            try:
                # Handle American odds (-110, +150) and decimal odds (2.5)
                if odds_input.startswith('-') or odds_input.startswith('+'):
                    # American odds
                    odds_value = int(odds_input)
                    if odds_value == 0:
                        return {
                            "valid": False,
                            "error": "Odds cannot be zero. Enter valid odds (e.g., -110, +150).",
                        }
                else:
                    # Decimal odds
                    odds_value = float(odds_input)
                    if odds_value <= 1.0:
                        return {
                            "valid": False,
                            "error": "Decimal odds must be greater than 1.0 (e.g., 2.5, 1.5).",
                        }
            except ValueError:
                return {
                    "valid": False,
                    "error": "Invalid odds format. Use American odds (-110, +150) or decimal odds (2.5).",
                }

            # All validations passed
            return {
                "valid": True,
                "bet_data": {
                    "player_name": selected_player.player_name,
                    "team_name": selected_player.team_name,
                    "league": self.league,
                    "sport": selected_player.sport,
                    "prop_type": prop_type,
                    "line_value": line_value,
                    "bet_direction": bet_direction,
                    "odds": odds_input,
                    "game_id": self.game_id,
                },
            }

        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            return {"valid": False, "error": "An error occurred during validation."}

    async def _create_player_prop_bet(
        self, interaction: discord.Interaction, bet_data: dict
    ) -> bool:
        """Create the player prop bet in the database."""
        try:
            # Insert into bets table
            query = """
                INSERT INTO bets (
                    user_id, guild_id, bet_type, player_prop, player_name,
                    team_name, league, sport, player_prop_type, player_prop_line,
                    player_prop_direction, odds, game_id, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """

            await self.db_manager.execute(
                query,
                (
                    interaction.user.id,
                    interaction.guild_id,
                    "player_prop",
                    True,
                    bet_data["player_name"],
                    bet_data["team_name"],
                    bet_data["league"],
                    bet_data["sport"],
                    bet_data["prop_type"],
                    bet_data["line_value"],
                    bet_data["bet_direction"],
                    bet_data["odds"],
                    bet_data["game_id"],
                    "pending",
                ),
            )

            # Add player to search cache for future searches
            await self.player_search_service.add_player_to_cache(
                bet_data["player_name"],
                bet_data["team_name"],
                bet_data["league"],
                bet_data["sport"],
            )

            return True

        except Exception as e:
            logger.error(f"Error creating player prop bet: {e}")
            return False

    async def _show_units_selection(self, interaction: discord.Interaction, bet_data: dict):
        """Show units selection screen after modal submission."""
        try:
            # Create units selection options
            units_options = [
                discord.SelectOption(label="0.5 Units", value="0.5", description="$50 bet"),
                discord.SelectOption(label="1 Unit", value="1.0", description="$100 bet"),
                discord.SelectOption(label="1.5 Units", value="1.5", description="$150 bet"),
                discord.SelectOption(label="2 Units", value="2.0", description="$200 bet"),
                discord.SelectOption(label="2.5 Units", value="2.5", description="$250 bet"),
                discord.SelectOption(label="3 Units", value="3.0", description="$300 bet"),
                discord.SelectOption(label="4 Units", value="4.0", description="$400 bet"),
                discord.SelectOption(label="5 Units", value="5.0", description="$500 bet"),
                discord.SelectOption(label="7.5 Units", value="7.5", description="$750 bet"),
                discord.SelectOption(label="10 Units", value="10.0", description="$1000 bet"),
            ]

            # Create units selection dropdown
            units_select = discord.ui.Select(
                placeholder="Select your bet amount...",
                options=units_options,
                min_values=1,
                max_values=1,
            )

            async def units_callback(units_interaction: discord.Interaction):
                selected_units = float(units_select.values[0])
                
                # Calculate bet amount (assuming $100 per unit)
                bet_amount = selected_units * 100
                
                # Update the bet with units and bet amount
                await self._update_bet_with_units(units_interaction, bet_data, selected_units, bet_amount)

            units_select.callback = units_callback

            # Create view with units selection
            view = discord.ui.View(timeout=300)
            view.add_item(units_select)

            # Show bet summary and units selection with default preview
            await interaction.response.edit_message(
                content=f"🎯 **Player Prop Bet Summary**\n\n"
                f"**Player:** {bet_data['player_name']}\n"
                f"**Prop:** {bet_data['prop_type']}\n"
                f"**Bet:** {bet_data['bet_direction'].upper()} {bet_data['line_value']} @ {bet_data['odds']}\n"
                f"**Units:** 1.0 (${100:,.0f})\n\n"
                f"**Select your bet amount:**",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing units selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing units selection. Please try again.",
                ephemeral=True
            )

    async def _update_bet_with_units(self, interaction: discord.Interaction, bet_data: dict, units: float, bet_amount: float):
        """Update the bet with units and bet amount, then show final confirmation."""
        try:
            # Update the bet in the database with units and bet amount
            query = """
                UPDATE bets 
                SET units = %s, bet_amount = %s, status = 'active'
                WHERE user_id = %s AND guild_id = %s AND bet_type = 'player_prop' 
                AND player_name = %s AND player_prop_type = %s AND player_prop_line = %s
                AND player_prop_direction = %s AND odds = %s AND game_id = %s
                ORDER BY created_at DESC LIMIT 1
            """

            await self.db_manager.execute(
                query,
                (
                    units,
                    bet_amount,
                    interaction.user.id,
                    interaction.guild_id,
                    bet_data["player_name"],
                    bet_data["prop_type"],
                    bet_data["line_value"],
                    bet_data["bet_direction"],
                    bet_data["odds"],
                    bet_data["game_id"],
                ),
            )

            # Show final confirmation
            await interaction.response.edit_message(
                content=f"✅ **Player Prop Bet Confirmed!**\n\n"
                f"**Player:** {bet_data['player_name']}\n"
                f"**Prop:** {bet_data['prop_type']}\n"
                f"**Bet:** {bet_data['bet_direction'].upper()} {bet_data['line_value']} @ {bet_data['odds']}\n"
                f"**Units:** {units} (${bet_amount:,.0f})\n\n"
                f"🎉 Your bet has been placed successfully!",
                view=None
            )

        except Exception as e:
            logger.error(f"Error updating bet with units: {e}")
            await interaction.response.send_message(
                "❌ Error confirming bet. Please try again.",
                ephemeral=True
            )


class PlayerPropSearchView(discord.ui.View):
    """View for player search with autocomplete."""

    def __init__(self, bot, db_manager, league: str, game_id: str, team_name: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.team_name = team_name
        self.player_search_service = PlayerSearchService(db_manager)

    @discord.ui.button(label="Search Players", style=discord.ButtonStyle.primary)
    async def search_players(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Search for players using the enhanced search service."""
        try:
            # Show popular players for this league and team directly
            search_results = await self.player_search_service.get_popular_players(
                self.league, self.team_name, limit=25
            )

            if not search_results:
                await interaction.response.send_message(
                    f"No players found for {self.team_name}. Please try a different team.",
                    ephemeral=True,
                )
                return

            # Create player selection dropdown
            options = []
            for result in search_results:
                # Add confidence indicator for team library players
                confidence_indicator = "⭐" if result.confidence > 80 else "🔍"
                label = f"{confidence_indicator} {result.player_name}"
                description = f"{result.team_name} ({result.confidence:.0f}% match)"

                options.append(
                    discord.SelectOption(
                        label=label[:100],  # Discord limit
                        value=result.player_name,
                        description=description[:100],  # Discord limit
                    )
                )

            # Create player selection dropdown
            player_select = discord.ui.Select(
                placeholder="Select a player...",
                options=options,
                min_values=1,
                max_values=1,
            )

            async def player_callback(interaction: discord.Interaction):
                selected_player = player_select.values[0]

                # Show prop type selection
                await self._show_prop_type_selection(interaction, selected_player)

            player_select.callback = player_callback

            # Create new view with player selection
            view = discord.ui.View(timeout=300)
            view.add_item(player_select)
            view.add_item(
                discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
            )

            await interaction.response.edit_message(
                content=f"**{self.team_name} Players:**\n"
                f"⭐ = High confidence (team library)\n"
                f"🔍 = Database match\n\n"
                f"Select a player to continue:",
                view=view,
            )

        except Exception as e:
            logger.error(f"Error in player search: {e}")
            await interaction.response.send_message(
                f"❌ Error searching for {self.team_name} players. Please try again.",
                ephemeral=True,
            )

    async def _show_prop_type_selection(
        self, interaction: discord.Interaction, selected_player: str
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
            self.selected_player = selected_player
            self.prop_templates = prop_templates

            # Create category options
            category_options = []
            for category_name, prop_types in prop_groups.items():
                # Count props in this category
                prop_count = len(prop_types)
                category_options.append(
                    discord.SelectOption(
                        label=f"{category_name} ({prop_count} props)",
                        value=category_name,
                        description=f"Select from {prop_count} {category_name.lower()} props",
                    )
                )

            # Create category selection dropdown
            category_select = discord.ui.Select(
                placeholder="Select a category...",
                options=category_options,
                min_values=1,
                max_values=1,
            )

            async def category_callback(interaction: discord.Interaction):
                selected_category = category_select.values[0]
                await self._show_props_for_category(interaction, selected_category)

            category_select.callback = category_callback

            # Create new view with category selection
            view = discord.ui.View(timeout=300)
            view.add_item(category_select)
            view.add_item(
                discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
            )

            await interaction.response.edit_message(
                content=f"**Select category for {selected_player}:**\n"
                f"Choose a stat category to see available props:",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing prop type selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing prop types. Please try again.",
                ephemeral=True,
            )

    async def _show_props_for_category(
        self, interaction: discord.Interaction, category_name: str
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
                        discord.SelectOption(
                            label=label,
                            value=prop_type,
                            description=range_text,
                        )
                    )

            # Create prop selection dropdown
            prop_select = discord.ui.Select(
                placeholder=f"Select {category_name.lower()} prop...",
                options=prop_options,
                min_values=1,
                max_values=1,
            )

            async def prop_callback(interaction: discord.Interaction):
                selected_prop_type = prop_select.values[0]
                template = self.prop_templates[selected_prop_type]

                # Store selected prop for later use
                self.selected_prop_type = selected_prop_type

                # Create a new view class for the final buttons
                class FinalButtonsView(discord.ui.View):
                    def __init__(self, parent_view):
                        super().__init__(timeout=300)
                        self.parent_view = parent_view

                    @discord.ui.button(label="Create Prop Bet", style=discord.ButtonStyle.success)
                    async def create_prop_bet(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        try:
                            # Check if we have the required data
                            if not hasattr(self.parent_view, 'selected_player') or not hasattr(self.parent_view, 'selected_prop_type'):
                                await button_interaction.response.send_message(
                                    "❌ Error: Missing player or prop selection. Please try again.",
                                    ephemeral=True
                                )
                                return

                            # Create the enhanced player prop modal
                            modal = EnhancedPlayerPropModal(
                                self.parent_view.bot, 
                                self.parent_view.db_manager, 
                                self.parent_view.league, 
                                self.parent_view.game_id, 
                                self.parent_view.team_name
                            )
                            
                            # Pre-fill the player name and prop type
                            modal.player_search.default = self.parent_view.selected_player
                            modal.prop_type.default = self.parent_view.selected_prop_type
                            
                            await button_interaction.response.send_modal(modal)

                        except Exception as e:
                            logger.error(f"Error opening player prop modal: {e}")
                            await button_interaction.response.send_message(
                                "❌ Error opening bet modal.", ephemeral=True
                            )

                    @discord.ui.button(label="Back to Categories", style=discord.ButtonStyle.secondary)
                    async def back_to_categories(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        try:
                            # Go back to category selection
                            await self.parent_view._show_prop_type_selection(button_interaction, self.parent_view.selected_player)
                        except Exception as e:
                            logger.error(f"Error going back to categories: {e}")
                            await button_interaction.response.send_message(
                                "❌ Error going back to categories.", ephemeral=True
                            )

                # Create the final view with working buttons
                final_view = FinalButtonsView(self)

                # Show success message with Create Prop Bet button
                await interaction.response.edit_message(
                    content=f"✅ **{self.selected_player}** - **{template.label}**\n\n"
                    f"📊 Range: {template.min_value}-{template.max_value} {template.unit}\n"
                    f"🎯 Click 'Create Prop Bet' below to set your line and bet amount!",
                    view=final_view,
                )

            prop_select.callback = prop_callback

            # Create new view with prop selection
            view = discord.ui.View(timeout=300)
            view.add_item(prop_select)
            view.add_item(
                discord.ui.Button(label="Back to Categories", style=discord.ButtonStyle.secondary)
            )

            await interaction.response.edit_message(
                content=f"**{category_name} Props for {self.selected_player}:**\n"
                f"Choose the specific stat you want to bet on:",
                view=view
            )

        except Exception as e:
            logger.error(f"Error showing props for category: {e}")
            await interaction.response.send_message(
                "❌ Error showing props for category. Please try again.",
                ephemeral=True,
            )




async def setup_enhanced_player_prop(
    bot, db_manager, league: str, game_id: str, team_name: str
):
    """Setup and return the enhanced player prop view."""
    return PlayerPropSearchView(bot, db_manager, league, game_id, team_name)
