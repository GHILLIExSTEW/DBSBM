"""
Enhanced Player Prop Modal
Provides improved player search, prop type selection, and validation.

VERSION: 1.1.0 - Fixed PlayerPropSearchView attribute error
"""

import logging

import discord

from bot.config.prop_templates import (
    get_prop_groups_for_league,
    get_prop_templates_for_league,
    validate_prop_value,
)
from bot.services.player_search_service import PlayerSearchService

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
                if odds_input.startswith("-") or odds_input.startswith("+"):
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
        """Create the player prop bet in the database using BetService."""
        try:
            logger.info(
                f"Creating player prop bet for user {interaction.user.id} in guild {interaction.guild_id}"
            )
            logger.info(f"Bet data: {bet_data}")

            # Get bet service from bot
            bet_service = getattr(interaction.client, "bet_service", None)
            if not bet_service:
                logger.error("BetService not found on bot instance")
                return False

            # Create the bet using BetService
            bet_serial = await bet_service.create_player_prop_bet(
                guild_id=interaction.guild_id,
                user_id=interaction.user.id,
                league=bet_data["league"],
                sport=bet_data["sport"],
                player_name=bet_data["player_name"],
                team_name=bet_data["team_name"],
                prop_type=bet_data["prop_type"],
                line_value=bet_data["line_value"],
                bet_direction=bet_data["bet_direction"],
                odds=bet_data["odds"],
                units=0.0,  # Default units value
                api_game_id=bet_data.get("game_id"),  # Pass as api_game_id
                confirmed=0,  # Not confirmed until units are set
            )

            if bet_serial:
                logger.info(
                    f"Player prop bet created successfully with bet_serial: {bet_serial}"
                )

                # Add player to search cache for future searches
                await self.player_search_service.add_player_to_cache(
                    bet_data["player_name"],
                    bet_data["team_name"],
                    bet_data["league"],
                    bet_data["sport"],
                )

                return True
            else:
                logger.error("Failed to create player prop bet - bet_serial is None")
                return False

        except Exception as e:
            logger.error(f"Error creating player prop bet: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _show_units_selection(
        self, interaction: discord.Interaction, bet_data: dict
    ):
        """Show units selection screen after modal submission."""
        try:
            # Create units selection options
            units_options = [
                discord.SelectOption(label="0.5 Units", value="0.5"),
                discord.SelectOption(label="1 Unit", value="1.0"),
                discord.SelectOption(label="1.5 Units", value="1.5"),
                discord.SelectOption(label="2 Units", value="2.0"),
                discord.SelectOption(label="2.5 Units", value="2.5"),
                discord.SelectOption(label="3 Units", value="3.0"),
                discord.SelectOption(label="4 Units", value="4.0"),
                discord.SelectOption(label="5 Units", value="5.0"),
                discord.SelectOption(label="7.5 Units", value="7.5"),
                discord.SelectOption(label="10 Units", value="10.0"),
            ]

            # Create units selection dropdown
            units_select = discord.ui.Select(
                placeholder="Select unit amount for bet...",
                options=units_options,
                min_values=1,
                max_values=1,
            )

            async def units_callback(units_interaction: discord.Interaction):
                selected_units = float(units_select.values[0])

                # Generate preview image with selected units
                await self._show_units_preview(
                    units_interaction, bet_data, selected_units
                )

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
                f"**Units:** 1.0\n\n"
                f"**Select unit amount for bet:**",
                view=view,
            )

        except Exception as e:
            logger.error(f"Error showing units selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing units selection. Please try again.", ephemeral=True
            )

    async def _show_units_preview(
        self, interaction: discord.Interaction, bet_data: dict, units: float
    ):
        """Show preview image after unit selection."""
        try:
            import io
            from datetime import datetime, timezone

            from discord import File

            from bot.utils.player_prop_image_generator import PlayerPropImageGenerator

            # Generate preview image
            generator = PlayerPropImageGenerator(guild_id=interaction.guild_id)

            # Format the line value properly
            line_value = bet_data.get("line_value", "N/A")
            if isinstance(line_value, (int, float)):
                line_value = str(line_value)

            # Format the prop type
            prop_type = bet_data.get("prop_type", "N/A")
            prop_type = prop_type.replace("_", " ").title()

            # Generate the image
            image_bytes = generator.generate_player_prop_bet_image(
                player_name=bet_data["player_name"],
                team_name=bet_data["team_name"],
                league=bet_data["league"],
                line=line_value,
                prop_type=prop_type,
                units=units,
                output_path=None,
                bet_id="PREVIEW",
                timestamp=datetime.now(timezone.utc),
                guild_id=str(interaction.guild_id),
                odds=bet_data.get("odds", 0.0),
                units_display_mode="auto",
                display_as_risk=False,
            )

            if image_bytes:
                # Create file object for Discord
                file = File(
                    io.BytesIO(image_bytes), filename="player_prop_preview.webp"
                )

                # Create confirmation buttons
                confirm_button = discord.ui.Button(
                    label="✅ Confirm Bet",
                    style=discord.ButtonStyle.success,
                    custom_id="confirm_bet",
                )

                back_button = discord.ui.Button(
                    label="🔄 Change Units",
                    style=discord.ButtonStyle.secondary,
                    custom_id="change_units",
                )

                async def confirm_callback(confirm_interaction: discord.Interaction):
                    await self._update_bet_with_units(
                        confirm_interaction, bet_data, units
                    )

                async def back_callback(back_interaction: discord.Interaction):
                    await self._show_units_selection(back_interaction, bet_data)

                confirm_button.callback = confirm_callback
                back_button.callback = back_callback

                # Create view with buttons
                view = discord.ui.View(timeout=300)
                view.add_item(confirm_button)
                view.add_item(back_button)

                # Send new message with file (can't edit with files)
                await interaction.response.send_message(
                    content=f"🎯 **Player Prop Bet Preview**\n\n"
                    f"**Player:** {bet_data['player_name']}\n"
                    f"**Prop:** {prop_type}\n"
                    f"**Bet:** {bet_data['bet_direction'].upper()} {line_value} @ {bet_data.get('odds', 'N/A')}\n"
                    f"**Units:** {units}\n\n"
                    f"**Preview your bet slip below:**",
                    view=view,
                    file=file,
                    ephemeral=True,
                )
            else:
                # Fallback if image generation fails
                await interaction.response.send_message(
                    "❌ Error generating preview image. Please try again.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.error(f"Error showing units preview: {e}")
            await interaction.response.send_message(
                "❌ Error showing preview. Please try again.", ephemeral=True
            )

    async def _update_bet_with_units(
        self, interaction: discord.Interaction, bet_data: dict, units: float
    ):
        """Update the bet with units, then show final confirmation."""
        try:
            logger.info(
                f"Updating bet with units: {units} for user {interaction.user.id}"
            )

            # Get bet service from bot
            bet_service = getattr(interaction.client, "bet_service", None)
            if not bet_service:
                logger.error("BetService not found on bot instance")
                await interaction.response.send_message(
                    "❌ Error updating bet. Please try again.", ephemeral=True
                )
                return

            # Get the most recent player prop bet for this user
            bet_record = await self.db_manager.fetch_one(
                "SELECT bet_serial FROM bets WHERE user_id = %s AND guild_id = %s AND bet_type = 'player_prop' ORDER BY created_at DESC LIMIT 1",
                (interaction.user.id, interaction.guild_id),
            )

            if not bet_record:
                logger.error("No player prop bet found to update")
                await interaction.response.send_message(
                    "❌ No bet found to update. Please try again.", ephemeral=True
                )
                return

            bet_serial = bet_record["bet_serial"]
            logger.info(f"Updating bet_serial: {bet_serial} with units: {units}")

            # Update the bet using BetService
            await bet_service.update_bet(
                bet_serial=bet_serial, units=units, status="pending"
            )

            logger.info(f"Bet updated successfully")

            # Show channel selection
            await self._show_channel_selection(interaction, bet_data, units)

        except Exception as e:
            logger.error(f"Error updating bet with units: {e}")
            await interaction.response.send_message(
                "❌ Error confirming bet. Please try again.", ephemeral=True
            )

    async def _show_channel_selection(
        self, interaction: discord.Interaction, bet_data: dict, units: float
    ):
        """Show channel selection for posting the bet."""
        try:
            # Get available channels from guild settings
            allowed_channels = []
            guild_settings = await self.db_manager.fetch_one(
                "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
                (str(interaction.guild_id),),
            )

            if guild_settings:
                for channel_id in (
                    guild_settings.get("embed_channel_1"),
                    guild_settings.get("embed_channel_2"),
                ):
                    if channel_id:
                        try:
                            cid = int(channel_id)
                            channel = interaction.client.get_channel(
                                cid
                            ) or await interaction.client.fetch_channel(cid)
                            if (
                                isinstance(channel, discord.TextChannel)
                                and channel.permissions_for(
                                    interaction.guild.me
                                ).send_messages
                            ):
                                if channel not in allowed_channels:
                                    allowed_channels.append(channel)
                        except Exception as e:
                            logger.error(f"Error processing channel {channel_id}: {e}")

            if not allowed_channels:
                await interaction.response.edit_message(
                    content="❌ No valid embed channels configured. Please contact an admin.",
                    view=None,
                )
                return

            # Create channel selection dropdown
            channel_options = []
            for channel in allowed_channels:
                channel_options.append(
                    discord.SelectOption(
                        label=f"#{channel.name}",
                        value=str(channel.id),
                        description=f"Post to {channel.name}",
                    )
                )

            channel_select = discord.ui.Select(
                placeholder="Select channel to post your bet...",
                options=channel_options,
                min_values=1,
                max_values=1,
            )

            async def channel_callback(channel_interaction: discord.Interaction):
                selected_channel_id = int(channel_select.values[0])
                await self._post_bet_to_channel(
                    channel_interaction, bet_data, units, selected_channel_id
                )

            channel_select.callback = channel_callback

            # Create view with channel selection
            view = discord.ui.View(timeout=300)
            view.add_item(channel_select)

            # Show bet summary and channel selection
            await interaction.response.edit_message(
                content=f"🎯 **Player Prop Bet Ready to Post**\n\n"
                f"**Player:** {bet_data['player_name']}\n"
                f"**Prop:** {bet_data['prop_type']}\n"
                f"**Bet:** {bet_data['bet_direction'].upper()} {bet_data['line_value']} @ {bet_data['odds']}\n"
                f"**Units:** {units}\n\n"
                f"**Select channel to post your bet:**",
                view=view,
            )

        except Exception as e:
            logger.error(f"Error showing channel selection: {e}")
            await interaction.response.send_message(
                "❌ Error showing channel selection. Please try again.", ephemeral=True
            )

    async def _post_bet_to_channel(
        self,
        interaction: discord.Interaction,
        bet_data: dict,
        units: float,
        channel_id: int,
    ):
        """Post the bet to the selected channel with image."""
        try:
            # Get the channel
            channel = interaction.client.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message(
                    "❌ Selected channel not found. Please try again.", ephemeral=True
                )
                return

            # Generate bet slip image
            import io
            from datetime import datetime, timezone

            from bot.utils.player_prop_image_generator import PlayerPropImageGenerator

            generator = PlayerPropImageGenerator(guild_id=interaction.guild_id)

            # Get bet ID from database using the most recent bet for this user
            logger.info(
                f"Retrieving bet_serial for user {interaction.user.id} in guild {interaction.guild_id}"
            )

            bet_record = await self.db_manager.fetch_one(
                "SELECT bet_serial FROM bets WHERE user_id = %s AND guild_id = %s AND bet_type = 'player_prop' ORDER BY created_at DESC LIMIT 1",
                (interaction.user.id, interaction.guild_id),
            )

            logger.info(f"Bet record found: {bet_record}")

            bet_id = str(bet_record.get("bet_serial", "")) if bet_record else ""
            logger.info(f"Retrieved bet_serial: {bet_id} for player prop bet")
            timestamp = datetime.now(timezone.utc)

            # Generate the bet slip image
            bet_slip_image_bytes = generator.generate_player_prop_bet_image(
                player_name=bet_data["player_name"],
                team_name=bet_data.get("team_name", "Team"),
                league=bet_data.get("league", "N/A"),
                line=f"{bet_data['bet_direction'].upper()} {bet_data['line_value']}",
                prop_type=bet_data["prop_type"],
                units=units,
                output_path=None,
                bet_id=bet_id,
                timestamp=timestamp,
                guild_id=str(interaction.guild_id),
                odds=float(bet_data["odds"]),
                units_display_mode="auto",
                display_as_risk=False,
            )

            if bet_slip_image_bytes:
                # Create Discord file
                image_file = discord.File(
                    io.BytesIO(bet_slip_image_bytes),
                    filename=f"player_prop_slip_{bet_id}.webp",
                )

                # Get capper data for webhook
                capper_data = await self.db_manager.fetch_one(
                    "SELECT display_name, image_path FROM cappers WHERE guild_id = %s AND user_id = %s",
                    (interaction.guild_id, interaction.user.id),
                )

                webhook_username = (
                    capper_data.get("display_name")
                    if capper_data and capper_data.get("display_name")
                    else interaction.user.display_name
                )
                webhook_avatar_url = None
                if capper_data and capper_data.get("image_path"):
                    from bot.utils.image_url_converter import convert_image_path_to_url

                    webhook_avatar_url = convert_image_path_to_url(
                        capper_data["image_path"]
                    )

                # Get member role for mention
                member_role_id = None
                guild_settings = await self.db_manager.fetch_one(
                    "SELECT member_role FROM guild_settings WHERE guild_id = %s",
                    (str(interaction.guild_id),),
                )
                if guild_settings and guild_settings.get("member_role"):
                    member_role_id = guild_settings["member_role"]

                # Prepare content with member role mention
                content = f"<@&{member_role_id}>" if member_role_id else None

                # Get webhook for the channel
                webhooks = await channel.webhooks()
                webhook = None

                # Find existing webhook or create new one
                for existing_webhook in webhooks:
                    if existing_webhook.name == "Bet Tracking AI":
                        webhook = existing_webhook
                        break

                if not webhook:
                    webhook = await channel.create_webhook(name="Bet Tracking AI")

                # Post to channel using webhook
                webhook_message = await webhook.send(
                    content=content,
                    file=image_file,
                    username=webhook_username,
                    avatar_url=webhook_avatar_url,
                )

                # Update bet with channel_id and message_id using BetService
                bet_service = getattr(interaction.client, "bet_service", None)
                if bet_service and bet_id:
                    try:
                        await bet_service.update_straight_bet_channel(
                            bet_serial=int(bet_id),
                            channel_id=channel_id,
                            message_id=webhook_message.id,
                        )
                        logger.info(
                            f"Updated player prop bet {bet_id} with message_id {webhook_message.id} and channel_id {channel_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to update player prop bet with message_id: {e}"
                        )
                        # Fallback to just updating channel_id
                        await bet_service.update_bet(
                            bet_serial=int(bet_id), channel_id=channel_id
                        )

                # Show success message
                await interaction.response.edit_message(
                    content=f"✅ **Player Prop Bet Posted Successfully!**\n\n"
                    f"**Player:** {bet_data['player_name']}\n"
                    f"**Prop:** {bet_data['prop_type']}\n"
                    f"**Bet:** {bet_data['bet_direction'].upper()} {bet_data['line_value']} @ {bet_data['odds']}\n"
                    f"**Units:** {units}\n\n"
                    f"🎉 Your bet has been posted to <#{channel_id}>!",
                    view=None,
                )

            else:
                await interaction.response.send_message(
                    "❌ Error generating bet slip image. Please try again.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.error(f"Error posting bet to channel: {e}")
            await interaction.response.send_message(
                "❌ Error posting bet to channel. Please try again.", ephemeral=True
            )


class PlayerPropSearchView(discord.ui.View):
    """View for searching and selecting players with pagination."""

    def __init__(self, bot, db_manager, league: str, game_id: str, team_name: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.team_name = team_name
        self.player_search_service = PlayerSearchService(db_manager)

        # Pagination state
        self.all_players = []
        self.current_page = 0
        self.players_per_page = 22  # Discord allows 25 total (24 + 1 placeholder)

    @discord.ui.button(label="Search Players", style=discord.ButtonStyle.primary)
    async def search_players(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Search for players using the enhanced search service with pagination."""
        try:
            # Load all players for this league and team
            self.all_players = await self.player_search_service.get_popular_players(
                self.league,
                self.team_name,
                limit=100,  # Get more players for pagination
            )

            if not self.all_players:
                await interaction.response.send_message(
                    f"No players found for {self.team_name}. Please try a different team.",
                    ephemeral=True,
                )
                return

            # Reset to first page and show players
            self.current_page = 0
            await self._show_current_page(interaction)

        except Exception as e:
            logger.error(f"Error in player search: {e}")
            await interaction.response.send_message(
                f"❌ Error searching for {self.team_name} players. Please try again.",
                ephemeral=True,
            )

    async def _show_current_page(self, interaction: discord.Interaction):
        """Show the current page of players with pagination controls."""
        try:
            # Calculate page boundaries
            start_idx = self.current_page * self.players_per_page
            end_idx = start_idx + self.players_per_page
            current_players = self.all_players[start_idx:end_idx]

            # Create player selection dropdown
            options = []
            for result in current_players:
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

            # Create pagination buttons
            prev_button = discord.ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_page == 0,
            )

            next_button = discord.ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                disabled=end_idx >= len(self.all_players),
            )

            async def prev_callback(prev_interaction: discord.Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await self._show_current_page(prev_interaction)

            async def next_callback(next_interaction: discord.Interaction):
                if end_idx < len(self.all_players):
                    self.current_page += 1
                    await self._show_current_page(next_interaction)

            prev_button.callback = prev_callback
            next_button.callback = next_callback

            # Create view with player selection and pagination
            view = discord.ui.View(timeout=300)
            view.add_item(player_select)
            view.add_item(prev_button)
            view.add_item(next_button)
            view.add_item(
                discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
            )

            # Calculate page info
            total_pages = (
                len(self.all_players) + self.players_per_page - 1
            ) // self.players_per_page
            page_info = f"Page {self.current_page + 1} of {total_pages}"

            await interaction.response.edit_message(
                content=f"**{self.team_name} Players:**\n"
                f"⭐ = High confidence (team library)\n"
                f"🔍 = Database match\n"
                f"📄 {page_info} ({len(self.all_players)} total players)\n\n"
                f"Select a player to continue:",
                view=view,
            )

        except Exception as e:
            logger.error(f"Error showing current page: {e}")
            await interaction.response.send_message(
                "❌ Error displaying players. Please try again.",
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
                view=view,
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
                    range_text = (
                        f"{template.min_value}-{template.max_value} {template.unit}"
                    )
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

                    @discord.ui.button(
                        label="Create Prop Bet", style=discord.ButtonStyle.success
                    )
                    async def create_prop_bet(
                        self,
                        button_interaction: discord.Interaction,
                        button: discord.ui.Button,
                    ):
                        try:
                            # Check if we have the required data
                            if not hasattr(
                                self.parent_view, "selected_player"
                            ) or not hasattr(self.parent_view, "selected_prop_type"):
                                await button_interaction.response.send_message(
                                    "❌ Error: Missing player or prop selection. Please try again.",
                                    ephemeral=True,
                                )
                                return

                            # Create the enhanced player prop modal
                            modal = EnhancedPlayerPropModal(
                                self.parent_view.bot,
                                self.parent_view.db_manager,
                                self.parent_view.league,
                                self.parent_view.game_id,
                                self.parent_view.team_name,
                            )

                            # Pre-fill the player name and prop type
                            modal.player_search.default = (
                                self.parent_view.selected_player
                            )
                            modal.prop_type.default = (
                                self.parent_view.selected_prop_type
                            )

                            await button_interaction.response.send_modal(modal)

                        except Exception as e:
                            logger.error(f"Error opening player prop modal: {e}")
                            await button_interaction.response.send_message(
                                "❌ Error opening bet modal.", ephemeral=True
                            )

                    @discord.ui.button(
                        label="Back to Categories", style=discord.ButtonStyle.secondary
                    )
                    async def back_to_categories(
                        self,
                        button_interaction: discord.Interaction,
                        button: discord.ui.Button,
                    ):
                        try:
                            # Go back to category selection
                            await self.parent_view._show_prop_type_selection(
                                button_interaction, self.parent_view.selected_player
                            )
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
                discord.ui.Button(
                    label="Back to Categories", style=discord.ButtonStyle.secondary
                )
            )

            await interaction.response.edit_message(
                content=f"**{category_name} Props for {self.selected_player}:**\n"
                f"Choose the specific stat you want to bet on:",
                view=view,
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
