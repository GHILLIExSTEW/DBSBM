# betting-bot/commands/parlay_betting.py

"""Parlay betting workflow for placing multi-leg bets."""

import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import discord
from config.leagues import LEAGUE_CONFIG
from data.game_utils import get_normalized_games_for_dropdown
from discord import (
    ButtonStyle,
    File,
    Interaction,
    Message,
    SelectOption,
    TextChannel,
    app_commands,
)
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, View

from utils.errors import ValidationError
from utils.league_loader import (
    get_all_league_names,
    get_all_sport_categories,
    get_leagues_by_sport,
)
from utils.parlay_bet_image_generator import ParlayBetImageGenerator

from .admin import require_registered_guild

logger = logging.getLogger(__name__)

# Add this near the top, after logger definition
ALLOWED_LEAGUES = [
    "NFL",
    "EPL",
    "NBA",
    "MLB",
    "NHL",
    "La Liga",
    "NCAA",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
    "MLS",
    "ChampionsLeague",
    "EuropaLeague",
    "Brazil Serie A",
    "WorldCup",
    "Formula 1",
    "Tennis",
    "ATP",
    "WTA",
    "MMA",
    "Bellator",
    "WNBA",
    "CFL",
    "AFL",
    "PDC",
    "BDO",
    "WDF",
    "Premier League Darts",
    "World Matchplay",
    "World Grand Prix",
    "UK Open",
    "Grand Slam",
    "Players Championship",
    "European Championship",
    "Masters",
    "EuroLeague",
    "NPB",
    "KBO",
    "KHL",
    "PGA",
    "LPGA",
    "EuropeanTour",
    "LIVGolf",
    "RyderCup",
    "PresidentsCup",
    "SuperRugby",
    "SixNations",
    "FIVB",
    "EHF",
]

# Add league name normalization mapping
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
    "MMA": "MMA",
    "Bellator": "Bellator",
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
    "ChampionsLeague": "ChampionsLeague",
    "EuropaLeague": "EuropaLeague",
    "WorldCup": "WorldCup",
    "SuperRugby": "SuperRugby",
    "SixNations": "SixNations",
    "FIVB": "FIVB",
    "EHF": "EHF",
    "Tennis": "Tennis",
    "ATP": "ATP",
    "WTA": "WTA",
    "PGA": "PGA",
    "LPGA": "LPGA",
    "EuropeanTour": "EuropeanTour",
    "LIVGolf": "LIVGolf",
    "RyderCup": "RyderCup",
    "PresidentsCup": "PresidentsCup",
    "ESPORTS": ["CSGO", "VALORANT", "LOL", "DOTA 2", "PUBG", "COD"],
    "OTHER_SPORTS": ["OTHER_SPORTS"],
    # Add more as needed
    "UEFA CL": "ChampionsLeague",
}


def get_league_file_key(league_name):
    key = LEAGUE_FILE_KEY_MAP.get(league_name, league_name.replace(" ", ""))
    if isinstance(key, list):
        return key[0]
    return key


# --- UI Component Classes ---
class SportSelect(Select):
    def __init__(self, parent_view: "ParlayBetWorkflowView", sports: List[str]):
        self.parent_view = parent_view
        options = [SelectOption(label=sport, value=sport) for sport in sports]
        super().__init__(
            placeholder="Select Sport Category...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_sport_select_{parent_view.original_interaction.id}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        self.parent_view.current_leg_construction_details["sport"] = value
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class LeagueSelect(Select):
    def __init__(
        self,
        parent_view: "ParlayBetWorkflowView",
        leagues: List[str],
        page: int = 0,
        per_page: int = 21,
    ):
        self.parent_view = parent_view
        self.page = page
        self.per_page = per_page
        self.leagues = leagues
        # Deduplicate while preserving order
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
            SelectOption(label=league, value=league.replace(" ", "_").upper())
            for league in page_leagues
        ]
        options.append(SelectOption(label="Manual", value="MANUAL"))
        if end < total_leagues:
            options.append(SelectOption(label="Next ➡️", value="NEXT"))
        if page > 0:
            options.insert(0, SelectOption(label="⬅️ Previous", value="PREVIOUS"))
        super().__init__(
            placeholder="Select League for this Leg...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_league_select_{uuid.uuid4()}",
        )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if value == "NEXT":
            await self.parent_view.update_league_page(interaction, self.page + 1)
            return
        elif value == "PREVIOUS":
            await self.parent_view.update_league_page(interaction, self.page - 1)
            return
        self.parent_view.current_leg_construction_details["league"] = value
        logger.debug(f"League selected: {value} by user {interaction.user.id}")
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class LineTypeSelect(Select):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
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
            placeholder="Select Line Type for this Leg...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_linetype_select_{uuid.uuid4()}",
        )

    async def callback(self, interaction: Interaction):
        try:
            logger.debug(
                f"[LineTypeSelect] Callback triggered. Value: {self.values[0]}"
            )
            self.parent_view.current_leg_construction_details["line_type"] = (
                self.values[0]
            )
            logger.debug(
                f"Parlay Leg - Line Type selected: {self.values[0]} by user {interaction.user.id}"
            )
            self.disabled = True
            for item in self.parent_view.children:
                if isinstance(item, Select) and item != self:
                    item.disabled = True
            await interaction.response.defer()
            await self.parent_view.go_next(interaction)
        except Exception as e:
            logger.exception(f"[LineTypeSelect] Error in callback: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing line type selection. Please try again.",
                    ephemeral=True,
                )
            except Exception as send_e:
                logger.error(f"[LineTypeSelect] Failed to send error message: {send_e}")


class ConfirmButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm",
            custom_id=f"parlay_confirm_{parent_view.original_interaction.id}_{uuid.uuid4()}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        selected_game = self.parent_view.current_leg_construction_details.get(
            "api_game_id"
        )
        is_manual = self.parent_view.current_leg_construction_details.get(
            "is_manual", False
        )
        home_team = self.parent_view.current_leg_construction_details.get(
            "home_team_name", ""
        )
        away_team = self.parent_view.current_leg_construction_details.get(
            "away_team_name", ""
        )
        self.parent_view.clear_items()
        self.parent_view.add_item(TeamSelect(self.parent_view, home_team, away_team))
        self.parent_view.add_item(CancelButton(self.parent_view))
        await self.parent_view.edit_message_for_current_leg(
            interaction,
            content="Select which team you are betting on:",
            view=self.parent_view,
        )
        self.parent_view.current_step += 1


