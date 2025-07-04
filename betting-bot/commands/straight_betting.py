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
from data.db_manager import DatabaseManager

from data.game_utils import get_normalized_games_for_dropdown

from utils.errors import (
    BetServiceError,
    ValidationError,
    GameNotFoundError,
)
from utils.modals import StraightBetDetailsModal
from config.leagues import LEAGUE_CONFIG
from api.sports_api import SportsAPI
from utils.game_line_image_generator import GameLineImageGenerator
from utils.player_prop_image_generator import PlayerPropImageGenerator
from utils.parlay_image_generator import ParlayImageGenerator

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
            SelectOption(label=league[:100], value=league[:100])
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
                label="Game Line"[:100],
                value="game_line"[:100],
                description="Moneyline or game over/under",
            ),
            SelectOption(
                label="Player Prop"[:100],
                value="player_prop"[:100],
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
        # Force update line_type to ensure correct preview for player prop
        if self.values[0] == "player_prop":
            self.parent_view.bet_details["line_type"] = "player_prop"
        else:
            self.parent_view.bet_details["line_type"] = self.values[0]
        logger.debug(f"Line Type selected: {self.parent_view.bet_details['line_type']} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class GameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict]):
        from datetime import datetime
        import pytz
        game_options = []
        seen_values = set()
        manual_value = "manual_entry"
        seen_values.add(manual_value)  # Prevent accidental duplicate manual_entry
        eastern = pytz.timezone("US/Eastern")
        # --- Filter out finished games here as well ---
        finished_statuses = [
            "Match Finished", "Finished", "FT", "Game Finished", "Final"
        ]
        filtered_games = []
        for game in games:
            status = (game.get('status') or '').strip()
            if status not in finished_statuses:
                filtered_games.append(game)
            else:
                logger.debug(f"[GameSelect] Excluding game {game.get('api_game_id')} ({game.get('home_team_name')} vs {game.get('away_team_name')}) - status: {status}")
        # Only include up to 24 games (Discord limit is 25 options including manual entry)
        for game in filtered_games[:24]:
            home_team = game.get('home_team_name', '').strip() or 'N/A'
            away_team = game.get('away_team_name', '').strip() or 'N/A'
            if home_team.lower() == 'manual entry' and away_team.lower() == 'manual entry':
                continue
            # Prefer api_game_id if present, else use internal id
            if game.get('api_game_id'):
                value = f"api_{game['api_game_id']}"
            elif game.get('id'):
                value = f"dbid_{game['id']}"
            else:
                continue  # skip if neither id present
            if value in seen_values or value == manual_value:
                continue
            seen_values.add(value)
            # Format the label with team names (no status)
            label = f"{home_team} vs {away_team}"
            label = label[:100] if label else "N/A"
            # Get start time for description
            start_time = game.get('start_time')
            if start_time:
                # Format start_time as EST string
                try:
                    eastern = pytz.timezone('US/Eastern')
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    est_time = start_time.astimezone(eastern)
                    desc = f"Estimated Start Time: {est_time.strftime('%a %b %d, %I:%M %p')} EST"
                except Exception:
                    desc = f"Estimated Start Time: {str(start_time)}"
            else:
                desc = "No start time"
            # Ensure value is at least 1 character and at most 100
            value = value[:100] if value else "N/A"
            game_options.append(
                SelectOption(
                    label=label,
                    value=value,
                    description=desc[:100]
                )
            )
        # Always add manual entry as the last option, only if not already present
        if manual_value not in [opt.value for opt in game_options]:
            game_options.append(
                SelectOption(
                    label="Manual Entry",
                    value=manual_value[:100],
                    description="Enter game details manually"
                )
            )
        super().__init__(
            placeholder="Select a game or choose Manual Entry",
            options=game_options,
            min_values=1,
            max_values=1,
        )
        self.parent_view = parent_view
        self.games = filtered_games
        logger.debug(f"Created GameSelect with {len(game_options)} unique options (including manual entry)")

    async def callback(self, interaction: Interaction):
        selected_value = self.values[0]
        logger.debug(f"Selected game value: {selected_value}")
        if selected_value == "manual_entry":
            self.parent_view.bet_details.update({
                'api_game_id': None,
                'is_manual': True,
                'home_team_name': "Manual Entry",
                'away_team_name': "Manual Entry",
            })
        else:
            selected_game = None
            if selected_value.startswith("api_"):
                api_game_id = selected_value[4:]
                selected_game = next((g for g in self.games if str(g.get('api_game_id')) == api_game_id), None)
            elif selected_value.startswith("dbid_"):
                dbid = selected_value[5:]
                selected_game = next((g for g in self.games if str(g.get('id')) == dbid), None)
            if selected_game:
                self.parent_view.bet_details.update({
                    'api_game_id': selected_game.get('api_game_id'),
                    'game_id': selected_game.get('id'),
                    'home_team_name': selected_game.get('home_team_name'),
                    'away_team_name': selected_game.get('away_team_name'),  # <-- FIXED KEY
                    'is_manual': False
                })
                logger.debug(f"Updated bet details: {self.parent_view.bet_details}")
            else:
                logger.error(f"Could not find game for selected value {selected_value}")
                await interaction.response.defer()
                await self.parent_view.edit_message(
                    content="Error: Could not find the selected game. Please try again or cancel.",
                    view=None
                )
                self.parent_view.stop()
                return

        # Always show team selection after game selection
        self.parent_view.clear_items()
        home_team = self.parent_view.bet_details.get("home_team_name", "")
        away_team = self.parent_view.bet_details.get("away_team_name", "")
        self.parent_view.add_item(TeamSelect(self.parent_view, home_team, away_team))
        self.parent_view.add_item(CancelButton(self.parent_view))
        await interaction.response.defer()
        await self.parent_view.edit_message(
            content="Select which team you are betting on:",
            view=self.parent_view
        )


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
                bet_service = getattr(self.parent_view.bot, "bet_service", None)
                if bet_service:
                    await bet_service.delete_bet(bet_serial)
                    logger.info(f"Deleted bet {bet_serial} after cancellation")
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
            SelectOption(label=home_team[:100], value=home_team[:100]),
            SelectOption(label=away_team[:100], value=away_team[:100]),
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
        is_manual = self.parent_view.bet_details.get('is_manual', False)
        # Always show modal for line/odds after team selection
        modal = StraightBetDetailsModal(
            line_type=line_type,
            selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
            bet_details_from_view=self.parent_view.bet_details,
            is_manual=is_manual,
        )
        modal.view_ref = self.parent_view
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)
            return
        else:
            logger.error("Tried to send modal, but interaction already responded to.")
            await self.parent_view.edit_message(
                content="❌ Error: Could not open modal. Please try again or cancel.",
                view=None
            )
            self.parent_view.stop()
            return


class UnitsSelect(Select):
    def __init__(self, parent_view: View, units_display_mode='auto'):
        self.parent_view = parent_view
        self.units_display_mode = units_display_mode
        options = []
        if units_display_mode == 'manual':
            # Add To Win group
            options.append(SelectOption(label='--- To Win ---', value='separator_win', default=False, description=None, emoji=None))
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(SelectOption(label=f'To Win {u:.1f} Unit' + ('' if u == 1.0 else 's'), value=f'{u}|win'))
            # Add To Risk group
            options.append(SelectOption(label='--- To Risk ---', value='separator_risk', default=False, description=None, emoji=None))
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(SelectOption(label=f'Risk {u:.1f} Unit' + ('' if u == 1.0 else 's'), value=f'{u}|risk'))
        else:
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(SelectOption(label=f'{u:.1f} Unit' + ('' if u == 1.0 else 's'), value=str(u)))
        super().__init__(
            placeholder="Select Units for Bet...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if self.units_display_mode == 'manual':
            if value.startswith('separator'):
                await interaction.response.defer(ephemeral=True)
                return
            units_str, mode = value.split('|')
            units = float(units_str)
            display_as_risk = (mode == 'risk')
            self.parent_view.bet_details['units_str'] = units_str
            self.parent_view.bet_details['units'] = units
            self.parent_view.bet_details['display_as_risk'] = display_as_risk
        else:
            self.parent_view.bet_details['units_str'] = value
            self.parent_view.bet_details['units'] = float(value)
            self.parent_view.bet_details['display_as_risk'] = None
        logger.debug(f"Units selected: {value} by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view._handle_units_selection(interaction, float(self.parent_view.bet_details['units']))


class ChannelSelect(Select):
    def __init__(self, parent_view: View, channels: List[TextChannel]):
        self.parent_view = parent_view
        sorted_channels = sorted(channels, key=lambda x: x.name.lower())
        options = [
            SelectOption(
                label=channel.name[:100],
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
            await interaction.response.defer()
            await self.parent_view.edit_message(
                content="❌ No channels available to select. Please contact an admin.",
                view=None
            )
            self.parent_view.stop()
            return
        self.parent_view.bet_details["channel_id"] = int(channel_id_str)
        logger.debug(f"Channel selected: {channel_id_str} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()


class ConfirmButton(Button):
    def __init__(self, parent_view: View):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm",
            custom_id=f"straight_confirm_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        # Check if manual entry is selected
        is_manual = self.parent_view.bet_details.get("is_manual", False)
        line_type = self.parent_view.bet_details.get("line_type", "game_line")
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
        self.parent_view.stop()
        return


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
        self.bet_slip_generator: Optional[Union[GameLineImageGenerator, PlayerPropImageGenerator]] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        self.home_team: Optional[str] = None
        self.away_team: Optional[str] = None
        self.league: Optional[str] = None
        self.line: Optional[str] = None
        self.odds: Optional[float] = None
        self.bet_id: Optional[str] = None
        self._stopped = False

    async def get_bet_slip_generator(self) -> Union[GameLineImageGenerator, PlayerPropImageGenerator]:
        bet_type = self.bet_details.get("line_type", "game_line")
        if bet_type == "player_prop":
            if not self.bet_slip_generator or not isinstance(self.bet_slip_generator, PlayerPropImageGenerator):
                self.bet_slip_generator = PlayerPropImageGenerator(guild_id=self.original_interaction.guild_id)
        else:
            if not self.bet_slip_generator or not isinstance(self.bet_slip_generator, GameLineImageGenerator):
                self.bet_slip_generator = GameLineImageGenerator(guild_id=self.original_interaction.guild_id)
        return self.bet_slip_generator

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        logger.debug(
            f"Starting straight bet workflow on message ID: {self.message.id if self.message else 'None'}"
        )
        if not self.message:
            logger.error("StraightBetWorkflowView.start_flow called but self.message is None.")
            self.stop()
            return
        try:
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.exception(f"Failed during initial go_next in StraightBetWorkflow: {e}")
            await self.edit_message(
                content="❌ Failed to start bet workflow. Please try again.",
                view=None
            )
            self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            # Don't send a new message, just deny the interaction silently
            # or edit the original message to show the error
            await interaction.response.defer()
            await self.edit_message(
                content="❌ Only the original user can interact with this bet workflow.",
                view=None
            )
            self.stop()
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
            logger.error("Cannot edit message: self.message is None. This should never happen. Stopping workflow.")
            self.stop()
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
        logger.info(f"[WORKFLOW TRACE] go_next called, current_step={self.current_step}, is_processing={self.is_processing}, stopped={getattr(self, '_stopped', False)}")
        if self.is_processing or self.is_finished() or getattr(self, '_stopped', False):
            logger.debug(f"Skipping go_next (step {self.current_step}); already processing or workflow stopped.")
            if not interaction.response.is_done():
                try:
                    await interaction.response.defer(ephemeral=True)
                except discord.HTTPException:
                    pass
            return
        self.is_processing = True
        try:
            # Only increment current_step if not set by modal (i.e., if called from a user action, not modal submit)
            if hasattr(self, '_skip_increment') and self._skip_increment:
                logger.debug(f"[WORKFLOW TRACE] Skipping current_step increment (set by modal)")
                self._skip_increment = False
            else:
                self.current_step += 1
            logger.info(f"[WORKFLOW TRACE] Advancing to step {self.current_step}")
            self.clear_items()
            content = self.get_content()
            new_view_items = []
            if self.current_step == 1:
                logger.info("[WORKFLOW TRACE] Step 1: League selection")
                allowed_leagues = [
                    "NFL", "EPL", "NBA", "MLB", "NHL", "La Liga", "NCAA", "Bundesliga",
                    "Serie A", "Ligue 1", "MLS", "Formula 1", "Tennis", "UFC/MMA",
                    "WNBA", "CFL", "AFL", "Darts", "EuroLeague", "NPB", "KBO", "KHL"
                ]
                new_view_items.append(LeagueSelect(self, allowed_leagues))
                new_view_items.append(CancelButton(self))
            elif self.current_step == 2:
                logger.info("[WORKFLOW TRACE] Step 2: Line type selection")
                new_view_items.append(LineTypeSelect(self))
                new_view_items.append(CancelButton(self))
            elif self.current_step == 3:
                logger.info("[WORKFLOW TRACE] Step 3: Game selection")
                league = self.bet_details.get("league")
                if not league:
                    await self.edit_message(content="❌ League not selected. Please restart.", view=None)
                    self.stop()
                    return
                logger.debug(f"Fetching games for league: {league}")
                self.games = await get_normalized_games_for_dropdown(self.bot.db, league)
                logger.debug(f"Retrieved {len(self.games)} games for league: {league}: {self.games}")
                finished_statuses = [
                    "Match Finished", "Finished", "FT", "Game Finished", "Final"
                ]
                filtered_games = []
                for game in self.games:
                    status = (game.get('status') or '').strip()
                    if status not in finished_statuses:
                        filtered_games.append(game)
                    else:
                        logger.debug(f"Excluding game {game.get('api_game_id')} ({game.get('home_team_name')} vs {game.get('away_team_name')}) - status: {status}")
                self.games = filtered_games
                logger.debug(f"Games after filtering: {self.games}")
                new_view_items.append(GameSelect(self, self.games))
                new_view_items.append(ConfirmButton(self))
                new_view_items.append(CancelButton(self))
                if not self.games:
                    content = f"No games available for {league} at this time. You can use Manual Entry to place your bet."
            elif self.current_step == 4:
                logger.info("[WORKFLOW TRACE] Step 4: Team selection/modal (auto-advance to units selection)")
                # Immediately advance to step 5 (units selection/preview)
                self.current_step = 5
                # Set default units to 1.0 if not already set
                if "units" not in self.bet_details:
                    self.bet_details["units"] = 1.0
                    self.bet_details["units_str"] = "1.0"
                from utils.bet_utils import fetch_next_bet_serial
                self.bet_details["preview_bet_serial"] = await fetch_next_bet_serial(self.bot)
                # Only regenerate preview if not already set
                if not self.preview_image_bytes:
                    try:
                        bet_type = self.bet_details.get("line_type", "game_line")
                        league = self.bet_details.get("league", "N/A")
                        home_team = self.bet_details.get("home_team_name", self.bet_details.get("team", "N/A"))
                        away_team = self.bet_details.get("away_team_name", self.bet_details.get("opponent", "N/A"))
                        line = self.bet_details.get("line", "N/A")
                        odds = float(self.bet_details.get("odds", 0.0))
                        bet_id = str(self.bet_details.get("preview_bet_serial", ""))
                        timestamp = datetime.now(timezone.utc)
                        units = 1.0
                        if bet_type == "game_line":
                            generator = GameLineImageGenerator(guild_id=self.original_interaction.guild_id)
                            bet_slip_image_bytes = generator.generate_bet_slip_image(
                                league=league,
                                home_team=home_team,
                                away_team=away_team,
                                line=line,
                                odds=odds,
                                units=units,
                                bet_id=bet_id,
                                timestamp=timestamp,
                                selected_team=self.bet_details.get("team", home_team),
                                output_path=None
                            )
                            if bet_slip_image_bytes:
                                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                                self.preview_image_bytes.seek(0)
                            else:
                                self.preview_image_bytes = None
                        elif bet_type == "player_prop":
                            generator = PlayerPropImageGenerator(guild_id=self.original_interaction.guild_id)
                            player_name = self.bet_details.get("player_name")
                            if not player_name and line:
                                player_name = line.split(' - ')[0] if ' - ' in line else line
                            team_name = home_team
                            league = self.bet_details.get("league", "N/A")
                            odds_str = str(self.bet_details.get("odds_str", "")).strip()
                            bet_slip_image_bytes = generator.generate_player_prop_bet_image(
                                player_name=player_name or team_name,
                                team_name=team_name,
                                league=league,
                                line=line,
                                units=units,
                                output_path=None,
                                bet_id=bet_id,
                                timestamp=timestamp,
                                guild_id=str(self.original_interaction.guild_id),
                                odds=odds
                            )
                            if bet_slip_image_bytes:
                                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                                self.preview_image_bytes.seek(0)
                            else:
                                self.preview_image_bytes = None
                        elif bet_type == "parlay":
                            pass

                        # Record the bet in the database after generating preview
                        bet_service = getattr(self.bot, "bet_service", None)
                        if bet_service:
                            try:
                                logger.info("[WORKFLOW TRACE] Creating straight bet in database after preview...")
                                bet_serial = await bet_service.create_straight_bet(
                                    guild_id=self.original_interaction.guild_id,
                                    user_id=self.original_interaction.user.id,
                                    league=league,
                                    bet_type=bet_type,
                                    units=float(units),
                                    odds=float(odds),
                                    team=self.bet_details.get("team"),
                                    opponent=self.bet_details.get("opponent"),
                                    line=line,
                                    api_game_id=self.bet_details.get("api_game_id"),
                                    channel_id=None,  # Will be set in final step
                                    confirmed=0  # Not confirmed until final submission
                                )
                                if bet_serial:
                                    self.bet_details["bet_serial"] = bet_serial
                                    logger.info(f"[WORKFLOW TRACE] Bet recorded with serial {bet_serial}")
                                else:
                                    logger.error("[WORKFLOW TRACE] Failed to create bet in database")
                                    await self.edit_message(content="❌ Failed to create bet in database. Please try again.", view=None)
                                    self.stop()
                                    return
                            except Exception as e:
                                logger.exception(f"[WORKFLOW TRACE] Error creating bet in database: {e}")
                                await self.edit_message(content=f"❌ Error creating bet: {str(e)}", view=None)
                                self.stop()
                                return
                        else:
                            logger.error("[WORKFLOW TRACE] No bet_service available")
                            await self.edit_message(content="❌ Bet service not available. Please try again.", view=None)
                            self.stop()
                            return

                    except Exception as e:
                        logger.exception(f"Error generating initial preview image for units step: {e}")
                        self.preview_image_bytes = None
                self.clear_items()
                self.add_item(UnitsSelect(self))
                self.add_item(ConfirmUnitsButton(self))
                self.add_item(CancelButton(self))
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"bet_preview_s{self.current_step}.png")
                await self.edit_message(content=self.get_content(), view=self, file=file_to_send)
                return
            elif self.current_step == 5:
                logger.info("[WORKFLOW TRACE] Step 5: Units selection/preview")
                # Show units selection and preview image
                self.clear_items()
                self.add_item(UnitsSelect(self))
                self.add_item(ConfirmUnitsButton(self))
                self.add_item(CancelButton(self))
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"bet_preview_s{self.current_step}.png")
                await self.edit_message(content=self.get_content(), view=self, file=file_to_send)
                return
            elif self.current_step == 6:
                logger.info("[WORKFLOW TRACE] Step 6: Channel selection/final confirm - starting")
                try:
                    # Fetch allowed channel IDs from guild_settings
                    guild_settings = await self.bot.db_manager.fetch_one(
                        "SELECT embed_channel_1, embed_channel_2, command_channel_1, command_channel_2 FROM guild_settings WHERE guild_id = %s",
                        (str(interaction.guild_id),)
                    )
                    allowed_channel_ids = set()
                    for key in ["embed_channel_1", "embed_channel_2", "command_channel_1", "command_channel_2"]:
                        val = guild_settings.get(key) if guild_settings else None
                        if isinstance(val, list):
                            allowed_channel_ids.update(int(v) for v in val if v)
                        elif val:
                            allowed_channel_ids.add(int(val))
                    # Get all text channels the user has access to and are allowed
                    channels = []
                    for channel in interaction.guild.text_channels:
                        if channel.permissions_for(interaction.user).send_messages and channel.id in allowed_channel_ids:
                            channels.append(channel)
                    logger.debug(f"[WORKFLOW TRACE] Step 6: Found {len(channels)} allowed channels: {[c.name for c in channels]}")
                    if not channels:
                        await self.edit_message(content="❌ No channels available to post bets. Please contact an admin.", view=None)
                        self.stop()
                        return
                    # Add channel selection and final confirm button
                    new_view_items.append(ChannelSelect(self, channels))
                    new_view_items.append(FinalConfirmButton(self))
                    new_view_items.append(CancelButton(self))
                    content = self.get_content()
                    logger.info("[WORKFLOW TRACE] Step 6: Sending channel selection dropdown and buttons.")
                    await self.edit_message(content=content, view=self)
                except Exception as e:
                    logger.exception(f"[WORKFLOW TRACE] Exception in step 6 (channel selection): {e}")
                    await self.edit_message(content=f"❌ Error in channel selection: {e}", view=None)
                    self.stop()
                    return
                logger.info("[WORKFLOW TRACE] Step 6: Channel selection/final confirm - completed")
            else:
                logger.error(f"Unexpected step in StraightBetWorkflow: {self.current_step}")
                await self.edit_message(
                    content="❌ An unexpected error occurred in the workflow.", view=None
                )
                self.stop()
                return
            for item in new_view_items:
                self.add_item(item)
            await self.edit_message(content=content, view=self)
        except Exception as e:
            logger.exception(f"[WORKFLOW TRACE] Exception in go_next: {e}")
            await self.edit_message(content=f"❌ Error in go_next: {e}", view=None)
            self.stop()
        finally:
            self.is_processing = False

    async def submit_bet(self, interaction: Interaction):
        logger.info("[WORKFLOW TRACE] submit_bet called!")
        try:
            details = self.bet_details
            bet_service = getattr(self.bot, "bet_service", None)
            logger.info(f"[submit_bet] Starting bet submission with details: {json.dumps(details, default=str)}")
            
            if not details.get("bet_serial"):
                logger.error("[submit_bet] No bet_serial found in details")
                await self.edit_message(content="❌ Error: Bet not found. Please try again.", view=None)
                self.stop()
                return

            # Update the bet with channel_id, units, and confirm it
            if bet_service:
                try:
                    await bet_service.update_bet(
                        bet_serial=details["bet_serial"],
                        channel_id=details.get("channel_id"),
                        units=details.get("units"),
                        confirmed=1
                    )
                except Exception as e:
                    logger.error(f"[submit_bet] Failed to update bet: {str(e)}", exc_info=True)
                    await self.edit_message(content=f"❌ Failed to update bet: {str(e)}", view=None)
                    self.stop()
                    return

            logger.info(f"Submitting straight bet {details['bet_serial']} by user {interaction.user.id}")
            await self.edit_message(content=f"Processing bet `{details['bet_serial']}`...", view=None, file=None)
            try:
                post_channel_id = details.get("channel_id")
                post_channel = self.bot.get_channel(post_channel_id) if post_channel_id else None
                if not post_channel or not isinstance(post_channel, TextChannel):
                    raise ValueError(f"Invalid channel <#{post_channel_id}> for bet posting.")

                # Use the preview image directly
                discord_file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    discord_file_to_send = File(self.preview_image_bytes, filename=f"bet_slip_{details['bet_serial']}.png")

                capper_data = await self.bot.db_manager.fetch_one(
                    "SELECT display_name, image_path FROM cappers WHERE guild_id = %s AND user_id = %s",
                    (interaction.guild_id, interaction.user.id)
                )
                webhook_username = capper_data.get("display_name") if capper_data and capper_data.get("display_name") else interaction.user.display_name
                webhook_avatar_url = None
                if capper_data and capper_data.get("image_path"):
                    webhook_avatar_url = capper_data["image_path"]

                # Fetch member_role for mention
                member_role_id = None
                guild_settings = await self.bot.db_manager.fetch_one(
                    "SELECT member_role FROM guild_settings WHERE guild_id = %s",
                    (str(interaction.guild_id),)
                )
                if guild_settings and guild_settings.get("member_role"):
                    member_role_id = guild_settings["member_role"]
                role_mention = f"<@&{member_role_id}>" if member_role_id else None

                webhooks = await post_channel.webhooks()
                target_webhook = None
                for webhook in webhooks:
                    if webhook.name == "Bet Bot":
                        target_webhook = webhook
                        break
                if not target_webhook:
                    target_webhook = await post_channel.create_webhook(name="Bet Bot")

                try:
                    webhook_content = role_mention if role_mention else None
                    # --- Capture the message returned by webhook.send ---
                    try:
                        webhook_message = await target_webhook.send(
                            content=webhook_content,
                            file=discord_file_to_send,
                            username=webhook_username,
                            avatar_url=webhook_avatar_url,
                            wait=True  # Ensure we get the Message object back
                        )
                    except Exception as e:
                        logger.error(f"Exception during webhook.send: {e}")
                        await self.edit_message(content="Error: Failed to post bet message via webhook (send failed).", view=None)
                        self.stop()
                        return
                    if not webhook_message:
                        logger.error("webhook.send returned None (no message object). Possible permission or Discord API error.")
                        await self.edit_message(content="Error: Bet message could not be posted (no message returned from webhook).", view=None)
                        self.stop()
                        return
                    # --- Update bet with message_id and channel_id ---
                    if bet_service:
                        try:
                            await bet_service.update_straight_bet_channel(
                                bet_serial=details["bet_serial"],
                                channel_id=webhook_message.channel.id,
                                message_id=webhook_message.id
                            )
                            logger.info(f"Updated bet {details['bet_serial']} with message_id {webhook_message.id} and channel_id {webhook_message.channel.id}")
                        except Exception as e:
                            logger.error(f"Failed to update bet with message_id: {e}")
                    await self.edit_message(content=f"✅ Bet #{details['bet_serial']} successfully posted!", view=None)
                    self.stop()
                except Exception as e:
                    logger.error(f"Error posting bet via webhook: {e}")
                    await self.edit_message(content="Error: Failed to post bet message.", view=None)
                    self.stop()
                    return
            except Exception as e:
                logger.exception(f"Error in submit_bet (outer try): {e}")
                await self.edit_message(content=f"❌ Error processing bet submission: {e}", view=None)
                self.stop()
        except Exception as e:
            logger.exception(f"[WORKFLOW TRACE] Exception in submit_bet: {e}")
            await self.edit_message(content=f"❌ Error in submit_bet: {e}", view=None)
            self.stop()

    async def on_timeout(self):
        logger.warning(f"StraightBetWorkflowView timed out for user {self.original_interaction.user.id}")
        await self.edit_message(
            content="⏰ Bet workflow timed out due to inactivity. Please start a new bet.", view=None
        )
        self.stop()

    def get_content(self, step_num: Optional[int] = None):
        if step_num is None:
            step_num = self.current_step
        if step_num == 1:
            return "Welcome to the Straight Betting Workflow! Please select your desired league from the list."
        if step_num == 2:
            return "Great choice! Now, please select the type of line you want to bet on."
        if step_num == 3:
            league = self.bet_details.get("league", "N/A")
            return f"Fetching available games for the selected league: **{league}**. Please wait..."
        if step_num == 4:
            return "No further action required. This is the final step."
        if step_num == 5:
            preview_info = "(Preview below)" if self.preview_image_bytes else "(Generating preview...)"
            return f"**Step {step_num}**: Select Units for your bet. {preview_info}"
        if step_num == 6:
            units = self.bet_details.get("units_str", "N/A")
            preview_info = "(Preview below)" if self.preview_image_bytes else "(Preview image failed)"
            return f"**Step {step_num}**: 🔒 Units: `{units}` 🔒 {preview_info}. Select Channel to post your bet."
        return "Processing your bet request..."

    async def _handle_units_selection(self, interaction: discord.Interaction, units: float):
        self.bet_details["units"] = units
        self.bet_details["units_str"] = str(units)
        bet_slip_image = None  # Always define this
        try:
            bet_type = self.bet_details.get("line_type", "game_line")
            league = self.bet_details.get("league", "N/A")
            home_team = self.bet_details.get("home_team_name", self.bet_details.get("team", "N/A"))
            away_team = self.bet_details.get("away_team_name", self.bet_details.get("opponent", "N/A"))
            line = self.bet_details.get("line", "N/A")
            odds = float(self.bet_details.get("odds", 0.0))
            bet_id = str(self.bet_details.get("preview_bet_serial", ""))
            timestamp = datetime.now(timezone.utc)
            if self.preview_image_bytes:
                self.preview_image_bytes.close()
                self.preview_image_bytes = None
            if bet_type == "game_line":
                generator = GameLineImageGenerator(guild_id=self.original_interaction.guild_id)
                bet_slip_image_bytes = generator.generate_bet_slip_image(
                    league=league,
                    home_team=home_team,
                    away_team=away_team,
                    line=line,
                    odds=odds,
                    units=units,
                    bet_id=bet_id,
                    timestamp=timestamp,
                    selected_team=self.bet_details.get("team", home_team),
                    output_path=None
                )
                if bet_slip_image_bytes:
                    self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                    self.preview_image_bytes.seek(0)
                    bet_slip_image = bet_slip_image_bytes
                else:
                    self.preview_image_bytes = None
                    bet_slip_image = None
            elif bet_type == "player_prop":
                generator = PlayerPropImageGenerator(guild_id=self.original_interaction.guild_id)
                player_name = self.bet_details.get("player_name")
                if not player_name and line:
                    player_name = line.split(' - ')[0] if ' - ' in line else line
                team_name = home_team
                league = self.bet_details.get("league", "N/A")
                odds_str = str(self.bet_details.get("odds_str", "")).strip()
                # Do NOT append odds to the line for player prop straight bets
                bet_slip_image_bytes = generator.generate_player_prop_bet_image(
                    player_name=player_name or team_name,
                    team_name=team_name,
                    league=league,
                    line=line,  # Only the line, no odds
                    units=units,
                    output_path=None,
                    bet_id=bet_id,
                    timestamp=timestamp,
                    guild_id=str(self.original_interaction.guild_id),
                    odds=odds  # Pass odds if needed for payout, not for display
                )
                if bet_slip_image_bytes:
                    self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                    self.preview_image_bytes.seek(0)
                    bet_slip_image = bet_slip_image_bytes
                else:
                    self.preview_image_bytes = None
                    bet_slip_image = None
            else:
                bet_slip_image = None
        except Exception as e:
            logger.exception(f"Error generating bet slip image after units selection: {e}")
            self.preview_image_bytes = None
        self.clear_items()
        self.add_item(UnitsSelect(self))
        self.add_item(ConfirmUnitsButton(self))
        self.add_item(CancelButton(self))
        file_to_send = None
        if self.preview_image_bytes:
            self.preview_image_bytes.seek(0)
            file_to_send = File(self.preview_image_bytes, filename="bet_preview_units.png")
        await self.edit_message(content=self.get_content(), view=self, file=file_to_send)

    def stop(self):
        self._stopped = True
        super().stop()


class StraightBetDetailsModal(Modal):
    def __init__(self, line_type: str, selected_league_key: str, bet_details_from_view: Dict, is_manual: bool = False):
        super().__init__(title="Enter Bet Details")
        self.line_type = line_type
        self.selected_league_key = selected_league_key
        self.bet_details = bet_details_from_view
        self.is_manual = is_manual
        self.view_ref = None

        # Always add player name input for player props
        if line_type == "player_prop":
            self.player_input = TextInput(
                label="Player Name",
                placeholder="Enter player name",
                required=True,
                custom_id="player_input"
            )
            self.add_item(self.player_input)

        # Add team/opponent fields for manual entry
        if is_manual:
            self.team_input = TextInput(
                label="Team",
                placeholder="Enter your team (e.g., Yankees)",
                required=True,
                custom_id="team_input"
            )
            self.add_item(self.team_input)
            if line_type == "game_line":
                self.opponent_input = TextInput(
                    label="Opponent",
                    placeholder="Enter opponent team (e.g., Red Sox)",
                    required=True,
                    custom_id="opponent_input"
                )
                self.add_item(self.opponent_input)

        # Add line input
        self.line_input = TextInput(
            label="Line (e.g., -110, +150, Over 2.5)",
            placeholder="Enter the line",
            required=True,
            custom_id="line_input"
        )
        self.add_item(self.line_input)

        # Add odds input
        self.odds_input = TextInput(
            label="Odds (e.g., -110, +150)",
            placeholder="Enter the odds",
            required=True,
            custom_id="odds_input"
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        # Set skip increment flag so go_next does not double-increment
        if self.view_ref:
            self.view_ref._skip_increment = True
        try:
            # --- FORCE line_type for player prop modal ---
            if self.line_type == "player_prop":
                self.bet_details["line_type"] = "player_prop"
            # Get values from inputs
            if self.is_manual:
                self.bet_details["team"] = self.team_input.value.strip()[:100] or "Team"
                self.bet_details["home_team_name"] = self.team_input.value.strip()[:100] or "Team"
                if self.line_type == "game_line":
                    self.bet_details["opponent"] = self.opponent_input.value.strip()[:100] or "Opponent"
                    self.bet_details["away_team_name"] = self.opponent_input.value.strip()[:100] or "Opponent"
                elif self.line_type == "player_prop":
                    self.bet_details["player_name"] = self.player_input.value.strip()[:100] or "Player"
                    # For player props, also set away_team_name to player name for right-side label
                    self.bet_details["away_team_name"] = self.bet_details["player_name"]
            elif self.line_type == "player_prop":
                # For non-manual, ensure player_name is set and used as away_team_name
                self.bet_details["player_name"] = self.player_input.value.strip()[:100] or "Player"
                self.bet_details["away_team_name"] = self.bet_details["player_name"]
            line = self.line_input.value.strip()[:100] or "Line"
            odds_str = self.odds_input.value.strip()[:100] or "0"
            # Validate odds format
            try:
                odds = float(odds_str)
            except ValueError:
                await interaction.followup.send("❌ Invalid odds format. Please enter a valid number (e.g., -110, +150)", ephemeral=True)
                return
            # Update bet details
            self.bet_details["line"] = line
            self.bet_details["odds"] = odds
            self.bet_details["odds_str"] = odds_str
            # Ensure all required fields are set for preview
            if 'home_team_name' not in self.bet_details:
                self.bet_details['home_team_name'] = self.view_ref.bet_details.get('home_team', self.view_ref.bet_details.get('team', 'Team'))[:100]
            if 'away_team_name' not in self.bet_details:
                # For player props, away_team_name should be player_name
                if self.bet_details.get("line_type") == "player_prop":
                    self.bet_details['away_team_name'] = self.bet_details.get('player_name', 'Player')[:100]
                else:
                    self.bet_details['away_team_name'] = self.view_ref.bet_details.get('away_team', self.view_ref.bet_details.get('opponent', 'Opponent'))[:100]
            if 'team' not in self.bet_details:
                self.bet_details['team'] = self.view_ref.bet_details.get('team', self.bet_details.get('home_team_name', 'Team'))[:100]
            if 'league' not in self.bet_details:
                self.bet_details['league'] = self.view_ref.bet_details.get('league', '')
            # Always generate preview image with units=1.0 for the first units selection
            preview_file = None
            preview_bytes = None
            try:
                # --- Use correct generator based on line_type ---
                if self.bet_details.get("line_type") == "player_prop":
                    generator = PlayerPropImageGenerator(guild_id=self.view_ref.original_interaction.guild_id)
                    image_bytes = generator.generate_player_prop_bet_image(
                        player_name=self.bet_details.get("player_name", self.bet_details.get("team", "")),
                        team_name=self.bet_details.get("team", ""),
                        league=self.bet_details.get("league", ""),
                        line=line,
                        units=1.0,
                        output_path=None,
                        bet_id=None,
                        timestamp=None,
                        guild_id=str(self.view_ref.original_interaction.guild_id),
                        odds=odds
                    )
                else:
                    generator = GameLineImageGenerator(guild_id=self.view_ref.original_interaction.guild_id)
                    image_bytes = generator.generate_bet_slip_image(
                        league=self.bet_details.get('league', ''),
                        home_team=self.bet_details.get('home_team_name', ''),
                        away_team=self.bet_details.get('away_team_name', ''),
                        line=line,
                        odds=odds_str,
                        units=1.0,
                        selected_team=self.bet_details.get('team', ''),
                        output_path=None
                    )
                preview_bytes = image_bytes
                preview_file = File(io.BytesIO(image_bytes), filename="bet_preview.png")
            except Exception as e:
                logging.error(f"[StraightBetDetailsModal] Failed to generate preview image: {e}\n{traceback.format_exc()}")
                preview_file = None
                preview_bytes = None

            # Set preview image bytes on the view for use in go_next
            if self.view_ref:
                if preview_bytes:
                    self.view_ref.preview_image_bytes = io.BytesIO(preview_bytes)
                    self.view_ref.preview_image_bytes.seek(0)
                else:
                    self.view_ref.preview_image_bytes = None
                # --- Assign bet serial for all bets after modal submit/preview ---
                if not self.bet_details.get("bet_serial"):
                    bet_service = getattr(self.view_ref.bot, "bet_service", None)
                    if bet_service:
                        bet_serial = await bet_service.create_straight_bet(
                            guild_id=self.view_ref.original_interaction.guild_id,
                            user_id=self.view_ref.original_interaction.user.id,
                            league=self.bet_details.get("league", "N/A"),
                            bet_type=self.line_type,
                            units=float(self.bet_details.get("units", 1.0)),
                            odds=float(self.bet_details.get("odds", 0.0)),
                            team=self.bet_details.get("team"),
                            opponent=self.bet_details.get("opponent"),
                            line=self.bet_details.get("line"),
                            api_game_id=self.bet_details.get("api_game_id"),
                            channel_id=None,
                            confirmed=0
                        )
                        if bet_serial:
                            self.bet_details["bet_serial"] = bet_serial
                            self.view_ref.bet_details["bet_serial"] = bet_serial
                if not interaction.response.is_done():
                    await interaction.response.defer()
                self.view_ref.current_step = 4  # Ensure next step is units selection
                await self.view_ref.go_next(interaction)
        except Exception as e:
            logging.error(f"[StraightBetDetailsModal] on_submit error: {e}\n{traceback.format_exc()}")
            await interaction.followup.send("❌ An error occurred while processing your bet. Please try again.", ephemeral=True)