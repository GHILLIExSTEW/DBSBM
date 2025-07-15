"""Centralized asset loading utilities with proper error handling."""

import difflib
import logging
import os
from typing import Optional, Tuple

from PIL import Image, ImageFont

logger = logging.getLogger(__name__)


class AssetLoader:
    """Centralized asset loading with proper error handling."""

    def __init__(self, base_dir: str = None):
        """Initialize the asset loader."""
        if base_dir is None:
            # Try to determine base directory automatically
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.dirname(current_dir)  # bot/
        else:
            self.base_dir = base_dir

        self.fonts_dir = os.path.join(self.base_dir, "assets", "fonts")
        self.static_dir = os.path.join(self.base_dir, "static")
        self.logos_dir = os.path.join(self.static_dir, "logos")

        # Cache for loaded assets
        self._font_cache = {}
        self._default_logo = None

    def load_font(
        self, font_name: str, size: int, fallback_to_default: bool = True
    ) -> Optional[ImageFont.FreeTypeFont]:
        """
        Load a font with proper error handling.

        Args:
            font_name: Name of the font file (e.g., "Roboto-Bold.ttf")
            size: Font size
            fallback_to_default: Whether to fall back to default font if loading fails

        Returns:
            PIL ImageFont object or None if loading fails
        """
        cache_key = f"{font_name}_{size}"
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font_path = os.path.join(self.fonts_dir, font_name)

        try:
            if not os.path.exists(font_path):
                logger.warning(f"Font file not found: {font_path}")
                if fallback_to_default:
                    logger.info("Falling back to default font")
                    font = ImageFont.load_default()
                else:
                    return None
            else:
                font = ImageFont.truetype(font_path, size)

            self._font_cache[cache_key] = font
            return font

        except Exception as e:
            logger.error(f"Error loading font {font_name} at size {size}: {e}")
            if fallback_to_default:
                logger.info("Falling back to default font")
                font = ImageFont.load_default()
                self._font_cache[cache_key] = font
                return font
            return None

    def load_image(
        self, image_path: str, convert_to_rgba: bool = True
    ) -> Optional[Image.Image]:
        """
        Load an image with proper error handling.

        Args:
            image_path: Path to the image file
            convert_to_rgba: Whether to convert to RGBA mode

        Returns:
            PIL Image object or None if loading fails
        """
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return None

            image = Image.open(image_path)
            if convert_to_rgba and image.mode != "RGBA":
                image = image.convert("RGBA")
            return image

        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None

    def load_team_logo(
        self, team_name: str, league: str, guild_id: str = None
    ) -> Optional[Image.Image]:
        """
        Load team logo with fallback chain.
        """
        # Import here to avoid circular imports
        from config.asset_paths import get_sport_category_for_path

        # Import team mappings
        try:
            from utils.league_dictionaries.team_mappings import LEAGUE_TEAM_MAPPINGS
        except ImportError:
            LEAGUE_TEAM_MAPPINGS = {}

        # Use mapping if available
        mapped_team = None
        league_key = league.upper()
        if league_key in LEAGUE_TEAM_MAPPINGS:
            mapping = LEAGUE_TEAM_MAPPINGS[league_key]
            # Try exact match, then lower, then fuzzy
            if team_name in mapping:
                mapped_team = mapping[team_name]
            elif team_name.lower() in mapping:
                mapped_team = mapping[team_name.lower()]
            else:
                # Fuzzy match
                import difflib

                matches = difflib.get_close_matches(
                    team_name.lower(), mapping.keys(), n=1, cutoff=0.7
                )
                if matches:
                    mapped_team = mapping[matches[0]]

        # Get normalized team name from league dictionary or mapping
        normalized_team = mapped_team or self._normalize_team_name(team_name, league)
        if not normalized_team:
            normalized_team = team_name

        # Convert normalized team name to filename format
        filename_team = self._team_name_to_filename(normalized_team)

        # Get sport category
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            logger.warning(f"No sport category found for league: {league}")
            return self._load_fallback_logo(guild_id)

        logger.info(
            f"[DEBUG] Looking for team '{team_name}' in league '{league}' -> sport '{sport}'"
        )

        # Try league directory in uppercase, capitalized, and lowercase
        league_variants = [league.upper(), league.capitalize(), league.lower()]
        logo_dir = None
        for variant in league_variants:
            candidate_dir = os.path.join(self.logos_dir, "teams", sport, variant)
            logger.info(f"[DEBUG] Trying directory: {candidate_dir}")
            if os.path.exists(candidate_dir):
                logo_dir = candidate_dir
                logger.info(f"[DEBUG] Found logo directory: {logo_dir}")
                break
        if not logo_dir:
            logger.warning(
                f"No logo directory found for league: {league} (tried {league_variants})"
            )
            return self._load_fallback_logo(guild_id)

        logger.info(f"[DEBUG] Using logo directory: {logo_dir}")
        logger.info(f"[DEBUG] Looking for filename: {filename_team}.png")

        # Try exact match (full name)
        logo_path = os.path.join(logo_dir, f"{filename_team}.png")
        if os.path.exists(logo_path):
            logger.info(f"Found exact logo match: {logo_path}")
            return self.load_image(logo_path)

        # Try mascot-only (last word)
        mascot = filename_team.split("_")[-1]
        mascot_path = os.path.join(logo_dir, f"{mascot}.png")
        if os.path.exists(mascot_path):
            logger.info(f"Found mascot-only logo match: {mascot_path}")
            return self.load_image(mascot_path)

        # Try city-only (first word)
        city = filename_team.split("_")[0]
        city_path = os.path.join(logo_dir, f"{city}.png")
        if os.path.exists(city_path):
            logger.info(f"Found city-only logo match: {city_path}")
            return self.load_image(city_path)

        # Try fuzzy matching
        candidates = [f for f in os.listdir(logo_dir) if f.endswith(".png")]
        candidate_names = [os.path.splitext(f)[0] for f in candidates]
        import difflib

        matches = difflib.get_close_matches(
            filename_team, candidate_names, n=1, cutoff=0.7
        )
        if matches:
            match_path = os.path.join(logo_dir, f"{matches[0]}.png")
            logger.info(f"Found fuzzy logo match: {match_path}")
            return self.load_image(match_path)

        # Fallback to default logo
        logger.warning(f"No logo found for team '{team_name}' in league '{league}'")
        return self._load_fallback_logo(guild_id)

    def load_player_image(
        self, player_name: str, team_name: str, league: str, guild_id: str = None
    ) -> Tuple[Optional[Image.Image], str]:
        """
        Load player image with fallback chain.

        Args:
            player_name: Name of the player
            team_name: Name of the team
            league: League name
            guild_id: Guild ID for guild-specific fallbacks

        Returns:
            Tuple of (PIL Image object, display name) or (None, original_name) if not found
        """
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league

        sport = get_sport_category_for_path(league.upper())
        if not sport:
            logger.warning(f"No sport category found for league: {league}")
            fallback = self._load_fallback_logo(guild_id)
            return fallback, player_name

        # Normalize names
        normalized_team = (
            normalize_team_name_any_league(team_name)
            .replace(".", "")
            .replace(" ", "_")
            .lower()
        )
        normalized_player = (
            normalize_team_name_any_league(player_name)
            .replace(".", "")
            .replace(" ", "_")
            .lower()
        )

        # Try exact match
        player_dir = os.path.join(
            self.logos_dir, "players", sport.lower(), normalized_team
        )
        player_path = os.path.join(player_dir, f"{normalized_player}.png")

        if os.path.exists(player_path):
            logger.info(f"Found exact player image: {player_path}")
            return self.load_image(player_path), player_name

        # Try fuzzy matching
        if os.path.exists(player_dir):
            candidates = [f for f in os.listdir(player_dir) if f.endswith(".png")]
            candidate_names = [os.path.splitext(f)[0] for f in candidates]
            matches = difflib.get_close_matches(
                normalized_player, candidate_names, n=1, cutoff=0.75
            )
            if matches:
                match_path = os.path.join(player_dir, f"{matches[0]}.png")
                display_name = matches[0].replace("_", " ").title()
                logger.info(f"Found fuzzy player image match: {match_path}")
                return self.load_image(match_path), display_name

        # Fallback
        logger.warning(
            f"No player image found for '{player_name}' in team '{team_name}'"
        )
        fallback = self._load_fallback_logo(guild_id)
        return fallback, player_name

    def load_league_logo(
        self, league_code: str, sport: str = None
    ) -> Optional[Image.Image]:
        """
        Load league logo with fallback chain.

        Args:
            league_code: League code (e.g., "EPL", "NBA", "MLB")
            sport: Sport category (optional, will be auto-detected if not provided)

        Returns:
            PIL Image object or None if no logo found
        """
        from config.asset_paths import get_sport_category_for_path
        from config.leagues import LEAGUE_IDS

        # Get league info from LEAGUE_IDS
        league_info = LEAGUE_IDS.get(league_code.upper())
        if not league_info:
            logger.warning(f"No league info found for code: {league_code}")
            return None

        league_name = league_info.get("name", league_code)
        league_info.get("sport", sport)

        # Get sport category if not provided
        if not sport:
            sport = get_sport_category_for_path(league_code.upper())
            if not sport:
                logger.warning(f"No sport category found for league: {league_code}")
                return None

        # Normalize league name for filename
        normalized_name = (
            league_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        )

        # Try to find the logo file
        logo_paths = [
            # Try the new naming convention first (full league name)
            os.path.join(
                self.logos_dir,
                "leagues",
                sport.upper(),
                league_code.upper(),
                f"{normalized_name}.png",
            ),
            # Fallback to old naming convention (league code)
            os.path.join(
                self.logos_dir,
                "leagues",
                sport.upper(),
                league_code.upper(),
                f"{league_code.lower()}.png",
            ),
            # Try without sport subdirectory
            os.path.join(
                self.logos_dir, "leagues", league_code.upper(), f"{normalized_name}.png"
            ),
            os.path.join(
                self.logos_dir,
                "leagues",
                league_code.upper(),
                f"{league_code.lower()}.png",
            ),
        ]

        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                logger.info(f"Found league logo: {logo_path}")
                return self.load_image(logo_path)

        # Try fuzzy matching in the league directory
        league_dir = os.path.join(
            self.logos_dir, "leagues", sport.upper(), league_code.upper()
        )
        if os.path.exists(league_dir):
            candidates = [f for f in os.listdir(league_dir) if f.endswith(".png")]
            candidate_names = [os.path.splitext(f)[0] for f in candidates]

            # Try matching against normalized league name
            matches = difflib.get_close_matches(
                normalized_name.lower(),
                [name.lower() for name in candidate_names],
                n=1,
                cutoff=0.75,
            )
            if matches:
                match_path = os.path.join(league_dir, f"{matches[0]}.png")
                logger.info(f"Found fuzzy league logo match: {match_path}")
                return self.load_image(match_path)

        logger.warning(f"No league logo found for '{league_code}' ({league_name})")
        return None

    def _normalize_team_name(self, team_name: str, league: str) -> Optional[str]:
        """Normalize team name using league dictionaries."""
        try:
            # Import appropriate league dictionary based on the league
            league_lower = league.lower()
            if league_lower == "mlb":
                from utils.league_dictionaries.baseball import (
                    TEAM_FULL_NAMES as league_dict,
                )
            elif league_lower == "nba":
                from utils.league_dictionaries.basketball import (
                    TEAM_NAMES as league_dict,
                )
            elif league_lower == "nfl":
                from utils.league_dictionaries.football import TEAM_NAMES as league_dict
            elif league_lower == "nhl":
                from utils.league_dictionaries.hockey import TEAM_NAMES as league_dict
            elif league_lower == "cfl":
                from utils.league_dictionaries.cfl import TEAM_NAMES as league_dict
            else:
                league_dict = {}

            team_name_lower = team_name.lower()

            # Try exact match
            if team_name_lower in league_dict:
                return league_dict[team_name_lower]

            # Try fuzzy matching against dictionary keys (within this league only)
            matches = difflib.get_close_matches(
                team_name_lower, league_dict.keys(), n=1, cutoff=0.75
            )
            if matches:
                normalized_team = league_dict[matches[0]]
                logger.info(
                    f"[LOGO] Fuzzy matched team name '{team_name}' to '{normalized_team}' using league dictionary"
                )
                return normalized_team

        except Exception as e:
            logger.warning(
                f"[LOGO] Error using league dictionary for '{team_name}': {e}"
            )

        return None

    def _team_name_to_filename(self, team_name: str) -> str:
        """Convert a full team name to a filename-friendly format."""
        # Convert to lowercase
        filename_team = team_name.lower()
        # Replace spaces with underscores
        filename_team = filename_team.replace(" ", "_")
        # Replace special characters with underscores
        filename_team = "".join(c for c in filename_team if c.isalnum() or c == "_")
        # Remove any leading/trailing underscores
        filename_team = filename_team.strip("_")
        return filename_team

    def _load_fallback_logo(self, guild_id: str = None) -> Optional[Image.Image]:
        """Load fallback logo with guild-specific priority."""
        fallback_paths = []

        if guild_id:
            fallback_paths.append(
                os.path.join(
                    self.static_dir, "guilds", str(guild_id), "default_image.png"
                )
            )

        fallback_paths.extend(
            [
                os.path.join(self.logos_dir, "default_image.png"),
                os.path.join(self.logos_dir, "default_logo.png"),
            ]
        )

        for path in fallback_paths:
            if os.path.exists(path):
                logger.info(f"Using fallback logo: {path}")
                return self.load_image(path)

        logger.error("No fallback logo found")
        return None


