# REV 1.0.0 - Enhanced straight betting workflow with improved game selection and bet slip generation
# betting-bot/commands/straight_betting.py

"""Straight betting workflow for placing single bets."""

import discord
from discord import (
    ButtonStyle,
    Interaction,
    SelectOption,
    TextChannel,
    File,
    Embed,
    Webhook,
    Message,
)
from discord.ui import View, Select, Modal, TextInput, Button
import logging
from typing import Optional, List, Dict, Union, Any
from datetime import datetime, timezone, timedelta
import io
import os
from discord.ext import commands
from io import BytesIO
import traceback
import json
import aiohttp
import pytz
import requests
from database import get_database_connection  # Ensure this is defined in your project

from data.game_utils import get_normalized_games_for_dropdown

from utils.errors import (
    BetServiceError,
    ValidationError,
    GameNotFoundError,
)
from utils.image_generator import BetSlipGenerator
from utils.modals import StraightBetDetailsModal
from config.leagues import LEAGUE_CONFIG
from betting_bot.api.sports_api import SportsAPI

logger = logging.getLogger(__name__)

# League name normalization mapping (used for display)
LEAGUE_FILE_KEY_MAP = {
    "La Liga": "LaLiga",
    "Serie A": "SerieA",
    "Ligue 1": "Ligue1",
    "EPL": "EPL",
    "Bundesliga": "Bundesliga",
    "MLS": "MLS",
    "NBA": "NBA",
    "WNBA": "WNBA",
    "MLB": "MLB",
    "NHL": "NHL",
    "NFL": "NFL",
    "NCAA": [
        "NCAAF",
        "NCAAB",
        "NCAABM",
        "NCAABW",
        "NCAAFBS",
        "NCAAVB",
        "NCAAFB",
        "NCAAWBB",
        "NCAAWVB",
        "NCAAWFB",
    ],
    "NPB": "NPB",
    "KBO": "KBO",
    "KHL": "KHL",
    "PDC": "PDC",
    "BDO": "BDO",
    "WDF": "WDF",
    "Premier League Darts": "PremierLeagueDarts",
    "World Matchplay": "WorldMatchplay",
    "World Grand Prix": "WorldGrandPrix",
    "UK Open": "UKOpen",
    "Grand Slam": "GrandSlam",
    "Players Championship": "PlayersChampionship",
    "European Championship": "EuropeanChampionship",
    "Masters": "Masters",
    "Champions League": "ChampionsLeague",
    "TENNIS": ["WTP", "ATP", "WTA"],
    "ESPORTS": ["CSGO", "VALORANT", "LOL", "DOTA 2", "PUBG", "COD"],
    "OTHER_SPORTS": ["OTHER_SPORTS"],
}


def get_league_file_key(league_name):
    key = LEAGUE_FILE_KEY_MAP.get(league_name, league_name.replace(" ", ""))
    if isinstance(key, list):
        return key[0]
    return key