class ParlayGameSelect(Select):
    def __init__(self, parent_view: View, games: List[Dict]):
        game_options = []
        seen_values = set()  # Track used values
        # Only include up to 24 games (Discord limit is 25 options including manual entry)
        for game in games[:24]:
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

            # Format the label with team names and status
            home_team = game.get("home_team_name", "N/A")
            away_team = game.get("away_team_name", "N/A")
            status = game.get("status", "")

            # Calculate max length for team names based on status length
            status_suffix = f" ({status})" if status else ""
            max_team_length = (
                90 - len(status_suffix)
            ) // 2  # Divide remaining space between teams

            # Truncate team names if needed
            if len(home_team) > max_team_length:
                home_team = home_team[: max_team_length - 3] + "..."
            if len(away_team) > max_team_length:
                away_team = away_team[: max_team_length - 3] + "..."

            label = f"{home_team} vs {away_team}{status_suffix}"

            # Get start time for description
            start_time = game.get("start_time")
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
                    label=label[:100], value=value[:100], description=desc[:100]
                )
            )
        # Always add manual entry as the last option
        manual_value = "manual_entry"
        game_options.append(
            SelectOption(
                label="Manual Entry",
                value=manual_value[:100],
                description="Enter game details manually",
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
        logger.debug(
            f"Created ParlayGameSelect with {len(game_options)} unique options (including manual entry)"
        )

    async def callback(self, interaction: Interaction):
        selected_value = self.values[0]
        logger.debug(f"Selected game value: {selected_value}")
        if selected_value == "manual_entry":
            self.parent_view.current_leg_construction_details.update(
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
                self.parent_view.current_leg_construction_details.update(
                    {
                        "api_game_id": selected_game.get("api_game_id"),
                        "game_id": selected_game.get("id"),
                        "home_team_name": selected_game.get("home_team_name"),
                        "away_team_name": selected_game.get("away_team_name"),
                        "is_manual": False,
                    }
                )
                logger.debug(
                    f"Updated leg construction details: {self.parent_view.current_leg_construction_details}"
                )
            else:
                logger.error(f"Could not find game for selected value {selected_value}")
                await interaction.response.defer()
                await self.parent_view.edit_message_for_current_leg(
                    interaction,
                    content="Error: Could not find the selected game. Please try again or cancel.",
                    view=None,
                )
                self.parent_view.stop()
                return
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class CancelButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.red,
            label="Cancel Parlay",
            custom_id=f"parlay_cancel_{parent_view.original_interaction.id}_{uuid.uuid4()}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Cancel Parlay button clicked by user {interaction.user.id}")
        for item in self.parent_view.children:
            item.disabled = True
        bet_serial = self.parent_view.bet_details.get("bet_serial")
        if bet_serial and hasattr(self.parent_view.bot, "bet_service"):
            try:
                await self.parent_view.bot.bet_service.delete_bet(bet_serial)
            except Exception as e:
                logger.error(f"Error deleting parlay bet {bet_serial} on cancel: {e}")
        await interaction.response.edit_message(
            content="Parlay workflow cancelled.", view=None
        )
        self.parent_view.stop()


class BetDetailsModal(Modal):
    def __init__(
        self,
        line_type: str,
        is_manual: bool = False,
        leg_number: int = 1,
        view_custom_id_suffix: str = "",
        bet_details_from_view: dict = None,
    ):
        self.line_type = line_type
        self.is_manual = is_manual
        self.leg_number = leg_number
        self.view_custom_id_suffix = view_custom_id_suffix
        self.view_ref = None
        bet_details_from_view = bet_details_from_view or {}
        league_key = (
            bet_details_from_view.get("league")
            or bet_details_from_view.get("selected_league_key")
            or self.view_ref.current_leg_construction_details.get("league")
            if self.view_ref
            else None
        )
        league_conf = LEAGUE_CONFIG.get(league_key, {})

        # Check if this is an individual sport
        sport_type = league_conf.get("sport_type", "Team Sport")
        is_individual_sport = sport_type == "Individual Player"

        if line_type == "player_prop":
            title = league_conf.get(
                "player_prop_modal_title", f"Parlay Leg {leg_number} Details"
            )
        else:
            title = league_conf.get(
                "game_line_modal_title", f"Parlay Leg {leg_number} Details"
            )
        if is_manual:
            title += " (Manual Entry)"
        super().__init__(title=title)

        # For manual entries, determine fields based on sport type
        if self.is_manual and line_type == "game_line":
            if is_individual_sport:
                # For individual sports (darts, tennis, golf, MMA, etc.), show player and opponent
                player_label = league_conf.get("participant_label", "Player")
                player_placeholder = league_conf.get(
                    "team_placeholder", "e.g., Player Name"
                )

                # League-specific player suggestions
                if league_key in [
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
                ]:
                    player_placeholder = "e.g., Michael van Gerwen, Peter Wright"
                elif league_key in ["ATP", "WTA", "Tennis"]:
                    player_placeholder = "e.g., Novak Djokovic, Iga Swiatek"
                elif league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                    player_placeholder = "e.g., Scottie Scheffler, Nelly Korda"
                elif league_key in ["MMA", "Bellator"]:
                    player_placeholder = "e.g., Jon Jones, Patricio Pitbull"
                elif league_key == "Formula-1":
                    player_placeholder = "e.g., Max Verstappen, Lewis Hamilton"

                self.player_input = TextInput(
                    label=player_label,
                    required=True,
                    max_length=100,
                    placeholder=player_placeholder,
                    default=bet_details_from_view.get(
                        "player_name", bet_details_from_view.get("team", "")
                    ),
                )
                self.add_item(self.player_input)

                opponent_label = league_conf.get("opponent_label", "Opponent")
                opponent_placeholder = league_conf.get(
                    "opponent_placeholder", "e.g., Opponent Name"
                )

                # League-specific opponent suggestions
                if league_key in [
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
                ]:
                    opponent_placeholder = "e.g., Peter Wright, Gerwyn Price"
                elif league_key in ["ATP", "WTA", "Tennis"]:
                    opponent_placeholder = "e.g., Rafael Nadal, Aryna Sabalenka"
                elif league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                    opponent_placeholder = "e.g., Rory McIlroy, Lydia Ko"
                elif league_key in ["MMA", "Bellator"]:
                    opponent_placeholder = "e.g., Francis Ngannou, Cris Cyborg"
                elif league_key == "Formula-1":
                    opponent_placeholder = "e.g., Lewis Hamilton, Charles Leclerc"

                self.opponent_input = TextInput(
                    label=opponent_label,
                    required=True,
                    max_length=100,
                    placeholder=opponent_placeholder,
                    default=bet_details_from_view.get("opponent", ""),
                )
                self.add_item(self.opponent_input)
            else:
                # For team sports, show team and opponent (existing logic)
                team_label = league_conf.get("participant_label", "Team")
                team_placeholder = league_conf.get("team_placeholder", "e.g., Team A")
                opponent_label = league_conf.get("opponent_label", "Opponent")
                opponent_placeholder = league_conf.get(
                    "opponent_placeholder", "e.g., Opponent Team"
                )
                self.team_input = TextInput(
                    label=team_label,
                    required=True,
                    max_length=100,
                    placeholder=team_placeholder,
                    default=bet_details_from_view.get("team", ""),
                )
                self.add_item(self.team_input)
                self.opponent_input = TextInput(
                    label=opponent_label,
                    required=True,
                    max_length=100,
                    placeholder=opponent_placeholder,
                    default=bet_details_from_view.get("opponent", ""),
                )
                self.add_item(self.opponent_input)

        # For game lines, use league-specific label/placeholder for line
        if line_type == "game_line":
            line_label = league_conf.get("line_label_game", "Game Line / Match Outcome")
            line_placeholder = league_conf.get(
                "line_placeholder_game", "e.g., Moneyline, Spread -7.5"
            )

            # League-specific line suggestions
            if league_key in [
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
            ]:
                line_placeholder = (
                    "e.g., To Win Match, Over/Under 180s, Checkout Percentage"
                )
            elif league_key in ["ATP", "WTA", "Tennis"]:
                line_placeholder = (
                    "e.g., To Win Match, Set Handicap -1.5, Total Games Over/Under 22.5"
                )
            elif league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                line_placeholder = (
                    "e.g., To Win Tournament, Top 5 Finish, Round Score Under 68.5"
                )
            elif league_key in ["MMA", "Bellator"]:
                line_placeholder = (
                    "e.g., To Win Fight, Method of Victory (KO/Sub/Decision)"
                )
            elif league_key == "Formula-1":
                line_placeholder = "e.g., To Win Race, Podium Finish, Fastest Lap"

            self.line_input = TextInput(
                label=line_label,
                required=True,
                max_length=100,
                placeholder=line_placeholder,
                default=bet_details_from_view.get("line", ""),
            )
            self.add_item(self.line_input)
        elif line_type == "player_prop":
            # For enhanced player props, we'll use a separate modal
            # This is just a placeholder - the actual enhanced modal will be called separately
            self.enhanced_player_prop_placeholder = TextInput(
                label="Enhanced Player Prop",
                placeholder="Click 'Continue' to use enhanced player prop selection",
                required=False,
                custom_id=f"parlay_enhanced_placeholder_{view_custom_id_suffix}",
            )
            self.add_item(self.enhanced_player_prop_placeholder)
        # Add odds input for every leg
        self.odds_input = TextInput(
            label="Leg Odds",
            placeholder="e.g. -110",
            required=True,
            max_length=10,
            default=(
                bet_details_from_view.get("odds", "") if bet_details_from_view else ""
            ),
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        # Set skip increment flag so go_next does not double-increment
        if self.view_ref:
            self.view_ref._skip_increment = True
        try:
            # Get league config to check sport type
            league_key = self.view_ref.current_leg_construction_details.get(
                "league", ""
            )
            league_conf = LEAGUE_CONFIG.get(league_key, {})
            sport_type = league_conf.get("sport_type", "Team Sport")
            is_individual_sport = sport_type == "Individual Player"

            # For manual game line, get team/opponent or player/opponent based on sport type
            if self.is_manual and self.line_type == "game_line":
                if is_individual_sport:
                    # For individual sports, use player and opponent
                    self.view_ref.current_leg_construction_details["player_name"] = (
                        self.player_input.value.strip()[:100] or "Player"
                    )
                    self.view_ref.current_leg_construction_details["team"] = (
                        self.player_input.value.strip()[:100] or "Player"
                    )
                    self.view_ref.current_leg_construction_details["home_team_name"] = (
                        self.player_input.value.strip()[:100] or "Player"
                    )
                    self.view_ref.current_leg_construction_details["opponent"] = (
                        self.opponent_input.value.strip()[:100] or "Opponent"
                    )
                    self.view_ref.current_leg_construction_details["away_team_name"] = (
                        self.opponent_input.value.strip()[:100] or "Opponent"
                    )
                else:
                    # For team sports, use team and opponent (existing logic)
                    self.view_ref.current_leg_construction_details["team"] = (
                        self.team_input.value.strip()[:100] or "Team"
                    )
                    self.view_ref.current_leg_construction_details["home_team_name"] = (
                        self.team_input.value.strip()[:100] or "Team"
                    )
                    self.view_ref.current_leg_construction_details["opponent"] = (
                        self.opponent_input.value.strip()[:100] or "Opponent"
                    )
                    self.view_ref.current_leg_construction_details["away_team_name"] = (
                        self.opponent_input.value.strip()[:100] or "Opponent"
                    )
            elif self.is_manual and self.line_type == "player_prop":
                # For enhanced player props, we'll handle this in a separate modal
                # Just store the basic info for now
                self.view_ref.current_leg_construction_details["line_type"] = (
                    "player_prop"
                )
                self.view_ref.current_leg_construction_details["league"] = (
                    self.view_ref.current_leg_construction_details.get("league", "")
                )
            elif self.line_type == "player_prop":
                # For enhanced player props, we'll handle this in a separate modal
                # Just store the basic info for now
                self.view_ref.current_leg_construction_details["line_type"] = (
                    "player_prop"
                )
                self.view_ref.current_leg_construction_details["league"] = (
                    self.view_ref.current_leg_construction_details.get("league", "")
                )

            line = self.line_input.value.strip()
            if not line:
                raise ValidationError("Line cannot be empty.")
            self.view_ref.current_leg_construction_details["line"] = line

            # Store odds for this leg
            odds = self.odds_input.value.strip()
            if not odds:
                raise ValidationError("Odds cannot be empty.")
            try:
                odds_float = float(odds)
                self.view_ref.current_leg_construction_details["odds"] = odds_float
            except ValueError:
                raise ValidationError(
                    "Invalid odds format. Please use numbers like -110 or +150."
                )
            self.view_ref.current_leg_construction_details["odds_str"] = odds

            # Generate preview image
            try:
                from utils.parlay_bet_image_generator import ParlayBetImageGenerator

                generator = ParlayBetImageGenerator(
                    guild_id=self.view_ref.original_interaction.guild_id
                )

                # Prepare leg data for preview
                leg_data = {
                    "bet_type": self.line_type,
                    "league": self.view_ref.current_leg_construction_details.get(
                        "league", ""
                    ),
                    "home_team": self.view_ref.current_leg_construction_details.get(
                        "home_team_name", ""
                    ),
                    "away_team": self.view_ref.current_leg_construction_details.get(
                        "away_team_name", ""
                    ),
                    "selected_team": self.view_ref.current_leg_construction_details.get(
                        "team", ""
                    ),
                    "line": line,
                    "odds": odds_float,
                }

                if self.line_type == "player_prop":
                    leg_data["player_name"] = (
                        self.view_ref.current_leg_construction_details.get(
                            "player_name", ""
                        )
                    )
                    # For player props, keep the home team as the selected team
                    leg_data["home_team"] = (
                        self.view_ref.current_leg_construction_details.get("team", "")
                    )
                    leg_data["away_team"] = (
                        self.view_ref.current_leg_construction_details.get(
                            "player_name", ""
                        )
                    )  # This will be replaced with player image
                    leg_data["selected_team"] = (
                        self.view_ref.current_leg_construction_details.get("team", "")
                    )  # Keep the team as selected

                # Generate preview with just this leg
                preview_legs = [leg_data]
                image_bytes = generator.generate_image(
                    legs=preview_legs,
                    output_path=None,
                    total_odds=odds_float,  # Use leg odds for preview
                    units=1.0,
                    bet_id="PREVIEW",
                    bet_datetime=datetime.now(timezone.utc),
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

            # Advance workflow
            if hasattr(self.view_ref, "current_step"):
                self.view_ref.current_step += 1
                logger.info(
                    f"[PARLAY MODAL] Advancing to step {self.view_ref.current_step}"
                )
                await self.view_ref.go_next(interaction)
            else:
                logger.error("View reference missing current_step attribute")
                await interaction.response.send_message(
                    "Error: Could not advance workflow", ephemeral=True
                )

        except ValidationError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error in BetDetailsModal on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing bet details. Please try again.",
                ephemeral=True,
            )


class TotalOddsModal(Modal):
    def __init__(self, view_custom_id_suffix: str):
        super().__init__(title="Enter Total Parlay Odds")
        self.view_custom_id_suffix = view_custom_id_suffix
        self.view_ref = None

        self.odds_input = TextInput(
            label="Total Odds",
            placeholder="Enter the total odds for your parlay (e.g., +1500)",
            required=True,
            custom_id=f"parlay_total_odds_input_{view_custom_id_suffix}",
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        try:
            odds_str = self.odds_input.value.strip()
            if not odds_str:
                raise ValidationError("Odds cannot be empty")

            # Store the total odds
            self.view_ref.bet_details["total_odds"] = float(odds_str)
            self.view_ref.bet_details["total_odds_str"] = odds_str

            # Show units selection
            self.view_ref.clear_items()
            self.view_ref.add_item(UnitsSelect(self.view_ref))
            self.view_ref.add_item(ConfirmUnitsButton(self.view_ref))
            self.view_ref.add_item(CancelButton(self.view_ref))
            await interaction.response.edit_message(
                content="Select units for your parlay:", view=self.view_ref
            )
        except ValidationError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error in TotalOddsModal on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing odds. Please try again.",
                ephemeral=True,
            )


class UnitsSelect(Select):
    def __init__(self, parent_view: "ParlayBetWorkflowView", units_display_mode="auto"):
        self.parent_view = parent_view
        self.units_display_mode = units_display_mode
        options = []
        if units_display_mode == "manual":
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
            placeholder="Select Total Units for Parlay...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_units_select_{parent_view.original_interaction.id}",
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
        logger.debug(f"Parlay Units selected: {value} by user {interaction.user.id}")
        self.disabled = True
        # Update preview image with selected units, but do not proceed to channel selection yet
        try:
            # Get guild settings for units display mode
            guild_settings = await self.parent_view.bot.db_manager.fetch_one(
                "SELECT units_display_mode FROM guild_settings WHERE guild_id = %s",
                (str(self.parent_view.original_interaction.guild_id),),
            )
            units_display_mode = (
                guild_settings.get("units_display_mode", "auto")
                if guild_settings
                else "auto"
            )
            display_as_risk = self.parent_view.bet_details.get("display_as_risk")

            generator = ParlayBetImageGenerator(
                guild_id=self.parent_view.original_interaction.guild_id
            )
            legs = []
            for leg in self.parent_view.bet_details.get("legs", []):
                leg_data = {
                    "bet_type": leg.get("line_type", "game_line"),
                    "league": leg.get("league", ""),
                    "home_team": leg.get("home_team_name", ""),
                    "away_team": leg.get("away_team_name", ""),
                    "selected_team": leg.get("team", ""),
                    "line": leg.get("line", ""),
                    "odds": leg.get("odds", leg.get("odds_str", "")),
                }
                if leg.get("line_type") == "player_prop":
                    leg_data["player_name"] = leg.get("player_name", "")
                legs.append(leg_data)
            # Defensive: ensure legs is a list
            if legs is None:
                legs = []
            total_odds = self.parent_view.bet_details.get("total_odds", None)
            bet_id = str(self.parent_view.bet_details.get("bet_serial", ""))
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=self.parent_view.bet_details["units"],
                bet_id=bet_id,
                bet_datetime=bet_datetime,
                finalized=True,
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )
            if image_bytes:
                self.parent_view.preview_image_bytes = io.BytesIO(image_bytes)
                self.parent_view.preview_image_bytes.seek(0)
                file_to_send = File(
                    self.parent_view.preview_image_bytes,
                    filename="parlay_preview_units.png",
                )
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
            attachments=[file_to_send] if file_to_send else [],
        )


class ChannelSelect(Select):
    def __init__(
        self, parent_view: "ParlayBetWorkflowView", channels: List[TextChannel]
    ):
        self.parent_view = parent_view
        sorted_channels = sorted(channels, key=lambda x: x.name.lower())
        options = [
            SelectOption(
                label=ch.name, value=str(ch.id), description=f"ID: {ch.id}"[:100]
            )
            for ch in sorted_channels[:25]
        ]
        if not options:
            options.append(
                SelectOption(
                    label="No embed channels configured",
                    value="none_configured",
                    emoji="🚫",
                )
            )

        super().__init__(
            placeholder="Select channel to post parlay...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"parlay_channel_select_{parent_view.original_interaction.id}",
            disabled=(not options or options[0].value == "none_configured"),
        )

    async def callback(self, interaction: Interaction):
        if self.values[0] == "none_configured":
            await interaction.response.send_message(
                "No embed channels are available. Please ask an admin to configure them.",
                ephemeral=True,
            )
            return

        self.parent_view.bet_details["channel_id"] = int(self.values[0])
        logger.debug(
            f"Parlay Channel selected: {self.values[0]} by user {interaction.user.id}"
        )
        self.disabled = True
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class FinalConfirmButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm & Post Parlay",
            custom_id=f"parlay_final_confirm_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(
            f"Final confirm parlay button clicked by user {interaction.user.id}"
        )
        await interaction.response.defer(ephemeral=True)
        await self.parent_view.submit_bet(interaction)


class AddAnotherLegButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.green,
            label="Add Another Leg",
            custom_id=f"parlay_add_leg_{parent_view.original_interaction.id}_{len(parent_view.bet_details.get('legs', [])) + 1}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        self.parent_view.current_step = 0
        self.parent_view.current_leg_construction_details = {}
        await interaction.response.defer()
        await self.parent_view.go_next(interaction)


class FinalizeParlayButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.green,
            label="Finalize Parlay",
            custom_id=f"parlay_finalize_{parent_view.original_interaction.id}_{len(parent_view.bet_details.get('legs', []))}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        # Proceed to odds and units selection
        self.parent_view.current_step = 7  # Step for odds modal
        await self.parent_view.go_next(interaction)


class OddsModal(Modal):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(title="Set Parlay Odds")
        self.parent_view = parent_view
        self.odds_input = TextInput(
            label="Enter total parlay odds (e.g. +150)",
            placeholder="+150",
            required=True,
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: Interaction):
        try:
            odds_str = self.odds_input.value.strip()
            if not odds_str:
                raise ValidationError("Odds cannot be empty")

            # Store the odds and default units
            self.parent_view.bet_details["total_odds"] = odds_str
            self.parent_view.bet_details["units"] = 1.0
            self.parent_view.bet_details["units_str"] = "1.0"

            # Generate preview with odds and default units
            try:
                image_generator = ParlayBetImageGenerator(
                    guild_id=self.parent_view.original_interaction.guild_id
                )
                legs = []
                for leg in self.parent_view.bet_details.get("legs", []):
                    leg_data = {
                        "bet_type": leg.get("line_type", "game_line"),
                        "league": leg.get("league", ""),
                        "home_team": leg.get("home_team_name", ""),
                        "away_team": leg.get("away_team_name", ""),
                        "selected_team": leg.get("team", ""),
                        "line": leg.get("line", ""),
                        "odds": leg.get("odds", leg.get("odds_str", "")),
                    }
                    if leg.get("line_type") == "player_prop":
                        leg_data["player_name"] = leg.get("team", "")
                        leg_data["home_team"] = leg.get("team", "")
                        leg_data["away_team"] = leg.get("player_name", "")
                        leg_data["selected_team"] = leg.get("team", "")
                    legs.append(leg_data)
                # Defensive: ensure legs is a list
                if legs is None:
                    legs = []

                # Show preview with odds and default units (1.0)
                image_bytes = image_generator.generate_image(
                    legs=legs,
                    output_path=None,
                    total_odds=odds_str,
                    units=1.0,
                    bet_id=None,
                    bet_datetime=datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M UTC"
                    ),
                    finalized=True,
                )

                if image_bytes:
                    self.parent_view.preview_image_bytes = io.BytesIO(image_bytes)
                    self.parent_view.preview_image_bytes.seek(0)
                    preview_file = discord.File(
                        self.parent_view.preview_image_bytes,
                        filename="parlay_preview.png",
                    )
                else:
                    self.parent_view.preview_image_bytes = None
                    preview_file = None
            except Exception as e:
                logger.error(f"Error generating parlay preview image: {e}")
                self.parent_view.preview_image_bytes = None
                preview_file = None

            # Show units selection with default of 1 unit
            content = "✅ Odds set! Select your units:"
            self.parent_view.clear_items()
            self.parent_view.add_item(UnitsSelect(self.parent_view))
            self.parent_view.add_item(CancelButton(self.parent_view))

            await interaction.response.edit_message(
                content=content,
                view=self.parent_view,
                attachments=[preview_file] if preview_file else [],
            )

        except ValidationError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error in OddsModal.on_submit: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting odds. Please try again.",
                ephemeral=True,
            )


