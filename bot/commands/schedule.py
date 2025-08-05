"""Schedule command for viewing upcoming games with dropdown selection."""

import logging
import os
import tempfile
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, Select, View
from PIL import Image, ImageDraw, ImageFont

from data.league_schedules.nfl.teams.arizona_cardinals_schedule import (
    ARIZONA_CARDINALS_SCHEDULE,
)
from data.league_schedules.nfl.teams.atlanta_falcons_schedule import (
    ATLANTA_FALCONS_SCHEDULE,
)
from data.league_schedules.nfl.teams.baltimore_ravens_schedule import (
    BALTIMORE_RAVENS_SCHEDULE,
)

# Import team schedules
from data.league_schedules.nfl.teams.buffalo_bills_schedule import (
    BUFFALO_BILLS_SCHEDULE,
)
from data.league_schedules.nfl.teams.carolina_panthers_schedule import (
    CAROLINA_PANTHERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.chicago_bears_schedule import (
    CHICAGO_BEARS_SCHEDULE,
)
from data.league_schedules.nfl.teams.cincinnati_bengals_schedule import (
    CINCINNATI_BENGALS_SCHEDULE,
)
from data.league_schedules.nfl.teams.cleveland_browns_schedule import (
    CLEVELAND_BROWNS_SCHEDULE,
)
from data.league_schedules.nfl.teams.dallas_cowboys_schedule import (
    DALLAS_COWBOYS_SCHEDULE,
)
from data.league_schedules.nfl.teams.denver_broncos_schedule import (
    DENVER_BRONCOS_SCHEDULE,
)
from data.league_schedules.nfl.teams.detroit_lions_schedule import (
    DETROIT_LIONS_SCHEDULE,
)
from data.league_schedules.nfl.teams.green_bay_packers_schedule import (
    GREEN_BAY_PACKERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.houston_texans_schedule import (
    HOUSTON_TEXANS_SCHEDULE,
)
from data.league_schedules.nfl.teams.indianapolis_colts_schedule import (
    INDIANAPOLIS_COLTS_SCHEDULE,
)
from data.league_schedules.nfl.teams.jacksonville_jaguars_schedule import (
    JACKSONVILLE_JAGUARS_SCHEDULE,
)
from data.league_schedules.nfl.teams.kansas_city_chiefs_schedule import (
    KANSAS_CITY_CHIEFS_SCHEDULE,
)
from data.league_schedules.nfl.teams.las_vegas_raiders_schedule import (
    LAS_VEGAS_RAIDERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.los_angeles_chargers_schedule import (
    LOS_ANGELES_CHARGERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.los_angeles_rams_schedule import (
    LOS_ANGELES_RAMS_SCHEDULE,
)
from data.league_schedules.nfl.teams.miami_dolphins_schedule import (
    MIAMI_DOLPHINS_SCHEDULE,
)
from data.league_schedules.nfl.teams.minnesota_vikings_schedule import (
    MINNESOTA_VIKINGS_SCHEDULE,
)
from data.league_schedules.nfl.teams.new_england_patriots_schedule import (
    NEW_ENGLAND_PATRIOTS_SCHEDULE,
)
from data.league_schedules.nfl.teams.new_orleans_saints_schedule import (
    NEW_ORLEANS_SAINTS_SCHEDULE,
)
from data.league_schedules.nfl.teams.new_york_giants_schedule import (
    NEW_YORK_GIANTS_SCHEDULE,
)
from data.league_schedules.nfl.teams.new_york_jets_schedule import (
    NEW_YORK_JETS_SCHEDULE,
)
from data.league_schedules.nfl.teams.philadelphia_eagles_schedule import (
    PHILADELPHIA_EAGLES_SCHEDULE,
)
from data.league_schedules.nfl.teams.pittsburgh_steelers_schedule import (
    PITTSBURGH_STEELERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.san_francisco_49ers_schedule import (
    SAN_FRANCISCO_49ERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.seattle_seahawks_schedule import (
    SEATTLE_SEAHAWKS_SCHEDULE,
)
from data.league_schedules.nfl.teams.tampa_bay_buccaneers_schedule import (
    TAMPA_BAY_BUCCANEERS_SCHEDULE,
)
from data.league_schedules.nfl.teams.tennessee_titans_schedule import (
    TENNESSEE_TITANS_SCHEDULE,
)
from data.league_schedules.nfl.teams.washington_commanders_schedule import (
    WASHINGTON_COMMANDERS_SCHEDULE,
)

# Import the league schedule data
from data.nfl_schedule_2025_2026 import NFL_SCHEDULE_2025_2026

logger = logging.getLogger(__name__)

# Team schedule mapping
TEAM_SCHEDULES = {
    "Buffalo Bills": BUFFALO_BILLS_SCHEDULE,
    "Miami Dolphins": MIAMI_DOLPHINS_SCHEDULE,
    "New England Patriots": NEW_ENGLAND_PATRIOTS_SCHEDULE,
    "New York Jets": NEW_YORK_JETS_SCHEDULE,
    "Baltimore Ravens": BALTIMORE_RAVENS_SCHEDULE,
    "Cincinnati Bengals": CINCINNATI_BENGALS_SCHEDULE,
    "Cleveland Browns": CLEVELAND_BROWNS_SCHEDULE,
    "Pittsburgh Steelers": PITTSBURGH_STEELERS_SCHEDULE,
    "Houston Texans": HOUSTON_TEXANS_SCHEDULE,
    "Indianapolis Colts": INDIANAPOLIS_COLTS_SCHEDULE,
    "Jacksonville Jaguars": JACKSONVILLE_JAGUARS_SCHEDULE,
    "Tennessee Titans": TENNESSEE_TITANS_SCHEDULE,
    "Denver Broncos": DENVER_BRONCOS_SCHEDULE,
    "Kansas City Chiefs": KANSAS_CITY_CHIEFS_SCHEDULE,
    "Las Vegas Raiders": LAS_VEGAS_RAIDERS_SCHEDULE,
    "Los Angeles Chargers": LOS_ANGELES_CHARGERS_SCHEDULE,
    "Dallas Cowboys": DALLAS_COWBOYS_SCHEDULE,
    "New York Giants": NEW_YORK_GIANTS_SCHEDULE,
    "Philadelphia Eagles": PHILADELPHIA_EAGLES_SCHEDULE,
    "Washington Commanders": WASHINGTON_COMMANDERS_SCHEDULE,
    "Chicago Bears": CHICAGO_BEARS_SCHEDULE,
    "Detroit Lions": DETROIT_LIONS_SCHEDULE,
    "Green Bay Packers": GREEN_BAY_PACKERS_SCHEDULE,
    "Minnesota Vikings": MINNESOTA_VIKINGS_SCHEDULE,
    "Atlanta Falcons": ATLANTA_FALCONS_SCHEDULE,
    "Carolina Panthers": CAROLINA_PANTHERS_SCHEDULE,
    "New Orleans Saints": NEW_ORLEANS_SAINTS_SCHEDULE,
    "Tampa Bay Buccaneers": TAMPA_BAY_BUCCANEERS_SCHEDULE,
    "Arizona Cardinals": ARIZONA_CARDINALS_SCHEDULE,
    "Los Angeles Rams": LOS_ANGELES_RAMS_SCHEDULE,
    "San Francisco 49ers": SAN_FRANCISCO_49ERS_SCHEDULE,
    "Seattle Seahawks": SEATTLE_SEAHAWKS_SCHEDULE,
}

# --- PAGINATED TEAM SELECT ---
ALL_TEAMS = list(TEAM_SCHEDULES.keys())
TEAMS_PER_PAGE = 25


class PaginatedTeamSelect(View):
    def __init__(self, cog=None, page=0, league="NFL"):
        super().__init__(timeout=60)
        self.cog = cog
        self.page = page
        self.league = league
        self.max_page = (len(ALL_TEAMS) - 1) // TEAMS_PER_PAGE
        self.update_dropdown()

    def update_dropdown(self):
        start = self.page * TEAMS_PER_PAGE
        end = start + TEAMS_PER_PAGE
        teams = ALL_TEAMS[start:end]
        options = [discord.SelectOption(label=team, value=team) for team in teams]
        if hasattr(self, "team_select"):
            self.remove_item(self.team_select)
        self.team_select = Select(placeholder="Choose a team...", options=options)
        self.team_select.callback = self.team_callback
        self.add_item(self.team_select)

    async def team_callback(self, interaction: discord.Interaction):
        team_name = self.team_select.values[0]
        team_schedule = TEAM_SCHEDULES[team_name]

        # Generate team season schedule image directly
        try:
            view = TeamSeasonSelect(team_name, team_schedule, self.cog)
            image_path = await view.generate_team_season_image(
                interaction.guild, team_name, team_schedule, self.league
            )

            # Find member role and mention it
            member_role = None
            for role in interaction.guild.roles:
                if "member" in role.name.lower() or "members" in role.name.lower():
                    member_role = role
                    break

            mention_text = f"{member_role.mention} " if member_role else ""
            await interaction.response.send_message(
                f"{mention_text}Here's your season schedule!",
                file=discord.File(image_path),
            )
            os.remove(image_path)  # Clean up temp file
        except Exception as e:
            logger.error(f"Error generating team season image: {e}")
            await interaction.response.send_message(
                "Error generating team season image.", ephemeral=True
            )

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, row=1)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.page > 0:
            self.page -= 1
            self.update_dropdown()
            await interaction.response.edit_message(content="Select a team:", view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, row=1)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.page < self.max_page:
            self.page += 1
            self.update_dropdown()
            await interaction.response.edit_message(content="Select a team:", view=self)
        else:
            await interaction.response.defer()


class ScheduleTypeSelect(View):
    def __init__(self, cog=None):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.button(label="League Schedule", style=discord.ButtonStyle.primary)
    async def league_schedule(self, interaction: discord.Interaction, button: Button):
        view = LeagueSelect(self.cog)
        await interaction.response.edit_message(content="Select a league:", view=view)

    @discord.ui.button(label="Team Schedule", style=discord.ButtonStyle.secondary)
    async def team_schedule(self, interaction: discord.Interaction, button: Button):
        # First show league selection for team schedules
        view = TeamLeagueSelect(self.cog)
        try:
            await interaction.response.edit_message(
                content="Select a league for team schedule:", view=view
            )
        except Exception:
            await interaction.response.send_message(
                content="Select a league for team schedule:", view=view, ephemeral=True
            )


class TeamLeagueSelect(View):
    """League selection view specifically for team schedules."""

    def __init__(self, cog=None):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a league...",
        options=[
            discord.SelectOption(
                label="NFL", value="nfl", description="National Football League"
            ),
            discord.SelectOption(
                label="NCAA Football",
                value="ncaa_football",
                description="College Football",
            ),
        ],
    )
    async def league_callback(self, interaction: discord.Interaction, select: Select):
        selected_league = select.values[0]

        # For now, only NFL is supported for team schedules
        if selected_league == "nfl":
            view = PaginatedTeamSelect(self.cog, page=0, league="NFL")
            try:
                await interaction.response.edit_message(
                    content="Select a team:", view=view
                )
            except Exception:
                await interaction.response.send_message(
                    content="Select a team:", view=view, ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "NCAA Football team schedules are not yet supported.", ephemeral=True
            )


class TeamSeasonSelect(View):
    def __init__(self, team_name: str, team_schedule: dict, cog=None):
        super().__init__(timeout=60)
        self.team_name = team_name
        self.team_schedule = team_schedule
        self.cog = cog

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> tuple:
        """
        Blend two hex colors based on a ratio.

        Args:
            color1 (str): First hex color (e.g., "#FF0000")
            color2 (str): Second hex color (e.g., "#0000FF")
            ratio (float): Blend ratio (0.0 = color1, 1.0 = color2)

        Returns:
            tuple: RGB color tuple
        """
        # Remove # from hex colors
        color1 = color1.lstrip("#")
        color2 = color2.lstrip("#")

        # Convert hex to RGB
        r1, g1, b1 = int(color1[0:2], 16), int(color1[2:4], 16), int(color1[4:6], 16)
        r2, g2, b2 = int(color2[0:2], 16), int(color2[2:4], 16), int(color2[4:6], 16)

        # Blend colors
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)

        return (r, g, b)

    async def generate_team_season_image(
        self, guild, team_name: str, team_schedule: dict, league="NFL"
    ):
        # Import team colors
        from config.team_colors import get_team_colors

        # Get team colors for background
        team_colors = get_team_colors(team_name, league)
        primary_color = team_colors["primary"]
        secondary_color = team_colors["secondary"]

        # Create a more compact image to fit all 18 weeks
        image = Image.new("RGB", (1200, 1800), color=primary_color)
        draw = ImageDraw.Draw(image)

        # Create gradient background using team colors
        for y in range(1800):
            progress = y / 1800
            # Blend from primary to secondary color
            color = self._blend_colors(primary_color, secondary_color, progress)
            draw.line([(0, y), (1200, y)], fill=color)

        # Add large faded league logo as background with enhanced styling (matching league schedule)
        try:
            league_logo_path = f"../../../StaticFiles/DBSBM/static/logos/leagues/{league.upper()}/{league.lower()}.webp"
            if os.path.exists(league_logo_path):
                league_logo = Image.open(league_logo_path)
                # Resize to be large and centered
                league_logo = league_logo.resize((800, 800))
                # Create a more faded version for better text readability
                faded_logo = league_logo.copy()
                faded_logo.putalpha(20)  # Very transparent (20/255)
                # Center the logo
                x_offset = (1200 - 800) // 2
                y_offset = (1800 - 800) // 2
                image.paste(faded_logo, (x_offset, y_offset), faded_logo)
        except Exception as e:
            logger.warning(f"Could not load league logo background: {e}")

        # Load enhanced fonts with better sizing (matching league schedule)
        try:
            title_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 48
            )
            subtitle_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 32
            )
            header_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 36
            )
            text_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 24
            )
            small_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 18
            )
            time_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 18
            )
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            time_font = ImageFont.load_default()

        # Add header section with proper spacing (matching league schedule)
        header_y_start = 50

        # Add logos first (top row) - matching league schedule styling
        try:
            # --- Bot Logo ---
            ptp_logo_path = "../../../StaticFiles/DBSBM/static/logos/default_image.webp"
            if os.path.exists(ptp_logo_path):
                ptp_logo = Image.open(ptp_logo_path)
                ptp_logo = ptp_logo.resize((70, 70))  # Slightly larger
                if ptp_logo.mode != "RGBA":
                    ptp_logo = ptp_logo.convert("RGBA")
                # Position logo at top left
                logo_x = 400 - 35
                logo_y = header_y_start
                # Add subtle glow effect
                draw.ellipse(
                    [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                    fill="#ffffff",
                    outline="#4a90e2",
                    width=3,
                )
                image.paste(ptp_logo, (logo_x, logo_y), ptp_logo)

            # --- Guild Logo ---
            if guild:
                guild_logo_paths = [
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/default_image.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/background_image.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/logo.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/guild_logo.webp",
                ]
                guild_logo_loaded = False
                for guild_logo_path in guild_logo_paths:
                    if os.path.exists(guild_logo_path):
                        try:
                            guild_logo = Image.open(guild_logo_path)
                            guild_logo = guild_logo.resize((70, 70))  # Slightly larger
                            if guild_logo.mode != "RGBA":
                                guild_logo = guild_logo.convert("RGBA")
                            # Position logo at top right
                            logo_x = 840 - 35
                            logo_y = header_y_start
                            # Add subtle glow effect
                            draw.ellipse(
                                [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                                fill="#ffffff",
                                outline="#4a90e2",
                                width=3,
                            )
                            image.paste(guild_logo, (logo_x, logo_y), guild_logo)
                            guild_logo_loaded = True
                            break
                        except Exception as e:
                            continue
        except Exception as e:
            logger.warning(f"Could not load logos: {e}")

        # Add text below logos with proper spacing (matching league schedule)
        text_y_start = header_y_start + 100  # 100px below logos

        # Add Bet Tracking Bot branding at 1/3 position (left side)
        draw.text(
            (400, text_y_start),
            "Bet Tracking Bot",
            font=title_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Add guild name at 2/3 position (right side)
        if guild:
            guild_name_text = f"{guild.name.upper()}"
        else:
            guild_name_text = "BET TRACKING BOT GUILD"
        draw.text(
            (840, text_y_start),
            guild_name_text,
            font=title_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Add league and schedule type info centered below (matching league schedule)
        draw.text(
            (600, text_y_start + 50),
            f"{league.upper()} SEASON SCHEDULE",
            font=subtitle_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Create enhanced background overlay with rounded corners effect (matching league schedule)
        width, height = image.size
        overlay = Image.new("RGBA", (width - 80, height - 150), (255, 255, 255, 80))
        image.paste(overlay, (40, 200), overlay)

        # Add a subtle border around the main content area (matching league schedule)
        border_color = (100, 150, 200, 150)  # Blue border
        border_overlay = Image.new("RGBA", (width - 60, height - 130), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_overlay)
        border_draw.rectangle(
            [0, 0, width - 60, height - 130], outline=border_color, width=3
        )
        image.paste(border_overlay, (50, 210), border_overlay)

        # Add team title with enhanced styling (matching league schedule)
        draw.text(
            (600, 280),
            f"{team_name} - Full Season Schedule",
            font=header_font,
            fill="#1a1a1a",
            anchor="mm",
        )

        # Add all games for the season with compact spacing and formatting
        y_position = 320  # Start a bit lower to account for header
        current_day = None

        for week_num in range(1, 19):  # Weeks 1-18
            week_key = f"week_{week_num}"
            if week_key in team_schedule:
                game_info = team_schedule[week_key]
                day, date, opponent, time, network = game_info

                # Add week designation on the left
                week_text = f"Week {week_num}"
                draw.text((80, y_position), week_text, font=text_font, fill="#ffffff")

                if day == "BYE WEEK":
                    # Draw bye week in different style
                    draw.text(
                        (200, y_position),
                        f"BYE WEEK: {opponent}",
                        font=text_font,
                        fill="#666666",
                    )
                    y_position += 45
                else:
                    # Draw game details with compact layout
                    # Add subtle background for each game
                    game_bg = Image.new("RGBA", (width - 180, 30), (240, 248, 255, 100))
                    image.paste(game_bg, (90, y_position - 3), game_bg)

                    # Team matchup in the middle
                    draw.text(
                        (200, y_position), opponent, font=text_font, fill="#1a1a1a"
                    )

                    # Time and channel on the right side
                    time_text = f"{time} - {network}"
                    time_width = draw.textlength(time_text, font=time_font)
                    draw.text(
                        (width - 110 - time_width, y_position),
                        time_text,
                        font=time_font,
                        fill="#2a4a6a",
                    )

                    y_position += 30

                    # Add date underneath
                    draw.text(
                        (200, y_position),
                        f"{day}, {date}",
                        font=small_font,
                        fill="#666666",
                    )
                    y_position += 25

                    # Add enhanced separator line between games - but not if we're near the bottom
                    if y_position < height - 50:
                        # Gradient separator line (matching league schedule)
                        for i in range(3):
                            alpha = 100 - (i * 30)
                            line_color = (100, 150, 200, alpha)
                            line_overlay = Image.new(
                                "RGBA", (width - 200, 1), (0, 0, 0, 0)
                            )
                            line_draw = ImageDraw.Draw(line_overlay)
                            line_draw.line(
                                [(0, 0), (width - 200, 0)], fill=line_color, width=1
                            )
                            image.paste(
                                line_overlay, (100, y_position - 3 + i), line_overlay
                            )
                        y_position += 10

        # Add copyright watermark (matching league schedule)
        current_year = datetime.now().year
        draw.text(
            (600, 1780),
            f"© Bet Tracking Bot {current_year}",
            font=text_font,
            fill="#666666",
            anchor="mm",
        )

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webp")
        image.save(temp_file.name)
        return temp_file.name


class SportSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Football", value="football", description="NFL, NCAA, etc."
            ),
            discord.SelectOption(
                label="Basketball", value="basketball", description="NBA, NCAA, etc."
            ),
            discord.SelectOption(
                label="Baseball", value="baseball", description="MLB, etc."
            ),
            discord.SelectOption(
                label="Hockey", value="hockey", description="NHL, etc."
            ),
            discord.SelectOption(
                label="Soccer", value="soccer", description="Premier League, MLS, etc."
            ),
        ]
        super().__init__(placeholder="Choose a sport...", options=options)

    async def callback(self, interaction: discord.Interaction):
        sport = self.values[0]

        if sport == "football":
            view = LeagueSelect()
            await interaction.response.edit_message(
                content="Select a league:", view=view
            )
        else:
            await interaction.response.edit_message(
                content=f"Schedule data for {sport} is not available yet.", view=None
            )


class LeagueSelect(View):
    def __init__(self, cog=None):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a league...",
        options=[
            discord.SelectOption(
                label="NFL", value="nfl", description="National Football League"
            ),
            discord.SelectOption(
                label="NCAA Football",
                value="ncaa_football",
                description="College Football",
            ),
        ],
    )
    async def league_callback(self, interaction: discord.Interaction, select: Select):
        league = select.values[0]

        if league == "nfl":
            view = WeekSelect("nfl", self.cog)
        elif league == "ncaa_football":
            view = NCAAWeekSelect(self.cog)
        else:
            await interaction.response.edit_message(
                content="League not supported yet.", view=None
            )
            return

        await interaction.response.edit_message(content="Select a week:", view=view)


class WeekSelect(View):
    def __init__(self, league: str, cog=None):
        super().__init__(timeout=60)
        self.league = league
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a week...",
        options=[
            discord.SelectOption(label="Week 1", value="week_1"),
            discord.SelectOption(label="Week 2", value="week_2"),
            discord.SelectOption(label="Week 3", value="week_3"),
            discord.SelectOption(label="Week 4", value="week_4"),
            discord.SelectOption(label="Week 5", value="week_5"),
            discord.SelectOption(label="Week 6", value="week_6"),
            discord.SelectOption(label="Week 7", value="week_7"),
            discord.SelectOption(label="Week 8", value="week_8"),
            discord.SelectOption(label="Week 9", value="week_9"),
            discord.SelectOption(label="Week 10", value="week_10"),
            discord.SelectOption(label="Week 11", value="week_11"),
            discord.SelectOption(label="Week 12", value="week_12"),
            discord.SelectOption(label="Week 13", value="week_13"),
            discord.SelectOption(label="Week 14", value="week_14"),
            discord.SelectOption(label="Week 15", value="week_15"),
            discord.SelectOption(label="Week 16", value="week_16"),
            discord.SelectOption(label="Week 17", value="week_17"),
            discord.SelectOption(label="Week 18", value="week_18"),
            discord.SelectOption(label="Playoffs", value="playoffs"),
            discord.SelectOption(label="Championship", value="championship"),
        ],
    )
    async def week_callback(self, interaction: discord.Interaction, select: Select):
        week = select.values[0]
        try:
            # Determine league based on the view type
            league = (
                "NFL" if hasattr(self, "league") and self.league == "nfl" else "NCAA"
            )
            image_path = await self.generate_schedule_image(
                interaction.guild, week, league
            )

            # Find member role and mention it
            member_role = None
            for role in interaction.guild.roles:
                if "member" in role.name.lower() or "members" in role.name.lower():
                    member_role = role
                    break

            mention_text = f"{member_role.mention} " if member_role else ""
            await interaction.response.send_message(
                f"{mention_text}Here's your schedule!", file=discord.File(image_path)
            )
            os.remove(image_path)  # Clean up temp file
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}")
            await interaction.response.send_message(
                "Error generating schedule image.", ephemeral=True
            )

    async def generate_schedule_image(self, guild, week: str, league="NFL"):
        """Generate schedule image for a specific week and league"""
        try:
            # Create base image using cog reference
            if self.cog:
                image = self.cog._create_schedule_base_image(guild, league, week)
            else:
                # Fallback: create basic image
                image = Image.new("RGB", (1200, 1600), color="#1a1a1a")
                draw = ImageDraw.Draw(image)
                draw.text(
                    (600, 800),
                    "Error: Could not access image creation method",
                    fill="#ffffff",
                    anchor="mm",
                )

            # Add schedule data
            self._add_schedule_data(image, week)

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webp")
            image.save(temp_file.name, "PNG")
            temp_file.close()

            return temp_file.name
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}")
            raise

    async def generate_placeholder_schedule_image(self, guild, week: str):
        """Generate placeholder schedule image for other leagues"""
        try:
            # Create base image
            image = self._create_schedule_base_image(guild, "NCAA", week)
            draw = ImageDraw.Draw(image)

            # Load fonts
            try:
                header_font = ImageFont.truetype(
                    "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 36
                )
                text_font = ImageFont.truetype(
                    "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 24
                )
            except:
                header_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            # Add placeholder text
            draw.text(
                (600, 800),
                f"Schedule data for {week} coming soon!",
                font=header_font,
                fill="#ffffff",
                anchor="mm",
            )

            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webp")
            image.save(temp_file.name)
            return temp_file.name

        except Exception as e:
            logger.error(f"Error generating placeholder schedule image: {e}")
            raise

    def _add_schedule_data(self, image, week: str):
        """Add schedule data to the image"""
        draw = ImageDraw.Draw(image)

        # Load fonts with smaller sizing to fit all games
        try:
            header_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 36
            )
            title_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 24
            )
            text_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 18
            )
            small_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 16
            )
            time_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 16
            )
        except:
            header_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            time_font = ImageFont.load_default()

        # Get image dimensions
        width, height = image.size

        # Get games for the selected week from external data
        games = NFL_SCHEDULE_2025_2026.get(week, [])
        if not games:
            # If no data for this week, show placeholder
            draw.text(
                (600, 800),
                f"No schedule data available for {week.replace('_', ' ').title()}",
                font=header_font,
                fill="#ffffff",
                anchor="mm",
            )
            return

        # Create enhanced background overlay with rounded corners effect
        overlay = Image.new("RGBA", (width - 80, height - 150), (255, 255, 255, 80))
        image.paste(overlay, (40, 200), overlay)

        # Add a subtle border around the main content area
        border_color = (100, 150, 200, 150)  # Blue border
        border_overlay = Image.new("RGBA", (width - 60, height - 130), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_overlay)
        border_draw.rectangle(
            [0, 0, width - 60, height - 130], outline=border_color, width=3
        )
        image.paste(border_overlay, (50, 210), border_overlay)

        # Add games with enhanced spacing and formatting
        y_position = 300  # Start a bit lower to account for header
        current_day = None

        for day, date, matchup, time, channel in games:
            # Check if this is a bye week entry
            if day == "BYE WEEK":
                # Draw bye week in different style
                draw.text(
                    (80, y_position),
                    f"BYE WEEK: {matchup}",
                    font=title_font,
                    fill="#666666",
                )
                y_position += 60
            else:
                # Group games by day with enhanced day headers
                if current_day != day:
                    current_day = day
                    # Add enhanced day separator with gradient background
                    day_bg = Image.new("RGBA", (width - 160, 45), (80, 140, 200, 220))
                    image.paste(day_bg, (80, y_position - 10), day_bg)

                    # Add day text with shadow effect
                    day_text = f"{day}, {date}"
                    # Shadow
                    draw.text(
                        (602, y_position + 10),
                        day_text,
                        font=title_font,
                        fill="#2a4a6a",
                        anchor="mm",
                    )
                    # Main text
                    draw.text(
                        (600, y_position + 8),
                        day_text,
                        font=title_font,
                        fill="#ffffff",
                        anchor="mm",
                    )
                    y_position += 50

                # Draw game details with enhanced styling
                # Add subtle background for each game
                game_bg = Image.new("RGBA", (width - 180, 35), (240, 248, 255, 100))
                image.paste(game_bg, (90, y_position - 5), game_bg)

                # Team matchup with enhanced styling
                draw.text((110, y_position), matchup, font=text_font, fill="#1a1a1a")

                # Time and channel on the right side with better contrast
                time_text = f"{time} - {channel}"
                time_width = draw.textlength(time_text, font=time_font)
                draw.text(
                    (width - 110 - time_width, y_position),
                    time_text,
                    font=time_font,
                    fill="#2a4a6a",
                )

                y_position += 40

                # Add enhanced separator line between games - but not if we're near the bottom
                if y_position < height - 50:
                    # Gradient separator line
                    for i in range(3):
                        alpha = 100 - (i * 30)
                        line_color = (100, 150, 200, alpha)
                        line_overlay = Image.new("RGBA", (width - 200, 1), (0, 0, 0, 0))
                        line_draw = ImageDraw.Draw(line_overlay)
                        line_draw.line(
                            [(0, 0), (width - 200, 0)], fill=line_color, width=1
                        )
                        image.paste(
                            line_overlay, (100, y_position - 5 + i), line_overlay
                        )
                    y_position += 15