class LeagueSelect(Select):
    def __init__(self, parent_view: View, leagues: List[str]):
        self.parent_view = parent_view
        seen = set()
        unique_leagues = []
        for league in leagues:
            norm = league.replace(" ", "_").upper()
            if norm not in seen:
                seen.add(norm)
                unique_leagues.append(league)
        options = [
            SelectOption(label=league, value=league)
            for league in unique_leagues[:24]
        ]
        options.append(SelectOption(label="Other", value="OTHER"))
        super().__init__(
            placeholder="Select League...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"straight_league_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        self.parent_view.bet_details["league"] = self.values[0]
        logger.debug(f"League selected: {self.values[0]} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class LineTypeSelect(Select):
    def __init__(self, parent_view: View):
        self.parent_view = parent_view
        options = [
            SelectOption(
                label="Game Line",
                value="game_line",
                description="Moneyline or game over/under",
            ),
            SelectOption(
                label="Player Prop",
                value="player_prop",
                description="Bet on player performance",
            ),
        ]
        super().__init__(
            placeholder="Select Line Type...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        self.parent_view.bet_details["line_type"] = self.values[0]
        logger.debug(f"Line Type selected: {self.values[0]} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class GameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict]):
        self.parent_view = parent_view
        options = []
        # Only include games whose status does NOT contain 'finished' (case-insensitive)
        active_games = []
        for game in games:
            if game.get("api_game_id") == "manual":
                continue  # Skip manual entry from games list as we'll add it separately
            status = str(game.get("status", "")).lower()
            if "finished" in status:
                continue
            active_games.append(game)
        # Limit to 24 active games (so Manual Entry is always present and total is 25)
        for game in active_games[:24]:
            game_api_id = game.get("api_game_id")
            home_team = game.get("home_team_name", "Unknown")
            away_team = game.get("away_team_name", "Unknown")
            start_time = game.get("start_time", "")
            if isinstance(start_time, str) and len(start_time) > 16:
                start_time = start_time[:16]
            label = f"{home_team} vs {away_team}"
            if start_time:
                label += f" ({start_time})"
            if game_api_id is None:
                logger.warning(f"Game missing 'api_game_id': {game}")
                continue
            options.append(SelectOption(label=label, value=str(game_api_id)))
        # Always add Manual Entry option at the end
        options.append(SelectOption(label="Manual Entry", value="manual"))
        super().__init__(
            placeholder="Select Game (or Manual Entry)...",
            options=options,
            min_values=1,
            max_values=1,
            disabled=False  # Never disable since Manual Entry is always available
        )
        logger.debug(f"Dropdown options: {options}")

    async def callback(self, interaction: Interaction):
        selected_api_game_id = self.values[0]
        self.parent_view.bet_details["api_game_id"] = selected_api_game_id

        logger.debug(f"Selected api_game_id: {selected_api_game_id} by user {interaction.user.id}")

        if selected_api_game_id == "manual":
            # Handle manual entry
            self.parent_view.bet_details["home_team_name"] = "Manual Entry"
            self.parent_view.bet_details["away_team_name"] = "Manual Entry"
            self.parent_view.bet_details["is_manual"] = True
        else:
            # Handle game selection
            game = next(
                (g for g in self.parent_view.games if str(g.get("api_game_id")) == selected_api_game_id),
                None,
            )
            if game:
                self.parent_view.bet_details["home_team_name"] = game.get("home_team_name", "Unknown")
                self.parent_view.bet_details["away_team_name"] = game.get("away_team_name", "Unknown")
                self.parent_view.bet_details["is_manual"] = False

        logger.debug(f"Game selected: {selected_api_game_id} by user {interaction.user.id}")
        self.disabled = False
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class CancelButton(Button):
    def __init__(self, parent_view: View):
        super().__init__(
            style=ButtonStyle.red,
            label="Cancel",
            custom_id=f"straight_cancel_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Cancel button clicked by user {interaction.user.id}")
        self.disabled = True
        for item in self.parent_view.children:
            item.disabled = True
        bet_serial = self.parent_view.bet_details.get("bet_serial")
        if bet_serial:
            try:
                bet_status = await self.parent_view.bot.db_manager.fetch_one(
                    "SELECT confirmed FROM bets WHERE bet_serial = %s",
                    (bet_serial,)
                )
                if bet_status and bet_status["confirmed"] == 1:
                    await interaction.response.edit_message(
                        content=f"Bet `{bet_serial}` is already confirmed and cannot be cancelled.", view=None
                    )
                else:
                    if hasattr(self.parent_view.bot, "bet_service"):
                        await self.parent_view.bot.bet_service.delete_bet(bet_serial)
                    await interaction.response.edit_message(content=f"Bet `{bet_serial}` cancelled.", view=None)
            except Exception as e:
                logger.error(f"Failed to delete bet {bet_serial}: {e}")
                await interaction.response.edit_message(
                    content=f"Bet cancellation failed for `{bet_serial}`.", view=None
                )
        else:
            await interaction.response.edit_message(content="Bet workflow cancelled.", view=None)
        self.parent_view.stop()


class TeamSelect(Select):
    def __init__(self, parent_view: View, home_team: str, away_team: str):
        self.parent_view = parent_view
        options = [
            SelectOption(label=home_team, value=home_team),
            SelectOption(label=away_team, value=away_team),
        ]
        super().__init__(
            placeholder="Which team are you selecting?",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        selected_team = self.values[0]
        home_team = self.parent_view.bet_details.get("home_team_name", "")
        away_team = self.parent_view.bet_details.get("away_team_name", "")
        if selected_team == home_team:
            opponent = away_team
        else:
            opponent = home_team
        self.parent_view.bet_details["team"] = selected_team
        self.parent_view.bet_details["opponent"] = opponent
        line_type = self.parent_view.bet_details.get("line_type", "game_line")
        modal = StraightBetDetailsModal(
            line_type=line_type,
            selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
            bet_details_from_view=self.parent_view.bet_details,
            is_manual=False,
        )
        modal.view_ref = self.parent_view
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)
            await self.parent_view.edit_message(
                content="Please fill in the bet details in the popup form.", view=self.parent_view
            )
        else:
            logger.error("Tried to send modal, but interaction already responded to.")
            await interaction.followup.send(
                "❌ Error: Could not open modal. Please try again.", ephemeral=True
            )
            self.parent_view.stop()
            return


class BetDetailsModal(Modal):
    def __init__(self, line_type: str, is_manual: bool = False):
        super().__init__(title="Enter Bet Details")
        self.line_type = line_type
        self.is_manual = is_manual
        self.team = TextInput(
            label="Team Bet On/Player's Team",
            required=True,
            max_length=100,
            placeholder="Enter team name",
        )
        self.add_item(self.team)
        if self.is_manual:
            self.opponent = TextInput(
                label="Opponent",
                required=True,
                max_length=100,
                placeholder="Enter opponent name",
            )
            self.add_item(self.opponent)
        if line_type == "player_prop":
            self.player_line = TextInput(
                label="Player - Line (e.g., Name O/U Points)",
                required=True,
                max_length=100,
                placeholder="E.g., Connor McDavid - Shots Over 3.5",
            )
            self.add_item(self.player_line)
        else:
            self.line = TextInput(
                label="Line (e.g., Moneyline, Spread -7.5)",
                required=True,
                max_length=100,
                placeholder="E.g., Moneyline, Spread -7.5, Total Over 6.5",
            )
            self.add_item(self.line)
        self.odds = TextInput(
            label="Odds",
            required=True,
            max_length=10,
            placeholder="Enter American odds (e.g., -110, +200)",
        )
        self.add_item(self.odds)

    async def on_submit(self, interaction: Interaction):
        logger.debug(f"BetDetailsModal submitted by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            team_input = self.team.value.strip()
            if self.is_manual:
                opponent_input = (
                    self.opponent.value.strip() if hasattr(self, "opponent") else "N/A"
                )
            else:
                opponent_input = self.view.bet_details.get("away_team_name", "N/A")
                if team_input.lower() == self.view.bet_details.get("away_team_name", "").lower():
                    opponent_input = self.view.bet_details.get("home_team_name", "N/A")

            line_value = (
                self.player_line.value.strip()
                if self.line_type == "player_prop"
                else self.line.value.strip()
            )
            odds_str = self.odds.value.strip()

            if not team_input or not line_value or not odds_str:
                await interaction.followup.send("❌ All fields are required in the modal.", ephemeral=True)
                return

            try:
                odds_val = float(odds_str.replace("+", ""))
            except ValueError as ve:
                await interaction.followup.send(
                    f"❌ Invalid odds: '{odds_str}'. {ve}", ephemeral=True
                )
                return

            # Update bet details
            self.view.bet_details.update({
                "line": line_value,
                "odds_str": odds_str,
                "odds": odds_val,
                "team": team_input,
                "opponent": opponent_input,
            })

            # Update view properties
            self.view.home_team = team_input
            self.view.away_team = opponent_input
            self.view.league = self.view.bet_details.get("league", "UNKNOWN")
            self.view.line = line_value
            self.view.odds = odds_val

            try:
                api_game_id = self.view.bet_details.get("api_game_id")
                if api_game_id == "Other":
                    api_game_id = None

                # Create bet record if not exists
                if "bet_serial" not in self.view.bet_details:
                    bet_serial = await self.view.bot.bet_service.create_straight_bet(
                        guild_id=interaction.guild_id,
                        user_id=interaction.user.id,
                        api_game_id=api_game_id,
                        bet_type=self.line_type,
                        team=team_input,
                        opponent=opponent_input,
                        line=line_value,
                        units=1.0,
                        odds=odds_val,
                        channel_id=None,
                        league=self.view.league,
                    )
                    if not bet_serial:
                        raise BetServiceError("Failed to create bet record (no serial returned).")
                    self.view.bet_details["bet_serial"] = bet_serial
                    self.view.bet_id = str(bet_serial)
                else:
                    self.view.bet_id = str(self.view.bet_details["bet_serial"])

                # Generate bet slip
                try:
                    current_units = float(self.view.bet_details.get("units", 1.0))
                    bet_slip_generator = await self.view.get_bet_slip_generator()

                    # Prepare player prop specific details
                    player_name = None
                    player_image = None
                    display_vs = None
                    if self.line_type == "player_prop":
                        player_name = line_value.split(' - ')[0] if ' - ' in line_value else None
                        if player_name:
                            from utils.modals import get_player_image
                            player_image_path = get_player_image(player_name, team_input, self.view.league)
                            if player_image_path:
                                from PIL import Image
                                player_image = Image.open(player_image_path).convert("RGBA")
                        display_vs = f"{team_input} vs {opponent_input}"

                    bet_slip_image = await bet_slip_generator.generate_bet_slip(
                        league=self.view.league,
                        home_team=team_input,
                        away_team=opponent_input,
                        odds=odds_val,
                        units=current_units,
                        bet_type=self.line_type,
                        selected_team=team_input,
                        line=line_value,
                        bet_id=self.view.bet_id,
                        timestamp=datetime.now(timezone.utc),
                        player_name=player_name,
                        player_image=player_image,
                        display_vs=display_vs
                    )

                    if bet_slip_image:
                        self.view.preview_image_bytes = io.BytesIO(bet_slip_image)
                        self.view.preview_image_bytes.seek(0)
                    else:
                        self.view.preview_image_bytes = None

                except Exception as img_e:
                    logger.exception(f"Error generating bet slip image in modal: {img_e}")
                    self.view.preview_image_bytes = None

            except BetServiceError as bse:
                logger.exception(f"BetService error creating/updating bet from modal: {bse}")
                await interaction.followup.send(f"❌ Error saving bet record: {bse}", ephemeral=True)
                self.view.stop()
                return
            except Exception as e:
                logger.exception(f"Failed to save bet details from modal: {e}")
                await interaction.followup.send(f"❌ Error processing bet data: {e}", ephemeral=True)
                self.view.stop()
                return

            await self.view.edit_message(
                content="Bet details updated. Processing...", view=self.view
            )
            self.view.current_step = 4
            await self.view.go_next(interaction)
        except Exception as e:
            logger.exception(f"Error in BetDetailsModal on_submit (outer try): {e}")
            try:
                await interaction.followup.send("❌ Error processing details from modal.", ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send followup error in BetDetailsModal.")
            if hasattr(self, "view") and self.view:
                self.view.stop()

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.error(f"Error in BetDetailsModal: {error}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Modal error.", ephemeral=True)
            else:
                await interaction.followup.send("Modal error.", ephemeral=True)
        except discord.HTTPException:
            pass


class UnitsSelect(Select):
    def __init__(self, parent_view: View):
        self.parent_view = parent_view
        options = [
            SelectOption(label="0.5 Units", value="0.5"),
            SelectOption(label="1 Unit", value="1.0"),
            SelectOption(label="1.5 Units", value="1.5"),
            SelectOption(label="2 Units", value="2.0"),
            SelectOption(label="2.5 Units", value="2.5"),
            SelectOption(label="3 Units", value="3.0"),
        ]
        super().__init__(
            placeholder="Select Units for Bet...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        self.parent_view.bet_details["units_str"] = self.values[0]
        logger.debug(f"Units selected: {self.values[0]} by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view._handle_units_selection(interaction, float(self.values[0]))


class ChannelSelect(Select):
    def __init__(self, parent_view: View, channels: List[TextChannel]):
        self.parent_view = parent_view
        sorted_channels = sorted(channels, key=lambda x: x.name.lower())
        options = [
            SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"ID: {channel.id}"[:100],
            )
            for channel in sorted_channels[:24]
        ]
        if not options:
            options.append(SelectOption(label="No channels available", value="none_available", emoji="❌"))
        super().__init__(
            placeholder="Select channel to post bet...",
            options=options,
            min_values=1,
            max_values=1,
            disabled=(not options or options[0].value == "none_available"),
        )

    async def callback(self, interaction: Interaction):
        channel_id_str = self.values[0]
        if channel_id_str == "none_available":
            await interaction.response.send_message("No channels available to select.", ephemeral=True)
            return
        self.parent_view.bet_details["channel_id"] = int(channel_id_str)
        logger.debug(f"Channel selected: {channel_id_str} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class ConfirmButton(Button):
    def __init__(self, parent_view: View):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm",
            custom_id=f"straight_confirm_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        selected_api_game_id = self.parent_view.bet_details.get("api_game_id")
        line_type = self.parent_view.bet_details.get("line_type", "game_line")
        is_manual = selected_api_game_id == "Other"
        if is_manual:
            modal = StraightBetDetailsModal(
                line_type=line_type,
                selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
                bet_details_from_view=self.parent_view.bet_details,
                is_manual=True,
            )
            modal.view_ref = self.parent_view
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
                await self.parent_view.edit_message(
                    content="Please fill in the bet details in the popup form.", view=self.parent_view
                )
            else:
                logger.error("Tried to send modal, but interaction already responded to.")
                await interaction.followup.send(
                    "❌ Error: Could not open modal. Please try again.", ephemeral=True
                )
                self.parent_view.stop()
                return
        else:
            home_team = self.parent_view.bet_details.get("home_team_name", "")
            away_team = self.parent_view.bet_details.get("away_team_name", "")
            self.parent_view.clear_items()
            self.parent_view.add_item(TeamSelect(self.parent_view, home_team, away_team))
            await self.parent_view.edit_message(
                content="Select which team you are betting on:", view=self.parent_view
            )


class ConfirmUnitsButton(Button):
    def __init__(self, parent_view: View):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm Units",
            custom_id=f"straight_confirm_units_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Confirm Units button clicked by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view.go_next(interaction)


class FinalConfirmButton(Button):
    def __init__(self, parent_view: View):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm & Post Bet",
            custom_id=f"straight_final_confirm_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Final confirm button clicked by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view.submit_bet(interaction)


class StraightBetWorkflowView(View):
    def __init__(self, original_interaction: Interaction, bot: commands.Bot, message_to_control: Optional[Message] = None):
        super().__init__(timeout=1800)
        self.original_interaction = original_interaction
        self.bot = bot
        self.message = message_to_control
        self.current_step = 0
        self.bet_details: Dict[str, Any] = {}
        self.games: List[Dict] = []
        self.is_processing = False
        self.latest_interaction = original_interaction
        self.bet_slip_generator: Optional[BetSlipGenerator] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        self.home_team: Optional[str] = None
        self.away_team: Optional[str] = None
        self.league: Optional[str] = None
        self.line: Optional[str] = None
        self.odds: Optional[float] = None
        self.bet_id: Optional[str] = None

    async def get_bet_slip_generator(self) -> BetSlipGenerator:
        if self.bet_slip_generator is None:
            self.bet_slip_generator = await self.bot.get_bet_slip_generator(
                self.original_interaction.guild_id
            )
        return self.bet_slip_generator

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        logger.debug(
            f"Starting straight bet workflow on message ID: {self.message.id if self.message else 'None'}"
        )
        if not self.message:
            logger.error("StraightBetWorkflowView.start_flow called but self.message is None.")
            response_interaction = (
                interaction_that_triggered_workflow_start or self.original_interaction
            )
            try:
                if not response_interaction.response.is_done():
                    await response_interaction.response.send_message(
                        "❌ Workflow error: Message context lost.", ephemeral=True
                    )
                else:
                    await response_interaction.followup.send(
                        "❌ Workflow error: Message context lost.", ephemeral=True
                    )
            except discord.HTTPException as http_err:
                logger.error(f"Failed to send message context lost error: {http_err}")
            self.stop()
            return
        try:
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.exception(f"Failed during initial go_next in StraightBetWorkflow: {e}")
            response_interaction = (
                interaction_that_triggered_workflow_start or self.original_interaction
            )
            try:
                if not response_interaction.response.is_done():
                    await response_interaction.response.send_message(
                        "❌ Failed to start bet workflow.", ephemeral=True
                    )
                else:
                    await response_interaction.followup.send(
                        "❌ Failed to start bet workflow.", ephemeral=True
                    )
            except discord.HTTPException as http_err:
                logger.error(f"Failed to send workflow start error: {http_err}")
            self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message(
                "You cannot interact with this bet placement.", ephemeral=True
            )
            return False
        self.latest_interaction = interaction
        return True

    async def edit_message(
        self,
        content: Optional[str] = None,
        view: Optional[View] = None,
        embed: Optional[discord.Embed] = None,
        file: Optional[File] = None,
    ):
        logger.debug(
            f"Attempting to edit message: {self.message.id if self.message else 'None'} with content: '{content}'"
        )
        attachments = [file] if file else discord.utils.MISSING
        if not self.message:
            logger.error("Cannot edit message: self.message is None.")
            if self.latest_interaction and self.latest_interaction.response.is_done():
                try:
                    logger.debug("Self.message is None, trying to send followup via latest_interaction.")
                    if not self.latest_interaction.followup:
                        logger.error("Follow-up webhook is invalid or expired.")
                        return
                    await self.latest_interaction.followup.send(
                        content=content or "Updating...",
                        view=view,
                        files=attachments if attachments != discord.utils.MISSING else None,
                        ephemeral=True,
                    )
                    self.message = await self.latest_interaction.original_response()
                except Exception as e:
                    logger.error(f"Failed to send followup when self.message was None: {e}")
            return
        try:
            await self.message.edit(content=content, embed=embed, view=view, attachments=attachments)
        except discord.NotFound:
            logger.warning(f"Failed to edit message {self.message.id}: Not Found. Stopping view.")
            self.stop()
        except discord.HTTPException as e:
            logger.error(f"HTTP error editing message {self.message.id}: {e}", exc_info=True)
        except Exception as e:
            logger.exception(f"Unexpected error editing message {self.message.id}: {e}")

    async def go_next(self, interaction: Interaction):
        if self.is_processing:
            logger.debug(f"Skipping go_next (step {self.current_step}); already processing.")
            if not interaction.response.is_done():
                try:
                    await interaction.response.defer(ephemeral=True)
                except discord.HTTPException:
                    pass
            return
        self.is_processing = True
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=True)
            except discord.HTTPException as e:
                logger.warning(
                    f"Defer in go_next failed for interaction {interaction.id} (step {self.current_step}): {e}"
                )
                self.is_processing = False
                return
        try:
            self.current_step += 1
            logger.info(
                f"StraightBetWorkflow: Advancing to step {self.current_step} for user {interaction.user.id}"
            )
            self.clear_items()
            content = self.get_content()
            new_view_items = []
            if self.current_step == 1:
                allowed_leagues = [
                    "NFL", "EPL", "NBA", "MLB", "NHL", "La Liga", "NCAA", "Bundesliga",
                    "Serie A", "Ligue 1", "MLS", "Formula 1", "Tennis", "UFC/MMA",
                    "WNBA", "CFL", "AFL", "Darts", "EuroLeague", "NPB", "KBO", "KHL"
                ]
                new_view_items.append(LeagueSelect(self, allowed_leagues))
            elif self.current_step == 2:
                new_view_items.append(LineTypeSelect(self))
            elif self.current_step == 3:
                league = self.bet_details.get("league")
                if not league:
                    await self.edit_message(content="❌ League not selected. Please restart.", view=None)
                    self.stop()
                    return
                logger.debug(f"Fetching games for league: {league}")
                self.games = await get_normalized_games_for_dropdown(self.bot.db, league)
                logger.debug(f"Retrieved {len(self.games)} games for league: {league}")

                # Exclude games from yesterday in EST time
                est_now = datetime.now(pytz.timezone('US/Eastern'))
                est_yesterday = est_now - timedelta(days=1)
                self.games = [
                    game for game in self.games
                    if game.get('start_time') and datetime.fromisoformat(game['start_time']).astimezone(pytz.timezone('US/Eastern')).date() > est_yesterday.date()
                ]

                # Ensure odds are included in the game details
                for game in self.games:
                    game_odds = game.get("odds", {})
                    logger.debug(f"Game {game['api_game_id']} odds: {game_odds}")

                # Add GameSelect regardless of whether there are games
                new_view_items.append(GameSelect(self, self.games))
                new_view_items.append(ConfirmButton(self))

                # If no games available, show a message encouraging Manual Entry
                if not self.games:
                    content = f"No games available for {league} at this time. You can use Manual Entry to place your bet."
            elif self.current_step == 4:
                self.is_processing = False
                return
            elif self.current_step == 5:
                if "bet_serial" not in self.bet_details:
                    await self.edit_message(
                        content="❌ Bet details not fully captured or bet not created. Please restart.",
                        view=None,
                    )
                    self.stop()
                    return
                new_view_items.append(UnitsSelect(self))
                new_view_items.append(ConfirmUnitsButton(self))
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"bet_preview_s{self.current_step}.png")
                await self.edit_message(content=self.get_content(), view=self, file=file_to_send)
            elif self.current_step == 6:
                if not all(k in self.bet_details for k in ["bet_serial", "units_str"]):
                    await self.edit_message(
                        content="❌ Bet details incomplete. Please restart.", view=None
                    )
                    self.stop()
                    return
                logger.info(f"Step 6: Fetching embed channels for guild {self.original_interaction.guild_id}")
                guild_settings = await self.bot.db_manager.fetch_one(
                    "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
                    (str(self.original_interaction.guild_id),)
                )
                allowed_channels = []
                if guild_settings:
                    channel_ids = [
                        guild_settings.get("embed_channel_1"),
                        guild_settings.get("embed_channel_2")
                    ]
                    for channel_id in channel_ids:
                        if channel_id:
                            try:
                                channel_id_int = int(channel_id)
                                channel = self.bot.get_channel(channel_id_int)
                                if not channel:
                                    channel = await self.bot.fetch_channel(channel_id_int)
                                if channel and isinstance(channel, discord.TextChannel):
                                    permissions = channel.permissions_for(interaction.guild.me)
                                    if permissions.send_messages and permissions.view_channel:
                                        if channel not in allowed_channels:
                                            allowed_channels.append(channel)
                            except Exception as e:
                                logger.error(f"Error processing channel {channel_id}: {e}")
                if not allowed_channels:
                    await self.edit_message(
                        content="❌ No valid embed channels configured. Please contact an admin.",
                        view=None
                    )
                    self.stop()
                    return
                new_view_items.append(ChannelSelect(self, allowed_channels))
            elif self.current_step == 7:
                preview_info = "(Final Preview below)" if self.preview_image_bytes else "(Image generation failed)"
                content = f"**Confirm Your Bet** {preview_info}"
                new_view_items.append(FinalConfirmButton(self))
                new_view_items.append(CancelButton(self))
                for item in new_view_items:
                    self.add_item(item)
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"bet_preview_s{self.current_step}.png")
                await self.edit_message(content=content, view=self, file=file_to_send)
                self.is_processing = False
                return
            else:
                logger.error(f"Unexpected step in StraightBetWorkflow: {self.current_step}")
                await self.edit_message(
                    content="❌ An unexpected error occurred in the workflow.", view=None
                )
                self.stop()
                return
            if self.current_step < 8:
                new_view_items.append(CancelButton(self))
            for item in new_view_items:
                self.add_item(item)
            await self.edit_message(content=content, view=self)
        except Exception as e:
            logger.exception(f"Error in go_next (step {self.current_step}): {e}")
            await self.edit_message(
                content="❌ An error occurred. Please try again or cancel.", view=None
            )
            self.stop()
        finally:
            self.is_processing = False

    async def submit_bet(self, interaction: Interaction):
        details = self.bet_details
        bet_serial = details.get("bet_serial")
        if not bet_serial:
            logger.error("Straight bet: Attempted to submit without bet_serial.")
            await self.edit_message(content="❌ Bet ID missing.", view=None)
            self.stop()
            return

        logger.info(f"Submitting straight bet {bet_serial} by user {interaction.user.id}")
        await self.edit_message(content=f"Processing bet `{bet_serial}`...", view=None, file=None)

        try:
            post_channel_id = details.get("channel_id")
            post_channel = self.bot.get_channel(post_channel_id) if post_channel_id else None
            if not post_channel or not isinstance(post_channel, TextChannel):
                raise ValueError(f"Invalid channel <#{post_channel_id}> for bet posting.")

            units_val = float(details.get("units", 1.0))
            odds_val = float(details.get("odds", 0.0))
            bet_type = details.get("line_type", "straight")
            bet_details_json = json.dumps(details)

            # Fetch internal game_id from api_games table
            internal_game_id = None
            api_game_id = details.get("api_game_id")
            if api_game_id and api_game_id != "Other":
                try:
                    row = await self.bot.db_manager.fetch_one(
                        "SELECT id FROM api_games WHERE api_game_id = %s", (api_game_id,)
                    )
                    if row and row.get("id"):
                        internal_game_id = row["id"]
                        logger.info(f"Fetched internal game_id {internal_game_id} for api_game_id {api_game_id}")
                    else:
                        logger.warning(f"No game found in api_games for api_game_id {api_game_id}")
                except Exception as e:
                    logger.error(f"Error fetching internal game_id for api_game_id {api_game_id}: {e}")

            update_query = """
                UPDATE bets SET units = %s, odds = %s, channel_id = %s, confirmed = 1, 
                               bet_details = %s, status = %s, game_id = %s
                WHERE bet_serial = %s 
            """
            rowcount, _ = await self.bot.db_manager.execute(
                update_query, 
                (units_val, odds_val, post_channel_id, bet_details_json, "pending", internal_game_id, bet_serial)
            )
            if rowcount is None or rowcount == 0:
                logger.warning(f"Straight bet {bet_serial} DB update for confirmation affected 0 rows.")
                raise BetServiceError("Failed to confirm bet details in DB.")

            discord_file_to_send = None
            if self.preview_image_bytes:
                self.preview_image_bytes.seek(0)
                discord_file_to_send = File(self.preview_image_bytes, filename=f"bet_slip_{bet_serial}.png")
            else:
                logger.warning(f"Straight bet {bet_serial}: No preview image available at submit. Attempting to regenerate.")
                bet_slip_gen = await self.get_bet_slip_generator()
                bet_slip_image = await bet_slip_gen.generate_bet_slip(
                    home_team=self.home_team if self.home_team else details.get("team", "N/A"),
                    away_team=self.away_team if self.away_team else details.get("opponent", "N/A"),
                    league=self.league if self.league else details.get("league", "N/A"),
                    line=self.line if self.line else details.get("line", "N/A"),
                    odds=odds_val,
                    units=units_val,
                    bet_id=str(bet_serial),
                    timestamp=datetime.now(timezone.utc),
                    bet_type=bet_type,
                    selected_team=details.get("team"),
                )
                if bet_slip_image:
                    temp_bytes = io.BytesIO()
                    bet_slip_image.save(temp_bytes, format="PNG")
                    temp_bytes.seek(0)
                    discord_file_to_send = File(temp_bytes, filename=f"bet_slip_{bet_serial}.png")
                    temp_bytes.close()

            capper_data = await self.bot.db_manager.fetch_one(
                "SELECT display_name, image_path FROM cappers WHERE guild_id = %s AND user_id = %s",
                (interaction.guild_id, interaction.user.id)
            )
            webhook_username = capper_data.get("display_name") if capper_data and capper_data.get("display_name") else interaction.user.display_name
            webhook_avatar_url = None
            if capper_data and capper_data.get("image_path") and capper_data.get("image_path").startswith(("http://", "https://")):
                webhook_avatar_url = capper_data.get("image_path")
            else:
                webhook_avatar_url = interaction.user.display_avatar.url if interaction.user.display_avatar else None

            target_webhook = None
            try:
                webhooks = await post_channel.webhooks()
                target_webhook = discord.utils.find(lambda wh: wh.user and wh.user.id == self.bot.user.id, webhooks)
                if not target_webhook:
                    target_webhook = await post_channel.create_webhook(name=f"{self.bot.user.name} Bets")
            except Exception as e:
                logger.error(f"Straight bet: Webhook setup failed for channel {post_channel.id}: {e}")
                raise ValueError("Webhook setup failed.")

            sent_message = await target_webhook.send(
                file=discord_file_to_send,
                username=webhook_username[:80],
                avatar_url=webhook_avatar_url,
                wait=True
            )

            if sent_message and hasattr(self.bot.bet_service, "pending_reactions"):
                self.bot.bet_service.pending_reactions[sent_message.id] = {
                    "bet_serial": bet_serial,
                    "user_id": interaction.user.id,
                    "guild_id": interaction.guild_id,
                    "channel_id": post_channel_id,
                    "bet_type": bet_type
                }
            await self.edit_message(content=f"✅ Bet ID `{bet_serial}` posted to {post_channel.mention}!", view=None, file=None)
        except Exception as e:
            logger.exception(f"Error submitting straight bet {bet_serial}: {e}")
            await self.edit_message(content=f"❌ Error placing bet: {e}", view=None)
        finally:
            if self.preview_image_bytes:
                self.preview_image_bytes.close()
                self.preview_image_bytes = None
            self.stop()

    def get_content(self) -> str:
        step_num = self.current_step
        if step_num == 1:
            return f"**Step {step_num}**: Select League"
        if step_num == 2:
            return f"**Step {step_num}**: Select Line Type"
        if step_num == 3:
            return f"**Step {step_num}**: Select Game or Enter Manually"
        if step_num == 4:
            return "Please fill in the bet details in the popup form."
        if step_num == 5:
            preview_info = "(Preview below)" if self.preview_image_bytes else "(Generating preview...)"
            units = self.bet_details.get("units_str", "N/A")
            # Add lock emoji left and right of units for step 5 as well
            return f"**Step {step_num}**: Bet details captured {preview_info}. 🔒 Units: `{units}` 🔒 Select Units for your bet and confirm."
        if step_num == 6:
            units = self.bet_details.get("units_str", "N/A")
            preview_info = (
                "(Preview below with updated units)"
                if self.preview_image_bytes
                else "(Preview image failed)"
            )
            # Add lock emoji left and right of units
            return f"**Step {step_num}**: 🔒 Units: `{units}` 🔒 {preview_info}. Select Channel to post your bet."
        if step_num == 7:
            preview_info = (
                "(Final Preview below)" if self.preview_image_bytes else "(Image generation failed)"
            )
            return f"**Confirm Your Bet** {preview_info}"
        return "Processing your bet request..."

    async def _handle_units_selection(self, interaction: discord.Interaction, units: float):
        logger.debug(
            f"StraightBet _handle_units_selection: units={units}, bet_serial={self.bet_details.get('bet_serial')}"
        )
        self.bet_details["units"] = units
        self.bet_details["units_str"] = str(units)
        if "bet_serial" not in self.bet_details:
            logger.error("Straight: bet_serial missing when trying to update units in DB.")
            try:
                bet_serial = await self.bot.bet_service.create_straight_bet(
                    guild_id=self.original_interaction.guild_id,
                    user_id=self.original_interaction.user.id,
                    api_game_id=self.bet_details.get("api_game_id"),
                    bet_type=self.bet_details.get("line_type", "game_line"),
                    team=self.bet_details.get("team"),
                    opponent=self.bet_details.get("opponent"),
                    line=self.bet_details.get("line"),
                    units=units,
                    odds=self.bet_details.get("odds"),
                    channel_id=None,
                    league=self.bet_details.get("league", "UNKNOWN"),
                )
                if not bet_serial:
                    raise BetServiceError("Failed to create bet record before units update.")
                self.bet_details["bet_serial"] = bet_serial
                logger.info(f"Straight bet record {bet_serial} created during units selection.")
            except BetServiceError as bse:
                logger.error(f"Error creating straight record in _handle_units_selection: {bse}")
                await interaction.followup.send(f"❌ Error initializing bet: {bse}", ephemeral=True)
                self.stop()
                return
        try:
            await self.bot.db_manager.execute(
                "UPDATE bets SET units = %s WHERE bet_serial = %s",
                (units, self.bet_details["bet_serial"]),
            )
            logger.info(f"Units for straight bet {self.bet_details['bet_serial']} updated to {units}.")
        except Exception as e:
            logger.error(
                f"Failed to update units in DB for straight bet {self.bet_details.get('bet_serial')}: {e}"
            )
            await interaction.followup.send(
                "❌ Error saving unit selection. Please try again.", ephemeral=True
            )
            return
        try:
            bet_slip_gen = await self.get_bet_slip_generator()
            bet_slip_image = await bet_slip_gen.generate_bet_slip(
                home_team=self.home_team or self.bet_details.get("team", "N/A"),
                away_team=self.away_team or self.bet_details.get("opponent", "N/A"),
                league=self.league or self.bet_details.get("league", "N/A"),
                line=self.line or self.bet_details.get("line", "N/A"),
                odds=self.bet_details.get("odds", 0.0),
                units=units,
                bet_id=str(self.bet_details.get("bet_serial", "N/A")),
                timestamp=datetime.now(timezone.utc),
                bet_type=self.bet_details.get("line_type", "straight"),
                selected_team=self.bet_details.get("team"),
            )
            if bet_slip_image:
                if self.preview_image_bytes:
                    self.preview_image_bytes.close()
                self.preview_image_bytes = io.BytesIO()
                bet_slip_image.save(self.preview_image_bytes, format="PNG")
                self.preview_image_bytes.seek(0)
                logger.debug(
                    f"Straight slip preview updated for bet {self.bet_details.get('bet_serial')} with units {units}."
                )
            else:
                logger.warning(
                    f"Failed to regen straight preview for bet {self.bet_details.get('bet_serial')}."
                )
                if self.preview_image_bytes:
                    self.preview_image_bytes.close()
                    self.preview_image_bytes = None
        except Exception as img_e:
            logger.error(
                f"Error regen straight preview in _handle_units_selection: {img_e}", exc_info=True
            )
            if self.preview_image_bytes:
                self.preview_image_bytes.close()
        file_to_send = None
        if self.preview_image_bytes:
            self.preview_image_bytes.seek(0)
            file_to_send = File(self.preview_image_bytes, filename=f"bet_preview_s{self.current_step}.png")
        await self.edit_message(content=self.get_content(), view=self, file=file_to_send)


async def populate_api_games_on_restart(db):
    async with SportsAPI(db_manager=db) as api:
        await api.fetch_and_save_daily_games()

# Example usage during server startup
async def on_server_startup():
    db = await get_database_connection()
    await populate_api_games_on_restart(db)