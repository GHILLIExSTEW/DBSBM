"""Schedule command for viewing upcoming games with dropdown selection."""

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Button
import logging
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
from datetime import datetime

# Import the league schedule data
from bot.data.nfl_schedule_2025_2026 import NFL_SCHEDULE_2025_2026_PART1

# Import team schedules
from bot.data.league_schedules.nfl.teams.buffalo_bills_schedule import BUFFALO_BILLS_SCHEDULE
from bot.data.league_schedules.nfl.teams.miami_dolphins_schedule import MIAMI_DOLPHINS_SCHEDULE
from bot.data.league_schedules.nfl.teams.new_england_patriots_schedule import NEW_ENGLAND_PATRIOTS_SCHEDULE
from bot.data.league_schedules.nfl.teams.new_york_jets_schedule import NEW_YORK_JETS_SCHEDULE
from bot.data.league_schedules.nfl.teams.baltimore_ravens_schedule import BALTIMORE_RAVENS_SCHEDULE
from bot.data.league_schedules.nfl.teams.cincinnati_bengals_schedule import CINCINNATI_BENGALS_SCHEDULE
from bot.data.league_schedules.nfl.teams.cleveland_browns_schedule import CLEVELAND_BROWNS_SCHEDULE
from bot.data.league_schedules.nfl.teams.pittsburgh_steelers_schedule import PITTSBURGH_STEELERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.houston_texans_schedule import HOUSTON_TEXANS_SCHEDULE
from bot.data.league_schedules.nfl.teams.indianapolis_colts_schedule import INDIANAPOLIS_COLTS_SCHEDULE
from bot.data.league_schedules.nfl.teams.jacksonville_jaguars_schedule import JACKSONVILLE_JAGUARS_SCHEDULE
from bot.data.league_schedules.nfl.teams.tennessee_titans_schedule import TENNESSEE_TITANS_SCHEDULE
from bot.data.league_schedules.nfl.teams.denver_broncos_schedule import DENVER_BRONCOS_SCHEDULE
from bot.data.league_schedules.nfl.teams.kansas_city_chiefs_schedule import KANSAS_CITY_CHIEFS_SCHEDULE
from bot.data.league_schedules.nfl.teams.las_vegas_raiders_schedule import LAS_VEGAS_RAIDERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.los_angeles_chargers_schedule import LOS_ANGELES_CHARGERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.dallas_cowboys_schedule import DALLAS_COWBOYS_SCHEDULE
from bot.data.league_schedules.nfl.teams.new_york_giants_schedule import NEW_YORK_GIANTS_SCHEDULE
from bot.data.league_schedules.nfl.teams.philadelphia_eagles_schedule import PHILADELPHIA_EAGLES_SCHEDULE
from bot.data.league_schedules.nfl.teams.washington_commanders_schedule import WASHINGTON_COMMANDERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.chicago_bears_schedule import CHICAGO_BEARS_SCHEDULE
from bot.data.league_schedules.nfl.teams.detroit_lions_schedule import DETROIT_LIONS_SCHEDULE
from bot.data.league_schedules.nfl.teams.green_bay_packers_schedule import GREEN_BAY_PACKERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.minnesota_vikings_schedule import MINNESOTA_VIKINGS_SCHEDULE
from bot.data.league_schedules.nfl.teams.atlanta_falcons_schedule import ATLANTA_FALCONS_SCHEDULE
from bot.data.league_schedules.nfl.teams.carolina_panthers_schedule import CAROLINA_PANTHERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.new_orleans_saints_schedule import NEW_ORLEANS_SAINTS_SCHEDULE
from bot.data.league_schedules.nfl.teams.tampa_bay_buccaneers_schedule import TAMPA_BAY_BUCCANEERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.arizona_cardinals_schedule import ARIZONA_CARDINALS_SCHEDULE
from bot.data.league_schedules.nfl.teams.los_angeles_rams_schedule import LOS_ANGELES_RAMS_SCHEDULE
from bot.data.league_schedules.nfl.teams.san_francisco_49ers_schedule import SAN_FRANCISCO_49ERS_SCHEDULE
from bot.data.league_schedules.nfl.teams.seattle_seahawks_schedule import SEATTLE_SEAHAWKS_SCHEDULE

logger = logging.getLogger(__name__)

# Use the NFL schedule data
NFL_SCHEDULE_2025_2026 = NFL_SCHEDULE_2025_2026_PART1

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
    "Seattle Seahawks": SEATTLE_SEAHAWKS_SCHEDULE
}