# Global instance for easy access
asset_loader = AssetLoader()


def find_team_logo_path(team_name, league, sport_category, static_root):
    # Normalize team name
    normalized_team = (
        team_name.replace(" ", "_").replace("-", "_").replace("'", "").lower()
    )
    league_dir = os.path.join(static_root, "logos", "teams", sport_category, league)
    logger.warning(f"[DEBUG] Searching for team logo in: {league_dir}")
    logger.warning(f"[DEBUG] Normalized team name: {normalized_team}")
    if not os.path.isdir(league_dir):
        logger.warning(f"[DEBUG] Directory does not exist: {league_dir}")
        return None
    files = [
        f
        for f in os.listdir(league_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    logger.warning(f"[DEBUG] Files in directory: {files}")
    # Try exact match first
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = os.path.join(league_dir, f"{normalized_team}{ext}")
        if os.path.isfile(candidate):
            logger.warning(f"[DEBUG] Found exact logo: {candidate}")
            return candidate
    from rapidfuzz import process

    matches = process.extract(
        normalized_team, files, limit=1, scorer=process.fuzz.partial_ratio
    )
    if matches and matches[0][1] > 80:
        logger.warning(f"[DEBUG] Found fuzzy logo match: {matches[0][0]}")
        return os.path.join(league_dir, matches[0][0])
    logger.warning(f"[DEBUG] No logo found for team '{team_name}' in league '{league}'")
    return None
