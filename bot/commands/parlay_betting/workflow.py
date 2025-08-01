"""Main workflow view for parlay betting functionality."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import discord
from discord import ButtonStyle, File, Interaction, Message, TextChannel
from discord.ext import commands
from discord.ui import View

from bot.commands.admin import require_registered_guild
from bot.data.db_manager import get_db_manager
from bot.utils.errors import ValidationError
from bot.utils.parlay_bet_image_generator import ParlayBetImageGenerator

from .constants import DEFAULT_UNITS
from .modals import BetDetailsModal, OddsModal, TotalOddsModal
from .ui_components import (
    AddAnotherLegButton,
    CancelButton,
    ChannelSelect,
    ConfirmButton,
    FinalConfirmButton,
    FinalizeParlayButton,
    LeagueSelect,
    LineTypeSelect,
    ParlayGameSelect,
    SportSelect,
    TeamSelect,
    UnitsSelect,
)
from .utils import (
    calculate_parlay_odds,
    format_odds_with_sign,
    generate_parlay_summary_text,
    get_leagues_for_sport,
    get_sport_categories,
    validate_bet_details,
)

logger = logging.getLogger(__name__)


class ParlayBetWorkflowView(View):
    """Main workflow view for creating parlay bets."""

    def __init__(
        self,
        original_interaction: Interaction,
        bot: commands.Bot,
        message_to_control: Optional[Message] = None,
    ):
        super().__init__(timeout=300)  # 5 minute timeout

        self.original_interaction = original_interaction
        self.bot = bot
        self.message_to_control = message_to_control

        # Workflow state
        self.current_step = "sport_selection"
        self.legs = []
        self.current_leg = {}

        # Selected values
        self.selected_sport = None
        self.selected_league = None
        self.selected_line_type = None
        self.selected_game = None
        self.selected_team = None
        self.selected_team_type = None
        self.selected_channel_id = None
        self.current_leg_odds = None

        # Bet details
        self.total_odds = None
        self.units = DEFAULT_UNITS
        self.parlay_notes = ""

        # UI state
        self.league_page = 0

        # Generate unique ID for this workflow
        self.workflow_id = str(uuid.uuid4())

    async def get_bet_slip_generator(self) -> ParlayBetImageGenerator:
        """Get the bet slip image generator."""
        return ParlayBetImageGenerator()

    async def add_leg(
        self, modal_interaction: Interaction, leg_details: Dict[str, Any], file=None
    ):
        """Add a leg to the parlay."""
        try:
            # Validate leg details
            if not validate_bet_details(leg_details):
                await modal_interaction.response.send_message(
                    "❌ Invalid leg details. Please try again.", ephemeral=True
                )
                return

            # Add sport and league info if not present
            if "sport" not in leg_details:
                leg_details["sport"] = self.selected_sport
            if "league" not in leg_details:
                leg_details["league"] = self.selected_league

            # Add game info if available
            if self.selected_game:
                leg_details["game"] = self.selected_game

            # Add leg number
            leg_details["leg_number"] = len(self.legs) + 1

            # Add to legs list
            self.legs.append(leg_details)

            # Reset current leg
            self.current_leg = {}

            await modal_interaction.response.send_message(
                f"✅ Leg {leg_details['leg_number']} added successfully!",
                ephemeral=True,
            )

            # Show parlay summary
            await self._show_parlay_summary(modal_interaction)

        except Exception as e:
            logger.error(f"Error adding leg: {e}")
            await modal_interaction.response.send_message(
                "❌ Error adding leg. Please try again.", ephemeral=True
            )

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        """Start the parlay betting workflow."""
        try:
            # Get available sports
            sports = get_sport_categories()

            # Create sport selection view
            view = View(timeout=300)
            view.add_item(SportSelect(self, sports))
            view.add_item(CancelButton(self))

            embed = discord.Embed(
                title="🏈 Parlay Bet Creation",
                description="Select a sport to begin creating your parlay bet.",
                color=discord.Color.blue(),
            )

            await interaction_that_triggered_workflow_start.response.edit_message(
                embed=embed, view=view
            )

        except Exception as e:
            logger.error(f"Error starting parlay flow: {e}")
            await interaction_that_triggered_workflow_start.response.send_message(
                "❌ Error starting parlay creation. Please try again.", ephemeral=True
            )

    async def go_next(self, interaction: Interaction):
        """Progress to the next step in the workflow."""
        try:
            if self.current_step == "sport_selection":
                await self._handle_sport_selection(interaction)
            elif self.current_step == "league_selection":
                await self._handle_league_selection(interaction)
            elif self.current_step == "line_type_selection":
                await self._handle_line_type_selection(interaction)
            elif self.current_step == "game_selection":
                await self._handle_game_selection(interaction)
            elif self.current_step == "team_selection":
                await self._handle_team_selection(interaction)
            elif self.current_step == "odds_entry":
                await self._handle_odds_entry(interaction)
            elif self.current_step == "bet_details":
                await self._handle_bet_details(interaction)
            elif self.current_step == "parlay_summary":
                await self._handle_parlay_summary(interaction)
            elif self.current_step == "units_selection":
                await self._handle_units_selection(interaction)
            elif self.current_step == "channel_selection":
                await self._handle_channel_selection(interaction)
            elif self.current_step == "final_confirmation":
                await self._handle_final_confirmation(interaction)
            else:
                await interaction.response.send_message(
                    "❌ Unknown workflow step.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in workflow step {self.current_step}: {e}")
            await interaction.response.send_message(
                "❌ Error in workflow. Please try again.", ephemeral=True
            )

    async def _handle_sport_selection(self, interaction: Interaction):
        """Handle sport selection."""
        # Get leagues for selected sport
        leagues = get_leagues_for_sport(self.selected_sport)

        # Create league selection view
        view = View(timeout=300)
        view.add_item(LeagueSelect(self, leagues, self.league_page))
        view.add_item(CancelButton(self))

        embed = discord.Embed(
            title=f"🏈 {self.selected_sport} - League Selection",
            description="Select a league for your parlay bet.",
            color=discord.Color.blue(),
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "league_selection"

    async def _handle_league_selection(self, interaction: Interaction):
        """Handle league selection."""
        # Create line type selection view
        view = View(timeout=300)
        view.add_item(LineTypeSelect(self))
        view.add_item(CancelButton(self))

        embed = discord.Embed(
            title=f"🏈 {self.selected_sport} - {self.selected_league}",
            description="Select the type of bet for this leg.",
            color=discord.Color.blue(),
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "line_type_selection"

    async def _handle_line_type_selection(self, interaction: Interaction):
        """Handle line type selection."""
        # Get games for the selected league
        try:
            db_manager = get_db_manager()
            games = await db_manager.get_normalized_games_for_dropdown(
                self.selected_league
            )

            if not games:
                await interaction.response.send_message(
                    "❌ No games available for the selected league.", ephemeral=True
                )
                return

            # Create game selection view
            view = View(timeout=300)
            view.add_item(ParlayGameSelect(self, games))
            view.add_item(CancelButton(self))

            embed = discord.Embed(
                title=f"🏈 {self.selected_sport} - {self.selected_league}",
                description="Select a game for this leg.",
                color=discord.Color.blue(),
            )

            await interaction.response.edit_message(embed=embed, view=view)
            self.current_step = "game_selection"

        except Exception as e:
            logger.error(f"Error getting games: {e}")
            await interaction.response.send_message(
                "❌ Error loading games. Please try again.", ephemeral=True
            )

    async def _handle_game_selection(self, interaction: Interaction):
        """Handle game selection."""
        # Check if manual entry was selected
        if self.selected_game.get("is_manual", False):
            # For manual entry, show bet details modal directly
            modal = BetDetailsModal(
                line_type=self.selected_line_type,
                leg_number=len(self.legs) + 1,
                is_manual=True,
            )
            await interaction.response.send_modal(modal)
            self.current_step = "bet_details"
            return

        home_team = self.selected_game.get("home_team", "Unknown")
        away_team = self.selected_game.get("away_team", "Unknown")

        # Create team selection view
        view = View(timeout=300)
        view.add_item(TeamSelect(self, home_team, away_team))
        view.add_item(CancelButton(self))

        embed = discord.Embed(
            title=f"🏈 {away_team} @ {home_team}",
            description="Select the team for your bet.",
            color=discord.Color.blue(),
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "team_selection"

    async def _handle_team_selection(self, interaction: Interaction):
        """Handle team selection."""
        # For now, proceed to odds entry
        # In a full implementation, this might involve more complex logic
        self.current_step = "odds_entry"

        # Show odds entry modal
        modal = OddsModal(self)
        await interaction.response.send_modal(modal)

    async def _handle_odds_entry(self, interaction: Interaction):
        """Handle odds entry."""
        # Create bet details modal
        modal = BetDetailsModal(
            line_type=self.selected_line_type, leg_number=len(self.legs) + 1
        )
        await interaction.response.send_modal(modal)
        self.current_step = "bet_details"

    async def _handle_bet_details(self, interaction: Interaction):
        """Handle bet details entry."""
        # This would typically be handled by the modal submission
        # For now, we'll proceed to parlay summary
        await self._show_parlay_summary(interaction)

    async def _show_parlay_summary(self, interaction: Interaction):
        """Show parlay summary."""
        if not self.legs:
            await interaction.response.send_message(
                "❌ No legs added to parlay.", ephemeral=True
            )
            return

        # Create parlay summary view
        view = View(timeout=300)
        view.add_item(AddAnotherLegButton(self))
        view.add_item(FinalizeParlayButton(self))
        view.add_item(CancelButton(self))

        summary_text = generate_parlay_summary_text(
            self.legs, self.total_odds or 0, self.units
        )

        embed = discord.Embed(
            title="🏈 Parlay Summary",
            description=summary_text,
            color=discord.Color.green(),
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "parlay_summary"

    async def _handle_parlay_summary(self, interaction: Interaction):
        """Handle parlay summary."""
        # Show total odds entry modal
        modal = TotalOddsModal(self.workflow_id)
        await interaction.response.send_modal(modal)
        self.current_step = "units_selection"

    async def _handle_units_selection(self, interaction: Interaction, units: float = None):
        """Handle units selection."""
        if units is not None:
            # Update units and generate preview
            self.units = units
            
            # Generate preview image with 1 unit
            await self._generate_parlay_preview(interaction)
            
            # Create units selection view
            view = View(timeout=300)
            view.add_item(UnitsSelect(self))
            view.add_item(CancelButton(self))

            embed = discord.Embed(
                title="🏈 Units Selection",
                description="Select the number of units for this parlay.",
                color=discord.Color.blue(),
            )

            await interaction.response.edit_message(embed=embed, view=view)
        else:
            # Initial units selection setup
            view = View(timeout=300)
            view.add_item(UnitsSelect(self))
            view.add_item(CancelButton(self))

            embed = discord.Embed(
                title="🏈 Units Selection",
                description="Select the number of units for this parlay.",
                color=discord.Color.blue(),
            )

            await interaction.response.edit_message(embed=embed, view=view)

    async def _handle_channel_selection(self, interaction: Interaction):
        """Handle channel selection."""
        # Create channel selection view
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "❌ Error: Guild not found.", ephemeral=True
            )
            return

        # Get allowed embed channels from guild settings
        allowed_channels = []
        try:
            guild_settings = await self.bot.db_manager.fetch_one(
                "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
                (str(guild.id),),
            )
            if guild_settings:
                for channel_id in (
                    guild_settings.get("embed_channel_1"),
                    guild_settings.get("embed_channel_2"),
                ):
                    if channel_id:
                        try:
                            cid = int(channel_id)
                            channel = self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)
                            if (
                                isinstance(channel, discord.TextChannel)
                                and channel.permissions_for(guild.me).send_messages
                            ):
                                if channel not in allowed_channels:
                                    allowed_channels.append(channel)
                        except Exception as e:
                            logger.error(f"Error processing channel {channel_id}: {e}")
        except Exception as e:
            logger.error(f"Error fetching guild settings: {e}")

        if not allowed_channels:
            await interaction.response.edit_message(
                content="❌ No valid embed channels configured. Please contact an admin.",
                view=None,
            )
            return

        view = View(timeout=300)
        view.add_item(ChannelSelect(self, allowed_channels))
        view.add_item(CancelButton(self))

        embed = discord.Embed(
            title="🏈 Channel Selection",
            description="Select the channel to post your parlay bet.",
            color=discord.Color.blue(),
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "channel_selection"

    async def _handle_channel_selection(self, interaction: Interaction):
        """Handle channel selection."""
        # Create final confirmation view
        view = View(timeout=300)
        view.add_item(FinalConfirmButton(self))
        view.add_item(CancelButton(self))

        embed = discord.Embed(
            title="🏈 Final Confirmation",
            description="Review your parlay bet and confirm submission.",
            color=discord.Color.gold(),
        )

        # Add bet details to embed
        summary_text = generate_parlay_summary_text(
            self.legs, self.total_odds or 0, self.units
        )
        embed.add_field(name="Bet Summary", value=summary_text, inline=False)

        await interaction.response.edit_message(embed=embed, view=view)
        self.current_step = "final_confirmation"

    async def _handle_final_confirmation(self, interaction: Interaction):
        """Handle final confirmation."""
        await self.submit_bet(interaction)

    async def submit_bet(self, interaction: Interaction):
        """Submit the parlay bet."""
        try:
            # Generate bet slip image
            generator = await self.get_bet_slip_generator()

            # Create bet slip data
            bet_data = {
                "legs": self.legs,
                "total_odds": self.total_odds,
                "units": self.units,
                "notes": self.parlay_notes,
                "user": interaction.user,
                "timestamp": datetime.now(timezone.utc),
            }

            # Generate image
            image_bytes = generator.generate_image(
                legs=bet_data["legs"],
                output_path=None,
                total_odds=bet_data["total_odds"],
                units=bet_data["units"],
                bet_id=bet_data.get("bet_id"),
                bet_datetime=bet_data["timestamp"],
                finalized=True
            )

            if image_bytes:
                # Convert bytes to BytesIO for Discord File
                import io
                image_buffer = io.BytesIO(image_bytes)
                image_buffer.seek(0)
                
                # Create file
                file = File(image_buffer, filename=f"parlay_bet_{self.workflow_id}.png")

            # Post to selected channel
            if image_bytes and self.selected_channel_id:
                channel = self.bot.get_channel(self.selected_channel_id)
                if channel:
                    await channel.send(file=file)

                    await interaction.response.send_message(
                        "✅ Parlay bet submitted successfully!", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Error: Could not find selected channel.", ephemeral=True
                    )
            elif not image_bytes:
                await interaction.response.send_message(
                    "❌ Error: Could not generate bet slip image.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Error: No channel selected.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error submitting bet: {e}")
            await interaction.response.send_message(
                "❌ Error submitting bet. Please try again.", ephemeral=True
            )

    async def update_league_page(self, interaction, page):
        """Update the league selection page."""
        self.league_page = page
        await self._handle_sport_selection(interaction)

    async def _generate_parlay_preview(self, interaction: Interaction):
        """Generate parlay preview image with 1 unit and send as ephemeral message."""
        try:
            # Always use 1 unit for preview
            preview_units = 1.0
            
            # Generate preview image
            generator = await self.get_bet_slip_generator()
            
            # Create bet slip data for preview
            bet_data = {
                "legs": self.legs,
                "total_odds": self.total_odds,
                "units": preview_units,
                "notes": self.parlay_notes,
                "user": interaction.user,
                "timestamp": datetime.now(timezone.utc),
            }
            
            # Generate image
            image_bytes = generator.generate_parlay_preview(
                legs=bet_data["legs"],
                total_odds=bet_data["total_odds"],
                units=bet_data["units"]
            )
            
            if image_bytes:
                # Convert bytes to BytesIO for Discord File
                import io
                image_buffer = io.BytesIO(image_bytes)
                image_buffer.seek(0)
                
                # Create file
                file = File(image_buffer, filename=f"parlay_preview_{self.workflow_id}.png")
                
                # Send ephemeral message with preview
                await interaction.followup.send(
                    "**Preview of your parlay bet with 1 unit:**",
                    file=file,
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Error generating preview image.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error generating parlay preview: {e}")
            await interaction.followup.send(
                "❌ Error generating preview image.",
                ephemeral=True
            )

    async def cleanup(self):
        """Clean up the workflow."""
        # Cleanup logic here
        pass

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Check if interaction is valid for this view."""
        # Add any validation logic here
        return True
