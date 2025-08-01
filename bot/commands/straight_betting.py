# REV 1.0.0 - Enhanced straight betting workflow with improved game selection and bet slip generation
# betting-bot/commands/straight_betting.py

"""Straight betting workflow for placing single bets."""

import io
import json
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import discord
from discord import ButtonStyle, File, Interaction, Message, SelectOption, TextChannel
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, View

from bot.utils.game_line_image_generator import GameLineImageGenerator
from bot.utils.image_url_converter import convert_image_path_to_url
from bot.utils.league_loader import (
    get_all_league_names,
    get_all_sport_categories,
    get_leagues_by_sport,
)

# Using local StraightBetDetailsModal class instead of importing from utils.modals
from bot.utils.player_prop_image_generator import PlayerPropImageGenerator

logger = logging.getLogger(__name__)

# League name normalization mapping (used for display)
LEAGUE_FILE_KEY_MAP = {
    "La Liga": "LaLiga",
    "Serie A": "SerieA",
    "Ligue 1": "Ligue1",
    "EPL": "EPL",
    "Bundesliga": "Bundesliga",
    "MLS": "MLS",
    "Brazil Serie A": "Brazil_Serie_A",
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
    "MMA": "MMA",
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

# Add 'UEFA CL' as an alias for ChampionsLeague
LEAGUE_FILE_KEY_MAP["UEFA CL"] = "ChampionsLeague"


def get_league_file_key(league_name):
    key = LEAGUE_FILE_KEY_MAP.get(league_name, league_name.replace(" ", ""))
    if isinstance(key, list):
        return key[0]
    return key


class SportSelect(Select):
    def __init__(self, parent_view: View, sports: List[str]):
        self.parent_view = parent_view
        options = [SelectOption(label=sport, value=sport) for sport in sports]
        super().__init__(
            placeholder="Select Sport Category...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"straight_sport_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        self.parent_view.bet_details["sport"] = value
        self.disabled = True

        # Special handling for darts - send modal directly without deferring
        if value.lower() == "darts":
            logger.info(
                "[WORKFLOW TRACE] Darts selected in SportSelect - sending modal directly"
            )
            self.parent_view.bet_details["league"] = "DARTS"
            self.parent_view.bet_details["line_type"] = "game_line"
            self.parent_view.bet_details["is_manual"] = True
            self.parent_view.bet_details["home_team_name"] = "Manual Entry"
            self.parent_view.bet_details["away_team_name"] = "Manual Entry"

            # Create and send the modal directly
            modal = StraightBetDetailsModal(
                line_type="game_line",
                selected_league_key="DARTS",
                bet_details_from_view=self.parent_view.bet_details,
                is_manual=True,
                view_custom_id_suffix=str(interaction.id),
            )
            modal.view_ref = self.parent_view
            await interaction.response.send_modal(modal)
            return

        # For other sports, continue with normal flow
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class LeagueSelect(Select):
    def __init__(
        self, parent_view: View, leagues: List[str], page: int = 0, per_page: int = 21
    ):
        self.parent_view = parent_view
        self.page = page
        self.per_page = per_page
        self.leagues = leagues
        seen = set()
        unique_leagues = []
        for league in leagues:
            norm = league.replace(" ", "_").upper()
            if norm not in seen:
                seen.add(norm)
                unique_leagues.append(league)
        total_leagues = len(unique_leagues)
        max_page = max(0, (total_leagues - 1) // per_page)
        page = max(0, min(page, max_page))
        start = page * per_page
        end = start + per_page
        page_leagues = unique_leagues[start:end]
        if not page_leagues:
            page_leagues = unique_leagues[0:per_page]
            self.page = 0
        options = [
            SelectOption(label=league[:100], value=league[:100])
            for league in page_leagues
        ]
        options.append(SelectOption(label="Manual", value="MANUAL"))
        if end < total_leagues:
            options.append(SelectOption(label="Next ➡️", value="NEXT"))
        if page > 0:
            options.insert(0, SelectOption(label="⬅️ Previous", value="PREVIOUS"))
        super().__init__(
            placeholder="Select League...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"straight_league_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if value == "NEXT":
            await self.parent_view.update_league_page(interaction, self.page + 1)
            return
        elif value == "PREVIOUS":
            await self.parent_view.update_league_page(interaction, self.page - 1)
            return
        self.parent_view.bet_details["league"] = value
        logger.debug(f"League selected: {value} by user {interaction.user.id}")
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
                label="Player Props"[:100],
                value="player_prop"[:100],
                description="Player-specific betting lines",
            ),
        ]
        super().__init__(
            placeholder="Select Line Type...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        # Set line type for game line
        self.parent_view.bet_details["line_type"] = self.values[0]
        logger.debug(
            f"Line Type selected: {self.parent_view.bet_details['line_type']} by user {interaction.user.id}"
        )
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class GameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict]):
        pass

        import pytz

        game_options = []
        seen_values = set()
        eastern = pytz.timezone("US/Eastern")
        # --- Filter out finished games here as well ---
        finished_statuses = [
            "Match Finished",
            "Finished",
            "FT",
            "Game Finished",
            "Final",
        ]
        filtered_games = []
        for game in games:
            status = (game.get("status") or "").strip()
            if status not in finished_statuses:
                filtered_games.append(game)
            else:
                logger.debug(
                    f"[GameSelect] Excluding game {game.get('api_game_id')} ({game.get('home_team_name')} vs {game.get('away_team_name')}) - status: {status}"
                )
        # Always add manual entry as the first option
        game_options.append(
            SelectOption(
                label="📝 Manual Entry",
                value="manual",
                description="Enter game details manually",
            )
        )

        # Only include up to 23 games (Discord limit is 25 options, we have 1 manual entry + 23 games = 24 total)
        for game in filtered_games[:23]:
            # Skip manual entry if it exists in the games list
            if game.get("id") == "manual" or game.get("api_game_id") == "manual":
                continue

            # Prefer api_game_id if present, else use internal id
            if game.get("api_game_id"):
                value = f"api_{game['api_game_id']}"
            elif game.get("id"):
                value = f"dbid_{game['id']}"
            else:
                continue  # skip if neither id present
            if value in seen_values:
                continue
            seen_values.add(value)

            home_team = game.get("home_team_name", "").strip() or "N/A"
            away_team = game.get("away_team_name", "").strip() or "N/A"

            # Format the label with team names (no status)
            label = f"{home_team} vs {away_team}"
            label = label[:100] if label else "N/A"
            # Get start time for description
            start_time = game.get("start_time")
            if start_time:
                # Format start_time as EST string
                try:
                    eastern = pytz.timezone("US/Eastern")
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
                SelectOption(label=label, value=value, description=desc[:100])
            )
        super().__init__(
            placeholder="Select a game or choose Manual Entry",
            options=game_options,
            min_values=1,
            max_values=1,
        )
        self.parent_view = parent_view
        self.games = filtered_games
        logger.debug(
            f"Created GameSelect with {len(game_options)} unique options (including manual entry)."
        )

    async def callback(self, interaction: Interaction):
        selected_value = self.values[0]
        logger.debug(f"Selected game value: {selected_value}")
        if selected_value == "manual":
            self.parent_view.bet_details.update(
                {
                    "api_game_id": None,
                    "is_manual": True,
                    "home_team_name": "Manual Entry",
                    "away_team_name": "Manual Entry",
                }
            )
        else:
            selected_game = None
            if selected_value.startswith("api_"):
                api_game_id = selected_value[4:]
                selected_game = next(
                    (g for g in self.games if str(g.get("api_game_id")) == api_game_id),
                    None,
                )
            elif selected_value.startswith("dbid_"):
                dbid = selected_value[5:]
                selected_game = next(
                    (g for g in self.games if str(g.get("id")) == dbid), None
                )
            if selected_game:
                self.parent_view.bet_details.update(
                    {
                        "api_game_id": selected_game.get("api_game_id"),
                        "game_id": selected_game.get("id"),
                        "home_team_name": selected_game.get("home_team_name"),
                        "away_team_name": selected_game.get(
                            "away_team_name"
                        ),  # <-- FIXED KEY
                        "is_manual": False,
                    }
                )
                logger.debug(f"Updated bet details: {self.parent_view.bet_details}")
            else:
                logger.error(f"Could not find game for selected value {selected_value}")
                await interaction.response.defer()
                await self.parent_view.edit_message(
                    content="Error: Could not find the selected game. Please try again or cancel.",
                    view=None,
                )
                self.parent_view.stop()
                return

            # Always proceed to the next step in the workflow
            # Team selection will be handled in go_next method
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
                bet_service = getattr(self.parent_view.bot, "bet_service", None)
                if bet_service:
                    await bet_service.delete_bet(bet_serial)
                    logger.info(f"Deleted bet {bet_serial} after cancellation")
                await interaction.response.edit_message(
                    content=f"Bet `{bet_serial}` cancelled.", view=None
                )
            except Exception as e:
                logger.error(f"Failed to delete bet {bet_serial}: {e}")
                await interaction.response.edit_message(
                    content=f"Bet cancellation failed for `{bet_serial}`.", view=None
                )
        else:
            await interaction.response.edit_message(
                content="Bet workflow cancelled.", view=None
            )
        self.parent_view.stop()


