# REV 1.0.0 - Enhanced betting modals with improved validation and error handling
# betting-bot/utils/modals.py
import discord
from discord.ui import Modal, TextInput
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
import io
from datetime import datetime, timezone
import os
from PIL import Image
import glob
from rapidfuzz import process, fuzz

# Import your project's configurations and utilities
# Adjust these paths if your config/utils structure is different
# relative to the 'betting-bot' root when this module is imported.
from config.leagues import LEAGUE_CONFIG
from utils.errors import BetServiceError # Example, if used directly in modal
from config.asset_paths import BASE_DIR
# Import the correct version of the image generator
from utils.image_generator import BetSlipGenerator

# Add this mapping at the top of the file (after imports)
PLAYER_PROP_SPORT_ID_MAP = {
    "NHL": "ice_hockey",
    "NFL": "american_football",
    "NBA": "basketball",
    "MLB": "baseball",
    "MLS": "soccer",
    # Add more as needed
}

# For type hinting the parent view reference without circular imports
if TYPE_CHECKING:
    from commands.straight_betting import StraightBetWorkflowView
    from commands.parlay_betting import ParlayBetWorkflowView # Example
    # Add other view types if modals reference them specifically
    # from commands.setid import ImageUploadView # Example for CapperImageURLModal's parent

logger = logging.getLogger(__name__)