class ScheduleTypeSelect(View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="League Schedule", style=discord.ButtonStyle.primary)
    async def league_schedule(self, interaction: discord.Interaction, button: Button):
        # Create league selection view
        view = LeagueSelect()
        await interaction.response.edit_message(content="Select a league:", view=view)
        
    @discord.ui.button(label="Team Schedule", style=discord.ButtonStyle.secondary)
    async def team_schedule(self, interaction: discord.Interaction, button: Button):
        # Create team selection view
        view = TeamSelect()
        await interaction.response.edit_message(content="Select a team:", view=view)

class TeamSelect(View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.select(
        placeholder="Choose a team...",
        options=[
            discord.SelectOption(label="Buffalo Bills", value="Buffalo Bills"),
            discord.SelectOption(label="Miami Dolphins", value="Miami Dolphins"),
            discord.SelectOption(label="New England Patriots", value="New England Patriots"),
            discord.SelectOption(label="New York Jets", value="New York Jets"),
            discord.SelectOption(label="Baltimore Ravens", value="Baltimore Ravens"),
            discord.SelectOption(label="Cincinnati Bengals", value="Cincinnati Bengals"),
            discord.SelectOption(label="Cleveland Browns", value="Cleveland Browns"),
            discord.SelectOption(label="Pittsburgh Steelers", value="Pittsburgh Steelers"),
            discord.SelectOption(label="Houston Texans", value="Houston Texans"),
            discord.SelectOption(label="Indianapolis Colts", value="Indianapolis Colts"),
            discord.SelectOption(label="Jacksonville Jaguars", value="Jacksonville Jaguars"),
            discord.SelectOption(label="Tennessee Titans", value="Tennessee Titans"),
            discord.SelectOption(label="Denver Broncos", value="Denver Broncos"),
            discord.SelectOption(label="Kansas City Chiefs", value="Kansas City Chiefs"),
            discord.SelectOption(label="Las Vegas Raiders", value="Las Vegas Raiders"),
            discord.SelectOption(label="Los Angeles Chargers", value="Los Angeles Chargers"),
            discord.SelectOption(label="Dallas Cowboys", value="Dallas Cowboys"),
            discord.SelectOption(label="New York Giants", value="New York Giants"),
            discord.SelectOption(label="Philadelphia Eagles", value="Philadelphia Eagles"),
            discord.SelectOption(label="Washington Commanders", value="Washington Commanders"),
            discord.SelectOption(label="Chicago Bears", value="Chicago Bears"),
            discord.SelectOption(label="Detroit Lions", value="Detroit Lions"),
            discord.SelectOption(label="Green Bay Packers", value="Green Bay Packers"),
            discord.SelectOption(label="Minnesota Vikings", value="Minnesota Vikings"),
            discord.SelectOption(label="Atlanta Falcons", value="Atlanta Falcons"),
            discord.SelectOption(label="Carolina Panthers", value="Carolina Panthers"),
            discord.SelectOption(label="New Orleans Saints", value="New Orleans Saints"),
            discord.SelectOption(label="Tampa Bay Buccaneers", value="Tampa Bay Buccaneers"),
            discord.SelectOption(label="Arizona Cardinals", value="Arizona Cardinals"),
            discord.SelectOption(label="Los Angeles Rams", value="Los Angeles Rams"),
            discord.SelectOption(label="San Francisco 49ers", value="San Francisco 49ers"),
            discord.SelectOption(label="Seattle Seahawks", value="Seattle Seahawks")
        ]
    )
    async def team_callback(self, interaction: discord.Interaction, select: Select):
        team_name = select.values[0]
        team_schedule = TEAM_SCHEDULES[team_name]
        
        # Create week selection view for team schedule
        view = TeamWeekSelect(team_name, team_schedule)
        await interaction.response.edit_message(content=f"Select a week for {team_name}:", view=view)

class TeamWeekSelect(View):
    def __init__(self, team_name: str, team_schedule: dict):
        super().__init__(timeout=60)
        self.team_name = team_name
        self.team_schedule = team_schedule
        
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
            discord.SelectOption(label="Week 18", value="week_18")
        ]
    )
    async def week_callback(self, interaction: discord.Interaction, select: Select):
        week = select.values[0]
        game_info = self.team_schedule[week]
        
        # Generate team schedule image
        try:
            image_path = await self.generate_team_schedule_image(interaction.guild, self.team_name, week, game_info)
            await interaction.response.send_message(file=discord.File(image_path))
            os.remove(image_path)  # Clean up temp file
        except Exception as e:
            logger.error(f"Error generating team schedule image: {e}")
            await interaction.response.send_message("Error generating team schedule image.", ephemeral=True)
    
    async def generate_team_schedule_image(self, guild, team_name: str, week: str, game_info: tuple):
        # Create base image similar to league schedule
        image = self._create_schedule_base_image(guild)
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        try:
            header_font = ImageFont.truetype("bot/static/fonts/Roboto-Bold.ttf", 36)
            text_font = ImageFont.truetype("bot/static/fonts/Roboto-Regular.ttf", 24)
            small_font = ImageFont.truetype("bot/static/fonts/Roboto-Regular.ttf", 18)
        except:
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Get image dimensions
        width, height = image.size
        
        # Create white semi-transparent overlay box
        overlay = Image.new('RGBA', (width - 100, height - 500), (255, 255, 255, 100))
        image.paste(overlay, (50, 450), overlay)
        
        # Add team and week title
        week_title = week.replace('_', ' ').title()
        draw.text((100, 500), f"{team_name} - {week_title}", font=header_font, fill='#000000')
        
        # Add game information
        day, date, opponent, time, network = game_info
        
        if day == "BYE WEEK":
            draw.text((100, 600), "BYE WEEK", font=text_font, fill='#666666')
        else:
            draw.text((100, 600), f"{day}, {date}", font=small_font, fill='#000000')
            draw.text((100, 625), opponent, font=text_font, fill='#000000')
            draw.text((100, 650), f"{time} - {network}", font=small_font, fill='#000000')
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image.save(temp_file.name)
        return temp_file.name
    
    def _create_schedule_base_image(self, guild):
        # Create base image (same as league schedule)
        image = Image.new('RGB', (1200, 1600), color='#1a1a1a')
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 32)
            text_font = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Add PlayTracker Pro branding
        draw.text((600, 50), "PlayTracker Pro", font=title_font, fill='#ffffff', anchor="mm")
        
        # Add guild name
        guild_name = guild.name if guild else "Unknown Guild"
        draw.text((600, 120), f"{guild_name} Team Schedule", font=subtitle_font, fill='#ffffff', anchor="mm")
        
        # Add copyright watermark
        current_year = datetime.now().year
        draw.text((600, 1550), f"© PlayTracker Pro {current_year}", font=text_font, fill='#666666', anchor="mm")
        
        return image

class SportSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Football", value="football", description="NFL, NCAA, etc."),
            discord.SelectOption(label="Basketball", value="basketball", description="NBA, NCAA, etc."),
            discord.SelectOption(label="Baseball", value="baseball", description="MLB, etc."),
            discord.SelectOption(label="Hockey", value="hockey", description="NHL, etc."),
            discord.SelectOption(label="Soccer", value="soccer", description="Premier League, MLS, etc.")
        ]
        super().__init__(placeholder="Choose a sport...", options=options)

    async def callback(self, interaction: discord.Interaction):
        sport = self.values[0]
        
        if sport == "football":
            view = LeagueSelect()
            await interaction.response.edit_message(content="Select a league:", view=view)
        else:
            await interaction.response.edit_message(content=f"Schedule data for {sport} is not available yet.", view=None)

class LeagueSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="NFL", value="nfl", description="National Football League"),
            discord.SelectOption(label="NCAA Football", value="ncaa_football", description="College Football")
        ]
        super().__init__(placeholder="Choose a league...", options=options)

    async def callback(self, interaction: discord.Interaction):
        league = self.values[0]
        
        if league == "nfl":
            view = WeekSelect("nfl")
            await interaction.response.edit_message(content="Select a week:", view=view)
        elif league == "ncaa_football":
            view = WeekSelect("ncaa_football")
            await interaction.response.edit_message(content="Select a week:", view=view)
        else:
            await interaction.response.edit_message(content=f"Schedule data for {league} is not available yet.", view=None)

