"""
Enhanced Player Props Command
Provides advanced player prop betting with search, validation, and modern UI.
"""

import logging
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord
from config.leagues import LEAGUE_CONFIG
from discord import ButtonStyle, Interaction, SelectOption, app_commands, File
from discord.ext import commands
from discord.ui import Button, Select, View

from commands.admin import require_registered_guild
from commands.enhanced_player_prop_modal import setup_enhanced_player_prop
from utils.player_prop_image_generator import PlayerPropImageGenerator

logger = logging.getLogger(__name__)


class EnhancedPlayerPropsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager

    @app_commands.command(
        name="playerprops",
        description="🏀 Place a player performance bet - points, rebounds, assists, etc.",
    )
    @require_registered_guild()
    async def playerprops(self, interaction: discord.Interaction):
        """Enhanced player props command with search and validation."""
        try:
            # Check if user is in allowed channel
            from commands.betting import is_allowed_command_channel

            if not await is_allowed_command_channel(interaction):
                return

            # Create the player props workflow view
            view = PlayerPropsWorkflowView(
                interaction, self.bot, message_to_control=None
            )
            
            await view.start_flow(interaction)

        except Exception as e:
            logger.error(f"Error in playerprops command: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


class PlayerPropsWorkflowView(View):
    """Workflow view for player props that follows the same pattern as other bet types."""
    
    def __init__(
        self,
        original_interaction: Interaction,
        bot: commands.Bot,
        message_to_control: Optional[discord.Message] = None,
    ):
        super().__init__(timeout=1800)
        self.original_interaction = original_interaction
        self.bot = bot
        self.message = message_to_control
        self.current_step = 0
        self.bet_details: Dict[str, Any] = {}
        self.preview_image_bytes: Optional[io.BytesIO] = None
        self._stopped = False

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        """Start the player props workflow."""
        try:
            self.current_step = 0
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.error(f"Error starting player props workflow: {e}")
            await interaction_that_triggered_workflow_start.followup.send(
                "❌ Error starting player props workflow. Please try again.",
                ephemeral=True,
            )

    async def go_next(self, interaction: Interaction):
        """Advance to the next step in the player props workflow."""
        if hasattr(self, "_skip_increment") and self._skip_increment:
            self._skip_increment = False
            return

        self.current_step += 1
        logger.info(f"[PLAYER PROPS WORKFLOW] go_next called for step {self.current_step}")

        if self.current_step == 1:
            # Step 1: League selection
            from commands.straight_betting import get_all_league_names, LeagueSelect, CancelButton
            leagues = get_all_league_names()
            self.clear_items()
            self.add_item(LeagueSelect(self, leagues))
            self.add_item(CancelButton(self))
            await self.edit_message(content=self.get_content(), view=self)
            return
        elif self.current_step == 2:
            # Step 2: Game selection
            from commands.straight_betting import GameSelect, CancelButton
            from data.game_utils import get_normalized_games_for_dropdown
            
            league = self.bet_details.get("league", "N/A")
            logger.info(f"[PLAYER PROPS WORKFLOW] Fetching games for league: {league}")

            try:
                games = await get_normalized_games_for_dropdown(
                    self.bot.db_manager, league
                )

                if not games:
                    await self.edit_message(
                        content=f"No games found for {league}. Please try a different league or check back later.",
                        view=None,
                    )
                    self.stop()
                    return

                self.clear_items()
                self.add_item(GameSelect(self, games))
                self.add_item(CancelButton(self))
                await self.edit_message(content=self.get_content(), view=self)

            except Exception as e:
                logger.error(f"Error fetching games: {e}")
                await self.edit_message(
                    content=f"Error fetching games for {league}. Please try again or contact support.",
                    view=None,
                )
                self.stop()
                return
        elif self.current_step == 3:
            # Step 3: Team selection
            from commands.straight_betting import TeamSelect, CancelButton
            
            home_team = self.bet_details.get("home_team_name", "")
            away_team = self.bet_details.get("away_team_name", "")
            self.clear_items()
            self.add_item(TeamSelect(self, home_team, away_team))
            self.add_item(CancelButton(self))
            await self.edit_message(
                content="Select which team's players you want to bet on:", view=self
            )
            return
        elif self.current_step == 4:
            # Step 4: Player/Prop selection (enhanced modal)
            from commands.enhanced_player_prop_modal import setup_enhanced_player_prop
            
            team_name = self.bet_details.get("team", "")
            game_id = self.bet_details.get("api_game_id", "")
            league = self.bet_details.get("league", "")
            
            # Create the enhanced player prop view
            view = await setup_enhanced_player_prop(
                self.bot, self.bot.db_manager, league, game_id, team_name
            )
            
            # Store the view reference for later use
            self.player_prop_view = view
            
            embed = discord.Embed(
                title=f"🎯 Player Props - {team_name}",
                description=f"Create player prop bets for {team_name} players.\n\n"
                f"**Features:**\n"
                f"• 🔍 Smart player search\n"
                f"• ✅ Automatic validation\n"
                f"• 📊 Performance stats\n"
                f"• 🎨 Modern bet slips",
                color=discord.Color.gold(),
            )

            embed.add_field(name="🏆 League", value=league, inline=True)
            embed.add_field(
                name="🎮 Game", 
                value=f"{self.bet_details.get('away_team_name', '')} @ {self.bet_details.get('home_team_name', '')}", 
                inline=True
            )
            embed.add_field(name="👥 Team", value=team_name, inline=True)

            await self.edit_message(embed=embed, view=view)
            return
        elif self.current_step == 5:
            # Step 5: Units selection
            from commands.straight_betting import UnitsSelect, ConfirmUnitsButton, CancelButton
            
            self.clear_items()
            self.add_item(UnitsSelect(self))
            self.add_item(ConfirmUnitsButton(self))
            self.add_item(CancelButton(self))

            # Generate preview image
            try:
                if self.preview_image_bytes:
                    self.preview_image_bytes.close()
                    self.preview_image_bytes = None

                # Get player prop details from the enhanced modal
                player_name = self.bet_details.get("player_name", "Player")
                team_name = self.bet_details.get("team", "Team")
                league = self.bet_details.get("league", "N/A")
                line = self.bet_details.get("line", "N/A")
                bet_id = str(self.bet_details.get("preview_bet_serial", ""))
                timestamp = datetime.now(timezone.utc)

                generator = PlayerPropImageGenerator(
                    guild_id=self.original_interaction.guild_id
                )
                bet_slip_image_bytes = generator.generate_player_prop_bet_image(
                    player_name=player_name,
                    team_name=team_name,
                    league=league,
                    line=line,
                    units=1.0,
                    output_path=None,
                    bet_id=bet_id,
                    timestamp=timestamp,
                    guild_id=str(self.original_interaction.guild_id),
                    odds=0.0,  # Will be set later
                    units_display_mode="auto",
                    display_as_risk=False,
                )
                if bet_slip_image_bytes:
                    self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                    self.preview_image_bytes.seek(0)
                else:
                    self.preview_image_bytes = None
            except Exception as e:
                logger.exception(f"Error generating preview image: {e}")
                self.preview_image_bytes = None

            file_to_send = None
            if self.preview_image_bytes:
                self.preview_image_bytes.seek(0)
                file_to_send = File(
                    self.preview_image_bytes, filename="player_prop_preview.png"
                )

            await self.edit_message(
                content=self.get_content(), view=self, file=file_to_send
            )
            return
        elif self.current_step == 6:
            # Step 6: Channel selection
            from commands.straight_betting import ChannelSelect, CancelButton
            
            try:
                # Fetch allowed embed channels from guild settings
                allowed_channels = []
                guild_settings = await self.bot.db_manager.fetch_one(
                    "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
                    (str(self.original_interaction.guild_id),),
                )
                if guild_settings:
                    for channel_id in (
                        guild_settings.get("embed_channel_1"),
                        guild_settings.get("embed_channel_2"),
                    ):
                        if channel_id:
                            try:
                                cid = int(channel_id)
                                channel = self.bot.get_channel(
                                    cid
                                ) or await self.bot.fetch_channel(cid)
                                if (
                                    isinstance(channel, discord.TextChannel)
                                    and channel.permissions_for(
                                        self.original_interaction.guild.me
                                    ).send_messages
                                ):
                                    if channel not in allowed_channels:
                                        allowed_channels.append(channel)
                            except Exception as e:
                                logger.error(
                                    f"Error processing channel {channel_id}: {e}"
                                )
                if not allowed_channels:
                    await self.edit_message(
                        content="❌ No valid embed channels configured. Please contact an admin.",
                        view=None,
                    )
                    self.stop()
                    return
                self.clear_items()
                self.add_item(ChannelSelect(self, allowed_channels))
                self.add_item(CancelButton(self))
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(
                        self.preview_image_bytes, filename="player_prop_preview.png"
                    )
                await self.edit_message(
                    content=self.get_content(), view=self, file=file_to_send
                )
            except Exception as e:
                logger.error(f"Error in channel selection: {e}")
                await self.edit_message(
                    content="❌ Error loading channels. Please try again.",
                    view=None,
                )
                self.stop()
            return
        else:
            logger.warning(f"Unknown step: {self.current_step}")
            await self.edit_message(
                content="❌ Unknown workflow step. Please restart.", view=None
            )
            self.stop()

    async def edit_message(
        self,
        content: Optional[str] = None,
        view: Optional[View] = None,
        embed: Optional[discord.Embed] = None,
        file: Optional[File] = None,
    ):
        """Edit the message with new content."""
        try:
            if self.message:
                await self.message.edit(content=content, view=view, embed=embed, files=[file] if file else None)
            else:
                # If no message to control, send a new one
                if not hasattr(self, '_initial_message_sent'):
                    await self.original_interaction.response.send_message(
                        content=content, view=view, embed=embed, file=file, ephemeral=True
                    )
                    self._initial_message_sent = True
                else:
                    await self.original_interaction.followup.send(
                        content=content, view=view, embed=embed, file=file, ephemeral=True
                    )
        except discord.HTTPException as e:
            logger.error(f"HTTP error editing message: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error editing message: {e}")

    def get_content(self, step_num: Optional[int] = None):
        """Get content for the current step."""
        if step_num is None:
            step_num = self.current_step
        if step_num == 1:
            return "Welcome to the Player Props Workflow! Please select your desired league from the list."
        if step_num == 2:
            league = self.bet_details.get("league", "N/A")
            return f"Great choice! Now, please select a game from **{league}**."
        if step_num == 3:
            league = self.bet_details.get("league", "N/A")
            return f"Select which team's players you want to bet on from the **{league}** game."
        if step_num == 4:
            team = self.bet_details.get("team", "N/A")
            return f"Create player prop bets for **{team}** players using the enhanced search and validation tools."
        if step_num == 5:
            preview_info = (
                "(Preview below)"
                if self.preview_image_bytes
                else "(Generating preview...)"
            )
            return f"**Step {step_num}**: Select Units for your player prop bet. {preview_info}"
        if step_num == 6:
            units = self.bet_details.get("units", "N/A")
            preview_info = (
                "(Preview below)"
                if self.preview_image_bytes
                else "(Preview image failed)"
            )
            return f"**Step {step_num}**: 🔒 Units: `{units}` 🔒 {preview_info}. Select Channel to post your player prop bet."
        return "Processing your player prop bet request..."

    async def _handle_units_selection(self, interaction: discord.Interaction, units: float):
        """Handle units selection for player props."""
        self.bet_details["units"] = units
        self.bet_details["units_str"] = str(units)

        # Get guild settings for units display mode
        guild_settings = await self.bot.db_manager.fetch_one(
            "SELECT units_display_mode FROM guild_settings WHERE guild_id = %s",
            (str(self.original_interaction.guild_id),),
        )
        units_display_mode = (
            guild_settings.get("units_display_mode", "auto")
            if guild_settings
            else "auto"
        )
        display_as_risk = self.bet_details.get("display_as_risk")

        try:
            player_name = self.bet_details.get("player_name", "Player")
            team_name = self.bet_details.get("team", "Team")
            league = self.bet_details.get("league", "N/A")
            line = self.bet_details.get("line", "N/A")
            bet_id = str(self.bet_details.get("preview_bet_serial", ""))
            timestamp = datetime.now(timezone.utc)

            if self.preview_image_bytes:
                self.preview_image_bytes.close()
                self.preview_image_bytes = None

            generator = PlayerPropImageGenerator(
                guild_id=self.original_interaction.guild_id
            )
            bet_slip_image_bytes = generator.generate_player_prop_bet_image(
                player_name=player_name,
                team_name=team_name,
                league=league,
                line=line,
                units=units,
                output_path=None,
                bet_id=bet_id,
                timestamp=timestamp,
                guild_id=str(self.original_interaction.guild_id),
                odds=0.0,  # Will be set later
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )
            if bet_slip_image_bytes:
                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                self.preview_image_bytes.seek(0)
            else:
                self.preview_image_bytes = None
        except Exception as e:
            logger.exception(f"Error generating player prop preview image: {e}")
            self.preview_image_bytes = None

        self.clear_items()
        from commands.straight_betting import UnitsSelect, ConfirmUnitsButton, CancelButton
        self.add_item(UnitsSelect(self))
        self.add_item(ConfirmUnitsButton(self))
        self.add_item(CancelButton(self))
        
        file_to_send = None
        if self.preview_image_bytes:
            self.preview_image_bytes.seek(0)
            file_to_send = File(
                self.preview_image_bytes, filename="player_prop_preview_units.png"
            )
        await self.edit_message(
            content=self.get_content(), view=self, file=file_to_send
        )

    def stop(self):
        """Stop the workflow."""
        self._stopped = True
        super().stop()

    async def on_timeout(self):
        """Handle timeout."""
        logger.info(
            f"PlayerPropsWorkflowView timed out for user {self.original_interaction.user.id}"
        )
        await self.edit_message(
            content="⏰ Player props workflow timed out due to inactivity. Please start a new bet.",
            view=None,
        )
        self.stop()


# Keep the existing classes for backward compatibility
class LeagueSelectionView(View):
    """View for league selection in player props."""
    
    def __init__(self, bot: commands.Bot, db_manager):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager

    @discord.ui.button(label="NBA", style=discord.ButtonStyle.primary, emoji="🏀")
    async def nba_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_league(interaction, "NBA")

    @discord.ui.button(label="NFL", style=discord.ButtonStyle.primary, emoji="🏈")
    async def nfl_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_league(interaction, "NFL")

    @discord.ui.button(label="MLB", style=discord.ButtonStyle.primary, emoji="⚾")
    async def mlb_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_league(interaction, "MLB")

    @discord.ui.button(label="NHL", style=discord.ButtonStyle.primary, emoji="🏒")
    async def nhl_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_league(interaction, "NHL")

    async def select_league(self, interaction: discord.Interaction, league: str):
        """Handle league selection."""
        try:
            # Create the player props workflow view
            view = PlayerPropsWorkflowView(
                interaction, self.bot, message_to_control=None
            )
            
            # Set the league
            view.bet_details["league"] = league
            
            await view.start_flow(interaction)

        except Exception as e:
            logger.error(f"Error selecting league {league}: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


class GameSelectionView(View):
    """View for game selection in player props."""
    
    def __init__(self, bot: commands.Bot, db_manager, league: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league

    async def setup_games(self, games: List[Dict]):
        """Setup game selection buttons."""
        for i, game in enumerate(games[:10]):  # Limit to 10 games
            button = Button(
                label=f"{game['away_team']} @ {game['home_team']}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"game_{i}"
            )
            
            async def game_callback(interaction: discord.Interaction, game_data=game):
                await self.select_game(interaction, game_data)
            
            button.callback = game_callback
            self.add_item(button)

    async def select_game(self, interaction: discord.Interaction, game: Dict):
        """Handle game selection."""
        try:
            # Create the player props workflow view
            view = PlayerPropsWorkflowView(
                interaction, self.bot, message_to_control=None
            )
            
            # Set the game details
            view.bet_details.update({
                "league": self.league,
                "api_game_id": game["api_game_id"],
                "home_team_name": game["home_team"],
                "away_team_name": game["away_team"],
                "game_start_time": game["start_time"]
            })
            
            await view.start_flow(interaction)

        except Exception as e:
            logger.error(f"Error selecting game: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


class TeamSelectionView(View):
    """View for team selection in player props."""
    
    def __init__(self, bot: commands.Bot, db_manager, league: str, game_id: str, home_team: str, away_team: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team

    @discord.ui.button(label="Home Team", style=discord.ButtonStyle.primary)
    async def home_team_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_team_selection(interaction, self.home_team)

    @discord.ui.button(label="Away Team", style=discord.ButtonStyle.primary)
    async def away_team_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_team_selection(interaction, self.away_team)

    async def handle_team_selection(self, interaction: discord.Interaction, team_name: str):
        """Handle team selection and show enhanced player prop modal."""
        try:
            # Create the enhanced player prop view
            view = await setup_enhanced_player_prop(
                self.bot, self.db_manager, self.league, self.game_id, team_name
            )

            embed = discord.Embed(
                title=f"🎯 Player Props - {team_name}",
                description=f"Create player prop bets for {team_name} players.\n\n"
                f"**Features:**\n"
                f"• 🔍 Smart player search\n"
                f"• ✅ Automatic validation\n"
                f"• 📊 Performance stats\n"
                f"• 🎨 Modern bet slips",
                color=discord.Color.gold(),
            )

            embed.add_field(name="🏆 League", value=self.league, inline=True)
            embed.add_field(
                name="🎮 Game", value=f"{self.away_team} @ {self.home_team}", inline=True
            )
            embed.add_field(name="👥 Team", value=team_name, inline=True)

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error handling team selection: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup the enhanced player props cog."""
    await bot.add_cog(EnhancedPlayerPropsCog(bot))
    logger.info("Enhanced Player Props cog loaded successfully")