class PlayerPropModal(Modal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        league_key = bet_details_from_view.get('selected_league_key', 'DEFAULT')
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        super().__init__(title=f"{league_conf.get('player_label', 'Player')} Prop Bet Details")

        self.league_key = league_key
        self.league_conf = league_conf
        self.single_participant = league_conf.get('single_participant', False)

        self.player_input = TextInput(
            label=league_conf.get('player_label', 'Player'),
            required=True,
            max_length=100,
            placeholder=league_conf.get('player_placeholder', 'e.g., John Smith'),
            default=bet_details_from_view.get('player_name', '')
        )
        self.add_item(self.player_input)

        if not self.single_participant:
            self.opponent_input = TextInput(
                label=league_conf.get('opponent_label', 'Opponent'),
                required=True,
                max_length=100,
                placeholder=league_conf.get('opponent_placeholder', 'e.g., Opponent Name'),
                default=bet_details_from_view.get('opponent', '')
            )
            self.add_item(self.opponent_input)
        else:
            self.opponent_input = None

        self.player_prop_input = TextInput(
            label=league_conf.get('prop_line_label', 'Player Prop / Line'),
            required=True,
            max_length=100,
            placeholder=league_conf.get('prop_line_placeholder', 'e.g., Over 25.5 Points'),
            default=bet_details_from_view.get('line', '')
        )
        self.add_item(self.player_prop_input)

        self.odds_input = TextInput(
            label="Odds",
            required=True,
            max_length=10,
            placeholder=league_conf.get('odds_placeholder', 'e.g., -110 or +200'),
            default=bet_details_from_view.get('odds_str', '')
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            player = self.player_input.value.strip()
            player_prop_line = self.player_prop_input.value.strip()
            odds_str = self.odds_input.value.strip()
            units = 1.0  # Default, or fetch from view_ref if you support custom units
            bet_id = getattr(self.view_ref, 'bet_id', 'N/A') if hasattr(self, 'view_ref') else 'N/A'
            league = getattr(self.view_ref, 'league', 'N/A') if hasattr(self, 'view_ref') else 'N/A'
            timestamp = datetime.now(timezone.utc)
            team = self.league_conf.get('team_name', '') or getattr(self.view_ref, 'team', '') or ''
            if not team:
                team = self.league_key  # fallback to league key if no team
            if not self.single_participant and self.opponent_input:
                opponent = self.opponent_input.value.strip()
            else:
                opponent = None

            # Save to bet_details
            if hasattr(self, 'view_ref') and hasattr(self.view_ref, 'bet_details'):
                self.view_ref.bet_details.update({
                    "team": team,
                    "opponent": opponent,
                    "line": player_prop_line,
                    "odds_str": odds_str,
                    "odds": float(odds_str.replace('+', '')) if odds_str.replace('+', '').replace('.', '', 1).isdigit() else odds_str,
                    "player_name": player,
                    "line_type": "player_prop"
                })

            # Get player image
            from utils.modals import get_player_image  # or import at top
            player_image_path = get_player_image(player, team, self.league_key)
            player_image = None
            if player_image_path:
                from PIL import Image
                player_image = Image.open(player_image_path).convert("RGBA")

            # Generate bet slip
            bet_slip_generator = await self.view_ref.get_bet_slip_generator() if hasattr(self, 'view_ref') else None
            if not self.single_participant and opponent:
                display_vs = f"{team} vs {opponent}"
            else:
                display_vs = player
            bet_slip_image = None
            if bet_slip_generator:
                bet_slip_image = await bet_slip_generator.generate_bet_slip(
                    home_team=team,
                    away_team=opponent or '',
                    league=league,
                    line=player_prop_line,
                    odds=float(odds_str.replace('+', '')) if odds_str.replace('+', '').replace('.', '', 1).isdigit() else odds_str,
                    units=units,
                    bet_id=bet_id,
                    timestamp=timestamp,
                    bet_type="player_prop",
                    player_name=player,
                    player_image=player_image,
                    display_vs=display_vs
                )
            if bet_slip_image and hasattr(self.view_ref, 'preview_image_bytes'):
                import io
                self.view_ref.preview_image_bytes = io.BytesIO()
                bet_slip_image.save(self.view_ref.preview_image_bytes, format='PNG')
                self.view_ref.preview_image_bytes.seek(0)
            elif hasattr(self.view_ref, 'preview_image_bytes'):
                self.view_ref.preview_image_bytes = None

            if hasattr(self.view_ref, 'current_step'):
                self.view_ref.current_step = 4
            if hasattr(self.view_ref, 'go_next'):
                await self.view_ref.go_next(interaction)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in PlayerPropModal.on_submit: {e}")
            await interaction.followup.send(f"❌ Error processing player prop bet: {str(e)}", ephemeral=True)

class StraightBetDetailsModal(Modal):
    def __init__(self, line_type: str, selected_league_key: str, bet_details_from_view: Dict[str, Any], is_manual: bool = False):
        league_conf = LEAGUE_CONFIG.get(selected_league_key, {})
        # Get league-specific title
        if line_type == "player_prop":
            title = league_conf.get('player_prop_modal_title', f"{league_conf.get('name', 'Game')} Player Prop")
        else:
            title = league_conf.get('game_line_modal_title', f"{league_conf.get('name', 'Game')} Bet Details")
        super().__init__(title=title)
        
        self.line_type = line_type
        self.selected_league_key = selected_league_key
        self.is_manual = is_manual
        self.view_ref = bet_details_from_view.get('view_ref')
        self.league_config = league_conf

        # For manual entries, always ask for team and opponent first
        if self.is_manual:
            # Get league-specific team labels and placeholders
            team_label = league_conf.get('participant_label', 'Team')
            team_placeholder = league_conf.get('team_placeholder', 'e.g., Team A')
            if selected_league_key == "NBA":
                team_placeholder = "e.g., Los Angeles Lakers"
            elif selected_league_key == "MLB":
                team_placeholder = "e.g., New York Yankees"
            elif selected_league_key == "NHL":
                team_placeholder = "e.g., Toronto Maple Leafs"
            elif selected_league_key == "NFL":
                team_placeholder = "e.g., Kansas City Chiefs"
            
            self.team_input = TextInput(
                label=team_label,
                required=True,
                max_length=100,
                placeholder=team_placeholder,
                default=bet_details_from_view.get('team', '')
            )
            self.add_item(self.team_input)

            opponent_label = league_conf.get('opponent_label', 'Opponent')
            opponent_placeholder = league_conf.get('opponent_placeholder', 'e.g., Opponent Team')
            if selected_league_key == "NBA":
                opponent_placeholder = "e.g., Boston Celtics"
            elif selected_league_key == "MLB":
                opponent_placeholder = "e.g., Boston Red Sox"
            elif selected_league_key == "NHL":
                opponent_placeholder = "e.g., Montreal Canadiens"
            elif selected_league_key == "NFL":
                opponent_placeholder = "e.g., San Francisco 49ers"
            
            self.opponent_input = TextInput(
                label=opponent_label,
                required=True,
                max_length=100,
                placeholder=opponent_placeholder,
                default=bet_details_from_view.get('opponent', '')
            )
            self.add_item(self.opponent_input)

        # For player props, add player name field with league-specific suggestions
        if self.line_type == "player_prop":
            player_label = league_conf.get('player_label', 'Player Name')
            player_placeholder = league_conf.get('player_placeholder', 'e.g., John Smith')
            
            # League-specific player suggestions
            if selected_league_key == "NBA":
                player_placeholder = "e.g., LeBron James, Stephen Curry"
            elif selected_league_key == "MLB":
                player_placeholder = "e.g., Aaron Judge, Shohei Ohtani"
            elif selected_league_key == "NHL":
                player_placeholder = "e.g., Connor McDavid, Nathan MacKinnon"
            elif selected_league_key == "NFL":
                player_placeholder = "e.g., Patrick Mahomes, Travis Kelce"
            
            self.player_name_input = TextInput(
                label=player_label,
                required=True,
                max_length=100,
                placeholder=player_placeholder,
                default=bet_details_from_view.get('player_name', '')
            )
            self.add_item(self.player_name_input)

        # Line/market field with league-specific suggestions
        if self.line_type == "player_prop":
            line_label = league_conf.get('prop_line_label', 'Player Prop / Line')
            line_placeholder = league_conf.get('prop_line_placeholder', 'e.g., Over 25.5 Points')
            
            # League-specific prop suggestions
            if selected_league_key == "NBA":
                line_placeholder = "e.g., Over 25.5 Points, Over 7.5 Assists"
            elif selected_league_key == "MLB":
                line_placeholder = "e.g., Over 1.5 Hits, Over 0.5 Home Runs"
            elif selected_league_key == "NHL":
                line_placeholder = "e.g., Over 2.5 Shots, Over 0.5 Goals"
            elif selected_league_key == "NFL":
                line_placeholder = "e.g., Over 250.5 Passing Yards, Over 0.5 Touchdowns"
        else:
            line_label = league_conf.get('line_label_game', 'Game Line / Match Outcome')
            line_placeholder = league_conf.get('line_placeholder_game', 'e.g., Moneyline, Spread -7.5')
            
            # League-specific game line suggestions
            if selected_league_key == "NBA":
                line_placeholder = "e.g., Moneyline, Spread -5.5, Over/Under 220.5"
            elif selected_league_key == "MLB":
                line_placeholder = "e.g., Moneyline, Run Line -1.5, Over/Under 8.5"
            elif selected_league_key == "NHL":
                line_placeholder = "e.g., Moneyline, Puck Line -1.5, Over/Under 5.5"
            elif selected_league_key == "NFL":
                line_placeholder = "e.g., Moneyline, Spread -3.5, Over/Under 45.5"
        
        self.line_input = TextInput(
            label=line_label,
            required=True,
            max_length=100,
            placeholder=line_placeholder,
            default=bet_details_from_view.get('line', '')
        )
        self.add_item(self.line_input)

        # Odds field with league-specific suggestions
        odds_placeholder = league_conf.get('odds_placeholder', 'e.g., -110 or +200')
        if selected_league_key == "NBA":
            odds_placeholder = "e.g., -110 (favorite) or +150 (underdog)"
        elif selected_league_key == "MLB":
            odds_placeholder = "e.g., -150 (favorite) or +130 (underdog)"
        elif selected_league_key == "NHL":
            odds_placeholder = "e.g., -120 (favorite) or +100 (underdog)"
        elif selected_league_key == "NFL":
            odds_placeholder = "e.g., -110 (favorite) or +110 (underdog)"
        
        self.odds_input = TextInput(
            label="Odds",
            required=True,
            max_length=10,
            placeholder=odds_placeholder,
            default=bet_details_from_view.get('odds_str', '')
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        player_name = None  # Ensure player_name is always defined
        try:
            # Handle player props
            if self.line_type == "player_prop":
                player_name = self.player_name_input.value.strip()
                line_value = self.line_input.value.strip()
                odds_str = self.odds_input.value.strip()
                
                # For manual entries, get team and opponent from inputs
                if self.is_manual:
                    team_input = self.team_input.value.strip()
                    opponent_input = self.opponent_input.value.strip()
                else:
                    team_input = self.view_ref.bet_details.get("team", self.view_ref.bet_details.get("home_team_name", ""))
                    opponent_input = self.view_ref.bet_details.get("opponent", self.view_ref.bet_details.get("away_team_name", ""))
            else:
                # Handle regular game lines
                if self.is_manual:
                    team_input = self.team_input.value.strip()
                    opponent_input = self.opponent_input.value.strip()
                else:
                    team_input = self.view_ref.bet_details.get("team", self.view_ref.bet_details.get("home_team_name", ""))
                    opponent_input = self.view_ref.bet_details.get("opponent", self.view_ref.bet_details.get("away_team_name", ""))
                line_value = self.line_input.value.strip()
                odds_str = self.odds_input.value.strip()

            if not line_value or not odds_str or (self.line_type == "player_prop" and not player_name):
                await interaction.followup.send("❌ All details are required in the modal.", ephemeral=True)
                return

            try:
                odds_val = float(odds_str.replace("+", ""))
            except ValueError:
                await interaction.followup.send(f"❌ Invalid odds format: '{odds_str}'. Use numbers e.g., -110 or 200.", ephemeral=True)
                return

            self.view_ref.bet_details.update({
                "line": line_value,
                "odds_str": odds_str,
                "odds": odds_val,
                "team": team_input,
                "opponent": opponent_input,
                "selected_league_key": self.selected_league_key,
                "player_name": player_name if self.line_type == "player_prop" else None
            })

            # Update view properties
            self.view_ref.home_team = team_input
            self.view_ref.away_team = opponent_input
            self.view_ref.league = self.league_config.get("name", self.selected_league_key)
            self.view_ref.line = line_value
            self.view_ref.odds = odds_val

            # Create or get bet_id
            if "bet_serial" not in self.view_ref.bet_details:
                # Use the API game ID stored from selection or manual entry
                api_game_id_for_bet = self.view_ref.bet_details.get("api_game_id")
                bet_serial = await self.view_ref.bot.bet_service.create_straight_bet(
                    guild_id=interaction.guild_id,
                    user_id=interaction.user.id,
                    api_game_id=api_game_id_for_bet,
                    bet_type=self.line_type,
                    team=team_input,
                    opponent=opponent_input,
                    line=line_value,
                    units=1.0,
                    odds=odds_val,
                    channel_id=None,
                    league=self.view_ref.league,
                )
                if not bet_serial: 
                    raise BetServiceError("Failed to create bet record.")
                self.view_ref.bet_details["bet_serial"] = bet_serial
                self.view_ref.bet_id = str(bet_serial)
            else:
                self.view_ref.bet_id = str(self.view_ref.bet_details['bet_serial'])

            # Generate bet slip
            current_units = float(self.view_ref.bet_details.get("units", 1.0))
            bet_slip_generator = await self.view_ref.get_bet_slip_generator()

            # Handle player props
            player_image = None
            display_vs = None
            if self.line_type == "player_prop" and player_name:
                # Try to get player image if available
                from utils.modals import get_player_image
                player_image_path = get_player_image(player_name, team_input, self.selected_league_key)
                if player_image_path:
                    player_image = Image.open(player_image_path).convert("RGBA")
                display_vs = f"{team_input} vs {opponent_input}"

            # Generate the bet slip
            bet_slip_image = await bet_slip_generator.generate_bet_slip(
                league=self.view_ref.league,
                home_team=team_input,
                away_team=opponent_input,
                odds=odds_val,
                units=current_units,
                bet_type=self.line_type,
                selected_team=team_input,
                line=line_value,
                bet_id=self.view_ref.bet_id,
                timestamp=datetime.now(timezone.utc),
                player_name=player_name,
                player_image=player_image,
                display_vs=display_vs
            )
            
            if bet_slip_image:
                self.view_ref.preview_image_bytes = io.BytesIO(bet_slip_image)
                self.view_ref.preview_image_bytes.seek(0)
            else:
                self.view_ref.preview_image_bytes = None

            self.view_ref.current_step = 4 
            await self.view_ref.go_next(interaction)

        except Exception as e:
            logger.exception(f"Error in StraightBetDetailsModal.on_submit: {e}")
            try:
                if not interaction.followup:
                    logger.error("Follow-up webhook is invalid or expired. Interaction details: %s", interaction)
                    # Fallback: Notify the user via a direct message or log the issue for manual resolution
                    try:
                        user = interaction.user
                        if user:
                            await user.send("❌ Unable to process your request due to a webhook issue. Please try again later.")
                    except discord.HTTPException as dm_err:
                        logger.error(f"Failed to send fallback DM to user: {dm_err}")
                    return

                await interaction.followup.send(f"❌ Error processing bet details: {str(e)}", ephemeral=True)
            except discord.HTTPException as http_err:
                logger.error(f"Failed to send follow-up message: {http_err}")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        logger.error(f"Error in StraightBetDetailsModal: {error}", exc_info=True)
        response_method = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        try:
            if not interaction.followup:
                logger.error("Follow-up webhook is invalid or expired.")
                return
            await response_method('❌ Modal error. Please try again.', ephemeral=True)
        except discord.HTTPException as http_err:
            logger.error(f"Failed to send error message: {http_err}")
        if hasattr(self, "view_ref") and self.view_ref: self.view_ref.stop()


# Add other modal classes here (ParlayLegDetailsModal, ParlayTotalOddsModal, etc.)
# For example:
# class ParlayLegDetailsModal(Modal): ...
# class ParlayTotalOddsModal(Modal): ...
# class CapperProfileModal(Modal): ...
# class CapperImageURLModal(Modal): ...
# class SubscriptionInfoModal(Modal): ...

def get_player_image(player_name: str, team: str, league_key: str) -> Optional[str]:
    """Get player image path using fuzzy matching."""
    try:
        # Get sport_id from mapping
        sport_id = PLAYER_PROP_SPORT_ID_MAP.get(league_key)
        if not sport_id:
            logger.warning(f"[Player Image] No sport_id mapping found for league: {league_key}")
            return None
            
        # Normalize team name for directory
        team_dir_name = team.lower().replace(' ', '_')
        team_dir = os.path.join(BASE_DIR, "static", "logos", "players", sport_id, team_dir_name)
        
        # logger.info(f"[Player Image] sport_id: '{sport_id}' (league_key: '{league_key}')")
        logger.info(f"[Player Image] Searching in team_dir: {team_dir}")
        
        if not os.path.exists(team_dir):
            logger.warning(f"[Player Image] Team directory not found: {team_dir}")
            return None
            
        # Get all image files in team directory
        image_files = [f for f in os.listdir(team_dir) if f.endswith('.png')]
        if not image_files:
            logger.warning(f"[Player Image] No player images found in: {team_dir}")
            return None
            
        # Get full paths
        candidates = [os.path.splitext(os.path.basename(f))[0] for f in image_files]
        logger.info(f"[Player Image] Found image files: {[os.path.join(team_dir, f) for f in candidates]}")
        
        # Normalize search name
        search_name = player_name.lower().replace(' ', '_')
        logger.info(f"[Player Image] Search names: {[search_name]}")
        
        # Get best match
        best_match = process.extractOne(search_name, candidates, scorer=fuzz.ratio)
        if best_match:
            if len(best_match) == 3:
                best_name, score, _ = best_match  # Unpack all three values, ignore index
            else:
                best_name, score = best_match  # Handle cases with only two values
            logger.info(f"[Player Image] Fuzzy match: '{search_name}' vs candidates -> '{best_name}' (score {score})")
            
            # Use best match if it's the only strong candidate or above threshold
            if score >= 60 or len(candidates) == 1:
                image_path = os.path.join(team_dir, best_name + '.png')
                logger.info(f"[Player Image] Using best match: {best_name} (score {score})")
                return image_path
            else:
                logger.warning(f"[Player Image] No match above threshold. Best: {best_name} (score {score})")
                return None
        else:
            logger.warning(f"[Player Image] No match found for '{search_name}'")
            return None
            
    except Exception as e:
        logger.error(f"[Player Image] Error getting player image: {str(e)}")
        return None

# --- League-specific Player Prop Modals ---

class BasePlayerPropModal(Modal):
    def __init__(self, league_key: str, bet_details_from_view: Dict[str, Any]):
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        super().__init__(title=league_conf.get("player_prop_modal_title", "Player Prop Bet Details"))
        self.league_key = league_key
        self.league_conf = league_conf
        self.view_ref = bet_details_from_view.get('view_ref')

        # Player Name
        self.player_name_input = TextInput(
            label=league_conf.get("player_prop_label", "Player Name"),
            required=True,
            max_length=100,
            placeholder=league_conf.get("player_prop_placeholder", "e.g., John Smith"),
            default=bet_details_from_view.get('player_name', '')
        )
        self.add_item(self.player_name_input)

        # Prop Details
        self.prop_details_input = TextInput(
            label=league_conf.get("prop_details_label", "Prop Details"),
            required=True,
            max_length=100,
            placeholder=league_conf.get("prop_details_placeholder", "e.g., Over 20.5 Points"),
            default=bet_details_from_view.get('line', '')
        )
        self.add_item(self.prop_details_input)

        # Odds
        self.odds_input = TextInput(
            label=league_conf.get("odds_label", "Odds"),
            required=True,
            max_length=10,
            placeholder=league_conf.get("odds_placeholder", "e.g., -110 or +200"),
            default=bet_details_from_view.get('odds_str', '')
        )
        self.add_item(self.odds_input)

class NBAPlayerPropModal(BasePlayerPropModal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        super().__init__("NBA", bet_details_from_view)

class MLBPlayerPropModal(BasePlayerPropModal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        super().__init__("MLB", bet_details_from_view)

class NHLPlayerPropModal(BasePlayerPropModal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        super().__init__("NHL", bet_details_from_view)

# Example LEAGUE_CONFIG additions (ensure these exist in your config/leagues.py):
# LEAGUE_CONFIG = {
#     "NBA": {
#         "player_prop_modal_title": "NBA Player Prop Bet",
#         "player_prop_label": "NBA Player Name",
#         "player_prop_placeholder": "e.g., LeBron James",
#         "prop_details_label": "Stat Line (Points, Rebounds, etc.)",
#         "prop_details_placeholder": "e.g., Over 25.5 Points",
#         "odds_label": "Odds",
#         "odds_placeholder": "e.g., -110 or +200",
#     },
#     "MLB": {
#         "player_prop_modal_title": "MLB Player Prop Bet",
#         "player_prop_label": "MLB Batter Name",
#         "player_prop_placeholder": "e.g., Aaron Judge",
#         "prop_details_label": "Stat Line (Hits, Home Runs, etc.)",
#         "prop_details_placeholder": "e.g., Over 1.5 Hits",
#         "odds_label": "Odds",
#         "odds_placeholder": "e.g., +150",
#     },
#     "NHL": {
#         "player_prop_modal_title": "NHL Player Prop Bet",
#         "player_prop_label": "NHL Player Name",
#         "player_prop_placeholder": "e.g., Connor McDavid",
#         "prop_details_label": "Stat Line (Goals, Assists, etc.)",
#         "prop_details_placeholder": "e.g., Over 2.5 Shots on Goal",
#         "odds_label": "Odds",
#         "odds_placeholder": "e.g., +200",
#     },
# }

# --- Parlay Modal (Stub for future expansion) ---
class ParlayBetDetailsModal(Modal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        super().__init__(title="Parlay Bet Details (Coming Soon)")
        # Add fields as needed for parlay legs, odds, etc.
        pass
