# REV 1.0.0 - Enhanced betting modals with improved validation and error handling
# bot/utils/modals.py
import io
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import discord
from discord.ui import Modal, TextInput

from bot.config.asset_paths import BASE_DIR

# Import your project's configurations and utilities
# Adjust these paths if your config/utils structure is different
# relative to the 'bot' root when this module is imported.
from bot.config.leagues import LEAGUE_CONFIG
# Example, if used directly in modal
from bot.utils.errors import BetServiceError

# Import the correct version of the image generator

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
    from commands.parlay_betting import ParlayBetWorkflowView  # Example

    # Add other view types if modals reference them specifically
    # from commands.setid import ImageUploadView # Example for CapperImageURLModal's parent

logger = logging.getLogger(__name__)


class PlayerPropModal(Modal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        league_key = bet_details_from_view.get(
            "selected_league_key", "DEFAULT")
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        super().__init__(
            title=f"{league_conf.get('player_label', 'Player')} Prop Bet Details"
        )

        self.league_key = league_key
        self.league_conf = league_conf
        self.single_participant = league_conf.get("single_participant", False)

        self.player_input = TextInput(
            label=league_conf.get("player_label", "Player"),
            required=True,
            max_length=100,
            placeholder=league_conf.get(
                "player_placeholder", "e.g., John Smith"),
            default=bet_details_from_view.get("player_name", ""),
        )
        self.add_item(self.player_input)

        if not self.single_participant:
            self.opponent_input = TextInput(
                label=league_conf.get("opponent_label", "Opponent"),
                required=True,
                max_length=100,
                placeholder=league_conf.get(
                    "opponent_placeholder", "e.g., Opponent Name"
                ),
                default=bet_details_from_view.get("opponent", ""),
            )
            self.add_item(self.opponent_input)
        else:
            self.opponent_input = None

        self.player_prop_input = TextInput(
            label=league_conf.get("prop_line_label", "Player Prop / Line"),
            required=True,
            max_length=100,
            placeholder=league_conf.get(
                "prop_line_placeholder", "e.g., Over 25.5 Points"
            ),
            default=bet_details_from_view.get("line", ""),
        )
        self.add_item(self.player_prop_input)

        self.odds_input = TextInput(
            label="Odds",
            required=True,
            max_length=10,
            placeholder=league_conf.get(
                "odds_placeholder", "e.g., -110 or +200"),
            default=bet_details_from_view.get("odds_str", ""),
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Set skip increment flag so go_next does not double-increment
        if hasattr(self, "view_ref") and self.view_ref:
            self.view_ref._skip_increment = True
        try:
            player = self.player_input.value.strip()
            player_prop_line = self.player_prop_input.value.strip()
            odds_str = self.odds_input.value.strip()
            units = 1.0  # Default, or fetch from view_ref if you support custom units
            bet_id = (
                getattr(self.view_ref, "bet_id", "N/A")
                if hasattr(self, "view_ref")
                else "N/A"
            )
            league = (
                getattr(self.view_ref, "league", "N/A")
                if hasattr(self, "view_ref")
                else "N/A"
            )
            team = (
                self.league_conf.get("team_name", "")
                or getattr(self.view_ref, "team", "")
                or ""
            )
            if not team:
                team = self.league_key  # fallback to league key if no team
            if not self.single_participant and self.opponent_input:
                opponent = self.opponent_input.value.strip()
            else:
                opponent = None

            # Save to bet_details
            if hasattr(self, "view_ref") and hasattr(self.view_ref, "bet_details"):
                self.view_ref.bet_details.update(
                    {
                        "team": team,
                        "opponent": opponent,
                        "line": player_prop_line,
                        "odds_str": odds_str,
                        "odds": (
                            float(odds_str.replace("+", ""))
                            if odds_str.replace("+", "").replace(".", "", 1).isdigit()
                            else odds_str
                        ),
                        "player_name": player,
                        "line_type": "player_prop",
                    }
                )

            # Get player image
            player_image_path, display_name = get_player_image(
                player, team, self.league_key
            )
            player_image = None
            if player_image_path:
                from PIL import Image

                player_image = Image.open(player_image_path).convert("RGBA")

            # Generate bet slip
            bet_slip_generator = (
                await self.view_ref.get_bet_slip_generator()
                if hasattr(self, "view_ref")
                else None
            )
            if not self.single_participant and opponent:
                display_vs = f"{team} vs {opponent}"
            else:
                display_vs = player
            bet_slip_image = None
            if bet_slip_generator:
                bet_slip_image = await bet_slip_generator.generate_bet_slip(
                    home_team=team,
                    away_team=opponent or "",
                    league=league,
                    line=player_prop_line,
                    odds=(
                        float(odds_str.replace("+", ""))
                        if odds_str.replace("+", "").replace(".", "", 1).isdigit()
                        else odds_str
                    ),
                    units=units,
                    bet_id=bet_id,
                    timestamp=datetime.now(timezone.utc),
                    bet_type="player_prop",
                    player_name=player,
                    player_image=player_image,
                    display_vs=display_vs,
                )
            if bet_slip_image and hasattr(self.view_ref, "preview_image_bytes"):
                import io

                self.view_ref.preview_image_bytes = io.BytesIO()
                bet_slip_image.save(
                    self.view_ref.preview_image_bytes, format="PNG")
                self.view_ref.preview_image_bytes.seek(0)
            elif hasattr(self.view_ref, "preview_image_bytes"):
                self.view_ref.preview_image_bytes = None

            if hasattr(self.view_ref, "current_step"):
                self.view_ref.current_step = 4
            if hasattr(self.view_ref, "go_next"):
                await self.view_ref.go_next(interaction)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception(f"Error in PlayerPropModal.on_submit: {e}")
            await interaction.followup.send(
                f"❌ Error processing player prop bet: {str(e)}", ephemeral=True
            )


class StraightBetDetailsModal(Modal):
    def __init__(
        self,
        line_type: str,
        selected_league_key: str,
        bet_details_from_view: Dict[str, Any],
        is_manual: bool = False,
    ):
        league_conf = LEAGUE_CONFIG.get(selected_league_key, {})

        # Get modal title
        title = self._get_modal_title(line_type, league_conf)
        super().__init__(title=title)

        self.line_type = line_type
        self.selected_league_key = selected_league_key
        self.is_manual = is_manual
        self.view_ref = bet_details_from_view.get("view_ref")
        self.league_config = league_conf

        # Create fields based on type and manual entry
        if self.is_manual:
            self._create_manual_entry_fields(
                selected_league_key, bet_details_from_view)
        else:
            self._create_game_line_fields(bet_details_from_view)

    def _get_modal_title(self, line_type: str, league_conf: Dict) -> str:
        """Get the modal title based on line type and league configuration."""
        if line_type == "player_prop":
            return league_conf.get(
                "player_prop_modal_title",
                f"{league_conf.get('name', 'Game')} Player Prop",
            )
        else:
            return league_conf.get(
                "game_line_modal_title",
                f"{league_conf.get('name', 'Game')} Bet Details",
            )

    def _get_player_placeholder(self, selected_league_key: str) -> str:
        """Get player placeholder text based on league."""
        league_placeholders = {
            "PDC": "e.g., Michael van Gerwen, Peter Wright",
            "BDO": "e.g., Michael van Gerwen, Peter Wright",
            "WDF": "e.g., Michael van Gerwen, Peter Wright",
            "PremierLeagueDarts": "e.g., Michael van Gerwen, Peter Wright",
            "WorldMatchplay": "e.g., Michael van Gerwen, Peter Wright",
            "WorldGrandPrix": "e.g., Michael van Gerwen, Peter Wright",
            "UKOpen": "e.g., Michael van Gerwen, Peter Wright",
            "GrandSlam": "e.g., Michael van Gerwen, Peter Wright",
            "PlayersChampionship": "e.g., Michael van Gerwen, Peter Wright",
            "EuropeanChampionship": "e.g., Michael van Gerwen, Peter Wright",
            "Masters": "e.g., Michael van Gerwen, Peter Wright",
            "ATP": "e.g., Novak Djokovic, Iga Swiatek",
            "WTA": "e.g., Novak Djokovic, Iga Swiatek",
            "Tennis": "e.g., Novak Djokovic, Iga Swiatek",
            "PGA": "e.g., Scottie Scheffler, Nelly Korda",
            "LPGA": "e.g., Scottie Scheffler, Nelly Korda",
            "EuropeanTour": "e.g., Scottie Scheffler, Nelly Korda",
            "LIVGolf": "e.g., Scottie Scheffler, Nelly Korda",
            "MMA": "e.g., Jon Jones, Patricio Pitbull",
            "Bellator": "e.g., Jon Jones, Patricio Pitbull",
            "Formula-1": "e.g., Max Verstappen, Lewis Hamilton",
        }
        return league_placeholders.get(selected_league_key, "e.g., Player Name")

    def _get_opponent_placeholder(self, selected_league_key: str) -> str:
        """Get opponent placeholder text based on league."""
        league_placeholders = {
            "PDC": "e.g., Peter Wright, Gerwyn Price",
            "BDO": "e.g., Peter Wright, Gerwyn Price",
            "WDF": "e.g., Peter Wright, Gerwyn Price",
            "PremierLeagueDarts": "e.g., Peter Wright, Gerwyn Price",
            "WorldMatchplay": "e.g., Peter Wright, Gerwyn Price",
            "WorldGrandPrix": "e.g., Peter Wright, Gerwyn Price",
            "UKOpen": "e.g., Peter Wright, Gerwyn Price",
            "GrandSlam": "e.g., Peter Wright, Gerwyn Price",
            "PlayersChampionship": "e.g., Peter Wright, Gerwyn Price",
            "EuropeanChampionship": "e.g., Peter Wright, Gerwyn Price",
            "Masters": "e.g., Peter Wright, Gerwyn Price",
            "ATP": "e.g., Rafael Nadal, Aryna Sabalenka",
            "WTA": "e.g., Rafael Nadal, Aryna Sabalenka",
            "Tennis": "e.g., Rafael Nadal, Aryna Sabalenka",
            "PGA": "e.g., Rory McIlroy, Lydia Ko",
            "LPGA": "e.g., Rory McIlroy, Lydia Ko",
            "EuropeanTour": "e.g., Rory McIlroy, Lydia Ko",
            "LIVGolf": "e.g., Rory McIlroy, Lydia Ko",
            "MMA": "e.g., Jon Jones, Patricio Pitbull",
            "Bellator": "e.g., Jon Jones, Patricio Pitbull",
            "Formula-1": "e.g., Max Verstappen, Lewis Hamilton",
        }
        return league_placeholders.get(selected_league_key, "e.g., Opponent Name")

    def _create_individual_sport_fields(self, selected_league_key: str, bet_details_from_view: Dict[str, Any]):
        """Create fields for individual sports (darts, tennis, golf, MMA, etc.)."""
        league_conf = self.league_config
        player_label = league_conf.get("participant_label", "Player")
        player_placeholder = self._get_player_placeholder(selected_league_key)

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
        opponent_placeholder = self._get_opponent_placeholder(
            selected_league_key)

        self.opponent_input = TextInput(
            label=opponent_label,
            required=True,
            max_length=100,
            placeholder=opponent_placeholder,
            default=bet_details_from_view.get("opponent", ""),
        )
        self.add_item(self.opponent_input)

    def _create_team_sport_fields(self, bet_details_from_view: Dict[str, Any]):
        """Create fields for team sports."""
        # Team name field
        self.team_input = TextInput(
            label="Team Name",
            required=True,
            max_length=100,
            placeholder="e.g., Los Angeles Lakers",
            default=bet_details_from_view.get("team", ""),
        )
        self.add_item(self.team_input)

        # Opponent field
        self.opponent_input = TextInput(
            label="Opponent",
            required=True,
            max_length=100,
            placeholder="e.g., Golden State Warriors",
            default=bet_details_from_view.get("opponent", ""),
        )
        self.add_item(self.opponent_input)

    def _create_common_fields(self, bet_details_from_view: Dict[str, Any]):
        """Create common fields for all bet types."""
        # Line field
        self.line_input = TextInput(
            label="Line",
            required=True,
            max_length=50,
            placeholder="e.g., -7.5, +110, Over 220.5",
            default=bet_details_from_view.get("line", ""),
        )
        self.add_item(self.line_input)

        # Odds field
        self.odds_input = TextInput(
            label="Odds",
            required=True,
            max_length=20,
            placeholder="e.g., -110, +150",
            default=str(bet_details_from_view.get("odds", "")),
        )
        self.add_item(self.odds_input)

    def _create_manual_entry_fields(self, selected_league_key: str, bet_details_from_view: Dict[str, Any]):
        """Create fields for manual entry based on sport type."""
        sport_type = self.league_config.get("sport_type", "Team Sport")
        is_individual_sport = sport_type == "Individual Player"

        if is_individual_sport:
            self._create_individual_sport_fields(
                selected_league_key, bet_details_from_view)
        else:
            self._create_team_sport_fields(bet_details_from_view)

        self._create_common_fields(bet_details_from_view)

    def _create_game_line_fields(self, bet_details_from_view: Dict[str, Any]):
        """Create fields for game line bets."""
        # Line field
        self.line_input = TextInput(
            label="Line",
            required=True,
            max_length=50,
            placeholder="e.g., -7.5, +110, Over 220.5",
            default=bet_details_from_view.get("line", ""),
        )
        self.add_item(self.line_input)

        # Odds field
        self.odds_input = TextInput(
            label="Odds",
            required=True,
            max_length=20,
            placeholder="e.g., -110, +150",
            default=str(bet_details_from_view.get("odds", "")),
        )
        self.add_item(self.odds_input)

    def _collect_input_values(self) -> Dict[str, str]:
        """Collect and return input values from the modal."""
        inputs = {
            "line": self.line_input.value.strip(),
            "odds_str": self.odds_input.value.strip(),
        }

        # Collect optional fields if they exist
        if hasattr(self, "team_input"):
            inputs["team"] = self.team_input.value.strip()
        if hasattr(self, "opponent_input"):
            inputs["opponent"] = self.opponent_input.value.strip()
        if hasattr(self, "player_input"):
            inputs["player_name"] = self.player_input.value.strip()
        if hasattr(self, "player_name_input"):
            inputs["player_name"] = self.player_name_input.value.strip()

        return inputs

    def _update_bet_details(self, inputs: Dict[str, str]):
        """Update the view reference bet details with collected inputs."""
        if not self.view_ref or not hasattr(self.view_ref, "bet_details"):
            return

        self.view_ref.bet_details["line"] = inputs["line"]
        self.view_ref.bet_details["odds_str"] = inputs["odds_str"]

        try:
            self.view_ref.bet_details["odds"] = float(
                inputs["odds_str"].replace("+", ""))
        except Exception:
            self.view_ref.bet_details["odds"] = inputs["odds_str"]

        # Default units for preview
        self.view_ref.bet_details["units"] = 1.0
        self.view_ref.bet_details["units_str"] = "1.0"

        # Update other fields
        if "team" in inputs:
            self.view_ref.bet_details["team"] = inputs["team"]
        if "opponent" in inputs:
            self.view_ref.bet_details["opponent"] = inputs["opponent"]
        if "player_name" in inputs:
            self.view_ref.bet_details["player_name"] = inputs["player_name"]
            # For individual sports, set team to player name for consistency
            self.view_ref.bet_details["team"] = inputs["player_name"]

    async def _generate_preview_image(self) -> bool:
        """Generate preview image for the bet. Returns True if successful."""
        try:
            gen = await self.view_ref.get_bet_slip_generator()
            # Use game line slip for preview
            image = await gen.generate_game_line_slip(
                league=self.view_ref.bet_details.get("league", ""),
                home_team=self.view_ref.bet_details.get("home_team_name", ""),
                away_team=self.view_ref.bet_details.get("away_team_name", ""),
                odds=self.view_ref.bet_details.get("odds", 0.0),
                units=1.0,
                selected_team=self.view_ref.bet_details.get("team", ""),
                line=self.view_ref.bet_details.get("line", ""),
                bet_id=str(self.view_ref.bet_details.get("bet_serial", "")),
                timestamp=datetime.now(timezone.utc),
            )
            if image:
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)
                self.view_ref.preview_image_bytes = buf
                return True
            else:
                self.view_ref.preview_image_bytes = None
                return False
        except Exception as e:
            logger.error(f"Error generating preview image: {e}")
            self.view_ref.preview_image_bytes = None
            return False

    async def _advance_workflow(self, interaction: discord.Interaction):
        """Advance the workflow to the next step."""
        if hasattr(self.view_ref, "current_step"):
            # Set to step 4 (units selection with preview)
            self.view_ref.current_step = 4
            logger.info(f"[MODAL SUBMIT] Calling go_next for step 4.")
            await self.view_ref.go_next(interaction)
        else:
            logger.error("View reference missing current_step attribute")
            await interaction.response.send_message(
                "Error: Could not advance workflow", ephemeral=True
            )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle submission of game line/prop details to generate preview and advance to units selection."""
        # Collect inputs
        inputs = self._collect_input_values()

        # Update bet details
        self._update_bet_details(inputs)

        # Generate preview image
        await self._generate_preview_image()

        # Advance workflow to units selection
        await self._advance_workflow(interaction)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        logger.error(
            f"Error in StraightBetDetailsModal: {error}", exc_info=True)
        try:
            # Always try to edit the original ephemeral message instead of sending new ones
            await interaction.response.defer()
            await self.view_ref.edit_message(
                content="❌ Error processing bet details. Please try again or cancel.",
                view=None,
            )
            self.view_ref.stop()
        except Exception as edit_error:
            logger.error(
                f"Failed to edit message after modal error: {edit_error}")
            # Only as last resort, try to send a followup
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(
                        "❌ Modal error. Please restart the workflow.", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Modal error. Please restart the workflow.", ephemeral=True
                    )
            except discord.HTTPException:
                pass


# Add other modal classes here (ParlayLegDetailsModal, ParlayTotalOddsModal, etc.)
# For example:
# class ParlayLegDetailsModal(Modal): ...
# class ParlayTotalOddsModal(Modal): ...
# class CapperProfileModal(Modal): ...
# class CapperImageURLModal(Modal): ...
# class SubscriptionInfoModal(Modal): ...


def get_player_image(
    player_name: str, team: str, league_key: str
) -> tuple[Optional[str], str]:
    """Get player image path using fuzzy matching, and return the normalized display name."""
    import difflib
    import os

    try:
        # Get sport_id from mapping
        sport_id = PLAYER_PROP_SPORT_ID_MAP.get(league_key)
        if not sport_id:
            logger.warning(
                f"[Player Image] No sport_id mapping found for league: {league_key}"
            )
            return None, player_name
        # Normalize team name for directory
        team_dir_name = team.lower().replace(" ", "_")
        team_dir = os.path.join(
            BASE_DIR, "static", "logos", "players", sport_id, team_dir_name
        )
        if not os.path.exists(team_dir):
            logger.warning(
                f"[Player Image] Team directory not found: {team_dir}")
            return None, player_name
        # Get all image files in team directory
        image_files = [f for f in os.listdir(team_dir) if f.endswith(".webp")]
        if not image_files:
            logger.warning(
                f"[Player Image] No player images found in: {team_dir}")
            return None, player_name
        # Get full paths
        candidates = [os.path.splitext(os.path.basename(f))[
            0] for f in image_files]
        # Normalize search name
        search_name = player_name.lower().replace(" ", "_")
        # Fuzzy match
        matches = difflib.get_close_matches(
            search_name, candidates, n=1, cutoff=0.6)
        if matches:
            best_name = matches[0]
            image_path = os.path.join(team_dir, best_name + ".webp")
            display_name = best_name.replace("_", " ").title()
            logger.info(f"[Player Image] Using fuzzy match: {best_name}")
            return image_path, display_name
        else:
            logger.warning(
                f"[Player Image] No fuzzy match found for '{search_name}'")
            return None, player_name
    except Exception as e:
        logger.error(f"[Player Image] Error getting player image: {str(e)}")
        return None, player_name


# --- League-specific Player Prop Modals ---


class BasePlayerPropModal(Modal):
    def __init__(self, league_key: str, bet_details_from_view: Dict[str, Any]):
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        super().__init__(
            title=league_conf.get("player_prop_modal_title",
                                  "Player Prop Bet Details")
        )
        self.league_key = league_key
        self.league_conf = league_conf
        self.view_ref = bet_details_from_view.get("view_ref")

        # Player Name
        self.player_name_input = TextInput(
            label=league_conf.get("player_prop_label", "Player Name"),
            required=True,
            max_length=100,
            placeholder=league_conf.get(
                "player_prop_placeholder", "e.g., John Smith"),
            default=bet_details_from_view.get("player_name", ""),
        )
        self.add_item(self.player_name_input)

        # Prop Details
        self.prop_details_input = TextInput(
            label=league_conf.get("prop_details_label", "Prop Details"),
            required=True,
            max_length=100,
            placeholder=league_conf.get(
                "prop_details_placeholder", "e.g., Over 20.5 Points"
            ),
            default=bet_details_from_view.get("line", ""),
        )
        self.add_item(self.prop_details_input)

        # Odds
        self.odds_input = TextInput(
            label=league_conf.get("odds_label", "Odds"),
            required=True,
            max_length=10,
            placeholder=league_conf.get(
                "odds_placeholder", "e.g., -110 or +200"),
            default=bet_details_from_view.get("odds_str", ""),
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


# --- Parlay Modal ---
class ParlayBetDetailsModal(Modal):
    def __init__(self, bet_details_from_view: Dict[str, Any]):
        super().__init__(title="Parlay Bet Details")
        self.view_ref = bet_details_from_view.get("view_ref")
        self.bet_details = bet_details_from_view

        # Total Odds (calculated from legs, but user can override)
        self.total_odds_input = TextInput(
            label="Total Odds",
            required=True,
            max_length=10,
            placeholder="e.g., +500 or -150",
            default=bet_details_from_view.get("total_odds_str", ""),
        )
        self.add_item(self.total_odds_input)

        # Units
        self.units_input = TextInput(
            label="Units",
            required=True,
            max_length=10,
            placeholder="e.g., 1.0 or 2.5",
            default=bet_details_from_view.get("units_str", "1.0"),
        )
        self.add_item(self.units_input)

    def _validate_total_odds(self, total_odds_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
        """Validate total odds input. Returns (is_valid, odds_value, error_message)."""
        try:
            total_odds = float(total_odds_str)
            return True, total_odds, None
        except ValueError:
            return False, None, "❌ Invalid total odds format. Please use numbers like +500 or -150."

    def _validate_units(self, units_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
        """Validate units input. Returns (is_valid, units_value, error_message)."""
        try:
            units = float(units_str)
            if units <= 0:
                return False, None, "❌ Units must be greater than 0."
            return True, units, None
        except ValueError:
            return False, None, "❌ Invalid units format. Please use numbers like 1.0 or 2.5."

    def _update_bet_details(self, total_odds: float, total_odds_str: str, units: float, units_str: str):
        """Update bet details with validated values."""
        self.view_ref.bet_details["total_odds"] = total_odds
        self.view_ref.bet_details["total_odds_str"] = total_odds_str
        self.view_ref.bet_details["units"] = units
        self.view_ref.bet_details["units_str"] = units_str

    async def _generate_parlay_preview_image(self, total_odds: float, units: float) -> bool:
        """Generate parlay preview image. Returns True if successful."""
        try:
            from bot.utils.parlay_bet_image_generator import ParlayBetImageGenerator

            generator = ParlayBetImageGenerator(
                guild_id=self.view_ref.original_interaction.guild_id
            )

            # Get legs from bet details
            legs = self.view_ref.bet_details.get("legs", [])

            # Generate the parlay image
            image_bytes = generator.generate_image(
                legs=legs,
                output_path=None,
                total_odds=total_odds,
                units=units,
                bet_id=str(self.view_ref.bet_details.get("bet_serial", "")),
                timestamp=datetime.now(timezone.utc),
            )

            if image_bytes:
                self.view_ref.preview_image_bytes = io.BytesIO(image_bytes)
                self.view_ref.preview_image_bytes.seek(0)
                return True
            else:
                self.view_ref.preview_image_bytes = None
                return False
        except Exception as e:
            logger.error(f"Error generating parlay preview image: {e}")
            self.view_ref.preview_image_bytes = None
            return False

    async def _advance_parlay_workflow(self, interaction: discord.Interaction):
        """Advance the parlay workflow to the next step."""
        if hasattr(self.view_ref, "current_step"):
            # Set to step 4 (units selection with preview)
            self.view_ref.current_step = 4
            logger.info(f"[PARLAY MODAL SUBMIT] Calling go_next for step 4.")
            await self.view_ref.go_next(interaction)
        else:
            logger.error("View reference missing current_step attribute")
            await interaction.response.send_message(
                "Error: Could not advance workflow", ephemeral=True
            )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle submission of parlay bet details."""
        try:
            # Validate total odds
            total_odds_str = self.total_odds_input.value.strip()
            is_valid_odds, total_odds, odds_error = self._validate_total_odds(
                total_odds_str)
            if not is_valid_odds:
                await interaction.response.send_message(odds_error, ephemeral=True)
                return

            # Validate units
            units_str = self.units_input.value.strip()
            is_valid_units, units, units_error = self._validate_units(
                units_str)
            if not is_valid_units:
                await interaction.response.send_message(units_error, ephemeral=True)
                return

            # Update bet details
            self._update_bet_details(
                total_odds, total_odds_str, units, units_str)

            # Generate preview image
            await self._generate_parlay_preview_image(total_odds, units)

            # Advance workflow
            await self._advance_parlay_workflow(interaction)

        except Exception as e:
            logger.error(
                f"Error in ParlayBetDetailsModal on_submit: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Error processing parlay bet details. Please try again.",
                ephemeral=True,
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        logger.error(f"Error in ParlayBetDetailsModal: {error}", exc_info=True)
        try:
            await interaction.response.send_message(
                "❌ Error processing parlay details. Please try again.", ephemeral=True
            )
        except discord.HTTPException:
            pass