class LegDecisionView(View):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(timeout=600)
        self.parent_view = parent_view
        self.add_item(AddAnotherLegButton(self.parent_view))
        finalize_button = FinalizeParlayButton(self.parent_view)
        finalize_button.disabled = len(self.parent_view.bet_details.get("legs", [])) < 1
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
        home_team = self.parent_view.current_leg_construction_details.get(
            "home_team_name", ""
        )
        away_team = self.parent_view.current_leg_construction_details.get(
            "away_team_name", ""
        )
        if selected_team == home_team:
            opponent = away_team
        else:
            opponent = home_team
        self.parent_view.current_leg_construction_details["team"] = selected_team
        self.parent_view.current_leg_construction_details["opponent"] = opponent
        line_type = self.parent_view.current_leg_construction_details.get(
            "line_type", "game_line"
        )

        # Use enhanced player prop modal for player props
        if line_type == "player_prop":
            from commands.parlay_enhanced_player_prop_modal import (
                ParlayEnhancedPlayerPropModal,
            )

            modal = ParlayEnhancedPlayerPropModal(
                self.parent_view.bot,
                self.parent_view.bot.db_manager,
                self.parent_view.current_leg_construction_details.get("league", ""),
                leg_number=len(self.parent_view.bet_details.get("legs", [])) + 1,
                view_custom_id_suffix=self.parent_view.original_interaction.id,
                bet_details_from_view=self.parent_view.current_leg_construction_details,
            )
            modal.view_ref = self.parent_view
        else:
            # Use regular bet details modal for game lines
            modal = BetDetailsModal(
                line_type=line_type,
                is_manual=self.parent_view.current_leg_construction_details.get(
                    "is_manual", False
                ),
                leg_number=len(self.parent_view.bet_details.get("legs", [])) + 1,
                view_custom_id_suffix=self.parent_view.original_interaction.id,
                bet_details_from_view=self.parent_view.current_leg_construction_details,
            )
            modal.view_ref = self.parent_view
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)
            await self.parent_view.edit_message_for_current_leg(
                interaction,
                content="Please fill in the bet details in the popup form.",
                view=self.parent_view,
            )
        else:
            logger.error("Tried to send modal, but interaction already responded to.")
            await self.parent_view.edit_message_for_current_leg(
                interaction,
                content="❌ Error: Could not open modal. Please try again or cancel.",
                view=None,
            )
            self.parent_view.stop()


