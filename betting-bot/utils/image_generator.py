"""Compatibility wrapper around the legacy `image_generator_old.BetSlipGenerator`.

Other modules import `BetSlipGenerator` from here and expect three helper
coroutines:
    • generate_game_line_slip
    • generate_player_prop_slip
    • generate_parlay_slip

This file re-exports the original implementation and adds those wrappers so
legacy call-sites continue to work even after slimming the code-base down to
specialised generators.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional, List, Dict

from PIL import Image
from config.asset_paths import get_sport_category_for_path, BASE_DIR  # re-export for legacy imports

# Re-use the full implementation that already lives in utils.image_generator_old
# from .image_generator_old import BetSlipGenerator as _BaseBetSlipGenerator

from config.team_mappings import normalize_team_name
from data.game_utils import normalize_team_name_any_league

__all__ = ["BetSlipGenerator", "get_sport_category_for_path"]


class BetSlipGenerator:
    """Light-weight generator that chooses the correct dedicated image builder
    (game line, player prop, parlay) without relying on the legacy
    `image_generator_old` implementation.
    """

    def __init__(self, guild_id: int | None = None):
        self.guild_id = guild_id  # kept for interface parity

    # ------------------------------------------------------------------
    # internal utility
    # ------------------------------------------------------------------
    async def _img_to_bytes(self, img: Image.Image | bytes | None):
        if img is None:
            return None
        if isinstance(img, (bytes, bytearray)):
            return img
        buf = io.BytesIO()
        try:
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
        finally:
            buf.close()

    # ------------------------------------------------------------------
    # public helpers expected by the rest of the code-base
    # ------------------------------------------------------------------
    async def generate_game_line_slip(
        self,
        *,
        league: str,
        home_team: str,
        away_team: str,
        odds: float,
        units: float,
        selected_team: Optional[str] = None,
        line: Optional[str] = None,
        bet_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        # Use the new dedicated generator for game lines so visuals match design
        from utils.game_line_image_generator import GameLineImageGenerator
        import os, tempfile

        def _resolve_logo_path(t_name: str) -> str | None:
            sport = get_sport_category_for_path(league.upper())
            if not sport:
                return None
            normalized = normalize_team_name_any_league(t_name).replace(".", "")
            fname = f"{normalize_team_name(normalized)}.png"
            path = os.path.join(BASE_DIR, "static", "logos", "teams", sport, league.upper(), fname)
            return path if os.path.exists(path) else None

        home_logo_path = _resolve_logo_path(home_team)
        away_logo_path = _resolve_logo_path(away_team)

        gen = GameLineImageGenerator()
        png_bytes = gen.generate_bet_slip_image(
            team1_name=home_team,
            team1_logo_path=home_logo_path or "betting-bot/static/logos/default_logo.png",
            team2_name=away_team,
            team2_logo_path=away_logo_path or "betting-bot/static/logos/default_logo.png",
            line=(line or "ML"),
            units=units,
            output_path=None,
            league=league,
            bet_id=bet_id,
            odds=odds,
            selected_team=selected_team,
        )
        return png_bytes

    async def generate_player_prop_slip(
        self,
        *,
        league: str,
        home_team: str,
        away_team: str,
        odds: float,
        units: float,
        selected_team: Optional[str] = None,
        line: Optional[str] = None,
        bet_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        player_name: Optional[str] = None,
        player_picture_path: Optional[str] = None,
        team_logo_path: Optional[str] = None,
    ):
        # Use the dedicated player prop image generator
        from utils.game_line_image_generator import generate_player_prop_bet_image
        # If logo paths are not provided, try to resolve them
        import os
        def _resolve_logo_path(t_name: str) -> str | None:
            sport = get_sport_category_for_path(league.upper())
            if not sport:
                return None
            normalized = normalize_team_name_any_league(t_name).replace(".", "")
            fname = f"{normalize_team_name(normalized)}.png"
            path = os.path.join(BASE_DIR, "static", "logos", "teams", sport, league.upper(), fname)
            return path if os.path.exists(path) else None

        logo_path = team_logo_path or _resolve_logo_path(home_team)
        # player_picture_path must be provided by caller
        png_bytes = generate_player_prop_bet_image(
            player_name=player_name or "",
            player_picture_path=player_picture_path or "betting-bot/static/logos/default_logo.png",
            team_name=home_team,
            team_logo_path=logo_path or "betting-bot/static/logos/default_logo.png",
            line=line or "",
            units=units,
            output_path=None,
        )
        return png_bytes

    async def generate_parlay_slip(
        self,
        *,
        league: str,
        home_team: str,
        away_team: str,
        odds: float,
        units: float,
        selected_team: Optional[str] = None,
        line: Optional[str] = None,
        bet_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        parlay_legs: Optional[List[Dict]] = None,
        is_same_game: bool = False,
        team_logo_paths: Optional[List[str]] = None,
    ):
        img = await self.generate_bet_slip(
            home_team=home_team,
            away_team=away_team,
            league=league,
            odds=odds,
            units=units,
            bet_id=str(bet_id) if bet_id is not None else "",
            timestamp=timestamp or datetime.utcnow(),
            bet_type="parlay",
            line=line,
            selected_team=selected_team,
            parlay_legs=parlay_legs,
            is_same_game=is_same_game,
            team_logo_paths=team_logo_paths,
        )
        return img

    # ---------------------------------------------------------
    # unified entry-point (kept for legacy calls)
    # ---------------------------------------------------------
    async def generate_bet_slip(
        self,
        *,
        home_team: str,
        away_team: str,
        league: str,
        odds: float,
        units: float,
        bet_id: str | None = None,
        timestamp: datetime | None = None,
        bet_type: str = "game_line",
        line: str | None = None,
        parlay_legs: List[Dict] | None = None,
        is_same_game: bool = False,
        team_logo_paths: List[str] | None = None,
        selected_team: str | None = None,
        player_name: str | None = None,
        player_picture_path: Optional[str] = None,
    ):
        """Legacy-compatible entry point that returns a PIL.Image."""

        bet_type_lower = bet_type.lower() if bet_type else "game_line"

        if bet_type_lower == "player_prop":
            data = await self.generate_player_prop_slip(
                league=league,
                home_team=home_team,
                away_team=away_team,
                odds=odds,
                units=units,
                selected_team=selected_team,
                line=line,
                bet_id=bet_id,
                timestamp=timestamp,
                player_name=player_name,
                player_picture_path=player_picture_path,
                team_logo_path=team_logo_paths[0] if team_logo_paths else None,
            )
            return data

        if bet_type_lower == "parlay":
            data = await self.generate_parlay_slip(
                league=league,
                home_team=home_team,
                away_team=away_team,
                odds=odds,
                units=units,
                selected_team=selected_team,
                line=line,
                bet_id=bet_id,
                timestamp=timestamp,
                parlay_legs=parlay_legs,
                is_same_game=is_same_game,
                team_logo_paths=team_logo_paths,
            )
            return data

        # default to game line
        data = await self.generate_game_line_slip(
            league=league,
            home_team=home_team,
            away_team=away_team,
            odds=odds,
            units=units,
            selected_team=selected_team,
            line=line,
            bet_id=bet_id,
            timestamp=timestamp,
        )
        return data 