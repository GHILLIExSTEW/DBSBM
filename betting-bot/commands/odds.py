import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class OddsDropdown(discord.ui.Select):
    def __init__(
        self,
        games: List[Dict],
        page: int,
        page_size: int,
        total_games: int,
        parent_view,
    ):
        self.games = games
        self.page = page
        self.page_size = page_size
        self.total_games = total_games
        self.parent_view = parent_view
        options = []
        start = page * page_size
        end = min(start + page_size, total_games)
        for i, g in enumerate(games, start):
            label = f"{g['home_team_name']} vs {g['away_team_name']}"
            value = str(i)
            options.append(discord.SelectOption(label=label[:100], value=value))
        if page > 0:
            options.insert(
                0, discord.SelectOption(label="⬅️ Previous", value="previous")
            )
        if end < total_games:
            options.append(discord.SelectOption(label="Next ➡️", value="next"))
        super().__init__(
            placeholder="Select a game or page...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "next":
            self.parent_view.page += 1
            await self.parent_view.update_dropdown(interaction)
        elif value == "previous":
            self.parent_view.page -= 1
            await self.parent_view.update_dropdown(interaction)
        else:
            idx = int(value)
            game = self.parent_view.all_games[idx]
            embed = await self.parent_view.cog.create_odds_embed_for_game(game)
            await interaction.response.edit_message(embed=embed, view=None)


class OddsDropdownView(discord.ui.View):
    def __init__(self, cog, all_games: List[Dict], page: int = 0, page_size: int = 23):
        super().__init__(timeout=120)
        self.cog = cog
        self.all_games = all_games
        self.page = page
        self.page_size = page_size
        self.update_dropdown_sync()

    def update_dropdown_sync(self):
        start = self.page * self.page_size
        end = min(start + self.page_size, len(self.all_games))
        games = self.all_games[start:end]
        logger.info(f"Dropdown page {self.page}: displaying games {start} to {end}:")
        for i, g in enumerate(games, start):
            logger.info(f"  {i}: {g['home_team_name']} vs {g['away_team_name']}")
        self.clear_items()
        self.add_item(
            OddsDropdown(games, self.page, self.page_size, len(self.all_games), self)
        )

    async def update_dropdown(self, interaction: discord.Interaction):
        self.update_dropdown_sync()
        await interaction.response.edit_message(view=self)


class Odds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_sports_key = os.getenv("API_KEY")
        if not self.api_sports_key:
            logger.warning("API-Sports key not found in environment variables")

    @app_commands.command(
        name="odds", description="Browse and get odds for upcoming games"
    )
    async def odds(self, interaction: discord.Interaction):
        if not self.api_sports_key:
            await interaction.response.send_message(
                "❌ API-Sports key not configured!", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        games = await self.get_upcoming_games()
        logger.info(f"Games fetched from DB for dropdown: {len(games)} games")
        for i, g in enumerate(games):
            logger.info(f"  {i}: {g['home_team_name']} vs {g['away_team_name']}")
        if not games:
            await interaction.followup.send("No games found.", ephemeral=True)
            return
        view = OddsDropdownView(self, games)
        await interaction.followup.send(
            "Select a game to view odds:", view=view, ephemeral=True
        )

    async def get_upcoming_games(self, hours_ahead: int = 0) -> List[Dict]:
        """Get all games from api_games table, no season filter"""
        try:
            db_manager = getattr(self.bot, "db_manager", None)
            if not db_manager:
                raise Exception("Database manager not available")
            query = """
                SELECT
                    api_game_id, sport, league_id, season, home_team_name, away_team_name, start_time, status
                FROM api_games
                ORDER BY start_time ASC
                LIMIT 100
            """
            games = await db_manager.fetch_all(query)
            logger.info(
                f"[get_upcoming_games] Found {len(games)} games in database (no filter)"
            )
            for i, game in enumerate(games[:5]):
                logger.info(
                    f"Game {i+1}: {game.get('home_team_name')} vs {game.get('away_team_name')} - {game.get('league_id')} - {game.get('start_time')} - Status: {game.get('status')}"
                )
            return games
        except Exception as e:
            logger.error(f"Error getting all games: {e}")
            return []

    async def fetch_odds_for_game(self, game: Dict) -> Optional[Dict]:
        """Fetch odds for a specific game from API-Sports"""
        sport = game.get("sport")
        league_id = game.get("league_id")
        season = game.get("season")
        api_game_id = game.get("api_game_id")
        if not (sport and league_id and season and api_game_id):
            logger.warning(f"Missing required fields for odds query: {game}")
            return None
        # Build the endpoint
        base_url = f"https://v1.{sport}.api-sports.io/odds"
        params = {"league": league_id, "season": season, "game": api_game_id}
        headers = {"x-apisports-key": self.api_sports_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    base_url, params=params, headers=headers
                ) as resp:
                    if resp.status != 200:
                        logger.error(
                            f"API-Sports odds error {resp.status}: {await resp.text()}"
                        )
                        return None
                    data = await resp.json()
                    logger.info(f"Fetched odds for game {api_game_id}: {data}")
                    return data
        except Exception as e:
            logger.error(f"Error fetching odds from API-Sports: {e}")
            return None

    async def create_odds_embed_for_game(self, game: Dict) -> discord.Embed:
        odds_data = await self.fetch_odds_for_game(game)
        sport = game.get("sport", "").lower()
        sport_icon = {
            "football": "⚽",  # API-Sports 'football' is soccer
            "soccer": "⚽",
            "basketball": "🏀",
            "american-football": "🏈",
            "baseball": "⚾",
            "hockey": "🏒",
            "tennis": "🎾",
            "mma": "🥊",
            "golf": "⛳",
            "cricket": "🏏",
            "rugby": "🏉",
            "australian_rules": "🏉",
            "darts": "🎯",
            "handball": "🤾",
            "motorsport": "🏎️",
            "volleyball": "🏐",
            "table_tennis": "🏓",
            "badminton": "🏸",
            "snooker": "🎱",
            "boxing": "🥊",
            "esports": "🎮",
        }.get(sport, "🏆")
        start_time = game.get("start_time")
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except:
                pass
        time_str = (
            f"<t:{int(start_time.timestamp())}:F>"
            if isinstance(start_time, datetime)
            else str(start_time)
        )
        time_relative = (
            f"<t:{int(start_time.timestamp())}:R>"
            if isinstance(start_time, datetime)
            else ""
        )
        embed = discord.Embed(
            title=f"{sport_icon} {game['home_team_name']} vs {game['away_team_name']}",
            description=f"**Start Time:** {time_str} {time_relative}\n**League ID:** {game.get('league_id', 'Unknown')}",
            color=0x00FF00,
            timestamp=datetime.utcnow(),
        )
        if odds_data and odds_data.get("response"):
            # Display odds info (customize as needed)
            odds_list = odds_data["response"]
            for bookmaker in odds_list:
                book_name = bookmaker.get("bookmaker", {}).get(
                    "name", "Unknown Bookmaker"
                )
                for bet in bookmaker.get("bets", []):
                    bet_name = bet.get("name", "Unknown Bet")
                    values = bet.get("values", [])
                    odds_str = ", ".join(
                        [f"{v.get('value')}: {v.get('odd')}" for v in values]
                    )
                    embed.add_field(
                        name=f"{book_name} - {bet_name}",
                        value=odds_str or "No odds",
                        inline=False,
                    )
        else:
            embed.add_field(name="Odds", value="No odds available for this matchup.")
        return embed

    @app_commands.command(
        name="debug_games",
        description="Debug: Check what games are in the api_games table",
    )
    async def debug_games(self, interaction: discord.Interaction):
        """Debug command to check what's in the api_games table"""
        try:
            games = await self.get_upcoming_games()
            if not games:
                await interaction.response.send_message(
                    "No games found in the database.", ephemeral=True
                )
                return
            msg = f"Found {len(games)} games in the database:\n"
            for i, g in enumerate(games[:10]):
                msg += f"{i+1}. {g['home_team_name']} vs {g['away_team_name']} (League: {g['league_id']}, Season: {g['season']})\n"
            await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in debug_games: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="sports", description="List all available sports and leagues for odds"
    )
    async def sports(self, interaction: discord.Interaction):
        """List all available sports and leagues for odds"""

        embed = discord.Embed(
            title="🏆 Available Sports & Leagues for Odds",
            description="Here are all the sports and leagues supported by the `/odds` command:",
            color=0x00FF00,
            timestamp=datetime.utcnow(),
        )

        # Group sports by category
        categories = {
            "⚽ Soccer/Football": [
                "EPL",
                "Premier League",
                "WorldCup",
                "Champions League",
                "La Liga",
                "Bundesliga",
                "Serie A",
                "Ligue 1",
                "MLS",
                "A-League",
                "J League",
                "Brazil Série A",
                "UEFA Euro",
            ],
            "🏀 Basketball": ["NBA", "WNBA", "NCAA", "EuroLeague", "BIG3", "NIT"],
            "🏈 American Football": ["NFL", "NCAA", "CFL", "XFL", "AFL"],
            "🏒 Ice Hockey": ["NHL", "KHL"],
            "⚾ Baseball": [
                "MLB",
                "NPB",
                "KBO",
                "CPBL",
                "LIDOM",
                "World Baseball Classic",
            ],
            "🎾 Tennis": [
                "ATP",
                "WTA",
                "ATP French Open",
                "WTA French Open",
                "ATP US Open",
                "WTA US Open",
                "ATP Wimbledon",
                "WTA Wimbledon",
                "ATP Australian Open",
                "WTA Australian Open",
            ],
            "🥊 MMA": ["UFC", "MMA"],
            "⛳ Golf": [
                "PGA Championship",
                "Masters Tournament",
                "US Open",
                "The Open",
                "Ryder Cup",
                "Presidents Cup",
            ],
            "🏏 Cricket": [
                "Test Matches",
                "ODI",
                "T20",
                "IPL",
                "Big Bash League",
                "Caribbean Premier League",
            ],
            "🏉 Rugby": [
                "NRL",
                "Super Rugby",
                "Six Nations",
                "Rugby Championship",
                "Heineken Cup",
            ],
            "🎯 Other Sports": [
                "AFL (Australian Rules)",
                "PDC (Darts)",
                "EHF (Handball)",
                "Formula 1",
                "NASCAR",
                "IndyCar",
                "MotoGP",
                "Volleyball",
                "Table Tennis",
                "Badminton",
                "Snooker",
                "Boxing",
            ],
            "🎮 Esports": [
                "CS:GO",
                "Dota 2",
                "League of Legends",
                "Overwatch",
                "Rocket League",
                "Valorant",
            ],
        }

        for category, leagues in categories.items():
            # Split long lists into multiple fields if needed
            if len(leagues) <= 8:
                embed.add_field(name=category, value=", ".join(leagues), inline=False)
            else:
                # Split into chunks
                chunks = [leagues[i : i + 8] for i in range(0, len(leagues), 8)]
                for i, chunk in enumerate(chunks):
                    field_name = category if i == 0 else f"{category} (cont.)"
                    embed.add_field(
                        name=field_name, value=", ".join(chunk), inline=False
                    )

        embed.set_footer(text="Use /odds to get current odds for upcoming games")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Odds(bot))