class ConfirmUnitsButton(Button):
    def __init__(self, parent_view: "ParlayBetWorkflowView"):
        super().__init__(
            style=ButtonStyle.green,
            label="Confirm Units",
            custom_id=f"parlay_confirm_units_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(f"Confirm Units button clicked by user {interaction.user.id}")
        await self.parent_view._handle_units_selection(
            interaction, float(self.parent_view.bet_details["units"])
        )


# --- Main Workflow View ---
class ParlayBetWorkflowView(View):
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
        self.bet_details: Dict[str, Any] = {"legs": [], "total_odds": 1.0}
        self.current_leg_construction_details: Dict[str, Any] = {}
        self.games: List[Dict] = []
        self.is_processing = False
        self.latest_interaction = original_interaction
        self.bet_slip_generator: Optional[ParlayBetImageGenerator] = None
        self.preview_image_bytes: Optional[io.BytesIO] = None
        logger.info(
            f"[ParlayBetWorkflowView] Initialized for user {original_interaction.user.id}"
        )

    async def get_bet_slip_generator(self) -> ParlayBetImageGenerator:
        if not self.bet_slip_generator:
            self.bet_slip_generator = ParlayBetImageGenerator(
                guild_id=self.original_interaction.guild_id
            )
        return self.bet_slip_generator

    def _format_odds_with_sign(self, odds: Optional[Union[float, int]]) -> str:
        if odds is None:
            return "N/A"
        try:
            odds_num = int(float(odds))
            return f"+{odds_num}" if odds_num > 0 else str(odds_num)
        except (ValueError, TypeError):
            return "N/A"

    def _calculate_parlay_odds(self, legs: List[Dict[str, Any]]) -> float:
        # Since odds are now provided by TotalOddsModal, return stored total odds
        return self.bet_details.get("total_odds", 0.0)

    async def add_leg(
        self, modal_interaction: Interaction, leg_details: Dict[str, Any], file=None
    ):
        try:
            # Add the leg to the parlay
            if "legs" not in self.bet_details:
                self.bet_details["legs"] = []
            self.bet_details["legs"].append(leg_details)
            # Reset current leg construction details
            self.current_leg_construction_details = {}
            # Generate preview image for the entire parlay
            try:
                image_generator = ParlayBetImageGenerator()
                legs = []
                for leg in self.bet_details.get("legs", []):
                    leg_data = {
                        "bet_type": leg.get("line_type", "game_line"),
                        "league": leg.get("league", ""),
                        "home_team": leg.get("home_team_name", ""),
                        "away_team": leg.get("away_team_name", ""),
                        "selected_team": leg.get("team", ""),
                        "line": leg.get("line", ""),
                        "odds": leg.get("odds", leg.get("odds_str", "")),
                    }
                    if leg.get("line_type") == "player_prop":
                        leg_data["player_name"] = leg.get("player_name", "")
                    legs.append(leg_data)
                image_bytes = image_generator.generate_parlay_preview(legs)
                if image_bytes:
                    self.preview_image_bytes = io.BytesIO(image_bytes)
                    self.preview_image_bytes.seek(0)
                    preview_file = discord.File(
                        self.preview_image_bytes, filename=f"parlay_preview.png"
                    )
                    embed = discord.Embed(
                        title=f"{len(self.bet_details['legs'])}-Leg Parlay Bet"
                    )
                    embed.set_image(url="attachment://parlay_preview.png")
                else:
                    self.preview_image_bytes = None
                    preview_file = None
                    embed = None
            except Exception as e:
                logger.error(f"Error generating parlay preview image: {e}")
                self.preview_image_bytes = None
                preview_file = None
                embed = None
            # Show decision view for adding another leg or finalizing
            leg_count = len(self.bet_details["legs"])
            summary_text = self._generate_parlay_summary_text()
            decision_view = LegDecisionView(self)
            await self.edit_message_for_current_leg(
                modal_interaction,
                content=f"✅ Line added for Leg {leg_count}\n\n{summary_text}\n\nAdd another leg or finalize?",
                view=decision_view,
                embed=embed,
                file=preview_file,
            )
        except Exception as e:
            logger.error(f"Error in add_leg: {e}")
            await modal_interaction.response.send_message(
                "❌ Error adding leg to parlay. Please try again.", ephemeral=True
            )

    async def start_flow(self, interaction_that_triggered_workflow_start: Interaction):
        logger.debug(
            f"Starting parlay bet workflow for user {self.original_interaction.user.id}"
        )
        try:
            if not self.message:
                logger.error(
                    "ParlayBetWorkflowView.start_flow called but self.message is None."
                )
                self.stop()
                return
            await self.go_next(interaction_that_triggered_workflow_start)
        except Exception as e:
            logger.exception(f"Failed during initial go_next in ParlayBetWorkflow: {e}")
            await self.edit_message_for_current_leg(
                content="❌ Failed to start parlay workflow. Please try again.",
                view=None,
            )
            self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message(
                "You cannot interact with this parlay.", ephemeral=True
            )
            return False
        self.latest_interaction = interaction
        return True

    async def edit_message_for_current_leg(
        self,
        interaction_context: Interaction,
        content: Optional[str] = None,
        view: Optional[View] = None,
        embed: Optional[discord.Embed] = None,
        file: Optional[File] = None,
    ):
        logger.debug(
            f"Parlay: Attempting to edit message {self.message.id if self.message else 'None'}. Content: {content is not None}, View: {view is not None}"
        )
        attachments = [file] if file else discord.utils.MISSING
        try:
            if self.message:
                await self.message.edit(
                    content=content, embed=embed, view=view, attachments=attachments
                )
            else:
                logger.warning(
                    "Parlay: self.message is None during edit_message_for_current_leg. Using original_interaction followup."
                )
                if self.original_interaction.response.is_done():
                    self.message = await self.original_interaction.followup.send(
                        content=content or "Updating...",
                        view=view,
                        files=attachments if attachments else None,
                        ephemeral=True,
                    )
                else:
                    await self.original_interaction.response.send_message(
                        content=content or "Updating...",
                        view=view,
                        files=attachments if attachments else None,
                        ephemeral=True,
                    )
                    self.message = await self.original_interaction.original_response()
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(
                f"Parlay: Failed to edit message {self.message.id if self.message else 'Original Interaction'}: {e}. Interaction type: {interaction_context.type if interaction_context else 'N/A'}"
            )
            if (
                interaction_context
                and interaction_context.response.is_done()
                and (
                    not self.message
                    or interaction_context.message.id != self.message.id
                )
            ):
                try:
                    self.message = await interaction_context.followup.send(
                        content=content or "Updating display...",
                        ephemeral=True,
                        view=view,
                        files=attachments if attachments else None,
                    )
                except discord.HTTPException as fe:
                    logger.error(
                        f"Parlay: Failed to send followup after message edit error: {fe}"
                    )
            elif not interaction_context.response.is_done():
                try:
                    await interaction_context.response.send_message(
                        content=content or "Updating display...",
                        ephemeral=True,
                        view=view,
                        files=attachments if attachments else None,
                    )
                    self.message = await interaction_context.original_response()
                except discord.HTTPException as fe:
                    logger.error(
                        f"Parlay: Failed to send new message after previous edit error: {fe}"
                    )
            else:
                logger.error(
                    f"Parlay: Cannot reliably update user after message edit error. Main message: {self.message.id if self.message else 'None'}"
                )
        except Exception as e:
            logger.exception(f"Parlay: Unexpected error editing message: {e}")

    async def go_next(self, interaction: Interaction):
        """Advance to the next step in the parlay workflow."""
        if hasattr(self, "_skip_increment") and self._skip_increment:
            self._skip_increment = False
            return

        self.current_step += 1
        logger.info(f"[PARLAY WORKFLOW] go_next called for step {self.current_step}")

        if self.current_step == 1:
            # Step 1: Sport category selection
            sports = get_all_sport_categories()
            self.clear_items()
            self.add_item(SportSelect(self, sports))
            self.add_item(CancelButton(self))
            await self.edit_message_for_current_leg(
                interaction,
                content="Select a sport category for your parlay:",
                view=self,
            )
            return
        elif self.current_step == 2:
            # Step 2: League selection within selected sport
            sport = self.current_leg_construction_details.get("sport")
            leagues = get_leagues_by_sport(sport)
            self.clear_items()
            self.add_item(LeagueSelect(self, leagues))
            self.add_item(CancelButton(self))
            await self.edit_message_for_current_leg(
                interaction, content=f"Select a league from {sport}:", view=self
            )
            return
        elif self.current_step == 3:
            # Step 3: Line type selection
            self.clear_items()
            self.add_item(LineTypeSelect(self))
            self.add_item(CancelButton(self))
            await self.edit_message_for_current_leg(
                interaction, content="Select the type of bet for this leg:", view=self
            )
            return
        elif self.current_step == 4:
            # Step 4: Game selection
            league = self.current_leg_construction_details.get("league", "N/A")
            line_type = self.current_leg_construction_details.get(
                "line_type", "game_line"
            )
            logger.info(
                f"[PARLAY WORKFLOW] Fetching games for league: {league}, line_type: {line_type}"
            )

            try:
                # Fetch games using the correct method
                games = await get_normalized_games_for_dropdown(
                    self.bot.db_manager, league
                )

                if not games:
                    await self.edit_message_for_current_leg(
                        interaction,
                        content=f"No games found for {league}. Please try a different league or check back later.",
                        view=None,
                    )
                    self.stop()
                    return

                self.clear_items()
                self.add_item(ParlayGameSelect(self, games))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(
                    interaction, content="Select a game for this leg:", view=self
                )

            except Exception as e:
                logger.error(f"Error fetching games: {e}")
                await self.edit_message_for_current_leg(
                    interaction,
                    content=f"Error fetching games for {league}. Please try again or contact support.",
                    view=None,
                )
                self.stop()
                return
        elif self.current_step == 5:
            # Step 5: Team selection or modal (depending on manual entry and sport type)
            league = self.current_leg_construction_details.get("league", "N/A")
            line_type = self.current_leg_construction_details.get(
                "line_type", "game_line"
            )
            is_manual = self.current_leg_construction_details.get("is_manual", False)

            if is_manual:
                # For manual entry, check if this is an individual sport
                from config.leagues import LEAGUE_CONFIG

                league_conf = LEAGUE_CONFIG.get(league, {})
                sport_type = league_conf.get("sport_type", "Team Sport")
                is_individual_sport = sport_type == "Individual Player"

                if is_individual_sport:
                    # For individual sports, skip team selection and go directly to modal
                    if line_type == "player_prop":
                        # Use enhanced player prop modal
                        from commands.parlay_enhanced_player_prop_modal import (
                            ParlayEnhancedPlayerPropModal,
                        )

                        modal = ParlayEnhancedPlayerPropModal(
                            self.bot,
                            self.bot.db_manager,
                            league,
                            leg_number=len(self.bet_details.get("legs", [])) + 1,
                            view_custom_id_suffix=self.original_interaction.id,
                            bet_details_from_view=self.current_leg_construction_details,
                        )
                        modal.view_ref = self
                    else:
                        # Use regular bet details modal for game lines
                        modal = BetDetailsModal(
                            line_type=line_type,
                            is_manual=True,
                            leg_number=len(self.bet_details.get("legs", [])) + 1,
                            view_custom_id_suffix=self.original_interaction.id,
                            bet_details_from_view=self.current_leg_construction_details,
                        )
                        modal.view_ref = self

                    if not interaction.response.is_done():
                        await interaction.response.send_modal(modal)
                        await self.edit_message_for_current_leg(
                            interaction,
                            content="Please fill in the bet details in the popup form.",
                            view=self,
                        )
                    else:
                        logger.error(
                            "Tried to send modal, but interaction already responded to."
                        )
                        await self.edit_message_for_current_leg(
                            interaction,
                            content="❌ Error: Could not open modal. Please try again or cancel.",
                            view=None,
                        )
                        self.stop()
                    return
                else:
                    # For team sports, show team selection (existing logic)
                    home_team = self.current_leg_construction_details.get(
                        "home_team_name", ""
                    )
                    away_team = self.current_leg_construction_details.get(
                        "away_team_name", ""
                    )
                    self.add_item(TeamSelect(self, home_team, away_team))
                    self.add_item(CancelButton(self))
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="Select which team you are betting on:",
                        view=self,
                    )
                    return
            else:
                # For regular games, show team selection
                home_team = self.current_leg_construction_details.get(
                    "home_team_name", ""
                )
                away_team = self.current_leg_construction_details.get(
                    "away_team_name", ""
                )
                self.add_item(TeamSelect(self, home_team, away_team))
                self.add_item(CancelButton(self))
                await self.edit_message_for_current_leg(
                    interaction,
                    content="Select which team you are betting on:",
                    view=self,
                )
                return
        elif self.current_step == 6:
            # Show bet details modal (handled by modal, so just return)
            return
        elif self.current_step == 7:
            # Show summary and decision view
            summary_text = self._generate_parlay_summary_text()
            decision_view = LegDecisionView(self)
            await self.edit_message_for_current_leg(
                interaction,
                content=f"Current Parlay:\n{summary_text}",
                view=decision_view,
            )
            self.current_step += 1
            return
        elif self.current_step == 8:
            # Show total odds modal
            modal = TotalOddsModal(view_custom_id_suffix=self.original_interaction.id)
            modal.view_ref = self
            await interaction.response.send_modal(modal)
            return
        elif self.current_step == 9:
            # Show units select
            self.add_item(UnitsSelect(self))
            self.add_item(ConfirmUnitsButton(self))
            self.add_item(CancelButton(self))
            await self.edit_message_for_current_leg(
                interaction, content="Select units for your parlay:", view=self
            )
            self.current_step += 1
            return
        elif self.current_step == 10:
            # Show channel selection
            try:
                # Get available channels for the user
                guild = self.original_interaction.guild
                if not guild:
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="❌ Error: Could not access guild information.",
                        view=None,
                    )
                    self.stop()
                    return

                # Get channels where the bot can send messages
                available_channels = []
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        available_channels.append(channel)

                if not available_channels:
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="❌ No channels available for posting bets.",
                        view=None,
                    )
                    self.stop()
                    return

                self.clear_items()
                self.add_item(ChannelSelect(self, available_channels))
                self.add_item(FinalConfirmButton(self))
                self.add_item(CancelButton(self))

                file_to_send = None
                if self.preview_image_bytes:
                    self.preview_image_bytes.seek(0)
                    file_to_send = File(
                        self.preview_image_bytes, filename="parlay_preview.png"
                    )

                await self.edit_message_for_current_leg(
                    interaction,
                    content="Select channel to post your parlay:",
                    view=self,
                    file=file_to_send,
                )
                return

            except Exception as e:
                logger.error(f"Error in step 10: {e}")
                await self.edit_message_for_current_leg(
                    interaction, content=f"❌ Error: {e}", view=None
                )
                self.stop()
                return
        else:
            logger.warning(f"Unknown step: {self.current_step}")
            await self.edit_message_for_current_leg(
                interaction,
                content="❌ Unknown workflow step. Please restart.",
                view=None,
            )
            self.stop()

    def _generate_parlay_summary_text(self) -> str:
        summary_parts = []
        legs = self.bet_details.get("legs", [])
        for i, leg in enumerate(legs, 1):
            summary_parts.append(
                f"**Leg {i}**: {leg.get('league','N/A')} - "
                f"{leg.get('team','N/A')} vs {leg.get('opponent','N/A')} - {leg.get('line','N/A')}"
            )
        summary_text = "\n".join(summary_parts)
        summary_text += (
            f"\n\nTotal Odds: **{self.bet_details.get('total_odds_str', 'N/A')}**"
        )
        summary_text += f"\nUnits: **{self.bet_details.get('units_str', 'N/A')}**"
        selected_channel_id = self.bet_details.get("channel_id")
        channel_mention = (
            f"<#{selected_channel_id}>" if selected_channel_id else "Not selected"
        )
        summary_text += f"\nPost to Channel: {channel_mention}"
        summary_text += "\n\nClick Confirm to place your parlay."
        return summary_text

    async def _handle_units_selection(self, interaction: Interaction, units: float):
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
            generator = ParlayBetImageGenerator(
                guild_id=self.original_interaction.guild_id
            )
            legs = []
            for leg in self.bet_details.get("legs", []) or []:
                leg_data = {
                    "bet_type": leg.get("line_type", "game_line"),
                    "league": leg.get("league", ""),
                    "home_team": leg.get("home_team_name", ""),
                    "away_team": leg.get("away_team_name", ""),
                    "selected_team": leg.get("team", ""),
                    "line": leg.get("line", ""),
                    "odds": leg.get("odds", leg.get("odds_str", "")),
                }
                if leg.get("line_type") == "player_prop":
                    leg_data["player_name"] = leg.get("player_name", "")
                    # For player props, keep the home team as the selected team
                    leg_data["home_team"] = leg.get("team", "")
                    leg_data["away_team"] = leg.get(
                        "player_name", ""
                    )  # This will be replaced with player image
                    leg_data["selected_team"] = leg.get(
                        "team", ""
                    )  # Keep the team as selected
                legs.append(leg_data)
            # Defensive: ensure legs is a list
            if legs is None:
                legs = []
            total_odds = self.bet_details.get("total_odds", None)
            bet_id = str(self.bet_details.get("bet_serial", ""))
            bet_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units,
                bet_id=bet_id,
                bet_datetime=bet_datetime,
                finalized=True,
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                file_to_send = File(
                    self.preview_image_bytes, filename="parlay_preview_units.png"
                )
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
                            isinstance(channel, TextChannel)
                            and channel.permissions_for(
                                interaction.guild.me
                            ).send_messages
                        ):
                            if channel not in allowed_channels:
                                allowed_channels.append(channel)
                    except Exception as e:
                        logger.error(f"Error processing channel {channel_id}: {e}")
        if not allowed_channels:
            await self.edit_message_for_current_leg(
                interaction,
                content="❌ No valid embed channels configured. Please contact an admin.",
                view=None,
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
            file=file_to_send,
        )

    async def update_league_page(self, interaction, page):
        leagues = get_all_league_names()
        self.clear_items()
        self.add_item(LeagueSelect(self, leagues, page=page))
        self.add_item(CancelButton(self))
        await self.edit_message_for_current_leg(
            interaction, content="Select a league for your parlay:", view=self
        )

    async def submit_bet(self, interaction: Interaction):
        details = self.bet_details
        bet_serial = details.get("bet_serial")
        bet_service = getattr(self.bot, "bet_service", None)
        if not bet_serial:
            # Insert the bet now with all final values
            if bet_service:
                try:
                    primary_league = (
                        details.get("legs", [{}])[0].get("league", "PARLAY")
                        if details.get("legs")
                        else "PARLAY"
                    )
                    bet_serial = await bet_service.create_parlay_bet(
                        guild_id=self.original_interaction.guild_id,
                        user_id=self.original_interaction.user.id,
                        league=primary_league,
                        legs_data=details.get("legs", []),
                        units=float(details.get("units", 1.0)),
                        channel_id=details.get("channel_id"),
                        confirmed=1,  # <-- pass confirmed=1 if supported
                    )
                    if not bet_serial:
                        logger.error(
                            "Failed to create parlay bet in DB at submit step."
                        )
                        await self.edit_message_for_current_leg(
                            interaction,
                            content="❌ Failed to create parlay bet in database. Please try again.",
                            view=None,
                        )
                        self.stop()
                        return
                    self.bet_details["bet_serial"] = bet_serial
                except Exception as e:
                    logger.error(
                        f"Failed to create parlay bet in DB at submit step: {e}"
                    )
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="❌ Failed to create parlay bet in database. Please try again.",
                        view=None,
                    )
                    self.stop()
                    return
        logger.info(f"Submitting parlay bet {bet_serial} by user {interaction.user.id}")
        # Regenerate image with all details before posting
        try:
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
            display_as_risk = details.get("display_as_risk")

            generator = ParlayBetImageGenerator(
                guild_id=self.original_interaction.guild_id
            )
            legs = []
            for leg in details.get("legs", []):
                leg_data = {
                    "bet_type": leg.get("line_type", "game_line"),
                    "league": leg.get("league", ""),
                    "home_team": leg.get("home_team_name", ""),
                    "away_team": leg.get("away_team_name", ""),
                    "selected_team": leg.get("team", ""),
                    "line": leg.get("line", ""),
                    "odds": leg.get("odds", leg.get("odds_str", "")),
                }
                if leg.get("line_type") == "player_prop":
                    leg_data["player_name"] = leg.get("team", "")
                legs.append(leg_data)
            # Defensive: ensure legs is a list
            if legs is None:
                legs = []
            total_odds = details.get("total_odds", 0.0)
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
                finalized=True,
                units_display_mode=units_display_mode,
                display_as_risk=display_as_risk,
            )
            discord_file_to_send = None
            if image_bytes:
                self.preview_image_bytes = io.BytesIO(image_bytes)
                self.preview_image_bytes.seek(0)
                discord_file_to_send = File(
                    self.preview_image_bytes, filename=f"parlay_slip_{bet_id}.png"
                )
            else:
                logger.warning(
                    f"Parlay bet {bet_id}: Failed to generate bet slip image."
                )

            # Post the bet to the selected channel
            try:
                post_channel_id = details.get("channel_id")
                post_channel = (
                    self.bot.get_channel(post_channel_id) if post_channel_id else None
                )
                if not post_channel or not isinstance(post_channel, TextChannel):
                    raise ValueError(
                        f"Invalid channel <#{post_channel_id}> for bet posting."
                    )

                # Get capper data for webhook
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
                    from utils.image_url_converter import convert_image_path_to_url

                    webhook_avatar_url = convert_image_path_to_url(
                        capper_data["image_path"]
                    )

                # Fetch member_role for mention
                member_role_id = None
                guild_settings = await self.bot.db_manager.fetch_one(
                    "SELECT member_role FROM guild_settings WHERE guild_id = %s",
                    (str(interaction.guild_id),),
                )
                if guild_settings and guild_settings.get("member_role"):
                    member_role_id = guild_settings["member_role"]

                # Post the bet slip image to the channel using a webhook
                if member_role_id:
                    content = f"<@&{member_role_id}>"
                else:
                    content = None

                # Create or find webhook
                webhooks = await post_channel.webhooks()
                target_webhook = None
                for webhook in webhooks:
                    if webhook.name == "Bet Bot":
                        target_webhook = webhook
                        break
                if not target_webhook:
                    target_webhook = await post_channel.create_webhook(name="Bet Bot")

                try:
                    webhook_message = await target_webhook.send(
                        content=content,
                        file=discord_file_to_send,
                        username=webhook_username,
                        avatar_url=webhook_avatar_url,
                        wait=True,
                    )
                except Exception as e:
                    logger.error(f"Exception during parlay webhook.send: {e}")
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="Error: Failed to post parlay bet message via webhook (send failed).",
                        view=None,
                    )
                    self.stop()
                    return
                if not webhook_message:
                    logger.error(
                        "Parlay webhook.send returned None (no message object). Possible permission or Discord API error."
                    )
                    await self.edit_message_for_current_leg(
                        interaction,
                        content="Error: Parlay bet message could not be posted (no message returned from webhook).",
                        view=None,
                    )
                    self.stop()
                    return

                # Save message_id and channel_id in the bets table
                if bet_service:
                    try:
                        await bet_service.update_parlay_bet_channel(
                            bet_serial=details["bet_serial"],
                            channel_id=webhook_message.channel.id,
                            message_id=webhook_message.id,
                        )
                        logger.info(
                            f"Updated parlay bet {details['bet_serial']} with message_id {webhook_message.id} and channel_id {webhook_message.channel.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to update parlay bet with message_id: {e}"
                        )

                await self.edit_message_for_current_leg(
                    interaction,
                    content="✅ Parlay bet posted successfully!",
                    view=None,
                    file=None,
                )
                self.stop()

            except Exception as e:
                logger.error(
                    f"[submit_bet] Failed to post parlay bet: {str(e)}", exc_info=True
                )
                await self.edit_message_for_current_leg(
                    interaction,
                    content=f"❌ Failed to post parlay bet: {str(e)}",
                    view=None,
                )
                self.stop()

        except Exception as e:
            logger.exception(f"Error generating final parlay image: {e}")
            await self.edit_message_for_current_leg(
                interaction,
                content=f"❌ Error generating parlay image: {str(e)}",
                view=None,
            )
            self.stop()


class ParlayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.info("ParlayCog initialized")

    @app_commands.command(
        name="parlay",
        description="🎲 Create a multi-leg parlay - combine multiple bets for bigger payouts",
    )
    @require_registered_guild()
    async def parlay(self, interaction: Interaction):
        logging.info(
            f"/parlay command invoked by {interaction.user} (ID: {interaction.user.id})"
        )
        try:
            view = ParlayBetWorkflowView(interaction, self.bot)
            logging.debug("ParlayBetWorkflowView initialized successfully.")
            await interaction.response.send_message(
                "Let's build your parlay! Add legs (game lines or player props) and finalize when ready:",
                view=view,
                ephemeral=True,
            )
            view.message = await interaction.original_response()
            logging.info("/parlay command response sent successfully.")

            # Start the workflow
            await view.start_flow(interaction)
            logging.info("Parlay workflow started successfully.")
        except Exception as e:
            logging.error(f"Error in /parlay command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while processing your parlay request.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    logging.info("Setting up parlay commands...")
    try:
        await bot.add_cog(ParlayCog(bot))
        logging.info("ParlayCog loaded successfully")
    except Exception as e:
        logging.error(f"Error during parlay command setup: {e}", exc_info=True)
        raise
