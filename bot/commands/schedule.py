"""Schedule command for viewing upcoming games with dropdown selection."""

import logging
import os
import tempfile
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")

TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))


class SportSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Football",
                description="NFL, NCAA Football",
                value="football",
                emoji="🏈"
            ),
            discord.SelectOption(
                label="Basketball", 
                description="NBA, NCAA Basketball",
                value="basketball",
                emoji="🏀"
            ),
            discord.SelectOption(
                label="Baseball",
                description="MLB, NPB, KBO",
                value="baseball", 
                emoji="⚾"
            ),
            discord.SelectOption(
                label="Hockey",
                description="NHL, KHL",
                value="hockey",
                emoji="🏒"
            ),
            discord.SelectOption(
                label="Soccer",
                description="Premier League, La Liga, Serie A",
                value="soccer",
                emoji="⚽"
            ),
            discord.SelectOption(
                label="MMA",
                description="UFC, Bellator",
                value="mma",
                emoji="🥊"
            )
        ]
        super().__init__(
            placeholder="Select a sport category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.sport = self.values[0]
        
        # Create league selection dropdown based on sport
        league_options = self._get_league_options(self.values[0])
        league_select = LeagueSelect(league_options)
        
        # Update the view with league selection
        view.clear_items()
        view.add_item(league_select)
        
        await interaction.response.edit_message(
            content=f"Selected sport: **{self.values[0].title()}**\nNow select a league:",
            view=view
        )

    def _get_league_options(self, sport: str) -> list:
        """Get league options based on selected sport."""
        league_map = {
            "football": [
                ("NFL", "NFL", "🏈"),
                ("NCAA Football", "NCAA", "🏈")
            ],
            "basketball": [
                ("NBA", "NBA", "🏀"),
                ("NCAA Basketball", "NCAA", "🏀")
            ],
            "baseball": [
                ("MLB", "MLB", "⚾"),
                ("NPB", "NPB", "⚾"),
                ("KBO", "KBO", "⚾")
            ],
            "hockey": [
                ("NHL", "NHL", "🏒"),
                ("KHL", "KHL", "🏒")
            ],
            "soccer": [
                ("Premier League", "EPL", "⚽"),
                ("La Liga", "LA_LIGA", "⚽"),
                ("Serie A", "SERIE_A", "⚽"),
                ("Bundesliga", "BUNDESLIGA", "⚽")
            ],
            "mma": [
                ("UFC", "UFC", "🥊"),
                ("Bellator", "BELLATOR", "🥊")
            ]
        }
        return league_map.get(sport, [])


class LeagueSelect(discord.ui.Select):
    def __init__(self, league_options: list):
        options = [
            discord.SelectOption(
                label=label,
                description=f"{label} schedule",
                value=value,
                emoji=emoji
            ) for label, value, emoji in league_options
        ]
        super().__init__(
            placeholder="Select a league...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.league = self.values[0]
        
        # Generate the schedule image
        await interaction.response.edit_message(
            content="⏳ Generating schedule image...",
            view=None
        )
        
        # Generate the schedule image
        image_path = await view.generate_schedule_image(
            interaction.guild,
            view.sport,
            view.league
        )
        
        if image_path:
            await interaction.followup.send(
                f"**{view.sport.title()} - {view.league} Schedule**",
                file=discord.File(image_path),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ Failed to generate schedule image.",
                ephemeral=True
            )


class ScheduleView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        self.sport = None
        self.league = None
        self.add_item(SportSelect())

    async def generate_schedule_image(self, guild, sport: str, league: str) -> Optional[str]:
        """Generate schedule image for the selected sport and league."""
        try:
            # For now, focus on NFL 2025-2026
            if sport == "football" and league == "NFL":
                return await self.cog.generate_nfl_schedule_image(guild)
            else:
                # Placeholder for other leagues
                return await self.cog.generate_placeholder_schedule_image(guild, sport, league)
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None


class ScheduleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fonts_dir = os.path.join(self.base_dir, "assets", "fonts")
        self.logos_dir = os.path.join(self.base_dir, "static", "logos")

    @app_commands.command(
        name="schedule", 
        description="View schedule for different sports and leagues"
    )
    async def schedule_command(self, interaction: discord.Interaction):
        """Display a schedule with sport and league selection."""
        logger.info(
            f"Schedule command initiated by {interaction.user} in guild {interaction.guild_id}"
        )
        
        view = ScheduleView(self)
        await interaction.response.send_message(
            "**PlayTracker Pro Schedule**\nSelect a sport category:",
            view=view,
            ephemeral=True
        )

    async def generate_nfl_schedule_image(self, guild) -> Optional[str]:
        """Generate NFL 2025-2026 schedule image."""
        try:
            # Create the image
            image = self._create_schedule_base_image(guild)
            
            # Add NFL schedule data
            self._add_nfl_schedule_data(image, guild)
            
            # Save the image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image.save(temp_file.name, 'PNG')
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error generating NFL schedule image: {e}", exc_info=True)
            return None

    def _create_schedule_base_image(self, guild) -> Image.Image:
        """Create the base schedule image with branding."""
        # Create a large image for the schedule
        width, height = 1200, 1600
        image = Image.new('RGB', (width, height), '#0f1419')
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        title_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 48)
        subtitle_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 36)
        header_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 24)
        text_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 18)
        
        # Load default image (main background)
        default_image_path = os.path.join(self.logos_dir, "default_image.png")
        if os.path.exists(default_image_path):
            default_img = Image.open(default_image_path).convert('RGBA')
            # Resize and position as background
            default_img = default_img.resize((400, 400))
            image.paste(default_img, (50, 100), default_img)
        
        # Add PlayTracker Pro branding
        draw.text((50, 50), "PlayTracker Pro", font=title_font, fill='#ffffff')
        
        # Add guild name where "Schedule" would be
        guild_name = guild.name if guild else "Unknown Guild"
        draw.text((50, 120), f"{guild_name} Schedule", font=subtitle_font, fill='#ffffff')
        
        # Add NFL logo
        nfl_logo_path = os.path.join(self.logos_dir, "leagues", "FOOTBALL", "NFL", "nfl.png")
        if os.path.exists(nfl_logo_path):
            nfl_logo = Image.open(nfl_logo_path).convert('RGBA')
            nfl_logo = nfl_logo.resize((100, 100))
            image.paste(nfl_logo, (1050, 50), nfl_logo)
        
        # Add guild logo if available
        guild_logo_path = os.path.join(self.logos_dir, "guilds", str(guild.id), "guild_logo.png")
        if os.path.exists(guild_logo_path):
            guild_logo = Image.open(guild_logo_path).convert('RGBA')
            guild_logo = guild_logo.resize((100, 100))
            image.paste(guild_logo, (1050, 170), guild_logo)
        
        return image

    def _add_nfl_schedule_data(self, image: Image.Image, guild):
        """Add NFL 2025-2026 schedule data to the image."""
        draw = ImageDraw.Draw(image)
        header_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 24)
        text_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 18)
        
        # Add schedule title
        draw.text((500, 150), "2025-2026 NFL Schedule", font=header_font, fill='#ffffff')
        
        # Add Week 1 games (sample data)
        week1_games = [
            ("THURSDAY, SEPTEMBER 4, 2025", "DALLAS @ PHILADELPHIA", "8:20 PM", "NBC"),
            ("FRIDAY, SEPTEMBER 5, 2025", "KANSAS CITY @ LOS ANGELES (C)", "8:00 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "TAMPA BAY @ ATLANTA", "1:00 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "CINCINNATI @ CLEVELAND", "1:00 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "MIAMI @ INDIANAPOLIS", "1:00 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "LAS VEGAS @ NEW ENGLAND", "1:00 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "ARIZONA @ NEW ORLEANS", "1:00 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "PITTSBURGH @ NEW YORK (J)", "1:00 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "NEW YORK (G) @ WASHINGTON", "1:00 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "CAROLINA @ JACKSONVILLE", "1:00 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "TENNESSEE @ DENVER", "4:05 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "SAN FRANCISCO @ SEATTLE", "4:05 PM", "FOX"),
            ("SUNDAY, SEPTEMBER 7, 2025", "DETROIT @ GREEN BAY", "4:25 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "LOS ANGELES (R) @ CHICAGO", "4:25 PM", "CBS"),
            ("SUNDAY, SEPTEMBER 7, 2025", "BALTIMORE @ BUFFALO", "8:20 PM", "NBC"),
            ("MONDAY, SEPTEMBER 8, 2025", "MINNESOTA @ CINCINNATI", "8:15 PM", "ESPN")
        ]
        
        y_position = 250
        for date, matchup, time, channel in week1_games:
            # Draw date
            draw.text((500, y_position), date, font=text_font, fill='#ffffff')
            # Draw matchup
            draw.text((500, y_position + 25), matchup, font=text_font, fill='#ffffff')
            # Draw time and channel
            draw.text((500, y_position + 50), f"{time} - {channel}", font=text_font, fill='#ffffff')
            y_position += 100

    async def generate_placeholder_schedule_image(self, guild, sport: str, league: str) -> Optional[str]:
        """Generate placeholder schedule image for other leagues."""
        try:
            # Create a simple placeholder image
            width, height = 800, 600
            image = Image.new('RGB', (width, height), '#0f1419')
            draw = ImageDraw.Draw(image)
            
            title_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 36)
            text_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 24)
            
            # Add branding
            draw.text((50, 50), "PlayTracker Pro", font=title_font, fill='#ffffff')
            
            guild_name = guild.name if guild else "Unknown Guild"
            draw.text((50, 120), f"{guild_name} Schedule", font=title_font, fill='#ffffff')
            
            # Add placeholder text
            draw.text((50, 250), f"Schedule for {sport.title()} - {league}", font=text_font, fill='#ffffff')
            draw.text((50, 300), "Coming soon...", font=text_font, fill='#ffffff')
            
            # Save the image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image.save(temp_file.name, 'PNG')
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error generating placeholder schedule image: {e}", exc_info=True)
            return None

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for schedule commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need permissions to use this command.", ephemeral=True
            )
        else:
            logger.error(f"Error in schedule command: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduleCog(bot))
    logger.info("ScheduleCog loaded")
    # Register command to specific guild for testing
    try:
        if TEST_GUILD_ID:
            test_guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=test_guild)
            # await bot.tree.sync(guild=test_guild)  # DISABLED: Prevent rate limit
            logger.info(
                f"Successfully synced schedule command to test guild {TEST_GUILD_ID}"
            )
        else:
            logger.warning(
                "TEST_GUILD_ID not set, command will not be synced to test guild"
            )
    except Exception as e:
        logger.error(f"Failed to sync schedule command: {e}")