class TeamSelect(Select):
    def __init__(self, parent_view: View, home_team: str, away_team: str):
        self.parent_view = parent_view

        # Ensure we have valid team names
        if not home_team or not away_team:
            raise ValueError(
                f"Invalid team names: home_team='{home_team}', away_team='{away_team}'"
            )

        options = [
            SelectOption(
                label=home_team[:100],
                value=(home_team[:96] + "_home") if home_team else "home",
            ),
            SelectOption(
                label=away_team[:100],
                value=(away_team[:96] + "_away") if away_team else "away",
            ),
        ]
        super().__init__(
            placeholder="Which team are you selecting?",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        selected_value = self.values[0]
        # Map back to team names
        home_team = self.parent_view.bet_details.get("home_team_name", "")
        away_team = self.parent_view.bet_details.get("away_team_name", "")
        if selected_value.endswith("_home"):
            selected_team = home_team
            opponent = away_team
        else:
            selected_team = away_team
            opponent = home_team
        self.parent_view.bet_details["team"] = selected_team
        self.parent_view.bet_details["opponent"] = opponent
        logger.info(
            f"[TEAM SELECT] Selected team: {selected_team}, opponent: {opponent}"
        )
        logger.info(
            f"[TEAM SELECT] Updated bet details: {self.parent_view.bet_details}"
        )

        is_manual = self.parent_view.bet_details.get("is_manual", False)

        if is_manual:
            # For manual entries, show modal for line/odds input
            line_type = self.parent_view.bet_details.get("line_type", "game_line")
            modal = StraightBetDetailsModal(
                line_type=line_type,
                selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
                bet_details_from_view=self.parent_view.bet_details,
                is_manual=is_manual,
                view_custom_id_suffix=str(interaction.id),
            )
            modal.view_ref = self.parent_view
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
                return
            else:
                logger.error(
                    "Tried to send modal, but interaction already responded to."
                )
                await self.parent_view.edit_message(
                    content="❌ Error: Could not open modal. Please try again or cancel.",
                    view=None,
                )
                self.parent_view.stop()
                return
        else:
            # For regular game selections, show modal for line/odds input
            line_type = self.parent_view.bet_details.get("line_type", "game_line")
            modal = StraightBetDetailsModal(
                line_type=line_type,
                selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
                bet_details_from_view=self.parent_view.bet_details,
                is_manual=False,
                view_custom_id_suffix=str(interaction.id),
            )
            modal.view_ref = self.parent_view
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
                return
            else:
                logger.error(
                    "Tried to send modal, but interaction already responded to."
                )
                await self.parent_view.edit_message(
                    content="❌ Error: Could not open modal. Please try again or cancel.",
                    view=None,
                )
                self.parent_view.stop()
                return


class UnitsSelect(Select):
    def __init__(self, parent_view: View, units_display_mode="auto"):
        self.parent_view = parent_view
        self.units_display_mode = units_display_mode
        options = []
        if units_display_mode == "manual":
            # Add To Win group
            options.append(
                SelectOption(
                    label="--- To Win ---",
                    value="separator_win",
                    default=False,
                    description=None,
                    emoji=None,
                )
            )
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(
                    SelectOption(
                        label=f"To Win {u:.1f} Unit" + ("" if u == 1.0 else "s"),
                        value=f"{u}|win",
                    )
                )
            # Add To Risk group
            options.append(
                SelectOption(
                    label="--- To Risk ---",
                    value="separator_risk",
                    default=False,
                    description=None,
                    emoji=None,
                )
            )
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(
                    SelectOption(
                        label=f"Risk {u:.1f} Unit" + ("" if u == 1.0 else "s"),
                        value=f"{u}|risk",
                    )
                )
        else:
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(
                    SelectOption(
                        label=f"{u:.1f} Unit" + ("" if u == 1.0 else "s"), value=str(u)
                    )
                )
        super().__init__(
            placeholder="Select Units for Bet...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if self.units_display_mode == "manual":
            if value.startswith("separator"):
                await interaction.response.defer(ephemeral=True)
                return
            units_str, mode = value.split("|")
            units = float(units_str)
            display_as_risk = mode == "risk"
            self.parent_view.bet_details["units_str"] = units_str
            self.parent_view.bet_details["units"] = units
            self.parent_view.bet_details["display_as_risk"] = display_as_risk
        else:
            self.parent_view.bet_details["units_str"] = value
            self.parent_view.bet_details["units"] = float(value)
            self.parent_view.bet_details["display_as_risk"] = None
        logger.debug(f"Units selected: {value} by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view._handle_units_selection(
            interaction, float(self.parent_view.bet_details["units"])
        )


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
            options.append(
                SelectOption(
                    label="No channels available", value="none_available", emoji="❌"
                )
            )
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
                view=None,
            )
            self.parent_view.stop()
            return
        self.parent_view.bet_details["channel_id"] = int(channel_id_str)
        logger.debug(
            f"Channel selected: {channel_id_str} by user {interaction.user.id}"
        )
        self.disabled = True
        await interaction.response.defer()
        # Set to 7 so go_next increments to 8 (final confirm step)
        self.parent_view.current_step = 7
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
        # Check if manual entry is selected
        is_manual = self.parent_view.bet_details.get("is_manual", False)
        line_type = self.parent_view.bet_details.get("line_type", "game_line")
        if is_manual:
            modal = StraightBetDetailsModal(
                line_type=line_type,
                selected_league_key=self.parent_view.bet_details.get("league", "OTHER"),
                bet_details_from_view=self.parent_view.bet_details,
                is_manual=True,
                view_custom_id_suffix=str(interaction.id),
            )
            modal.view_ref = self.parent_view
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
                await self.parent_view.edit_message(
                    content="Please fill in the bet details in the popup form.",
                    view=self.parent_view,
                )
            else:
                logger.error(
                    "Tried to send modal, but interaction already responded to."
                )
                await interaction.followup.send(
                    "❌ Error: Could not open modal. Please try again.", ephemeral=True
                )
                self.parent_view.stop()
                return
        else:
            home_team = self.parent_view.bet_details.get("home_team_name", "")
            away_team = self.parent_view.bet_details.get("away_team_name", "")
            self.parent_view.clear_items()
            self.parent_view.add_item(
                TeamSelect(self.parent_view, home_team, away_team)
            )
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
    def __init__(
        self,
        original_interaction: Interaction,
        bot: commands.Bot,
        message_to_control: Optional[Message] = None,
    ):
        super().__init__(timeout=1800)
        self.original_interaction = original_interaction
        self.bot = bot
        self.message = message_to_control
        self.current_step = 0
        self.bet_details: Dict[str, Any] = {}
        self.games: List[Dict] = []
        self.is_processing = False
        self.latest_interaction = original_interaction
        self.bet_slip_generator: Optional[
            Union[GameLineImageGenerator, PlayerPropImageGenerator]
        ] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        self.home_team: Optional[str] = None
        self.away_team: Optional[str] = None
        self.league: Optional[str] = None
        self.line: Optional[str] = None
        self.odds: Optional[float] = None
        self.bet_id: Optional[str] = None
        self._stopped = False

    async def get_bet_slip_generator(
        self,
    ) -> GameLineImageGenerator:
        if not self.bet_slip_generator or not isinstance(
            self.bet_slip_generator, GameLineImageGenerator
        ):
            self.bet_slip_generator = GameLineImageGenerator(
                guild_id=self.original_interaction.guild_id
            )
        return self.bet_slip_generator

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        logger.debug(
            f"Starting straight bet workflow on message ID: {self.message.id if self.message else 'None'}"
        )
        if not self.message:
            logger.error(
                "StraightBetWorkflowView.start_flow called but self.message is None."
            )
            self.stop()
            return
        try:
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.exception(
                f"Failed during initial go_next in StraightBetWorkflow: {e}"
            )
            await self.edit_message(
                content="❌ Failed to start bet workflow. Please try again.", view=None
            )
            self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            # Don't send a new message, just deny the interaction silently
            # or edit the original message to show the error
            await interaction.response.defer()
            await self.edit_message(
                content="❌ Only the original user can interact with this bet workflow.",
                view=None,
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
            logger.error(
                "Cannot edit message: self.message is None. This should never happen. Stopping workflow."
            )
            self.stop()
            return
        try:
            await self.message.edit(
                content=content, embed=embed, view=view, attachments=attachments
            )
        except discord.NotFound:
            logger.warning(
                f"Failed to edit message {self.message.id}: Not Found. Stopping view."
            )
            self.stop()
        except discord.HTTPException as e:
            logger.error(
                f"HTTP error editing message {self.message.id}: {e}", exc_info=True
            )
        except Exception as e:
            logger.exception(f"Unexpected error editing message {self.message.id}: {e}")

    async def _handle_step_1_sport_selection(self, interaction: Interaction):
        """Handle step 1: Sport category selection."""
        sports = get_all_sport_categories()
        self.clear_items()
        self.add_item(SportSelect(self, sports))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_2_league_selection(self, interaction: Interaction):
        """Handle step 2: League selection within selected sport."""
        sport = self.bet_details.get("sport")
        leagues = get_leagues_by_sport(sport)
        self.clear_items()
        self.add_item(LeagueSelect(self, leagues))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_3_line_type_selection(self, interaction: Interaction):
        """Handle step 3: Line type selection."""
        self.clear_items()
        self.add_item(LineTypeSelect(self))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_4_game_selection(self, interaction: Interaction):
        """Handle step 4: Game selection based on line type."""
        line_type = self.bet_details.get("line_type", "game_line")
        league = self.bet_details.get("league", "N/A")
        logger.info(
            f"[WORKFLOW TRACE] Fetching games for league: {league}, line_type: {line_type}"
        )

        try:
            # For player props, we don't need to fetch games - show modal directly
            if line_type == "player_prop":
                logger.info(
                    "[WORKFLOW TRACE] Player prop selected - showing modal directly"
                )
                modal = StraightBetDetailsModal(
                    line_type=line_type,
                    selected_league_key=self.bet_details.get("league", "OTHER"),
                    bet_details_from_view=self.bet_details,
                    is_manual=True,  # Player props are always manual entry
                    view_custom_id_suffix=str(interaction.id),
                )
                modal.view_ref = self
                if not interaction.response.is_done():
                    await interaction.response.send_modal(modal)
                    return
                else:
                    logger.error(
                        "Tried to send modal, but interaction already responded to."
                    )
                    await self.edit_message(
                        content="❌ Error: Could not open modal. Please try again or cancel.",
                        view=None,
                    )
                    self.stop()
                    return

            # For game lines, fetch games
            from bot.data.game_utils import get_normalized_games_for_dropdown

            games = await get_normalized_games_for_dropdown(self.bot.db_manager, league)

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

    async def _handle_step_5_team_selection(self, interaction: Interaction):
        """Handle step 5: Team selection or modal for manual entry."""
        is_manual = self.bet_details.get("is_manual", False)

        if is_manual:
            # Show modal for manual entry
            modal = StraightBetDetailsModal(
                line_type=self.bet_details.get("line_type", "game_line"),
                selected_league_key=self.bet_details.get("league", "OTHER"),
                bet_details_from_view=self.bet_details,
                is_manual=True,
                view_custom_id_suffix=str(interaction.id),
            )
            modal.view_ref = self
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
            else:
                logger.error(
                    "Tried to send modal, but interaction already responded to."
                )
                await self.edit_message(
                    content="❌ Error: Could not open modal. Please try again or cancel.",
                    view=None,
                )
                self.stop()
        else:
            # Show team selection
            home_team = self.bet_details.get("home_team_name", "Unknown")
            away_team = self.bet_details.get("away_team_name", "Unknown")

            self.clear_items()
            self.add_item(TeamSelect(self, home_team, away_team))
            self.add_item(CancelButton(self))
            await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_6_units_selection(self, interaction: Interaction):
        """Handle step 6: Units selection."""
        self.clear_items()
        self.add_item(UnitsSelect(self))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_7_channel_selection(self, interaction: Interaction):
        """Handle step 7: Channel selection."""
        guild = interaction.guild
        if not guild:
            await self.edit_message(
                content="❌ Error: Could not determine guild. Please try again.",
                view=None,
            )
            self.stop()
            return

        # Get text channels with embed permissions
        channels = [
            channel
            for channel in guild.text_channels
            if channel.permissions_for(guild.me).embed_links
        ]

        if not channels:
            await self.edit_message(
                content="❌ No channels with embed permissions found. Please contact an administrator.",
                view=None,
            )
            self.stop()
            return

        self.clear_items()
        self.add_item(ChannelSelect(self, channels))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def _handle_step_8_final_confirmation(self, interaction: Interaction):
        """Handle step 8: Final confirmation."""
        self.clear_items()
        self.add_item(FinalConfirmButton(self))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)

    async def go_next(self, interaction: Interaction):
        """Advance to the next step in the betting workflow."""
        if hasattr(self, "_skip_increment") and self._skip_increment:
            self._skip_increment = False
            return

        self.current_step += 1
        logger.info(f"[WORKFLOW TRACE] go_next called for step {self.current_step}")

        # Use step-specific handlers
        step_handlers = {
            1: self._handle_step_1_sport_selection,
            2: self._handle_step_2_league_selection,
            3: self._handle_step_3_line_type_selection,
            4: self._handle_step_4_game_selection,
            5: self._handle_step_5_team_selection,
            6: self._handle_step_6_units_selection,
            7: self._handle_step_7_channel_selection,
            8: self._handle_step_8_final_confirmation,
        }

        handler = step_handlers.get(self.current_step)
        if handler:
            await handler(interaction)
        else:
            logger.error(f"Unknown step: {self.current_step}")
            await self.edit_message(
                content="❌ Error: Unknown workflow step. Please try again or cancel.",
                view=None,
            )
            self.stop()

    async def _generate_bet_slip_image(
        self, details: Dict, bet_id: str, timestamp
    ) -> Optional[File]:
        """Generate bet slip image and return as Discord File."""
        try:
            gen = await self.get_bet_slip_generator()
            bet_slip_image_bytes = gen.generate_bet_slip_image(
                league=details.get("league", ""),
                home_team=details.get("home_team_name", ""),
                away_team=details.get("away_team_name", ""),
                line=details.get("line", ""),
                odds=details.get("odds", 0.0),
                units=details.get("units", 1.0),
                bet_id=bet_id,
                timestamp=timestamp,
                selected_team=details.get("team", details.get("home_team_name", "")),
                output_path=None,
                units_display_mode="auto",
                display_as_risk=False,
            )

            if bet_slip_image_bytes:
                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                self.preview_image_bytes.seek(0)
                return File(
                    self.preview_image_bytes, filename=f"bet_slip_{bet_id}.webp"
                )
            else:
                logger.warning(
                    f"Straight bet {bet_id}: Failed to generate bet slip image."
                )
                return None
        except Exception as e:
            logger.error(f"Error generating bet slip image: {e}")
            return None

    async def _get_capper_data(
        self, interaction: discord.Interaction
    ) -> Tuple[str, Optional[str]]:
        """Get capper display name and avatar URL."""
        capper_data = await self.bot.db_manager.fetch_one(
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
            logger.info(f"Found capper image_path: {capper_data['image_path']}")
            webhook_avatar_url = convert_image_path_to_url(capper_data["image_path"])
            logger.info(f"Converted webhook_avatar_url: {webhook_avatar_url}")
        else:
            logger.info(f"No capper image_path found for user {interaction.user.id}")

        return webhook_username, webhook_avatar_url

    async def _get_member_role_mention(
        self, interaction: discord.Interaction
    ) -> Optional[str]:
        """Get member role mention if configured."""
        guild_settings = await self.bot.db_manager.fetch_one(
            "SELECT member_role FROM guild_settings WHERE guild_id = %s",
            (str(interaction.guild_id),),
        )

        if guild_settings and guild_settings.get("member_role"):
            return f"<@&{guild_settings['member_role']}>"
        return None

    async def _get_or_create_webhook(self, post_channel) -> Optional[discord.Webhook]:
        """Get existing webhook or create new one."""
        try:
            webhooks = await post_channel.webhooks()
            target_webhook = None
            for webhook in webhooks:
                if webhook.name == "Bet Bot":
                    target_webhook = webhook
                    break
            if not target_webhook:
                target_webhook = await post_channel.create_webhook(name="Bet Bot")
            return target_webhook
        except Exception as e:
            logger.error(f"Error getting/creating webhook: {e}")
            return None

    async def _post_bet_via_webhook(
        self,
        post_channel,
        webhook_username: str,
        webhook_avatar_url: Optional[str],
        discord_file_to_send: Optional[File],
        member_mention: Optional[str],
    ) -> Optional[discord.Message]:
        """Post bet via webhook and return message object."""
        target_webhook = await self._get_or_create_webhook(post_channel)
        if not target_webhook:
            return None

        try:
            webhook_message = await target_webhook.send(
                content=member_mention,
                file=discord_file_to_send,
                username=webhook_username,
                avatar_url=webhook_avatar_url,
                wait=True,
            )
            return webhook_message
        except Exception as e:
            logger.error(f"Exception during webhook.send: {e}")
            return None

    async def _update_bet_with_message_info(
        self, bet_service, details: Dict, webhook_message: discord.Message
    ):
        """Update bet record with message and channel information."""
        if bet_service:
            try:
                await bet_service.update_straight_bet_channel(
                    bet_serial=details["bet_serial"],
                    channel_id=webhook_message.channel.id,
                    message_id=webhook_message.id,
                )
                logger.info(f"Updated bet {details['bet_serial']} with message info")
            except Exception as e:
                logger.error(f"Error updating bet with message info: {e}")

    async def submit_bet(self, interaction: Interaction):
        """Submit the bet and post it to the selected channel."""
        try:
            # Get bet details
            details = self.bet_details
            post_channel = self.selected_channel

            if not post_channel:
                await self.edit_message(
                    content="❌ Error: No channel selected. Please try again.",
                    view=None,
                )
                self.stop()
                return

            # Create bet service and submit bet
            from bot.services.bet_service import BetService

            bet_service = BetService(self.bot.db_manager)

            bet_result = await bet_service.create_straight_bet(
                guild_id=interaction.guild_id,
                user_id=interaction.user.id,
                league=details.get("league", ""),
                sport=details.get("sport", ""),
                home_team=details.get("home_team_name", ""),
                away_team=details.get("away_team_name", ""),
                team=details.get("team", ""),
                opponent=details.get("opponent", ""),
                line=details.get("line", ""),
                odds=details.get("odds", 0.0),
                units=details.get("units", 1.0),
                line_type=details.get("line_type", "game_line"),
                player_name=details.get("player_name", ""),
                game_id=details.get("game_id"),
            )

            if not bet_result.get("success"):
                await self.edit_message(
                    content=f"❌ Error creating bet: {bet_result.get('error', 'Unknown error')}",
                    view=None,
                )
                self.stop()
                return

            # Generate bet slip image
            bet_id = str(bet_result["bet_serial"])
            timestamp = datetime.now(timezone.utc)
            discord_file_to_send = await self._generate_bet_slip_image(
                details, bet_id, timestamp
            )

            # Get capper data
            webhook_username, webhook_avatar_url = await self._get_capper_data(
                interaction
            )

            # Get member role mention
            member_mention = await self._get_member_role_mention(interaction)

            # Post bet via webhook
            webhook_message = await self._post_bet_via_webhook(
                post_channel,
                webhook_username,
                webhook_avatar_url,
                discord_file_to_send,
                member_mention,
            )

            if not webhook_message:
                await self.edit_message(
                    content="Error: Failed to post bet message via webhook.",
                    view=None,
                )
                self.stop()
                return

            # Update bet with message info
            await self._update_bet_with_message_info(
                bet_service, details, webhook_message
            )

            # Success message
            await self.edit_message(
                content=f"✅ Bet submitted successfully! Check <#{post_channel.id}>",
                view=None,
            )
            self.stop()

        except Exception as e:
            logger.error(f"Error in submit_bet: {e}", exc_info=True)
            await self.edit_message(
                content=f"❌ Error submitting bet: {str(e)}",
                view=None,
            )
            self.stop()

    async def on_timeout(self):
        logger.warning(
            f"StraightBetWorkflowView timed out for user {self.original_interaction.user.id}"
        )
        await self.edit_message(
            content="⏰ Bet workflow timed out due to inactivity. Please start a new bet.",
            view=None,
        )
        self.stop()

    def get_content(self, step_num: Optional[int] = None):
        if step_num is None:
            step_num = self.current_step
        if step_num == 1:
            return "Welcome to the Straight Betting Workflow! Please select your desired sport category from the list."
        if step_num == 2:
            return "Great choice! Now, please select the league within your chosen sport category."
        if step_num == 3:
            return "Now, please select the line type for your bet (Game Line or Player Props)."
        if step_num == 4:
            league = self.bet_details.get("league", "N/A")
            return f"Fetching available games for the selected league: **{league}**. Please wait..."
        if step_num == 5:
            return "No further action required. This is the final step."
        if step_num == 6:
            preview_info = (
                "(Preview below)"
                if self.preview_image_bytes
                else "(Generating preview...)"
            )
            return f"**Step {step_num}**: Select Units for your bet. {preview_info}"
        if step_num == 6:
            units = self.bet_details.get("units_str", "N/A")
            preview_info = (
                "(Preview below)"
                if self.preview_image_bytes
                else "(Preview image failed)"
            )
            return f"**Step {step_num}**: 🔒 Units: `{units}` 🔒 {preview_info}. Select Channel to post your bet."
        return "Processing your bet request..."

    def _determine_units_display_mode(
        self, units: float, odds: float
    ) -> Tuple[str, bool]:
        """Determine units display mode and risk display based on units and odds."""
        from bot.utils.bet_utils import determine_risk_win_display_auto

        units_display_mode = "auto"
        display_as_risk = determine_risk_win_display_auto(odds, units, 0.0)

        return units_display_mode, display_as_risk

    async def _generate_game_line_preview(
        self, units: float, units_display_mode: str, display_as_risk: bool
    ) -> bool:
        """Generate game line preview image. Returns True if successful."""
        try:
            gen = await self.get_bet_slip_generator()
            home_team = self.bet_details.get("home_team_name", "")
            away_team = self.bet_details.get("away_team_name", "")
            line = self.bet_details.get("line", "")
            odds = float(self.bet_details.get("odds", 0.0))
            bet_id = str(self.bet_details.get("bet_serial", ""))
            timestamp = datetime.now(timezone.utc)

            bet_slip_image_bytes = gen.generate_bet_slip_image(
                league=self.bet_details.get("league", ""),
                home_team=home_team,
                away_team=away_team,
                line=line,
                odds=odds,
                units=units,
                bet_id=bet_id,
                timestamp=timestamp,
                selected_team=self.bet_details.get("team", home_team),
                output_path=None,
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )

            if bet_slip_image_bytes:
                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                self.preview_image_bytes.seek(0)
                return True
            else:
                self.preview_image_bytes = None
                return False
        except Exception as e:
            logger.error(f"Error generating game line preview: {e}")
            self.preview_image_bytes = None
            return False

    async def _generate_player_prop_preview(
        self, units: float, units_display_mode: str, display_as_risk: bool
    ) -> bool:
        """Generate player prop preview image. Returns True if successful."""
        try:
            from bot.utils.player_prop_image_generator import PlayerPropImageGenerator

            generator = PlayerPropImageGenerator(
                guild_id=self.original_interaction.guild_id
            )

            player_name = self.bet_details.get("player_name")
            line = self.bet_details.get("line", "")
            if not player_name and line:
                player_name = line.split(" - ")[0] if " - " in line else line

            team_name = self.bet_details.get("home_team_name", "")
            league = self.bet_details.get("league", "N/A")
            odds = float(self.bet_details.get("odds", 0.0))
            bet_id = str(self.bet_details.get("bet_serial", ""))
            timestamp = datetime.now(timezone.utc)

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
                odds=odds,  # Pass odds if needed for payout, not for display
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )

            if bet_slip_image_bytes:
                self.preview_image_bytes = io.BytesIO(bet_slip_image_bytes)
                self.preview_image_bytes.seek(0)
                return True
            else:
                self.preview_image_bytes = None
                return False
        except Exception as e:
            logger.error(f"Error generating player prop preview: {e}")
            self.preview_image_bytes = None
            return False

    async def _generate_preview_image(self, units: float) -> bool:
        """Generate preview image based on bet type. Returns True if successful."""
        bet_type = self.bet_details.get("line_type", "game_line")

        # Determine display mode
        odds = float(self.bet_details.get("odds", 0.0))
        units_display_mode, display_as_risk = self._determine_units_display_mode(
            units, odds
        )

        try:
            if bet_type == "game_line":
                return await self._generate_game_line_preview(
                    units, units_display_mode, display_as_risk
                )
            elif bet_type == "player_prop":
                return await self._generate_player_prop_preview(
                    units, units_display_mode, display_as_risk
                )
            else:
                logger.warning(f"Unknown bet type: {bet_type}")
                return False
        except Exception as e:
            logger.exception(
                f"Error generating bet slip image after units selection: {e}"
            )
            self.preview_image_bytes = None
            return False

    async def _update_ui_with_preview(self):
        """Update the UI with preview image and buttons."""
        self.clear_items()
        self.add_item(UnitsSelect(self))
        self.add_item(ConfirmUnitsButton(self))
        self.add_item(CancelButton(self))

        file_to_send = None
        if self.preview_image_bytes:
            self.preview_image_bytes.seek(0)
            file_to_send = File(
                self.preview_image_bytes, filename="bet_preview_units.webp"
            )

        await self.edit_message(
            content=self.get_content(), view=self, file=file_to_send
        )

    async def _handle_units_selection(
        self, interaction: discord.Interaction, units: float
    ):
        """Handle units selection and generate preview image."""
        # Update bet details
        self.bet_details["units"] = units
        self.bet_details["units_str"] = str(units)

        # Generate preview image
        await self._generate_preview_image(units)

        # Update UI
        await self._update_ui_with_preview()

    def stop(self):
        self._stopped = True
        super().stop()

    async def update_league_page(self, interaction, page):
        leagues = get_all_league_names()
        self.clear_items()
        self.add_item(LeagueSelect(self, leagues, page=page))
        self.add_item(CancelButton(self))
        await self.edit_message(content=self.get_content(), view=self)


class StraightBetDetailsModal(Modal):
    def __init__(
        self,
        line_type: str,
        selected_league_key: str,
        bet_details_from_view: Dict,
        is_manual: bool = False,
        view_custom_id_suffix: str = "",
    ):
        # Get league-specific title
        title = self._get_league_specific_title(selected_league_key)
        super().__init__(title=title)
        self.line_type = line_type
        self.selected_league_key = selected_league_key
        self.bet_details = bet_details_from_view.copy() if bet_details_from_view else {}
        self.is_manual = is_manual
        self.view_ref = None
        self.view_custom_id_suffix = view_custom_id_suffix or str(uuid.uuid4())

        # Add manual entry fields if needed
        self._add_manual_entry_fields()

    def _get_league_specific_title(self, league: str) -> str:
        """Get league-specific modal title."""
        league_titles = {
            "Formula-1": "🏎️ Game Line Bet",
            "PGA": "⛳ Game Line Bet",
            "LPGA": "⛳ Game Line Bet",
            "EuropeanTour": "⛳ Game Line Bet",
            "LIVGolf": "⛳ Game Line Bet",
            "ATP": "🎾 Game Line Bet",
            "WTA": "🎾 Game Line Bet",
            "Tennis": "🎾 Game Line Bet",
            "MMA": "🥊 Game Line Bet",
            "Bellator": "🥊 Game Line Bet",
            "PDC": "🎯 Game Line Bet",
            "BDO": "🎯 Game Line Bet",
            "WDF": "🎯 Game Line Bet",
            "NBA": "🏀 Game Line Bet",
            "WNBA": "🏀 Game Line Bet",
            "NFL": "🏈 Game Line Bet",
            "MLB": "⚾ Game Line Bet",
            "NHL": "🏒 Game Line Bet",
            "Soccer": "⚽ Game Line Bet",
            "EPL": "⚽ Game Line Bet",
            "LaLiga": "⚽ Game Line Bet",
            "Bundesliga": "⚽ Game Line Bet",
            "SerieA": "⚽ Game Line Bet",
            "Ligue1": "⚽ Game Line Bet",
            "ChampionsLeague": "⚽ Game Line Bet",
            "EuropaLeague": "⚽ Game Line Bet",
            "WorldCup": "⚽ Game Line Bet",
        }
        return league_titles.get(league, "🎯 Game Line Bet")

    def _add_manual_entry_fields(self):
        """Add team/opponent fields for manual entry"""
        if self.is_manual:
            # Get league config to check sport type
            from bot.config.leagues import LEAGUE_CONFIG

            league_conf = LEAGUE_CONFIG.get(self.selected_league_key, {})
            sport_type = league_conf.get("sport_type", "Team Sport")
            is_individual_sport = sport_type == "Individual Player"

            # Handle player props
            if self.line_type == "player_prop":
                # For player props, add player name field
                player_label = league_conf.get("player_label", "Player Name")
                player_placeholder = league_conf.get(
                    "player_placeholder", "e.g., John Smith"
                )

                # League-specific player suggestions
                if self.selected_league_key == "NBA":
                    player_placeholder = "e.g., LeBron James, Stephen Curry"
                elif self.selected_league_key == "MLB":
                    player_placeholder = "e.g., Aaron Judge, Shohei Ohtani"
                elif self.selected_league_key == "NHL":
                    player_placeholder = "e.g., Connor McDavid, Nathan MacKinnon"
                elif self.selected_league_key == "NFL":
                    player_placeholder = "e.g., Patrick Mahomes, Travis Kelce"
                elif self.selected_league_key in ["ATP", "WTA", "Tennis"]:
                    player_placeholder = "e.g., Novak Djokovic, Iga Swiatek"
                elif self.selected_league_key in [
                    "PGA",
                    "LPGA",
                    "EuropeanTour",
                    "LIVGolf",
                ]:
                    player_placeholder = "e.g., Scottie Scheffler, Nelly Korda"
                elif self.selected_league_key in ["MMA", "Bellator"]:
                    player_placeholder = "e.g., Jon Jones, Patricio Pitbull"
                elif self.selected_league_key == "Formula-1":
                    player_placeholder = "e.g., Max Verstappen, Lewis Hamilton"
                elif self.selected_league_key in ["PDC", "BDO", "WDF", "DARTS"]:
                    player_placeholder = "e.g., Michael van Gerwen, Peter Wright"

                self.player_name_input = TextInput(
                    label=player_label,
                    placeholder=player_placeholder,
                    required=True,
                    custom_id=f"player_name_input_{self.view_custom_id_suffix}",
                )
                self.add_item(self.player_name_input)
                return  # Don't add other fields for player props

            if is_individual_sport or self.selected_league_key == "DARTS":
                # For individual sports (darts, tennis, golf, MMA, etc.), show player and opponent
                player_label = league_conf.get("participant_label", "Player")
                player_placeholder = league_conf.get(
                    "team_placeholder", "e.g., Player Name"
                )
                # League-specific player suggestions
                if (
                    self.selected_league_key
                    in [
                        "PDC",
                        "BDO",
                        "WDF",
                        "PremierLeagueDarts",
                        "WorldMatchplay",
                        "WorldGrandPrix",
                        "UKOpen",
                        "GrandSlam",
                        "PlayersChampionship",
                        "EuropeanChampionship",
                        "Masters",
                    ]
                    or self.selected_league_key == "DARTS"
                ):
                    player_placeholder = "e.g., Michael van Gerwen, Peter Wright"
                elif self.selected_league_key in ["ATP", "WTA", "Tennis"]:
                    player_placeholder = "e.g., Novak Djokovic, Iga Swiatek"
                elif self.selected_league_key in [
                    "PGA",
                    "LPGA",
                    "EuropeanTour",
                    "LIVGolf",
                ]:
                    player_placeholder = "e.g., Scottie Scheffler, Nelly Korda"
                elif self.selected_league_key in ["MMA", "Bellator"]:
                    player_placeholder = "e.g., Jon Jones, Patricio Pitbull"
                elif self.selected_league_key == "Formula-1":
                    player_placeholder = "e.g., Max Verstappen, Lewis Hamilton"
                self.player_input = TextInput(
                    label=player_label,
                    placeholder=player_placeholder,
                    required=True,
                    custom_id=f"player_input_{self.view_custom_id_suffix}",
                )
                self.add_item(self.player_input)
                if self.line_type == "game_line":
                    opponent_label = league_conf.get("opponent_label", "Opponent")
                    opponent_placeholder = league_conf.get(
                        "opponent_placeholder", "e.g., Opponent Name"
                    )
                    # League-specific opponent suggestions
                    if (
                        self.selected_league_key
                        in [
                            "PDC",
                            "BDO",
                            "WDF",
                            "PremierLeagueDarts",
                            "WorldMatchplay",
                            "WorldGrandPrix",
                            "UKOpen",
                            "GrandSlam",
                            "PlayersChampionship",
                            "EuropeanChampionship",
                            "Masters",
                        ]
                        or self.selected_league_key == "DARTS"
                    ):
                        opponent_placeholder = "e.g., Peter Wright, Gerwyn Price"
                    elif self.selected_league_key in ["ATP", "WTA", "Tennis"]:
                        opponent_placeholder = "e.g., Rafael Nadal, Aryna Sabalenka"
                    elif self.selected_league_key in [
                        "PGA",
                        "LPGA",
                        "EuropeanTour",
                        "LIVGolf",
                    ]:
                        opponent_placeholder = "e.g., Rory McIlroy, Lydia Ko"
                    elif self.selected_league_key in ["MMA", "Bellator"]:
                        opponent_placeholder = "e.g., Francis Ngannou, Cris Cyborg"
                    elif self.selected_league_key == "Formula-1":
                        opponent_placeholder = "e.g., Lewis Hamilton, Charles Leclerc"
                    self.opponent_input = TextInput(
                        label=opponent_label,
                        placeholder=opponent_placeholder,
                        required=True,
                        custom_id=f"opponent_input_{self.view_custom_id_suffix}",
                    )
                    self.add_item(self.opponent_input)
            else:
                # For team sports, show team and opponent (existing logic)
                self.team_input = TextInput(
                    label="Your Team",
                    placeholder="e.g., Yankees, Lakers, Chiefs",
                    required=True,
                    custom_id=f"team_input_{self.view_custom_id_suffix}",
                )
                self.add_item(self.team_input)
                if self.line_type == "game_line":
                    self.opponent_input = TextInput(
                        label="Opponent Team",
                        placeholder="e.g., Red Sox, Celtics, Bills",
                        required=True,
                        custom_id=f"opponent_input_{self.view_custom_id_suffix}",
                    )
                    self.add_item(self.opponent_input)

        # Add line input (for all types except player props which have their own)
        if self.line_type != "player_prop":
            self.line_input = TextInput(
                label="Bet Line",
                placeholder="e.g., -110, +150, Over 2.5, Under 1.5",
                required=True,
                custom_id=f"line_input_{self.view_custom_id_suffix}",
            )
            self.add_item(self.line_input)
        else:
            # For player props, add prop line input
            self.prop_line_input = TextInput(
                label="Player Prop Line",
                placeholder="e.g., Over 25.5 points, Under 8.5 rebounds, Over 2.5 touchdowns",
                required=True,
                custom_id=f"prop_line_input_{self.view_custom_id_suffix}",
            )
            self.add_item(self.prop_line_input)

        # Add odds input
        self.odds_input = TextInput(
            label="Odds",
            placeholder="e.g., -110, +150, +200",
            required=True,
            custom_id=f"odds_input_{self.view_custom_id_suffix}",
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        try:
            # Get values from inputs
            line = "Line"  # Default value

            if self.is_manual:
                # Handle player props
                if self.line_type == "player_prop":
                    self.bet_details["player_name"] = (
                        self.player_name_input.value.strip()[:100] or "Player"
                    )
                    self.bet_details["team"] = (
                        self.player_name_input.value.strip()[:100] or "Player"
                    )
                    self.bet_details["home_team_name"] = (
                        self.player_name_input.value.strip()[:100] or "Player"
                    )
                    # For player props, use the prop line as the main line
                    line = self.prop_line_input.value.strip()[:100] or "Prop Line"
                else:
                    # Get league config to check sport type
                    from bot.config.leagues import LEAGUE_CONFIG

                    league_conf = LEAGUE_CONFIG.get(self.selected_league_key, {})
                    sport_type = league_conf.get("sport_type", "Team Sport")
                    is_individual_sport = sport_type == "Individual Player"

                    if is_individual_sport or self.selected_league_key == "DARTS":
                        # For individual sports, use player and opponent
                        self.bet_details["player_name"] = (
                            self.player_input.value.strip()[:100] or "Player"
                        )
                        self.bet_details["team"] = (
                            self.player_input.value.strip()[:100] or "Player"
                        )
                        self.bet_details["home_team_name"] = (
                            self.player_input.value.strip()[:100] or "Player"
                        )
                        if self.line_type == "game_line" and hasattr(
                            self, "opponent_input"
                        ):
                            self.bet_details["opponent"] = (
                                self.opponent_input.value.strip()[:100] or "Opponent"
                            )
                            self.bet_details["away_team_name"] = (
                                self.opponent_input.value.strip()[:100] or "Opponent"
                            )

                    else:
                        # For team sports, use team and opponent (existing logic)
                        self.bet_details["team"] = (
                            self.team_input.value.strip()[:100] or "Team"
                        )
                        self.bet_details["home_team_name"] = (
                            self.team_input.value.strip()[:100] or "Team"
                        )
                        if self.line_type == "game_line":
                            self.bet_details["opponent"] = (
                                self.opponent_input.value.strip()[:100] or "Opponent"
                            )
                            self.bet_details["away_team_name"] = (
                                self.opponent_input.value.strip()[:100] or "Opponent"
                            )

                    line = self.line_input.value.strip()[:100] or "Line"
            else:
                # For non-manual entries (existing games), get line from line_input
                if hasattr(self, "line_input"):
                    line = self.line_input.value.strip()[:100] or "Line"

            odds_str = self.odds_input.value.strip()[:100] or "0"
            # Validate odds format
            try:
                odds = float(odds_str)
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid odds format. Please enter a valid number (e.g., -110, +150)",
                    ephemeral=True,
                )
                return
            # Update bet details
            self.bet_details["line"] = line
            self.bet_details["odds"] = odds
            self.bet_details["odds_str"] = odds_str
            # Ensure all required fields are set for preview
            if "home_team_name" not in self.bet_details:
                self.bet_details["home_team_name"] = self.view_ref.bet_details.get(
                    "home_team", self.view_ref.bet_details.get("team", "Team")
                )[:100]
            if "away_team_name" not in self.bet_details:
                self.bet_details["away_team_name"] = self.view_ref.bet_details.get(
                    "away_team",
                    self.view_ref.bet_details.get("opponent", "Opponent"),
                )[:100]
            if "team" not in self.bet_details:
                self.bet_details["team"] = self.view_ref.bet_details.get(
                    "team", self.bet_details.get("home_team_name", "Team")
                )[:100]
            if "league" not in self.bet_details:
                self.bet_details["league"] = self.view_ref.bet_details.get("league", "")
            # Always generate preview image with units=1.0 for the first units selection
            preview_file = None
            preview_bytes = None
            try:
                generator = GameLineImageGenerator(
                    guild_id=self.view_ref.original_interaction.guild_id
                )

                # Use different generator for player props
                if self.line_type == "player_prop":
                    from bot.utils.player_prop_image_generator import (
                        PlayerPropImageGenerator,
                    )

                    generator = PlayerPropImageGenerator(
                        guild_id=self.view_ref.original_interaction.guild_id
                    )
                    image_bytes = generator.generate_player_prop_bet_image(
                        league=self.bet_details.get("league", ""),
                        player_name=self.bet_details.get("player_name", ""),
                        prop_line=self.bet_details.get("line", ""),
                        odds=self.bet_details.get("odds_str", ""),
                        units=1.0,
                        user_id=self.view_ref.original_interaction.user.id,
                        guild_id=self.view_ref.original_interaction.guild_id,
                    )
                else:
                    image_bytes = generator.generate_bet_slip_image(
                        league=self.bet_details.get("league", ""),
                        home_team=self.bet_details.get("home_team_name", ""),
                        away_team=self.bet_details.get("away_team_name", ""),
                        line=line,
                        odds=odds_str,
                        units=1.0,
                        selected_team=self.bet_details.get("team", ""),
                        output_path=None,
                    )
                preview_bytes = image_bytes
                preview_file = File(
                    io.BytesIO(image_bytes), filename="bet_preview.webp"
                )
            except Exception as e:
                logging.error(
                    f"[StraightBetDetailsModal] Failed to generate preview image: {e}\n{traceback.format_exc()}"
                )
                preview_bytes = None

            # Set preview image bytes on the view for use in go_next
            if self.view_ref:
                if preview_bytes:
                    self.view_ref.preview_image_bytes = io.BytesIO(preview_bytes)
                    self.view_ref.preview_image_bytes.seek(0)
                else:
                    self.view_ref.preview_image_bytes = None

                # Update the view's bet_details with the modal data
                self.view_ref.bet_details.update(self.bet_details)

                if not interaction.response.is_done():
                    await interaction.response.defer()

                # Go to units selection (step 6)
                self.view_ref.current_step = (
                    5  # Set to 5 so go_next increments to 6 (units selection)
                )
                await self.view_ref.go_next(interaction)
        except Exception as e:
            logging.error(
                f"[StraightBetDetailsModal] on_submit error: {e}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(
                "❌ An error occurred while processing your bet. Please try again.",
                ephemeral=True,
            )
