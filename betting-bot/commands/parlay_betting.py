# betting-bot/commands/parlay_betting.py

"""Parlay betting workflow for placing multi-leg bets."""

import discord
from discord import app_commands, ButtonStyle, Interaction, SelectOption, TextChannel, File, Embed, Webhook, Message
from discord.ui import View, Select, Modal, TextInput, Button
import logging
from typing import Optional, List, Dict, Union, Any 
from datetime import datetime, timezone
import io
import uuid 
import os
import json 
from discord.ext import commands
from utils.errors import BetServiceError, ValidationError, GameNotFoundError
from utils.image_generator import BetSlipGenerator
from config.asset_paths import get_sport_category_for_path
from config.team_mappings import normalize_team_name
from data.game_utils import get_normalized_games_for_dropdown
from utils.validators import validate_units
from utils.formatters import format_parlay_bet_details_embed
from utils.bet_utils import calculate_parlay_payout, fetch_next_bet_serial
from utils.parlay_bet_image_generator import ParlayBetImageGenerator
from config.leagues import LEAGUE_IDS

logger = logging.getLogger(__name__)

# Add league name normalization mapping
LEAGUE_FILE_KEY_MAP = {
    'La Liga': 'LaLiga',
    'Serie A': 'SerieA',
    'Ligue 1': 'Ligue1',
    'EPL': 'EPL',
    'Bundesliga': 'Bundesliga',
    'MLS': 'MLS',
    'NBA': 'NBA',
    'WNBA': 'WNBA',
    'MLB': 'MLB',
    'NHL': 'NHL',
    'NFL': 'NFL',
    'NCAA': ['NCAAF' , 'NCAAB', 'NCAABM', 'NCAABW' , 'NCAAFBS', 'NCAAVB', 'NCAAFB', 'NCAAWBB', 'NCAAWVB', 'NCAAWFB'],
    'NPB': 'NPB',
    'KBO': 'KBO',
    'KHL': 'KHL',
    'PDC': 'PDC',
    'BDO': 'BDO',
    'WDF': 'WDF',
    'Premier League Darts': 'PremierLeagueDarts',
    'World Matchplay': 'WorldMatchplay',
    'World Grand Prix': 'WorldGrandPrix',
    'UK Open': 'UKOpen',
    'Grand Slam': 'GrandSlam',
    'Players Championship': 'PlayersChampionship',
    'European Championship': 'EuropeanChampionship',
    'Masters': 'Masters',
    'Champions League': 'ChampionsLeague',
    'TENNIS': ['WTP', 'ATP', 'WTA'],
    'ESPORTS':['CSGO', 'VALORANT', 'LOL', 'DOTA 2', 'PUBG', 'COD'],
    'OTHER_SPORTS':['OTHER_SPORTS'],
    # Add more as needed
}

def get_league_file_key(league_name):
    key = LEAGUE_FILE_KEY_MAP.get(league_name, league_name.replace(' ', ''))
    if isinstance(key, list):
        return key[0]
    return key

# --- UI Component Classes ---
class LeagueSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', leagues: List[str]):
        self.parent_view = parent_view
        # Deduplicate while preserving order
        seen = set()
        unique_leagues = []
        for league in leagues:
            norm = league.replace(" ", "_").upper()
            if norm not in seen:
                seen.add(norm)
                unique_leagues.append(league)
        options = [SelectOption(label=league, value=league.replace(" ", "_").upper()) for league in unique_leagues[:24]]
        options.append(SelectOption(label="Other", value="OTHER"))
        super().__init__(placeholder="Select League for this Leg...", options=options, min_values=1, max_values=1, custom_id=f"parlay_league_select_{uuid.uuid4()}")

    async def callback(self, interaction: Interaction):
        self.parent_view.current_leg_construction_details['league'] = self.values[0]
        logger.debug(f"Parlay Leg - League selected: {self.values[0]} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)

class LineTypeSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        self.parent_view = parent_view
        options = [
            SelectOption(label="Game Line", value="game_line", description="Moneyline or game over/under"),
            SelectOption(label="Player Prop", value="player_prop", description="Bet on player performance")
        ]
        super().__init__(placeholder="Select Line Type for this Leg...", options=options, min_values=1, max_values=1, custom_id=f"parlay_linetype_select_{uuid.uuid4()}")

    async def callback(self, interaction: Interaction):
        try:
            logger.debug(f"[LineTypeSelect] Callback triggered. Value: {self.values[0]}")
            self.parent_view.current_leg_construction_details['line_type'] = self.values[0]
            logger.debug(f"Parlay Leg - Line Type selected: {self.values[0]} by user {interaction.user.id}")
            self.disabled = True
            for item in self.parent_view.children:
                if isinstance(item, Select) and item != self:
                    item.disabled = True
            await interaction.response.defer()
            await self.parent_view.go_next(interaction)
        except Exception as e:
            logger.exception(f"[LineTypeSelect] Error in callback: {e}")
            try:
                await interaction.response.send_message("❌ Error processing line type selection. Please try again.", ephemeral=True)
            except Exception as send_e:
                logger.error(f"[LineTypeSelect] Failed to send error message: {send_e}")

class ConfirmGameButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', selected_game_id: str):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm Game Selection",
            custom_id=f"parlay_confirm_game_{parent_view.original_interaction.id}_{selected_game_id}"
        )
        self.parent_view = parent_view
        self.selected_game_id = selected_game_id

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        await self.parent_view.handle_game_selection(interaction, self.selected_game_id)

class ParlayGameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict], selected_games: List[str] = None, selected_value: str = None, confirmed: bool = False):
        self.parent_view = parent_view
        self.selected_value = selected_value
        self.confirmed = confirmed
        options = []
        selected_games = selected_games or []
        logger.info(f"[ParlayGameSelect] Initializing with {len(games)} games, {len(selected_games)} already selected")
        # Always add Manual Entry option first, with a unique value
        manual_entry_value = f"manual_entry_{uuid.uuid4()}"
        options.append(SelectOption(
            label="Manual Entry",
            value=manual_entry_value,
            description="Manually enter game details",
            default=(self.selected_value == manual_entry_value)
        ))
        logger.info("[ParlayGameSelect] Added Manual Entry option")
        # Only include up to 24 games (Discord limit is 25 options including manual entry)
        for game in games[:24]:
            try:
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
                    logger.warning(f"[ParlayGameSelect] Game missing api_game_id: {label}")
                    continue
                # Skip already selected games
                if str(game_api_id) in selected_games:
                    logger.info(f"[ParlayGameSelect] Skipping already selected game: {label}")
                    continue
                # Ensure unique value for each game
                option_value = f"game_{game_api_id}_{uuid.uuid4()}"
                option = SelectOption(
                    label=label[:100],  # Discord has a 100 char limit
                    value=option_value,
                    description=f"Start: {start_time}" if start_time else None,
                    default=(self.selected_value == option_value)
                )
                options.append(option)
                logger.info(f"[ParlayGameSelect] Added game option: {label} (ID: {game_api_id})")
            except Exception as e:
                logger.error(f"[ParlayGameSelect] Error processing game for dropdown: {e}", exc_info=True)
                continue
        super().__init__(
            placeholder="Select a Game for Parlay",
            min_values=1,
            max_values=1,
            options=options,
            disabled=self.confirmed
        )
        logger.info(f"[ParlayGameSelect] Initialized with {len(options)} total options")

    async def callback(self, interaction: Interaction):
        try:
            logger.info(f"[ParlayGameSelect] Game selected: {self.values[0]}")
            self.disabled = True
            confirm_button = ConfirmGameButton(self.parent_view, self.values[0])
            self.parent_view.clear_items()
            self.parent_view.add_item(self)  # Add the same (now disabled) dropdown
            self.parent_view.add_item(confirm_button)
            self.parent_view.add_item(CancelButton(self.parent_view))
            await self.parent_view.edit_message_for_current_leg(
                interaction,
                content="Confirm your game selection for this parlay leg.",
                view=self.parent_view
            )
        except Exception as e:
            logger.error(f"[ParlayGameSelect] Error in callback: {e}", exc_info=True)
            await interaction.response.send_message("Error processing game selection. Please try again.", ephemeral=True)

class ManualEntryButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(style=ButtonStyle.green, label="Manual Entry for Leg", custom_id=f"parlay_manual_entry_{parent_view.original_interaction.id}_{len(parent_view.bet_details.get('legs',[]))}")
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Manual Entry button clicked by user {interaction.user.id} for parlay leg.")
        self.parent_view.current_leg_construction_details['game_id'] = "Other"
        self.disabled = True
        for item in self.parent_view.children:
            if isinstance(item, (Select, Button)) and item != self: item.disabled = True
        
        line_type = self.parent_view.current_leg_construction_details.get('line_type', 'game_line')
        leg_number = len(self.parent_view.bet_details.get('legs', [])) + 1
        try:
            modal = BetDetailsModal(line_type=line_type, is_manual=True, leg_number=leg_number, view_custom_id_suffix=self.parent_view.original_interaction.id)
            modal.view_ref = self.parent_view
            await interaction.response.send_modal(modal)
            logger.debug("Manual entry modal for parlay leg sent.")
            await self.parent_view.edit_message_for_current_leg(
                interaction, content="Manual entry form opened for leg. Please fill details.", view=self.parent_view
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to send manual entry modal for parlay leg: {e}")
            await self.parent_view.edit_message_for_current_leg(interaction, content="❌ Failed to open form. Please restart.", view=None)
            self.parent_view.stop()

class CancelButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(style=ButtonStyle.red, label="Cancel Parlay", custom_id=f"parlay_cancel_{parent_view.original_interaction.id}")
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Cancel Parlay button clicked by user {interaction.user.id}")
        for item in self.parent_view.children: item.disabled = True
        bet_serial = self.parent_view.bet_details.get('bet_serial')
        if bet_serial and hasattr(self.parent_view.bot, 'bet_service'):
            try: await self.parent_view.bot.bet_service.delete_bet(bet_serial)
            except Exception as e: logger.error(f"Error deleting parlay bet {bet_serial} on cancel: {e}")
        await interaction.response.edit_message(content="Parlay workflow cancelled.", view=None)
        self.parent_view.stop()

class BetDetailsModal(Modal):
    def __init__(self, line_type: str, is_manual: bool = False, leg_number: int = 1, view_custom_id_suffix: str = ""):
        title = f"Leg {leg_number}: Enter Details"
        super().__init__(title=title[:45], custom_id=f"parlay_leg_modal_{leg_number}_{view_custom_id_suffix}")
        self.line_type = line_type
        self.is_manual = is_manual
        self.leg_number = leg_number
        self.view_ref: Optional['ParlayBetWorkflowView'] = None

        # For player prop, ask for player name and line (no odds)
        if self.line_type == "player_prop":
            self.player_name_input = TextInput(
                label="Player Name",
                required=True,
                max_length=100,
                placeholder="e.g., LeBron James, Shohei Ohtani"
            )
            self.add_item(self.player_name_input)
            self.prop_line_input = TextInput(
                label="Player Prop / Line",
                required=True,
                max_length=100,
                placeholder="e.g., Over 25.5 Points, Over 7.5 Assists"
            )
            self.add_item(self.prop_line_input)
        else:
            # Game line: if manual, ask for team/opponent
            if self.is_manual:
                self.team_input = TextInput(
                    label="Team Involved",
                    required=True,
                    max_length=100,
                    placeholder="Enter team name"
                )
                self.add_item(self.team_input)
                self.opponent_input = TextInput(
                    label="Opponent for this Leg",
                    required=True,
                    max_length=100,
                    placeholder="Enter opponent name"
                )
                self.add_item(self.opponent_input)
            self.line_input = TextInput(
                label="Line (e.g., Moneyline, Spread -X.X)",
                required=True,
                max_length=100,
                placeholder="Enter line details"
            )
            self.add_item(self.line_input)

    async def on_submit(self, interaction: Interaction):
        if not self.view_ref:
            logger.error("ParlayBetWorkflowView reference not found in BetDetailsModal.")
            await interaction.response.send_message("Internal error: View reference missing.", ephemeral=True)
            return

        logger.debug(f"Parlay Leg Modal {self.leg_number} submitted by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            current_details = self.view_ref.current_leg_construction_details
            league = current_details.get('league', 'UNKNOWN')
            leg_details_to_add = {
                'game_id': current_details.get('game_id') if current_details.get('game_id') != 'Other' else None,
                'bet_type': self.line_type,
                'league': league
            }
            if self.line_type == "player_prop":
                player_name = self.player_name_input.value.strip()
                prop_line = self.prop_line_input.value.strip()
                leg_details_to_add.update({
                    'player_name': player_name,
                    'team': player_name,
                    'line': prop_line
                })
            else:
                if self.is_manual:
                    team = self.team_input.value.strip()
                    opponent = self.opponent_input.value.strip()
                else:
                    team = current_details.get('home_team_name')
                    opponent = current_details.get('away_team_name')
                line_value = self.line_input.value.strip()
                leg_details_to_add.update({
                    'team': team,
                    'opponent': opponent,
                    'line': line_value
                })
            # Load team logo if available
            bet_slip_gen = await self.view_ref.get_bet_slip_generator()
            team_logo_path = None
            try:
                logo_image = bet_slip_gen._load_team_logo(leg_details_to_add.get('team'), league)
                if logo_image:
                    normalized_name = bet_slip_gen._normalize_team_name(leg_details_to_add.get('team', '')).replace('.', '')
                    sport = get_sport_category_for_path(league.upper()) or 'OTHER_SPORTS'
                    team_dir = os.path.join(bet_slip_gen.LEAGUE_TEAM_BASE_DIR, sport, league.upper())
                    logo_file = f"{normalize_team_name(normalized_name)}.png"
                    logo_path = os.path.join(team_dir, logo_file)
                    if os.path.exists(logo_path):
                        team_logo_path = logo_path
                    else:
                        team_logo_path = bet_slip_gen.DEFAULT_LOGO_PATH
                    logo_image.close()
            except Exception:
                team_logo_path = None
            if team_logo_path:
                leg_details_to_add['team_logo_path'] = team_logo_path
            await self.view_ref.add_leg(interaction, leg_details_to_add)
        except Exception as e:
            logger.exception(f"Error in Parlay Leg Modal {self.leg_number} on_submit: {e}")
            await interaction.followup.send("❌ Failed to process leg details. Please restart parlay.", ephemeral=True)
            self.view_ref.stop()

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.error(f"Error in Parlay Leg Modal {self.leg_number}: {error}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Modal error.', ephemeral=True)
            else:
                await interaction.followup.send('❌ Modal error.', ephemeral=True)
        except discord.HTTPException:
            pass
        if self.view_ref:
            self.view_ref.stop()

class TotalOddsModal(Modal):
    def __init__(self, view_custom_id_suffix: str = ""):
        super().__init__(title="Enter Total Parlay Odds", custom_id=f"parlay_total_odds_{view_custom_id_suffix}")
        self.view_ref: Optional['ParlayBetWorkflowView'] = None
        self.odds = TextInput(label="Total Parlay Odds", required=True, max_length=10, placeholder="American odds (e.g., -110, +200)")
        self.add_item(self.odds)

    async def on_submit(self, interaction: Interaction):
        if not self.view_ref:
            logger.error("ParlayBetWorkflowView reference not found in TotalOddsModal.")
            await interaction.response.send_message("Internal error: View reference missing.", ephemeral=True)
            return

        logger.debug(f"Parlay Total Odds Modal submitted by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            odds_str_value = self.odds.value.strip()
            if not odds_str_value:
                await interaction.followup.send("❌ Total odds are required.", ephemeral=True)
                return

            try:
                odds_float = float(odds_str_value.replace('+', ''))
                if -100 < odds_float < 100 and odds_float != 0:
                    raise ValueError("Odds out of range.")
            except ValueError as ve:
                await interaction.followup.send(f"❌ Invalid total odds: '{odds_str_value}'. {ve}", ephemeral=True)
                return

            self.view_ref.bet_details['total_odds'] = odds_float
            self.view_ref.bet_details['total_odds_str'] = odds_str_value
            logger.info(f"Total parlay odds set to {odds_str_value} for bet {self.view_ref.bet_details.get('bet_serial')}")

            await self.view_ref.go_next(interaction)
        except Exception as e:
            logger.exception(f"Error in TotalOddsModal on_submit: {e}")
            await interaction.followup.send("❌ Failed to process total odds. Please restart parlay.", ephemeral=True)
            if self.view_ref:
                self.view_ref.stop()

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.error(f"Error in TotalOddsModal: {error}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Modal error.', ephemeral=True)
            else:
                await interaction.followup.send('❌ Modal error.', ephemeral=True)
        except discord.HTTPException:
            pass
        if self.view_ref:
            self.view_ref.stop()

class UnitsSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', units_display_mode='auto'):
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
            placeholder="Select Total Units for Parlay...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_units_select_{parent_view.original_interaction.id}"
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
        logger.debug(f"Parlay Units selected: {value} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view._handle_units_selection(interaction, float(self.parent_view.bet_details['units']))

class ChannelSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', channels: List[TextChannel]):
        self.parent_view = parent_view
        sorted_channels = sorted(channels, key=lambda x: x.name.lower())
        options = [
            SelectOption(label=ch.name, value=str(ch.id), description=f"ID: {ch.id}"[:100])
            for ch in sorted_channels[:25]
        ]
        if not options:
            options.append(SelectOption(label="No embed channels configured", value="none_configured", emoji="🚫"))

        super().__init__(placeholder="Select channel to post parlay...", options=options, min_values=1, max_values=1, custom_id=f"parlay_channel_select_{parent_view.original_interaction.id}", disabled=(not options or options[0].value == "none_configured"))

    async def callback(self, interaction: Interaction):
        if self.values[0] == "none_configured":
            await interaction.response.send_message("No embed channels are available. Please ask an admin to configure them.", ephemeral=True)
            return
            
        self.parent_view.bet_details["channel_id"] = int(self.values[0])
        logger.debug(f"Parlay Channel selected: {self.values[0]} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)

class FinalConfirmButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm & Post Parlay",
            custom_id=f"parlay_final_confirm_{parent_view.original_interaction.id}"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Final confirm parlay button clicked by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        await self.parent_view.submit_bet(interaction)

class AddLegButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(style=ButtonStyle.green, label="Add Another Leg", custom_id=f"parlay_add_leg_{parent_view.original_interaction.id}_{len(parent_view.bet_details.get('legs',[])) +1}")
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Add Leg button clicked by user {interaction.user.id}")
        self.parent_view.current_step = 0
        self.parent_view.current_leg_construction_details = {}
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)

class FinalizeButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(style=ButtonStyle.blurple, label="Finalize Parlay", custom_id=f"parlay_finalize_{parent_view.original_interaction.id}", disabled=len(parent_view.bet_details.get('legs', [])) < 1)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Finalize Parlay button clicked by user {interaction.user.id}")
        legs_data = self.parent_view.bet_details.get('legs', [])
        if not legs_data:
            await interaction.response.send_message("❌ Cannot finalize empty parlay.", ephemeral=True); return

        if "bet_serial" not in self.parent_view.bet_details:
            try:
                primary_league = legs_data[0].get('league') if legs_data else "PARLAY"
                bet_serial = await self.parent_view.bot.bet_service.create_parlay_bet(
                    guild_id=interaction.guild_id, user_id=interaction.user.id,
                    legs=legs_data,
                    channel_id=None,
                    league=primary_league
                )
                if not bet_serial: raise BetServiceError("Failed to create parlay record (no serial).")
                self.parent_view.bet_details['bet_serial'] = bet_serial
                logger.info(f"Parlay bet record {bet_serial} created upon finalization attempt.")
            except BetServiceError as bse:
                logger.error(f"Error creating parlay record on finalize: {bse}")
                await interaction.response.send_message(f"❌ Error initializing parlay: {bse}", ephemeral=True)
                self.parent_view.stop(); return

        for item in self.parent_view.children: item.disabled = True
        await interaction.response.defer()
        self.parent_view.current_step = 4
        await self.parent_view.go_next(interaction)

class LegDecisionView(View):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(timeout=600)
        self.parent_view = parent_view
        self.add_item(AddLegButton(self.parent_view))
        finalize_button = FinalizeButton(self.parent_view)
        finalize_button.disabled = len(self.parent_view.bet_details.get('legs', [])) < 1
        self.add_item(finalize_button)
        self.add_item(CancelButton(self.parent_view))

class TeamSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', home_team: str, away_team: str):
        self.parent_view = parent_view
        # Ensure unique values even if team names are the same
        options = [
            SelectOption(label=home_team[:100], value=f"{home_team[:90]}-home"),
            SelectOption(label=away_team[:100], value=f"{away_team[:90]}-away"),
        ]
        super().__init__(
            placeholder="Which team are you selecting?",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        try:
            selected_value = self.values[0]
            home_team = self.parent_view.current_leg_construction_details.get("home_team_name", "")
            away_team = self.parent_view.current_leg_construction_details.get("away_team_name", "")
            logger.debug(f"[TeamSelect] Callback triggered. selected_value={selected_value}, home_team={home_team}, away_team={away_team}")
            if not home_team or not away_team:
                logger.error(f"[TeamSelect] Missing team names: home_team={home_team}, away_team={away_team}")
                await interaction.response.send_message("❌ Internal error: Team names missing. Please restart this parlay leg.", ephemeral=True)
                self.parent_view.stop()
                return
            if selected_value.endswith("-home"):
                selected_team = home_team
                opponent = away_team
            else:
                selected_team = away_team
                opponent = home_team
            self.parent_view.current_leg_construction_details["team"] = selected_team
            self.parent_view.current_leg_construction_details["opponent"] = opponent
            line_type = self.parent_view.current_leg_construction_details.get("line_type", "game_line")
            modal = BetDetailsModal(
                line_type=line_type,
                is_manual=False,
                leg_number=len(self.parent_view.bet_details.get('legs', [])) + 1,
                view_custom_id_suffix=self.parent_view.original_interaction.id
            )
            modal.view_ref = self.parent_view
            if not interaction.response.is_done():
                await interaction.response.send_modal(modal)
                return  # Fix: Do not edit message after sending modal
            else:
                logger.error("Tried to send modal, but interaction already responded to.")
                await self.parent_view.edit_message_for_current_leg(
                    interaction, content="❌ Error: Could not open modal. Please try again or cancel.", view=None
                )
                self.parent_view.stop()
                return
        except Exception as e:
            logger.exception(f"[TeamSelect] Error in callback: {e}")
            try:
                await interaction.response.send_message("❌ Error processing team selection. Please try again.", ephemeral=True)
            except Exception as send_e:
                logger.error(f"[TeamSelect] Failed to send error message: {send_e}")
            self.parent_view.stop()

# --- Main Workflow View ---
class ParlayBetWorkflowView(View):
    def __init__(self, original_interaction: Interaction, bot: commands.Bot, message_to_control: Optional[Message] = None):
        super().__init__(timeout=1800)
        self.original_interaction = original_interaction
        self.bot = bot
        self.message = message_to_control
        self.current_step = 0
        self.bet_details: Dict[str, Any] = {
            'legs': [],
            'total_odds': 1.0
        }
        self.current_leg_construction_details: Dict[str, Any] = {}
        self.games: List[Dict] = []
        self.is_processing = False
        self.latest_interaction = original_interaction
        self.bet_slip_generator: Optional[BetSlipGenerator] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        logger.info(f"[ParlayBetWorkflowView] Initialized for user {original_interaction.user.id}")

    async def get_bet_slip_generator(self) -> BetSlipGenerator:
        if self.bet_slip_generator is None:
            self.bet_slip_generator = await self.bot.get_bet_slip_generator(self.original_interaction.guild_id)
        return self.bet_slip_generator

    def _format_odds_with_sign(self, odds: Optional[Union[float, int]]) -> str:
        if odds is None: return "N/A"
        try:
            odds_num = int(float(odds))
            return f"+{odds_num}" if odds_num > 0 else str(odds_num)
        except (ValueError, TypeError): return "N/A"

    def _calculate_parlay_odds(self, legs: List[Dict[str, Any]]) -> float:
        # Since odds are now provided by TotalOddsModal, return stored total odds
        return self.bet_details.get('total_odds', 0.0)

    async def add_leg(self, modal_interaction: Interaction, leg_details: Dict[str, Any]):
        if 'legs' not in self.bet_details: self.bet_details['legs'] = []
        self.bet_details['legs'].append(leg_details)
        self.current_leg_construction_details = {}
        leg_count = len(self.bet_details['legs'])
        logger.info(f"Leg {leg_count} added to parlay by user {self.original_interaction.user.id}. Details: {leg_details}")
        
        # Generate preview image after each leg is added
        try:
            generator = ParlayBetImageGenerator(guild_id=self.original_interaction.guild_id)
            legs = []
            for leg in self.bet_details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', leg.get('team', '')),
                    'away_team': leg.get('away_team_name', leg.get('opponent', '')),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            bet_id = str(self.bet_details.get('bet_serial', ''))
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            total_odds = self.bet_details.get('total_odds', 0.0)
            units = float(self.bet_details.get('units', 1.0))
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units,
                bet_id=bet_id,
                bet_datetime=bet_datetime
            )
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                file_to_send = File(self.preview_image_bytes, filename=f"parlay_preview_leg{leg_count}.png")
            else:
                self.preview_image_bytes = None
                file_to_send = None
        except Exception as e:
            logger.exception(f"Error generating parlay preview image after leg add: {e}")
            self.preview_image_bytes = None
            file_to_send = None
        
        summary_lines = [f"**Parlay Legs ({leg_count}):**"]
        for i, leg in enumerate(self.bet_details['legs']):
            summary_lines.append(f"{i+1}. {leg.get('league','N/A')}: {leg.get('team','N/A')} {leg.get('line','N/A')}")
        summary_text = "\n".join(summary_lines)

        decision_view = LegDecisionView(self)
        try:
            await self.edit_message_for_current_leg(modal_interaction, content=f"{summary_text}\n\nAdd another leg or finalize?", view=decision_view, file=file_to_send)
        except Exception as e:
            logger.error(f"Failed to edit self.message in add_leg, trying followup on modal_interaction: {e}")
            await modal_interaction.followup.send(f"{summary_text}\n\nAdd another leg or finalize?", view=decision_view, ephemeral=True, file=file_to_send)
            self.message = await modal_interaction.original_response()

        self.current_step = 4

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        logger.debug(f"Starting parlay bet workflow for user {self.original_interaction.user.id}")
        try:
            if not self.message:
                logger.error("ParlayBetWorkflowView.start_flow called but self.message is None.")
                self.stop()
                return
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.exception(f"Failed during initial go_next in ParlayBetWorkflow: {e}")
            await self.edit_message_for_current_leg(
                content="❌ Failed to start parlay workflow. Please try again.",
                view=None
            )
            self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("You cannot interact with this parlay.", ephemeral=True)
            return False
        self.latest_interaction = interaction
        return True
    
    async def edit_message_for_current_leg(self, interaction_context: Interaction, content: Optional[str] = None, view: Optional[View] = None, embed: Optional[discord.Embed] = None, file: Optional[File] = None):
        logger.debug(f"Parlay: Attempting to edit message {self.message.id if self.message else 'None'}. Content: {content is not None}, View: {view is not None}")
        attachments = [file] if file else discord.utils.MISSING
        try:
            if self.message:
                await self.message.edit(content=content, embed=embed, view=view, attachments=attachments)
            else:
                logger.warning("Parlay: self.message is None during edit_message_for_current_leg. Using original_interaction followup.")
                if self.original_interaction.response.is_done():
                    self.message = await self.original_interaction.followup.send(content=content or "Updating...", view=view, files=attachments if attachments else None, ephemeral=True)
                else:
                    await self.original_interaction.response.send_message(content=content or "Updating...", view=view, files=attachments if attachments else None, ephemeral=True)
                    self.message = await self.original_interaction.original_response()
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(f"Parlay: Failed to edit message {self.message.id if self.message else 'Original Interaction'}: {e}. Interaction type: {interaction_context.type if interaction_context else 'N/A'}")
            if interaction_context and interaction_context.response.is_done() and (not self.message or interaction_context.message.id != self.message.id):
                try:
                    self.message = await interaction_context.followup.send(content=content or "Updating display...", ephemeral=True, view=view, files=attachments if attachments else None)
                except discord.HTTPException as fe: logger.error(f"Parlay: Failed to send followup after message edit error: {fe}")
            elif not interaction_context.response.is_done():
                try:
                    await interaction_context.response.send_message(content=content or "Updating display...", ephemeral=True, view=view, files=attachments if attachments else None)
                    self.message = await interaction_context.original_response()
                except discord.HTTPException as fe: logger.error(f"Parlay: Failed to send new message after previous edit error: {fe}")
            else:
                logger.error(f"Parlay: Cannot reliably update user after message edit error. Main message: {self.message.id if self.message else 'None'}")
        except Exception as e:
            logger.exception(f"Parlay: Unexpected error editing message: {e}")

    async def go_next(self, interaction: Interaction):
        if self.is_processing:
            logger.debug(f"Parlay: Skipping go_next for step {self.current_step}; already processing.")
            if not interaction.response.is_done():
                try: await interaction.response.defer()
                except discord.HTTPException: pass
            return
        self.is_processing = True

        if not interaction.response.is_done():
            try: await interaction.response.defer()
            except discord.HTTPException as e:
                logger.warning(f"Parlay: Defer failed for interaction {interaction.id} in go_next (step {self.current_step}): {e}")

        try:
            self.current_step += 1
            logger.info(f"Parlay Workflow: Advancing to step {self.current_step} for user {self.original_interaction.user.id}")
            self.clear_items()
            
            current_leg_count = len(self.bet_details.get('legs', []))
            content = f"**Parlay Leg {current_leg_count + 1} - Step {self.current_step}**: "

            if self.current_step == 1:
                allowed_leagues = [
                    "NFL",  # American Football
                    "EPL",  # Soccer
                    "NBA",  # Basketball
                    "MLB",  # Baseball
                    "NHL",  # Hockey
                    "La Liga",  # Soccer
                    "NCAA",  # American Football, Basketball
                    "Bundesliga",  # Soccer
                    "Serie A",  # Soccer
                    "Ligue 1",  # Soccer
                    "MLS",  # Soccer
                    "Formula 1",  # Motorsports
                    "Tennis",  # Tennis
                    "UFC/MMA",  # Mixed Martial Arts
                    "WNBA",  # Basketball
                    "CFL",  # American Football
                    "AFL",  # Australian Football
                    "Darts",  # Darts
                    "EuroLeague",  # Basketball
                    "NPB",  # Baseball
                    "KBO",  # Baseball
                    "KHL"  # Hockey
                ]
                self.add_item(LeagueSelect(self, allowed_leagues))
                content += "Select League"
            elif self.current_step == 2:
                self.add_item(LineTypeSelect(self))
                content += "Select Line Type"
            elif self.current_step == 3:
                league = self.current_leg_construction_details.get('league')
                if not league:
                    await self.edit_message_for_current_leg(interaction, content="❌ League not set for current leg. Cancelling.", view=None); self.stop(); return
                self.games = []
                if league != "Other":
                    league_key = league  # Use league name as key
                    from config.leagues import LEAGUE_IDS
                    league_info = LEAGUE_IDS.get(league_key)
                    logger.info(f"[Parlay] Fetching games for league='{league}', league_info='{league_info}'")
                    if not league_info:
                        await self.edit_message_for_current_leg(interaction, content=f"❌ League info not found for {league}. Cancelling.", view=None)
                        self.stop()
                        return
                    try:
                        self.games = await get_normalized_games_for_dropdown(self.bot.db, league_key)
                    except Exception as e:
                        logger.exception(f"Parlay: Error fetching games for {league}: {e}")
                if self.games: self.add_item(ParlayGameSelect(self, self.games))
                self.add_item(ManualEntryButton(self))
                content += f"Select Game for {league} Leg (or Enter Manually)"
            elif self.current_step == 4:
                line_type = self.parent_view.current_leg_construction_details.get('line_type')
                game_id = self.parent_view.current_leg_construction_details.get('game_id')
                is_manual = game_id == "Other"
                leg_number = current_leg_count + 1
                
                modal = BetDetailsModal(line_type=line_type, is_manual=is_manual, leg_number=leg_number, view_custom_id_suffix=self.original_interaction.id)
                modal.view_ref = self
                try:
                    await interaction.response.send_modal(modal)
                    content = f"**Parlay Leg {leg_number}**: Please fill details in the popup."
                    await self.edit_message_for_current_leg(interaction, content=content, view=self)
                except discord.HTTPException as e:
                    logger.error(f"Parlay: Failed to send BetDetailsModal (step 4): {e}")
                    await self.edit_message_for_current_leg(interaction, content="❌ Error opening leg details form.", view=None); self.stop()
                self.is_processing = False; return
            elif self.current_step == 5:
                # Set default units to 1.0 if not already set
                if "units" not in self.bet_details:
                    self.bet_details["units"] = 1.0
                    self.bet_details["units_str"] = "1.0"
                # Always assign the next bet serial for preview if not set
                if "bet_serial" not in self.bet_details or not self.bet_details["bet_serial"]:
                    from utils.bet_utils import fetch_next_bet_serial
                    self.bet_details["bet_serial"] = await fetch_next_bet_serial(self.bot)
                # Always generate preview for 1.0 units before showing the ephemeral message
                try:
                    generator = ParlayBetImageGenerator(guild_id=self.original_interaction.guild_id)
                    legs = []
                    for leg in self.bet_details.get('legs', []):
                        leg_data = {
                            'bet_type': leg.get('line_type', 'game_line'),
                            'league': leg.get('league', ''),
                            'home_team': leg.get('home_team_name', leg.get('team', '')),
                            'away_team': leg.get('away_team_name', leg.get('opponent', '')),
                            'player_name': leg.get('player_name', ''),
                            'line': leg.get('line', ''),
                            'selection': leg.get('selection', ''),
                        }
                        legs.append(leg_data)
                    bet_id = str(self.bet_details.get("bet_serial", ""))
                    bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                    units = 1.0
                    image_bytes = generator.generate_image(
                        legs=legs,
                        output_path=None,
                        total_odds=self.bet_details.get('total_odds', 0.0),
                        units=units,
                        bet_id=bet_id,
                        bet_datetime=bet_datetime
                    )
                    if image_bytes:
                        self.preview_image_bytes = io.BytesIO(image_bytes)
                        self.preview_image_bytes.seek(0)
                    else:
                        self.preview_image_bytes = None
                except Exception as e:
                    logger.exception(f"Error generating initial parlay preview image for units step: {e}")
                    self.preview_image_bytes = None
                self.add_item(UnitsSelect(self))
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"parlay_preview_s{self.current_step}.png")
                await self.edit_message_for_current_leg(
                    interaction,
                    content=self.get_content() if hasattr(self, 'get_content') else None,
                    view=self,
                    file=file_to_send
                )
                return
            elif self.current_step == 6:
                if not self.bet_details.get("units_str"):
                    await self.edit_message_for_current_leg(interaction, content="❌ Parlay units not set. Please restart.", view=None); self.stop(); return

                modal = TotalOddsModal(view_custom_id_suffix=self.original_interaction.id)
                modal.view_ref = self
                try:
                    await interaction.response.send_modal(modal)
                    content = "**Parlay Total Odds**: Please enter total odds in the popup."
                    await self.edit_message_for_current_leg(interaction, content=content, view=self)
                except discord.HTTPException as e:
                    logger.error(f"Parlay: Failed to send TotalOddsModal (step 6): {e}")
                    await self.edit_message_for_current_leg(interaction, content="❌ Error opening total odds form.", view=None); self.stop()
                self.is_processing = False; return
            elif self.current_step == 7:
                if not self.bet_details.get("total_odds_str"):
                    await self.edit_message_for_current_leg(interaction, content="❌ Total parlay odds not set. Please restart.", view=None); self.stop(); return

                guild_settings = await self.bot.db_manager.fetch_one(
                    "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
                    (self.original_interaction.guild_id,)
                )
                configured_channel_objects = []
                if guild_settings:
                    ids_to_check = filter(None, [guild_settings.get('embed_channel_1'), guild_settings.get('embed_channel_2')])
                    for ch_id_str in ids_to_check:
                        try:
                            ch_id = int(ch_id_str)
                            channel = self.original_interaction.guild.get_channel(ch_id) or await self.original_interaction.guild.fetch_channel(ch_id)
                            if channel and isinstance(channel, TextChannel) and channel.permissions_for(self.original_interaction.guild.me).send_messages:
                                if channel not in configured_channel_objects: configured_channel_objects.append(channel)
                            elif channel: logger.warning(f"Parlay: Embed channel {ch_id} invalid type or permissions.")
                            else: logger.warning(f"Parlay: Embed channel {ch_id} not found.")
                        except (ValueError, discord.NotFound, discord.Forbidden) as e: logger.error(f"Parlay: Error processing embed_channel_id {ch_id_str}: {e}")
                
                if not configured_channel_objects:
                    await self.edit_message_for_current_leg(interaction, content="❌ No configured embed channels. Admin: `/setup`.", view=None); self.stop(); return
                
                self.add_item(ChannelSelect(self, configured_channel_objects))
                content = f"**Finalizing Parlay - Step {self.current_step}**: Select Channel to Post Parlay"
            elif self.current_step == 8:
                if not all(k in self.bet_details for k in ['bet_serial', 'channel_id', 'units_str', 'legs', 'total_odds_str']):
                    await self.edit_message_for_current_leg(interaction, content="❌ Parlay details incomplete. Please restart.", view=None); self.stop(); return
                
                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(self.preview_image_bytes, filename=f"parlay_preview_s{self.current_step}.png")

                self.add_item(FinalConfirmButton(self))
                content = "**Confirm Your Parlay**\n\n" + self._generate_parlay_summary_text()
            else:
                logger.error(f"ParlayBetWorkflowView: Unexpected step: {self.current_step}")
                await self.edit_message_for_current_leg(interaction, content="❌ Workflow error.", view=None); self.stop(); return

            if self.current_step <= 8: self.add_item(CancelButton(self))
            
            await self.edit_message_for_current_leg(interaction, content=content, view=self, file=getattr(self, 'file_to_send', None))

        except Exception as e:
            logger.exception(f"Error in parlay go_next (step {self.current_step}): {e}")
            await self.edit_message_for_current_leg(interaction, content="❌ Unexpected error in parlay flow.", view=None)
            self.stop()
        finally:
            self.is_processing = False

    def _generate_parlay_summary_text(self) -> str:
        summary_parts = []
        legs = self.bet_details.get('legs', [])
        for i, leg in enumerate(legs, 1):
            summary_parts.append(
                f"**Leg {i}**: {leg.get('league','N/A')} - "
                f"{leg.get('team','N/A')} {leg.get('line','N/A')}"
            )
        summary_text = "\n".join(summary_parts)
        summary_text += f"\n\nTotal Odds: **{self.bet_details.get('total_odds_str', 'N/A')}**"
        summary_text += f"\nUnits: **{self.bet_details.get('units_str', 'N/A')}**"
        selected_channel_id = self.bet_details.get('channel_id')
        channel_mention = f"<#{selected_channel_id}>" if selected_channel_id else "Not selected"
        summary_text += f"\nPost to Channel: {channel_mention}"
        summary_text += "\n\nClick Confirm to place your parlay."
        return summary_text

    async def _handle_units_selection(self, interaction: Interaction, units: float):
        self.bet_details["units"] = units
        self.bet_details["units_str"] = str(units)
        try:
            generator = ParlayBetImageGenerator(guild_id=self.original_interaction.guild_id)
            legs = []
            for leg in self.bet_details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', ''),
                    'away_team': leg.get('away_team_name', ''),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            total_odds = self.bet_details.get('total_odds', 0.0)
            bet_id = str(self.bet_details.get('bet_serial', ''))
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units,
                bet_id=bet_id,
                bet_datetime=timestamp
            )
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
            else:
                self.preview_image_bytes = None
        except Exception as e:
            logger.exception(f"Error generating parlay preview image: {e}")
            self.preview_image_bytes = None
        self.clear_items()
        self.add_item(UnitsSelect(self))
        self.add_item(CancelButton(self))
        file_to_send = None
        if self.preview_image_bytes:
            self.preview_image_bytes.seek(0)
            file_to_send = File(self.preview_image_bytes, filename="parlay_preview_units.png")
        await self.edit_message_for_current_leg(
            interaction,
            content=self.get_content() if hasattr(self, 'get_content') else None,
            view=self,
            file=file_to_send
        )

    async def submit_bet(self, interaction: Interaction):
        details = self.bet_details
        bet_serial = details.get("bet_serial")
        bet_service = getattr(self.bot, "bet_service", None)
        if not bet_serial:
            # Insert the bet now with all final values
            if bet_service:
                try:
                    primary_league = details.get('legs', [{}])[0].get('league', 'PARLAY') if details.get('legs') else 'PARLAY'
                    bet_serial = await bet_service.create_parlay_bet(
                        guild_id=self.original_interaction.guild_id,
                        user_id=self.original_interaction.user.id,
                        league=primary_league,
                        legs_data=details.get('legs', []),
                        units=float(details.get("units", 1.0)),
                        channel_id=details.get("channel_id"),
                        confirmed=1 # <-- pass confirmed=1 if supported
                    )
                    if not bet_serial:
                        logger.error("Failed to create parlay bet in DB at submit step.")
                        await self.edit_message_for_current_leg(interaction, content="❌ Failed to create parlay bet in database. Please try again.", view=None)
                        self.stop()
                        return
                    self.bet_details["bet_serial"] = bet_serial
                except Exception as e:
                    logger.error(f"Failed to create parlay bet in DB at submit step: {e}")
                    await self.edit_message_for_current_leg(interaction, content="❌ Failed to create parlay bet in database. Please try again.", view=None)
                    self.stop()
                    return
        logger.info(f"Submitting parlay bet {bet_serial} by user {interaction.user.id}")
        await self.edit_message_for_current_leg(interaction, content=f"Processing parlay bet `{bet_serial}`...", view=None, file=None)
        try:
            post_channel_id = details.get("channel_id")
            post_channel = self.bot.get_channel(post_channel_id) if post_channel_id else None
            if not post_channel or not isinstance(post_channel, TextChannel):
                raise ValueError(f"Invalid channel <#{post_channel_id}> for bet posting.")
            units_val = float(details.get("units", 1.0))
            total_odds = float(details.get("total_odds", 0.0))
            # No update query here
            generator = ParlayBetImageGenerator(guild_id=self.original_interaction.guild_id)
            legs = []
            for leg in details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', ''),
                    'away_team': leg.get('away_team_name', ''),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units_val,
                bet_id=bet_serial,
                bet_datetime=timestamp
            )
            discord_file_to_send = None
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                discord_file_to_send = File(self.preview_image_bytes, filename=f"parlay_slip_{bet_serial}.png")
            else:
                logger.warning(f"Parlay bet {bet_serial}: Failed to generate bet slip image.")
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
                logger.error(f"Error creating or fetching webhook: {e}")
                await self.edit_message_for_current_leg(interaction, content="Error: Failed to create bet posting webhook.", view=None)
                self.stop()
                return
            # Fetch member_role for mention
            member_role_id = None
            guild_settings = await self.bot.db_manager.fetch_one(
                "SELECT member_role FROM guild_settings WHERE guild_id = %s",
                (str(interaction.guild_id),)
            )
            if guild_settings and guild_settings.get("member_role"):
                member_role_id = guild_settings["member_role"]
            role_mention = f"<@&{member_role_id}>" if member_role_id else None
            try:
                webhook_content = role_mention if role_mention else None
                await target_webhook.send(
                    content=webhook_content,
                    file=discord_file_to_send,
                    username=webhook_username,
                    avatar_url=webhook_avatar_url
                )
                await self.edit_message_for_current_leg(interaction, content=f"✅ Parlay bet #{bet_serial} successfully posted!", view=None)
                self.stop()
            except Exception as e:
                logger.error(f"Error posting parlay bet via webhook: {e}")
                await self.edit_message_for_current_leg(interaction, content="Error: Failed to post bet message.", view=None)
                self.stop()
                return
        except Exception as e:
            logger.exception(f"Error in submit_bet: {e}")
            await self.edit_message_for_current_leg(interaction, content=f"❌ Error processing bet submission: {e}", view=None)
            self.stop()

    async def handle_game_selection(self, interaction, selected_game_id):
        if selected_game_id.startswith("manual_entry_"):
            self.current_leg_construction_details['game_id'] = "Other"
            await self.go_next(interaction)
            return
        # For game options, extract api_game_id from value
        if selected_game_id.startswith("game_"):
            parts = selected_game_id.split('_')
            api_game_id = parts[1] if len(parts) > 2 else None
            selected_game = next((g for g in self.games if str(g.get("api_game_id")) == api_game_id), None)
            if not selected_game:
                await interaction.response.send_message("❌ Could not find the selected game. Please try again.", ephemeral=True)
                return
            self.current_leg_construction_details['game_id'] = selected_game.get('api_game_id')
            self.current_leg_construction_details['home_team_name'] = selected_game.get('home_team_name')
            self.current_leg_construction_details['away_team_name'] = selected_game.get('away_team_name')
            self.clear_items()
            self.add_item(TeamSelect(self, selected_game.get('home_team_name'), selected_game.get('away_team_name')))
            await self.edit_message_for_current_leg(
                interaction,
                content="Select which team you are betting on:",
                view=self
            )

def load_normalized_games(league_name):
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cache")
    file_key = get_league_file_key(league_name)
    file_path = os.path.join(cache_dir, f"league_{file_key}_normalized.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        games = json.load(f)
    # Only games with status 'Not Started'
    return [g for g in games if g.get("status", "").strip().lower() == "not started"]

def get_league_id_by_name(league_name):
    mapping = {
        "EPL": "39",
        "LaLiga": "140",
        "Bundesliga": "78",
        "SerieA": "135",
        "Ligue1": "61",
        "MLS": "253",
        "ChampionsLeague": "2",
        "EuropaLeague": "3",
        "WorldCup": "1",
        "NBA": "12",
        "WNBA": "13",
        "EuroLeague": "1",
        "MLB": "1",
        "NPB": "2",
        "KBO": "3",
        "NHL": "57",
        "KHL": "1",
        "NFL": "1",
        "NCAA": "2",
        "SuperRugby": "1",
        "SixNations": "2",
        "FIVB": "1",
        "EHF": "1",
        "AFL": "1",
        "Formula-1": "1",
        "MMA": "1",
        "Bellator": "2"
    }
    return mapping.get(league_name)