class WeekSelect(Select):
    def __init__(self, league: str):
        self.league = league
        
        if league == "nfl":
            options = [
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
                discord.SelectOption(label="Championship", value="championship")
            ]
        elif league == "ncaa_football":
            options = [
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
                discord.SelectOption(label="Bowl Games", value="bowl_games")
            ]
        else:
            options = []
            
        super().__init__(placeholder="Choose a week...", options=options)

    async def callback(self, interaction: discord.Interaction):
        week = self.values[0]
        
        try:
            if self.league == "nfl":
                image_path = await self.generate_nfl_schedule_image(interaction.guild, week)
            elif self.league == "ncaa_football":
                image_path = await self.generate_placeholder_schedule_image(interaction.guild, week)
            else:
                await interaction.response.send_message("League not supported yet.", ephemeral=True)
                return
                
            await interaction.response.send_message(file=discord.File(image_path))
            os.remove(image_path)  # Clean up temp file
            
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}")
            await interaction.response.send_message("Error generating schedule image.", ephemeral=True)

    async def generate_nfl_schedule_image(self, guild, week: str):
        """Generate NFL schedule image for the specified week"""
        try:
            # Create base image
            image = self._create_schedule_base_image(guild)
            
            # Add schedule data
            self._add_nfl_schedule_data(image, week)
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image.save(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error generating NFL schedule image: {e}")
            raise

    async def generate_placeholder_schedule_image(self, guild, week: str):
        """Generate placeholder schedule image for other leagues"""
        try:
            # Create base image
            image = self._create_schedule_base_image(guild)
            draw = ImageDraw.Draw(image)
            
            # Load fonts
            try:
                header_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 36)
                text_font = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 24)
            except:
                header_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Add placeholder text
            draw.text((600, 800), f"Schedule data for {week} coming soon!", font=header_font, fill='#ffffff', anchor="mm")
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image.save(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error generating placeholder schedule image: {e}")
            raise

    def _create_schedule_base_image(self, guild):
        """Create the base image with branding and layout"""
        # Create base image
        image = Image.new('RGB', (1200, 1600), color='#1a1a1a')
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 32)
            text_font = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Add PlayTracker Pro branding
        draw.text((600, 50), "PlayTracker Pro", font=title_font, fill='#ffffff', anchor="mm")
        
        # Add guild name
        guild_name = guild.name if guild else "Unknown Guild"
        draw.text((600, 120), f"{guild_name} Schedule", font=subtitle_font, fill='#ffffff', anchor="mm")
        
        # Add copyright watermark
        current_year = datetime.now().year
        draw.text((600, 1550), f"© PlayTracker Pro {current_year}", font=text_font, fill='#666666', anchor="mm")
        
        return image

    def _add_nfl_schedule_data(self, image, week: str):
        """Add NFL schedule data to the image"""
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        try:
            header_font = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 36)
            text_font = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 24)
            small_font = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 18)
        except:
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Get image dimensions
        width, height = image.size
        
        # Get games for the selected week from external data
        games = NFL_SCHEDULE_2025_2026.get(week, [])
        if not games:
            # If no data for this week, show placeholder
            draw.text((100, 500), f"No schedule data available for {week.replace('_', ' ').title()}", 
                     font=header_font, fill='#000000')
            return
        
        # Create white semi-transparent overlay box
        overlay = Image.new('RGBA', (width - 100, height - 500), (255, 255, 255, 100))
        image.paste(overlay, (50, 450), overlay)
        
        # Add week title
        week_title = week.replace('_', ' ').title()
        draw.text((100, 500), f"NFL 2025-2026 - {week_title}", font=header_font, fill='#000000')
        
        # Add games
        y_position = 550
        for day, date, matchup, time, channel in games:
            # Check if this is a bye week entry
            if day == "BYE WEEK":
                # Draw bye week in different style
                draw.text((100, y_position), f"BYE WEEK: {matchup}", font=text_font, fill='#666666')
                y_position += 60
            else:
                # Draw regular game
                draw.text((100, y_position), f"{day}, {date}", font=small_font, fill='#000000')
                draw.text((100, y_position + 25), matchup, font=text_font, fill='#000000')
                draw.text((100, y_position + 50), f"{time} - {channel}", font=small_font, fill='#000000')
                y_position += 100
            
            # Add separator line (but not after bye weeks)
            if day != "BYE WEEK" and y_position < height - 200:
                draw.line([(100, y_position - 10), (width - 100, y_position - 10)], 
                         fill='#cccccc', width=1)

class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="schedule", description="View sports schedules")
    async def schedule_command(self, interaction: discord.Interaction):
        """Main schedule command that initiates the flow"""
        logger.info(f"Schedule command initiated by {interaction.user.name} in guild {interaction.guild_id}")
        
        # Create the initial view with League Schedule vs Team Schedule buttons
        view = ScheduleTypeSelect()
        await interaction.response.send_message("Choose schedule type:", view=view)

async def setup(bot):
    await bot.add_cog(ScheduleCog(bot))