class NCAAWeekSelect(View):
    def __init__(self, cog=None):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a week...",
        options=[
            discord.SelectOption(label="Week 1", value="week_1"),
            discord.SelectOption(label="Week 2", value="week_2"),
            discord.SelectOption(label="Week 3", value="week_3"),
            discord.SelectOption(label="Week 4", value="week_4"),
            discord.SelectOption(label="Week 5", value="week_5"),
            discord.SelectOption(label="Week 6", value="week_6"),
            discord.SelectOption(label="Week 7", value="week_7"),
            discord.SelectOption(label="Week 8", value="week_8"),
            discord.SelectOption(label="Week 9", value="week_9"),
            discord.SelectOption(label="Week 10", value="week_10"),
            discord.SelectOption(label="Week 11", value="week_11"),
            discord.SelectOption(label="Week 12", value="week_12"),
            discord.SelectOption(label="Week 13", value="week_13"),
            discord.SelectOption(label="Week 14", value="week_14"),
            discord.SelectOption(label="Week 15", value="week_15"),
            discord.SelectOption(label="Bowl Games", value="bowl_games"),
        ],
    )
    async def week_callback(self, interaction: discord.Interaction, select: Select):
        week = select.values[0]

        try:
            image_path = await self.generate_schedule_image(
                interaction.guild, week, "NCAA"
            )

            # Find member role and mention it
            member_role = None
            for role in interaction.guild.roles:
                if "member" in role.name.lower() or "members" in role.name.lower():
                    member_role = role
                    break

            mention_text = f"{member_role.mention} " if member_role else ""
            await interaction.response.send_message(
                f"{mention_text}Here's your schedule!", file=discord.File(image_path)
            )
            os.remove(image_path)  # Clean up temp file

        except Exception as e:
            logger.error(f"Error generating schedule image: {e}")
            await interaction.response.send_message(
                "Error generating schedule image.", ephemeral=True
            )

    async def generate_placeholder_schedule_image(self, guild, week: str):
        """Generate placeholder schedule image for NCAA"""
        try:
            # Create base image using cog reference
            if self.cog:
                image = self.cog._create_schedule_base_image(guild, "NCAA", week)
            else:
                # Fallback: create basic image
                image = Image.new("RGB", (1200, 1600), color="#1a1a1a")
                draw = ImageDraw.Draw(image)
                draw.text(
                    (600, 800),
                    "Error: Could not access image creation method",
                    fill="#ffffff",
                    anchor="mm",
                )

            draw = ImageDraw.Draw(image)

            # Add placeholder text
            try:
                text_font = ImageFont.truetype(
                    "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 32
                )
            except:
                text_font = ImageFont.load_default()

            draw.text(
                (600, 800),
                f"NCAA Schedule for {week.replace('_', ' ').title()}",
                font=text_font,
                fill="#ffffff",
                anchor="mm",
            )
            draw.text(
                (600, 850), "Coming Soon!", font=text_font, fill="#ffffff", anchor="mm"
            )

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webp")
            image.save(temp_file.name, "PNG")
            temp_file.close()

            return temp_file.name
        except Exception as e:
            logger.error(f"Error generating placeholder schedule image: {e}")
            raise


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _create_schedule_base_image(self, guild, league="NFL", week="WEEK 1"):
        """Create the base image with branding and layout"""
        # Create base image with enhanced gradient background
        image = Image.new("RGB", (1200, 1600), color="#0a0a0a")
        draw = ImageDraw.Draw(image)

        # Create enhanced gradient background with more vibrant colors
        for y in range(1600):
            # Create a more vibrant gradient from deep blue to purple to dark red
            progress = y / 1600
            if progress < 0.5:
                # First half: deep blue to purple
                r = int(10 + (progress * 2) * 60)  # 10 to 70
                g = int(10 + (progress * 2) * 30)  # 10 to 40
                b = int(30 + (progress * 2) * 80)  # 30 to 110
            else:
                # Second half: purple to dark red
                r = int(70 + ((progress - 0.5) * 2) * 50)  # 70 to 120
                g = int(40 + ((progress - 0.5) * 2) * 20)  # 40 to 60
                b = int(110 + ((progress - 0.5) * 2) * 40)  # 110 to 150
            color = (r, g, b)
            draw.line([(0, y), (1200, y)], fill=color)

        # Load enhanced fonts with better sizing
        try:
            title_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 48
            )
            subtitle_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 32
            )
            text_font = ImageFont.truetype(
                "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 24
            )
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()

        # Add large faded league logo as background with enhanced styling
        try:
            league_logo_path = f"../../../StaticFiles/DBSBM/static/logos/leagues/{league.upper()}/{league.lower()}.webp"
            if os.path.exists(league_logo_path):
                league_logo = Image.open(league_logo_path)
                # Resize to be large and centered
                league_logo = league_logo.resize((900, 900))
                # Create a more faded version for better text readability
                faded_logo = league_logo.copy()
                faded_logo.putalpha(20)  # Very transparent (20/255)
                # Center the logo
                x_offset = (1200 - 900) // 2
                y_offset = (1600 - 900) // 2
                image.paste(faded_logo, (x_offset, y_offset), faded_logo)
                logger.info(f"Added faded {league} logo background")
        except Exception as e:
            logger.warning(f"Could not load league logo background: {e}")

        # Add header section with proper spacing
        header_y_start = 50

        # Add logos first (top row)
        try:
            # --- Bot Logo ---
            ptp_logo_path = "../../../StaticFiles/DBSBM/static/logos/default_image.webp"
            if os.path.exists(ptp_logo_path):
                ptp_logo = Image.open(ptp_logo_path)
                ptp_logo = ptp_logo.resize((70, 70))  # Slightly larger
                if ptp_logo.mode != "RGBA":
                    ptp_logo = ptp_logo.convert("RGBA")
                # Position logo at top left
                logo_x = 400 - 35
                logo_y = header_y_start
                # Add subtle glow effect
                draw.ellipse(
                    [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                    fill="#ffffff",
                    outline="#4a90e2",
                    width=3,
                )
                image.paste(ptp_logo, (logo_x, logo_y), ptp_logo)
                logger.info(f"Added Bet Tracking Bot logo from {ptp_logo_path}")
            else:
                logger.warning(f"Bet Tracking Bot logo not found at {ptp_logo_path}")
                logo_x = 400 - 35
                logo_y = header_y_start
                draw.ellipse(
                    [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                    fill="#ff0000",
                    outline="#ffffff",
                    width=3,
                )

            # --- Guild Logo ---
            if guild:
                guild_logo_paths = [
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/default_image.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/background_image.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/logo.webp",
                    f"../../../StaticFiles/DBSBM/static/guilds/{guild.id}/guild_logo.webp",
                ]
                guild_logo_loaded = False
                for guild_logo_path in guild_logo_paths:
                    if os.path.exists(guild_logo_path):
                        try:
                            guild_logo = Image.open(guild_logo_path)
                            guild_logo = guild_logo.resize((70, 70))  # Slightly larger
                            if guild_logo.mode != "RGBA":
                                guild_logo = guild_logo.convert("RGBA")
                            # Position logo at top right
                            logo_x = 840 - 35
                            logo_y = header_y_start
                            # Add subtle glow effect
                            draw.ellipse(
                                [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                                fill="#ffffff",
                                outline="#4a90e2",
                                width=3,
                            )
                            image.paste(guild_logo, (logo_x, logo_y), guild_logo)
                            logger.info(f"Added guild logo from {guild_logo_path}")
                            guild_logo_loaded = True
                            break
                        except Exception as e:
                            logger.warning(
                                f"Failed to load guild logo from {guild_logo_path}: {e}"
                            )
                            continue
                if not guild_logo_loaded:
                    logo_x = 840 - 35
                    logo_y = header_y_start
                    draw.ellipse(
                        [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                        fill="#4a90e2",
                        outline="#ffffff",
                        width=3,
                    )
            else:
                logo_x = 840 - 35
                logo_y = header_y_start
                draw.ellipse(
                    [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                    fill="#666666",
                    outline="#ffffff",
                    width=3,
                )
        except Exception as e:
            logger.error(f"Could not load logos: {e}")
            # Add fallback circles for debugging
            logo_x = 400 - 35
            logo_y = header_y_start
            draw.ellipse(
                [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                fill="#ff0000",
                outline="#ffffff",
                width=3,
            )
            logo_x = 840 - 35
            logo_y = header_y_start
            draw.ellipse(
                [logo_x - 5, logo_y - 5, logo_x + 75, logo_y + 75],
                fill="#00ff00",
                outline="#ffffff",
                width=3,
            )

        # Add text below logos with proper spacing
        text_y_start = header_y_start + 100  # 100px below logos

        # Add Bet Tracking Bot branding at 1/3 position (left side)
        draw.text(
            (400, text_y_start),
            "Bet Tracking Bot",
            font=title_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Add guild name at 2/3 position (right side)
        if guild:
            guild_name_text = f"{guild.name.upper()}"
        else:
            guild_name_text = "BET TRACKING BOT GUILD"
        draw.text(
            (840, text_y_start),
            guild_name_text,
            font=title_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Add league and schedule type info centered below
        schedule_type = week.replace("_", " ").title()
        draw.text(
            (600, text_y_start + 50),
            f"{league.upper()} {schedule_type} SCHEDULE",
            font=subtitle_font,
            fill="#ffffff",
            anchor="mm",
        )

        # Add copyright watermark
        current_year = datetime.now().year
        draw.text(
            (600, 1580),
            f"© Bet Tracking Bot {current_year}",
            font=text_font,
            fill="#666666",
            anchor="mm",
        )

        return image

    @app_commands.command(name="schedule", description="View sports schedules")
    async def schedule_command(self, interaction: discord.Interaction):
        """Main schedule command that initiates the flow"""
        logger.info(
            f"Schedule command initiated by {interaction.user.name} in guild {interaction.guild_id}"
        )

        # Create the initial view with League Schedule vs Team Schedule buttons
        view = ScheduleTypeSelect(self)
        await interaction.response.send_message(
            "Choose schedule type:", view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ScheduleCog(bot))
