# REV 1.0.0 - Enhanced betting modals with improved validation and error handling
# bot/utils/modals.py
import io
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

import discord
from config.asset_paths import BASE_DIR

# Import your project's configurations and utilities
# Adjust these paths if your config/utils structure is different
# relative to the 'bot' root when this module is imported.
from config.leagues import LEAGUE_CONFIG
from discord.ui import Modal, TextInput

from utils.errors import BetServiceError  # Example, if used directly in modal

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
        league_key = bet_details_from_view.get("selected_league_key", "DEFAULT")
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
            placeholder=league_conf.get("player_placeholder", "e.g., John Smith"),
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
            placeholder=league_conf.get("odds_placeholder", "e.g., -110 or +200"),
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
                bet_slip_image.save(self.view_ref.preview_image_bytes, format="PNG")
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
        # Get league-specific title
        if line_type == "player_prop":
            title = league_conf.get(
                "player_prop_modal_title",
                f"{league_conf.get('name', 'Game')} Player Prop",
            )
        else:
            title = league_conf.get(
                "game_line_modal_title",
                f"{league_conf.get('name', 'Game')} Bet Details",
            )
        super().__init__(title=title)

        self.line_type = line_type
        self.selected_league_key = selected_league_key
        self.is_manual = is_manual
        self.view_ref = bet_details_from_view.get("view_ref")
        self.league_config = league_conf

        # Check if this is an individual sport
        sport_type = league_conf.get("sport_type", "Team Sport")
        is_individual_sport = sport_type == "Individual Player"

        # For manual entries, determine fields based on sport type
        if self.is_manual:
            if is_individual_sport:
                # For individual sports (darts, tennis, golf, MMA, etc.), show player and opponent
                player_label = league_conf.get("participant_label", "Player")
                player_placeholder = league_conf.get(
                    "team_placeholder", "e.g., Player Name"
                )

                # League-specific player suggestions
                if selected_league_key in [
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
                elif selected_league_key in ["ATP", "WTA", "Tennis"]:
                    player_placeholder = "e.g., Novak Djokovic, Iga Swiatek"
                elif selected_league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                    player_placeholder = "e.g., Scottie Scheffler, Nelly Korda"
                elif selected_league_key in ["MMA", "Bellator"]:
                    player_placeholder = "e.g., Jon Jones, Patricio Pitbull"
                elif selected_league_key == "Formula-1":
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
                if selected_league_key in [
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
                elif selected_league_key in ["ATP", "WTA", "Tennis"]:
                    opponent_placeholder = "e.g., Rafael Nadal, Aryna Sabalenka"
                elif selected_league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                    opponent_placeholder = "e.g., Rory McIlroy, Lydia Ko"
                elif selected_league_key in ["MMA", "Bellator"]:
                    opponent_placeholder = "e.g., Francis Ngannou, Cris Cyborg"
                elif selected_league_key == "Formula-1":
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
                    default=bet_details_from_view.get("team", ""),
                )
                self.add_item(self.team_input)

                opponent_label = league_conf.get("opponent_label", "Opponent")
                opponent_placeholder = league_conf.get(
                    "opponent_placeholder", "e.g., Opponent Team"
                )
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
                    default=bet_details_from_view.get("opponent", ""),
                )
                self.add_item(self.opponent_input)

        # For player props, add player name field with league-specific suggestions
        if self.line_type == "player_prop":
            player_label = league_conf.get("player_label", "Player Name")
            player_placeholder = league_conf.get(
                "player_placeholder", "e.g., John Smith"
            )

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
                default=bet_details_from_view.get("player_name", ""),
            )
            self.add_item(self.player_name_input)

        # Line/market field with league-specific suggestions
        if self.line_type == "player_prop":
            line_label = league_conf.get("prop_line_label", "Player Prop / Line")
            line_placeholder = league_conf.get(
                "prop_line_placeholder", "e.g., Over 25.5 Points"
            )

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
            line_label = league_conf.get("line_label_game", "Game Line / Match Outcome")
            line_placeholder = league_conf.get(
                "line_placeholder_game", "e.g., Moneyline, Spread -7.5"
            )

            # League-specific game line suggestions
            if selected_league_key == "NBA":
                line_placeholder = "e.g., Moneyline, Spread -5.5, Over/Under 220.5"
            elif selected_league_key == "MLB":
                line_placeholder = "e.g., Moneyline, Run Line -1.5, Over/Under 8.5"
            elif selected_league_key == "NHL":
                line_placeholder = "e.g., Moneyline, Puck Line -1.5, Over/Under 5.5"
            elif selected_league_key == "NFL":
                line_placeholder = "e.g., Moneyline, Spread -3.5, Over/Under 45.5"
            elif selected_league_key in [
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
            elif selected_league_key in ["ATP", "WTA", "Tennis"]:
                line_placeholder = (
                    "e.g., To Win Match, Set Handicap -1.5, Total Games Over/Under 22.5"
                )
            elif selected_league_key in ["PGA", "LPGA", "EuropeanTour", "LIVGolf"]:
                line_placeholder = (
                    "e.g., To Win Tournament, Top 5 Finish, Round Score Under 68.5"
                )
            elif selected_league_key in ["MMA", "Bellator"]:
                line_placeholder = (
                    "e.g., To Win Fight, Method of Victory (KO/Sub/Decision)"
                )
            elif selected_league_key == "Formula-1":
                line_placeholder = "e.g., To Win Race, Podium Finish, Fastest Lap"

        self.line_input = TextInput(
            label=line_label,
            required=True,
            max_length=100,
            placeholder=line_placeholder,
            default=bet_details_from_view.get("line", ""),
        )
        self.add_item(self.line_input)

        # Odds field with league-specific suggestions
        odds_placeholder = league_conf.get("odds_placeholder", "e.g., -110 or +200")
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
            default=bet_details_from_view.get("odds_str", ""),
        )
        self.add_item(self.odds_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle submission of game line/prop details to generate preview and advance to units selection."""
        # Collect inputs
        line = self.line_input.value.strip()
        odds_str = self.odds_input.value.strip()

        # Update view_ref bet_details
        if self.view_ref and hasattr(self.view_ref, "bet_details"):
            self.view_ref.bet_details["line"] = line
            self.view_ref.bet_details["odds_str"] = odds_str
            try:
                self.view_ref.bet_details["odds"] = float(odds_str.replace("+", ""))
            except Exception:
                self.view_ref.bet_details["odds"] = odds_str
            # Default units for preview
            self.view_ref.bet_details["units"] = 1.0
            self.view_ref.bet_details["units_str"] = "1.0"

            # Update other fields if they exist
            if hasattr(self, "team_input"):
                self.view_ref.bet_details["team"] = self.team_input.value.strip()
            if hasattr(self, "opponent_input"):
                self.view_ref.bet_details["opponent"] = (
                    self.opponent_input.value.strip()
                )
            if hasattr(self, "player_input"):
                self.view_ref.bet_details["player_name"] = (
                    self.player_input.value.strip()
                )
                # For individual sports, set team to player name for consistency
                self.view_ref.bet_details["team"] = self.player_input.value.strip()
            if hasattr(self, "player_name_input"):
                self.view_ref.bet_details["player_name"] = (
                    self.player_name_input.value.strip()
                )

        # Generate preview image
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
                line=line,
                bet_id=str(self.view_ref.bet_details.get("bet_serial", "")),
                timestamp=datetime.now(timezone.utc),
            )
            if image:
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)
                self.view_ref.preview_image_bytes = buf
            else:
                self.view_ref.preview_image_bytes = None
        except Exception as e:
            logger.error(f"Error generating preview image: {e}")
            self.view_ref.preview_image_bytes = None

        # Advance workflow to units selection
        if hasattr(self.view_ref, "current_step"):
            self.view_ref.current_step = (
                4  # Set to step 4 (units selection with preview)
            )
            logger.info(f"[MODAL SUBMIT] Calling go_next for step 4.")
            await self.view_ref.go_next(interaction)
        else:
            logger.error("View reference missing current_step attribute")
            await interaction.response.send_message(
                "Error: Could not advance workflow", ephemeral=True
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        logger.error(f"Error in StraightBetDetailsModal: {error}", exc_info=True)
        try:
            # Always try to edit the original ephemeral message instead of sending new ones
            await interaction.response.defer()
            await self.view_ref.edit_message(
                content="❌ Error processing bet details. Please try again or cancel.",
                view=None,
            )
            self.view_ref.stop()
        except Exception as edit_error:
            logger.error(f"Failed to edit message after modal error: {edit_error}")
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
            logger.warning(f"[Player Image] Team directory not found: {team_dir}")
            return None, player_name
        # Get all image files in team directory
        image_files = [f for f in os.listdir(team_dir) if f.endswith(".png")]
        if not image_files:
            logger.warning(f"[Player Image] No player images found in: {team_dir}")
            return None, player_name
        # Get full paths
        candidates = [os.path.splitext(os.path.basename(f))[0] for f in image_files]
        # Normalize search name
        search_name = player_name.lower().replace(" ", "_")
        # Fuzzy match
        matches = difflib.get_close_matches(search_name, candidates, n=1, cutoff=0.6)
        if matches:
            best_name = matches[0]
            image_path = os.path.join(team_dir, best_name + ".png")
            display_name = best_name.replace("_", " ").title()
            logger.info(f"[Player Image] Using fuzzy match: {best_name}")
            return image_path, display_name
        else:
            logger.warning(f"[Player Image] No fuzzy match found for '{search_name}'")
            return None, player_name
    except Exception as e:
        logger.error(f"[Player Image] Error getting player image: {str(e)}")
        return None, player_name


# --- League-specific Player Prop Modals ---


class BasePlayerPropModal(Modal):
    def __init__(self, league_key: str, bet_details_from_view: Dict[str, Any]):
        league_conf = LEAGUE_CONFIG.get(league_key, {})
        super().__init__(
            title=league_conf.get("player_prop_modal_title", "Player Prop Bet Details")
        )
        self.league_key = league_key
        self.league_conf = league_conf
        self.view_ref = bet_details_from_view.get("view_ref")

        # Player Name
        self.player_name_input = TextInput(
            label=league_conf.get("player_prop_label", "Player Name"),
            required=True,
            max_length=100,
            placeholder=league_conf.get("player_prop_placeholder", "e.g., John Smith"),
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
            placeholder=league_conf.get("odds_placeholder", "e.g., -110 or +200"),
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

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            # Validate and store total odds
            total_odds_str = self.total_odds_input.value.strip()
            try:
                total_odds = float(total_odds_str)
                self.view_ref.bet_details["total_odds"] = total_odds
                self.view_ref.bet_details["total_odds_str"] = total_odds_str
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid total odds format. Please use numbers like +500 or -150.",
                    ephemeral=True,
                )
                return

            # Validate and store units
            units_str = self.units_input.value.strip()
            try:
                units = float(units_str)
                if units <= 0:
                    await interaction.response.send_message(
                        "❌ Units must be greater than 0.", ephemeral=True
                    )
                    return
                self.view_ref.bet_details["units"] = units
                self.view_ref.bet_details["units_str"] = units_str
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid units format. Please use numbers like 1.0 or 2.5.",
                    ephemeral=True,
                )
                return

            # Generate preview image
            try:
                from utils.parlay_bet_image_generator import ParlayBetImageGenerator

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
                    bet_datetime=datetime.now(timezone.utc),
                    finalized=True,
                    units_display_mode=self.view_ref.bet_details.get(
                        "units_display_mode", "auto"
                    ),
                    display_as_risk=self.view_ref.bet_details.get("display_as_risk"),
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

        except Exception as e:
            logger.error(f"Error in ParlayBetDetailsModal: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Error processing parlay details. Please try again.", ephemeral=True
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
