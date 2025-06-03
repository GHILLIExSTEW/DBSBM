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
from utils.parlay_image_generator import ParlayImageGenerator
from config.leagues import LEAGUE_IDS, LEAGUE_CONFIG
from PIL import Image, ImageDraw, ImageFont
from utils.game_line_image_generator import GameLineImageGenerator

logger = logging.getLogger(__name__)

# Add this near the top, after logger definition
ALLOWED_LEAGUES = [
    "NFL", "EPL", "NBA", "MLB", "NHL", "La Liga", "NCAA", "Bundesliga", "Serie A", "Ligue 1", "MLS",
    "Formula 1", "Tennis", "UFC/MMA", "WNBA", "CFL", "AFL", "Darts", "EuroLeague", "NPB", "KBO", "KHL"
]

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

class ConfirmButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm",
            custom_id=f"parlay_confirm_{parent_view.original_interaction.id}_{uuid.uuid4()}"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        selected_game = self.parent_view.current_leg_construction_details.get('api_game_id')
        is_manual = self.parent_view.current_leg_construction_details.get('is_manual', False)
        home_team = self.parent_view.current_leg_construction_details.get('home_team_name', '')
        away_team = self.parent_view.current_leg_construction_details.get('away_team_name', '')
        self.parent_view.clear_items()
        self.parent_view.add_item(TeamSelect(self.parent_view, home_team, away_team))
        self.parent_view.add_item(CancelButton(self.parent_view))
        await self.parent_view.edit_message_for_current_leg(
            interaction,
            content="Select which team you are betting on:",
            view=self.parent_view
        )
        self.parent_view.current_step += 1

class ParlayGameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict]):
        game_options = []
        seen_values = set()  # Track used values
        # Only include up to 24 games (Discord limit is 25 options including manual entry)
        for game in games[:24]:
            # Prefer api_game_id if present, else use internal id
            if game.get('api_game_id'):
                value = f"api_{game['api_game_id']}"
            elif game.get('id'):
                value = f"dbid_{game['id']}"
            else:
                continue  # skip if neither id present
            if value in seen_values:
                continue
            seen_values.add(value)
            
            # Format the label with team names and status
            home_team = game.get('home_team_name', 'N/A')
            away_team = game.get('away_team_name', 'N/A')
            status = game.get('status', '')
            
            # Calculate max length for team names based on status length
            status_suffix = f" ({status})" if status else ""
            max_team_length = (90 - len(status_suffix)) // 2  # Divide remaining space between teams
            
            # Truncate team names if needed
            if len(home_team) > max_team_length:
                home_team = home_team[:max_team_length-3] + "..."
            if len(away_team) > max_team_length:
                away_team = away_team[:max_team_length-3] + "..."
                
            label = f"{home_team} vs {away_team}{status_suffix}"
            
            # Get start time for description
            start_time = game.get('start_time')
            if start_time:
                if isinstance(start_time, str):
                    try:
                        from dateutil.parser import parse as dtparse
                        start_time = dtparse(start_time)
                    except Exception:
                        start_time = None
                if start_time:
                    desc = f"Start: {start_time.strftime('%Y-%m-%d %H:%M')}"
                else:
                    desc = ""
            else:
                desc = ""
                
            game_options.append(
                SelectOption(
                    label=label[:100],
                    value=value[:100],
                    description=desc[:100]
                )
            )
        # Always add manual entry as the last option
        manual_value = "manual_entry"
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
        self.games = games
        logger.debug(f"Created ParlayGameSelect with {len(game_options)} unique options (including manual entry)")

    async def callback(self, interaction: Interaction):
        selected_value = self.values[0]
        logger.debug(f"Selected game value: {selected_value}")
        if selected_value == "manual_entry":
            self.parent_view.current_leg_construction_details.update({
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
                self.parent_view.current_leg_construction_details.update({
                    'api_game_id': selected_game.get('api_game_id'),
                    'game_id': selected_game.get('id'),
                    'home_team_name': selected_game.get('home_team_name'),
                    'away_team_name': selected_game.get('away_team_name'),
                    'is_manual': False
                })
                logger.debug(f"Updated leg construction details: {self.parent_view.current_leg_construction_details}")
            else:
                logger.error(f"Could not find game for selected value {selected_value}")
                await interaction.response.defer()
                await self.parent_view.edit_message_for_current_leg(
                    interaction,
                    content="Error: Could not find the selected game. Please try again or cancel.",
                    view=None
                )
                self.parent_view.stop()
                return
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)

class CancelButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(style=ButtonStyle.red, label="Cancel Parlay", custom_id=f"parlay_cancel_{parent_view.original_interaction.id}_{uuid.uuid4()}")
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
    def __init__(self, line_type: str, is_manual: bool = False, leg_number: int = 1, view_custom_id_suffix: str = "", bet_details_from_view: dict = None):
        self.line_type = line_type
        self.is_manual = is_manual
        self.leg_number = leg_number
        self.view_custom_id_suffix = view_custom_id_suffix
        self.view_ref = None
        bet_details_from_view = bet_details_from_view or {}
        league_key = bet_details_from_view.get('league') or bet_details_from_view.get('selected_league_key') or self.view_ref.current_leg_construction_details.get('league') if self.view_ref else None
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        
        if line_type == "player_prop":
            title = league_conf.get('player_prop_modal_title', f"Parlay Leg {leg_number} Details")
        else:
            title = league_conf.get('game_line_modal_title', f"Parlay Leg {leg_number} Details")
        if is_manual:
            title += " (Manual Entry)"
        super().__init__(title=title)

        # For manual entries, always ask for team and opponent first (like straight betting)
        if self.is_manual and line_type == "game_line":
            team_label = league_conf.get('participant_label', 'Team')
            team_placeholder = league_conf.get('team_placeholder', 'e.g., Team A')
            opponent_label = league_conf.get('opponent_label', 'Opponent')
            opponent_placeholder = league_conf.get('opponent_placeholder', 'e.g., Opponent Team')
            self.team_input = TextInput(
                label=team_label,
                required=True,
                max_length=100,
                placeholder=team_placeholder,
                default=bet_details_from_view.get('team', '')
            )
            self.add_item(self.team_input)
            self.opponent_input = TextInput(
                label=opponent_label,
                required=True,
                max_length=100,
                placeholder=opponent_placeholder,
                default=bet_details_from_view.get('opponent', '')
            )
            self.add_item(self.opponent_input)

        # For game lines, use league-specific label/placeholder for line
        if line_type == "game_line":
            line_label = league_conf.get('line_label_game', 'Game Line / Match Outcome')
            line_placeholder = league_conf.get('line_placeholder_game', 'e.g., Moneyline, Spread -7.5')
            self.line_input = TextInput(
                label=line_label,
                required=True,
                max_length=100,
                placeholder=line_placeholder,
                default=bet_details_from_view.get('line', '')
            )
            self.add_item(self.line_input)
        elif line_type == "player_prop":
            # For player props, keep as before
            self.player_name_input = TextInput(
                label="Player Name",
                placeholder="Enter player name (e.g. LeBron James)",
                required=True,
                custom_id=f"parlay_player_name_input_{view_custom_id_suffix}"
            )
            self.line_input = TextInput(
                label="Player Prop Line",
                placeholder="Enter the prop line (e.g. Over 25.5 Points)",
                required=True,
                custom_id=f"parlay_line_input_{view_custom_id_suffix}"
            )
            self.add_item(self.player_name_input)
            self.add_item(self.line_input)

    async def on_submit(self, interaction: Interaction):
        try:
            # For manual game line, get team/opponent
            if self.is_manual and self.line_type == "game_line":
                team = self.team_input.value.strip()
                opponent = self.opponent_input.value.strip()
                self.view_ref.current_leg_construction_details['team'] = team
                self.view_ref.current_leg_construction_details['opponent'] = opponent
            line = self.line_input.value.strip()
            if not line:
                raise ValidationError("Line cannot be empty")
            self.view_ref.current_leg_construction_details['line'] = line
            if self.line_type == "player_prop":
                player_name = self.player_name_input.value.strip()
                if not player_name:
                    raise ValidationError("Player name cannot be empty")
                self.view_ref.current_leg_construction_details['player_name'] = player_name

            # Add the leg to the parlay
            if 'legs' not in self.view_ref.bet_details:
                self.view_ref.bet_details['legs'] = []
            self.view_ref.bet_details['legs'].append(self.view_ref.current_leg_construction_details.copy())
            
            # Reset current leg construction details
            self.view_ref.current_leg_construction_details = {}
            
            # Generate preview image for the entire parlay (all legs so far)
            try:
                image_generator = ParlayImageGenerator()
                legs = []
                for leg in self.view_ref.bet_details.get('legs', []):
                    leg_data = {
                        'bet_type': leg.get('line_type', 'game_line'),
                        'league': leg.get('league', ''),
                        'home_team': leg.get('home_team_name', ''),
                        'away_team': leg.get('away_team_name', ''),
                        'selected_team': leg.get('team', ''),
                        'line': leg.get('line', ''),
                        'odds': leg.get('odds', leg.get('odds_str', '')),
                    }
                    if leg.get('line_type') == 'player_prop':
                        leg_data['player_name'] = leg.get('player_name', '')
                    legs.append(leg_data)
                total_odds = self.view_ref.bet_details.get('total_odds', 0.0)
                units = float(self.view_ref.bet_details.get('units', 1.0))
                bet_id = str(self.view_ref.bet_details.get('bet_serial', ''))
                bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                image_bytes = image_generator.generate_image(
                    legs=legs,
                    output_path=None,
                    total_odds=None,
                    units=None,
                    bet_id=bet_id,
                    bet_datetime=bet_datetime,
                    finalized=True
                )
                if image_bytes:
                    self.view_ref.preview_image_bytes = io.BytesIO(image_bytes)
                    self.view_ref.preview_image_bytes.seek(0)
                    preview_file = discord.File(self.view_ref.preview_image_bytes, filename=f"parlay_preview.png")
                else:
                    self.view_ref.preview_image_bytes = None
                    preview_file = None
            except Exception as e:
                logger.error(f"Error generating parlay preview image: {e}")
                self.view_ref.preview_image_bytes = None
                preview_file = None
            
            # Update the message to show the added leg and preview image
            content = f"✅ Added leg {len(self.view_ref.bet_details['legs'])} to your parlay!\n\n"
            content += "**Current Parlay:**\n"
            for i, leg in enumerate(self.view_ref.bet_details['legs'], 1):
                if leg.get('line_type') == 'player_prop':
                    content += f"{i}. {leg.get('league', 'N/A')} - {leg.get('player_name', 'N/A')} {leg.get('line', 'N/A')}\n"
                else:
                    content += f"{i}. {leg.get('league', 'N/A')} - {leg.get('team', 'N/A')} vs {leg.get('opponent', 'N/A')} - {leg.get('line', 'N/A')}\n"
            content += "\nWould you like to add another leg or finalize your parlay?"
            
            # Add buttons for next action
            self.view_ref.clear_items()
            self.view_ref.add_item(AddAnotherLegButton(self.view_ref))
            self.view_ref.add_item(FinalizeParlayButton(self.view_ref))
            self.view_ref.add_item(CancelButton(self.view_ref))
            
            if preview_file:
                await interaction.response.edit_message(content=content, view=self.view_ref, attachments=[preview_file])
            else:
                await interaction.response.edit_message(content=content, view=self.view_ref)
            
        except ValidationError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error in BetDetailsModal.on_submit: {e}")
            await interaction.response.send_message("❌ An error occurred while processing your bet details. Please try again.", ephemeral=True)

class TotalOddsModal(Modal):
    def __init__(self, view_custom_id_suffix: str = ""):
        super().__init__(title="Enter Total Parlay Odds")
        self.view_custom_id_suffix = view_custom_id_suffix
        self.view_ref = None
        
        self.odds_input = TextInput(
            label="Total Odds",
            placeholder="Enter the total parlay odds (e.g. +500, -110)",
            required=True,
            custom_id=f"parlay_total_odds_input_{view_custom_id_suffix}"
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        try:
            odds = self.odds_input.value.strip()
            if not odds:
                raise ValidationError("Odds cannot be empty")
            self.view_ref.bet_details['total_odds'] = odds
            # Generate main parlay slip image and odds/units/footer image, then stack
            try:
                image_generator = ParlayImageGenerator()
                legs = []
                for leg in self.view_ref.bet_details.get('legs', []):
                    leg_data = {
                        'bet_type': leg.get('line_type', 'game_line'),
                        'league': leg.get('league', ''),
                        'home_team': leg.get('home_team_name', ''),
                        'away_team': leg.get('away_team_name', ''),
                        'selected_team': leg.get('team', ''),
                        'line': leg.get('line', ''),
                        'odds': leg.get('odds', leg.get('odds_str', '')),
                    }
                    if leg.get('line_type') == 'player_prop':
                        leg_data['player_name'] = leg.get('player_name', '')
                    legs.append(leg_data)
                total_odds = float(self.view_ref.bet_details.get('total_odds', 0.0))
                units = float(self.view_ref.bet_details.get('units', 1.0))
                bet_id = str(self.view_ref.bet_details.get('bet_serial', ''))
                bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                image_bytes = image_generator.generate_image(
                    legs=legs,
                    output_path=None,
                    total_odds=total_odds,
                    units=units,
                    bet_id=bet_id,
                    bet_datetime=bet_datetime,
                    finalized=True
                )
                if image_bytes:
                    self.view_ref.preview_image_bytes = io.BytesIO(image_bytes)
                    self.view_ref.preview_image_bytes.seek(0)
                    preview_file = discord.File(self.view_ref.preview_image_bytes, filename=f"parlay_preview.png")
                    # Show units dropdown with preview
                    self.view_ref.clear_items()
                    self.view_ref.add_item(UnitsSelect(self.view_ref))
                    self.view_ref.add_item(ConfirmUnitsButton(self.view_ref))
                    self.view_ref.add_item(CancelButton(self.view_ref))
                    await interaction.response.edit_message(
                        content="Select total units for your parlay:",
                        view=self.view_ref,
                        attachments=[preview_file]
                    )
                    return
                else:
                    self.view_ref.preview_image_bytes = None
                    preview_file = None
                    await interaction.response.edit_message(
                        content="Select total units for your parlay:",
                        view=self.view_ref
                    )
                    return
            except Exception as e:
                logger.error(f"Error generating parlay preview image after odds: {e}")
                self.view_ref.preview_image_bytes = None
                preview_file = None
            await interaction.response.defer()
            await self.view_ref.go_next(interaction)
        except ValidationError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in TotalOddsModal on_submit: {e}")
            await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.error(f"Error in TotalOddsModal: {error}")
        try:
            await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

class UnitsSelect(Select):
    def __init__(self, parent_view: 'ParlayBetWorkflowView', units_display_mode='auto'):
        self.parent_view = parent_view
        self.units_display_mode = units_display_mode
        options = []
        if units_display_mode == 'manual':
            options.append(SelectOption(label='--- To Win ---', value='separator_win', default=False, description=None, emoji=None))
            for u in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                options.append(SelectOption(label=f'To Win {u:.1f} Unit' + ('' if u == 1.0 else 's'), value=f'{u}|win'))
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
        # Update preview image with selected units, but do not proceed to channel selection yet
        try:
            generator = ParlayImageGenerator(guild_id=self.parent_view.original_interaction.guild_id)
            legs = []
            for leg in self.parent_view.bet_details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', ''),
                    'away_team': leg.get('away_team_name', ''),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                    'odds': leg.get('odds', leg.get('odds_str', '')),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            total_odds = self.parent_view.bet_details.get('total_odds', None)
            bet_id = str(self.parent_view.bet_details.get('bet_serial', ''))
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=self.parent_view.bet_details['units'],
                bet_id=bet_id,
                bet_datetime=bet_datetime,
                finalized=True
            )
            if image_bytes:
                self.parent_view.preview_image_bytes = io.BytesIO(image_bytes)
                self.parent_view.preview_image_bytes.seek(0)
                file_to_send = File(self.parent_view.preview_image_bytes, filename="parlay_preview_units.png")
            else:
                self.parent_view.preview_image_bytes = None
                file_to_send = None
        except Exception as e:
            logger.exception(f"Error generating parlay preview image: {e}")
            self.parent_view.preview_image_bytes = None
            file_to_send = None
        await interaction.response.edit_message(
            content="Confirm your units selection, then proceed.",
            view=self.parent_view,
            attachments=[file_to_send] if file_to_send else None
        )

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

class AddAnotherLegButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(
            style=ButtonStyle.green,
            label="Add Another Leg",
            custom_id=f"parlay_add_leg_{parent_view.original_interaction.id}_{len(parent_view.bet_details.get('legs', [])) + 1}"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        self.parent_view.current_step = 0
        self.parent_view.current_leg_construction_details = {}
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)

class FinalizeParlayButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(
            style=ButtonStyle.green,
            label="Finalize Parlay",
            custom_id=f"parlay_finalize_{parent_view.original_interaction.id}_{uuid.uuid4()}"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        try:
            # Show total odds modal first
            modal = TotalOddsModal(view_custom_id_suffix=self.parent_view.original_interaction.id)
            modal.view_ref = self.parent_view
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error in FinalizeParlayButton callback: {e}")
            await interaction.response.send_message("❌ Error finalizing parlay. Please try again.", ephemeral=True)

class LegDecisionView(View):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(timeout=600)
        self.parent_view = parent_view
        self.add_item(AddAnotherLegButton(self.parent_view))
        finalize_button = FinalizeParlayButton(self.parent_view)
        finalize_button.disabled = len(self.parent_view.bet_details.get('legs', [])) < 1
        self.add_item(finalize_button)
        self.add_item(CancelButton(self.parent_view))

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
        home_team = self.parent_view.current_leg_construction_details.get("home_team_name", "")
        away_team = self.parent_view.current_leg_construction_details.get("away_team_name", "")
        if selected_team == home_team:
            opponent = away_team
        else:
            opponent = home_team
        self.parent_view.current_leg_construction_details["team"] = selected_team
        self.parent_view.current_leg_construction_details["opponent"] = opponent
        line_type = self.parent_view.current_leg_construction_details.get("line_type", "game_line")
        modal = BetDetailsModal(
            line_type=line_type,
            is_manual=self.parent_view.current_leg_construction_details.get('is_manual', False),
            leg_number=len(self.parent_view.bet_details.get('legs', [])) + 1,
            view_custom_id_suffix=self.parent_view.original_interaction.id,
            bet_details_from_view=self.parent_view.current_leg_construction_details
        )
        modal.view_ref = self.parent_view
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)
            await self.parent_view.edit_message_for_current_leg(
                interaction,
                content="Please fill in the bet details in the popup form.",
                view=self.parent_view
            )
        else:
            logger.error("Tried to send modal, but interaction already responded to.")
            await self.parent_view.edit_message_for_current_leg(
                interaction,
                content="❌ Error: Could not open modal. Please try again or cancel.",
                view=None
            )
            self.parent_view.stop()

class ConfirmUnitsButton(Button):
    def __init__(self, parent_view: 'ParlayBetWorkflowView'):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm Units",
            custom_id=f"parlay_confirm_units_{parent_view.original_interaction.id}"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Confirm Units button clicked by user {interaction.user.id}")
        await self.parent_view._handle_units_selection(interaction, float(self.parent_view.bet_details['units']))

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
        self.bet_slip_generator: Optional[ParlayImageGenerator] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        logger.info(f"[ParlayBetWorkflowView] Initialized for user {original_interaction.user.id}")

    async def get_bet_slip_generator(self) -> ParlayImageGenerator:
        if not self.bet_slip_generator:
            self.bet_slip_generator = ParlayImageGenerator(guild_id=self.original_interaction.guild_id)
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

    async def add_leg(self, modal_interaction: Interaction, leg_details: Dict[str, Any], file=None):
        try:
            # Add the leg to the parlay
            if 'legs' not in self.bet_details:
                self.bet_details['legs'] = []
            self.bet_details['legs'].append(leg_details)
            # Reset current leg construction details
            self.current_leg_construction_details = {}
            # Generate preview image for the entire parlay
            try:
                image_generator = ParlayImageGenerator()
                image_bytes = await image_generator.generate_parlay_preview(self.bet_details)
                if image_bytes:
                    self.preview_image_bytes = io.BytesIO(image_bytes)
                    self.preview_image_bytes.seek(0)
                    preview_file = discord.File(self.preview_image_bytes, filename=f"parlay_preview.png")
                else:
                    self.preview_image_bytes = None
                    preview_file = None
            except Exception as e:
                logger.error(f"Error generating parlay preview image: {e}")
                self.preview_image_bytes = None
                preview_file = None
            # Show decision view for adding another leg or finalizing
            leg_count = len(self.bet_details['legs'])
            summary_text = self._generate_parlay_summary_text()
            decision_view = LegDecisionView(self)
            await self.edit_message_for_current_leg(
                modal_interaction,
                content=f"✅ Line added for Leg {leg_count}\n\n{summary_text}\n\nAdd another leg or finalize?",
                view=decision_view,
                file=preview_file
            )
        except Exception as e:
            logger.error(f"Error in add_leg: {e}")
            await modal_interaction.response.send_message(
                "❌ Error adding leg to parlay. Please try again.",
                ephemeral=True
            )

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
        if self.is_processing or self.is_finished() or getattr(self, '_stopped', False):
            return

        self.is_processing = True
        try:
            self.clear_items()  # Always clear items at the start of each step
            if self.current_step == 0:
                self.add_item(LeagueSelect(self, ALLOWED_LEAGUES))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Select a League for your Parlay Leg", view=self)
                self.current_step += 1
                return
            elif self.current_step == 1:
                self.add_item(LineTypeSelect(self))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Select Line Type for this Leg", view=self)
                self.current_step += 1
                return
            elif self.current_step == 2:
                league = self.current_leg_construction_details.get('league')
                if not league:
                    await self.edit_message_for_current_leg(interaction, content="❌ League not set for current leg. Cancelling.", view=None)
                    self.stop()
                    return
                self.games = []
                if league != "Other":
                    league_key = league  # Use league name as key
                    from config.leagues import LEAGUE_IDS
                    league_info = LEAGUE_IDS.get(league_key)
                    logger.info(f"[Parlay] Fetching games for league='{league}', league_info='{league_info}'")
                    if league_info:
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
                self.add_item(ParlayGameSelect(self, self.games))
                self.add_item(ConfirmButton(self))
                self.add_item(CancelButton(self))
                if not self.games:
                    content = f"No games available for {league} at this time. You can use Manual Entry to place your bet."
                else:
                    content = f"Select a game for your {league} parlay leg or choose Manual Entry:"
                await self.edit_message_for_current_leg(interaction, content=content, view=self)
                self.current_step += 1
                return
            elif self.current_step == 3:
                home_team = self.current_leg_construction_details.get('home_team_name', '')
                away_team = self.current_leg_construction_details.get('away_team_name', '')
                self.add_item(TeamSelect(self, home_team, away_team))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Select which team you are betting on:", view=self)
                self.current_step += 1
                return
            elif self.current_step == 4:
                self.is_processing = False
                return
            elif self.current_step == 5:
                self.add_item(UnitsSelect(self))
                self.add_item(ConfirmUnitsButton(self))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Select units for your parlay:", view=self)
            elif self.current_step == 6:
                self.add_item(TotalOddsInput(self))
                self.add_item(ConfirmTotalOddsButton(self))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Enter total odds for your parlay:", view=self)
            elif self.current_step == 7:
                self.add_item(ConfirmParlayButton(self))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(interaction, content="Confirm your parlay:", view=self)
            elif self.current_step == 8:
                await self.submit_bet(interaction)
                self.stop()
                return
        except Exception as e:
            logger.exception(f"Error in go_next: {e}")
            await self.edit_message_for_current_leg(interaction, content=f"❌ An error occurred: {str(e)}", view=None)
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
            generator = ParlayImageGenerator(guild_id=self.original_interaction.guild_id)
            legs = []
            for leg in self.bet_details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', ''),
                    'away_team': leg.get('away_team_name', ''),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                    'odds': leg.get('odds', leg.get('odds_str', '')),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            total_odds = self.bet_details.get('total_odds', None)
            bet_id = str(self.bet_details.get('bet_serial', ''))
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units,
                bet_id=bet_id,
                bet_datetime=bet_datetime,
                finalized=True
            )
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                file_to_send = File(self.preview_image_bytes, filename="parlay_preview_units.png")
            else:
                self.preview_image_bytes = None
                file_to_send = None
        except Exception as e:
            logger.exception(f"Error generating parlay preview image: {e}")
            self.preview_image_bytes = None
            file_to_send = None
        self.clear_items()
        # Fetch allowed embed channels from guild settings (like straight betting)
        allowed_channels = []
        guild_settings = await self.bot.db_manager.fetch_one(
            "SELECT embed_channel_1, embed_channel_2 FROM guild_settings WHERE guild_id = %s",
            (str(self.original_interaction.guild_id),)
        )
        if guild_settings:
            for channel_id in (guild_settings.get("embed_channel_1"), guild_settings.get("embed_channel_2")):
                if channel_id:
                    try:
                        cid = int(channel_id)
                        channel = self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)
                        if isinstance(channel, TextChannel) and channel.permissions_for(interaction.guild.me).send_messages:
                            if channel not in allowed_channels:
                                allowed_channels.append(channel)
                    except Exception as e:
                        logger.error(f"Error processing channel {channel_id}: {e}")
        if not allowed_channels:
            await self.edit_message_for_current_leg(
                interaction,
                content="❌ No valid embed channels configured. Please contact an admin.",
                view=None
            )
            self.stop()
            return
        self.add_item(ChannelSelect(self, allowed_channels))
        self.add_item(FinalConfirmButton(self))
        self.add_item(CancelButton(self))
        await self.edit_message_for_current_leg(
            interaction,
            content="Select the channel to post your parlay:",
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
        # Regenerate image with all details before posting
        try:
            generator = ParlayImageGenerator(guild_id=self.original_interaction.guild_id)
            legs = []
            for leg in details.get('legs', []):
                leg_data = {
                    'bet_type': leg.get('line_type', 'game_line'),
                    'league': leg.get('league', ''),
                    'home_team': leg.get('home_team_name', ''),
                    'away_team': leg.get('away_team_name', ''),
                    'selected_team': leg.get('team', ''),
                    'line': leg.get('line', ''),
                    'odds': leg.get('odds', leg.get('odds_str', '')),
                }
                if leg.get('line_type') == 'player_prop':
                    leg_data['player_name'] = leg.get('player_name', '')
                legs.append(leg_data)
            total_odds = details.get('total_odds', 0.0)
            units_val = float(details.get("units", 1.0))
            bet_id = str(bet_serial)
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units_val,
                bet_id=bet_id,
                bet_datetime=bet_datetime,
                finalized=True
            )
            discord_file_to_send = None
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                discord_file_to_send = File(self.preview_image_bytes, filename=f"parlay_slip_{bet_id}.png")
            else:
                logger.warning(f"Parlay bet {bet_id}: Failed to generate bet slip image.")
        except Exception as e:
            logger.exception(f"Error generating final parlay image: {e}")
            discord_file_to_send = None
        # ... rest of submit_bet logic unchanged ...

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
