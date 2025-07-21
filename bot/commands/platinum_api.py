import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class SportDropdown(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="⚽ Football (Soccer)", value="football", description="Soccer leagues worldwide"),
            discord.SelectOption(label="🏀 Basketball", value="basketball", description="NBA, WNBA, EuroLeague"),
            discord.SelectOption(label="⚾ Baseball", value="baseball", description="MLB, NPB, KBO"),
            discord.SelectOption(label="🏈 American Football", value="american-football", description="NFL, NCAA"),
            discord.SelectOption(label="🏒 Hockey", value="hockey", description="NHL, KHL"),
            discord.SelectOption(label="🎾 Tennis", value="tennis", description="ATP, WTA, Grand Slams"),
            discord.SelectOption(label="🥊 MMA", value="mma", description="UFC, Bellator"),
            discord.SelectOption(label="🏎️ Formula 1", value="formula-1", description="F1 Championship"),
            discord.SelectOption(label="🏉 Rugby", value="rugby", description="Super Rugby, Six Nations"),
            discord.SelectOption(label="🏐 Volleyball", value="volleyball", description="FIVB World League"),
            discord.SelectOption(label="🤾 Handball", value="handball", description="EHF Champions League"),
        ]
        super().__init__(
            placeholder="Select a sport...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        sport = self.values[0]
        await self.parent_view.show_query_type_dropdown(interaction, sport)


class QueryTypeDropdown(discord.ui.Select):
    def __init__(self, parent_view, sport: str):
        self.parent_view = parent_view
        self.sport = sport
        options = [
            discord.SelectOption(label="🏆 Leagues", value="leagues", description="Available leagues for this sport"),
            discord.SelectOption(label="👥 Players", value="players", description="Players by league or team"),
            discord.SelectOption(label="⚽ Teams", value="teams", description="Teams in a league"),
            discord.SelectOption(label="🏟️ Fixtures/Matches", value="fixtures", description="Upcoming and past matches"),
            discord.SelectOption(label="💰 Odds", value="odds", description="Betting odds for matches"),
            discord.SelectOption(label="📺 Live Matches", value="live", description="Currently live matches"),
        ]
        super().__init__(
            placeholder="Select what to query...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        query_type = self.values[0]
        await self.parent_view.show_league_dropdown(interaction, self.sport, query_type)


class LeagueDropdown(discord.ui.Select):
    def __init__(self, parent_view, sport: str, query_type: str):
        self.parent_view = parent_view
        self.sport = sport
        self.query_type = query_type
        
        # Define leagues for each sport
        leagues = {
            "football": [
                ("Premier League", 39, "England"),
                ("La Liga", 140, "Spain"),
                ("Bundesliga", 78, "Germany"),
                ("Serie A", 135, "Italy"),
                ("Ligue 1", 61, "France"),
                ("MLS", 253, "USA"),
                ("Champions League", 2, "Europe"),
                ("Europa League", 3, "Europe"),
                ("Brazil Serie A", 71, "Brazil"),
                ("World Cup", 15, "International"),
            ],
            "basketball": [
                ("NBA", 12, "USA"),
                ("WNBA", 13, "USA"),
                ("EuroLeague", 1, "Europe"),
            ],
            "baseball": [
                ("MLB", 1, "USA"),
                ("NPB", 2, "Japan"),
                ("KBO", 3, "South Korea"),
            ],
            "hockey": [
                ("NHL", 57, "USA/Canada"),
                ("KHL", 1, "Russia"),
            ],
            "american-football": [
                ("NFL", 1, "USA"),
                ("NCAA", 2, "USA"),
            ],
            "tennis": [
                ("ATP", 1, "International"),
                ("WTA", 2, "International"),
                ("Grand Slam", 3, "International"),
            ],
            "mma": [
                ("UFC", 1, "International"),
            ],
            "formula-1": [
                ("F1", 1, "International"),
            ],
            "rugby": [
                ("Super Rugby", 1, "International"),
                ("Six Nations", 2, "Europe"),
            ],
            "volleyball": [
                ("FIVB", 1, "International"),
            ],
            "handball": [
                ("EHF", 1, "Europe"),
            ],
        }
        
        sport_leagues = leagues.get(sport, [])
        options = []
        
        for league_name, league_id, country in sport_leagues:
            options.append(
                discord.SelectOption(
                    label=league_name,
                    value=str(league_id),
                    description=f"{country} • ID: {league_id}"
                )
            )
        
        super().__init__(
            placeholder="Select a league...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        league_id = int(self.values[0])
        await self.parent_view.execute_query(interaction, self.sport, self.query_type, league_id)


class APIFlowView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=120)
        self.cog = cog
        self.add_item(SportDropdown(self))

    async def show_query_type_dropdown(self, interaction: discord.Interaction, sport: str):
        """Show the query type dropdown after sport selection."""
        embed = discord.Embed(
            title=f"🔍 API Query - {sport.title()}",
            description="What would you like to query?",
            color=0x9b59b6
        )
        
        view = discord.ui.View(timeout=120)
        view.add_item(QueryTypeDropdown(self, sport))
        
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_league_dropdown(self, interaction: discord.Interaction, sport: str, query_type: str):
        """Show the league dropdown after query type selection."""
        embed = discord.Embed(
            title=f"🔍 API Query - {sport.title()} {query_type.title()}",
            description="Select a league:",
            color=0x9b59b6
        )
        
        view = discord.ui.View(timeout=120)
        view.add_item(LeagueDropdown(self, sport, query_type))
        
        await interaction.response.edit_message(embed=embed, view=view)

    async def execute_query(self, interaction: discord.Interaction, sport: str, query_type: str, league_id: int):
        """Execute the final API query and send results."""
        try:
            # Check Platinum status
            guild_id = interaction.guild_id
            if not await self.cog.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.edit_message(
                    content="❌ This feature requires a Platinum subscription.",
                    embed=None,
                    view=None
                )
                return

            await interaction.response.edit_message(
                content="⏳ Querying API...",
                embed=None,
                view=None
            )

            # Build parameters based on query type
            params = {"league": league_id}
            
            # Add season for most queries
            if query_type in ["players", "teams", "fixtures", "odds"]:
                params["season"] = datetime.now().year

            logger.info(f"Executing API query: sport={sport}, type={query_type}, params={params}")
            
            # Make API request
            result = await self.cog.make_api_request(sport, query_type, params)
            
            if 'error' in result:
                await interaction.followup.send(
                    f"❌ API Error: {result['error']}",
                    ephemeral=True
                )
                return

            # Process and display results
            await self.cog.display_query_results(interaction, sport, query_type, result)

        except Exception as e:
            logger.error(f"Error in API flow: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your request.",
                ephemeral=True
            )


class PlatinumAPICog(commands.Cog):
    """Platinum tier API query commands for direct sports data access."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_base_urls = {
            'football': 'https://v3.football.api-sports.io',
            'basketball': 'https://v1.basketball.api-sports.io',
            'baseball': 'https://v1.baseball.api-sports.io',
            'hockey': 'https://v1.hockey.api-sports.io',
            'rugby': 'https://v1.rugby.api-sports.io',
            'handball': 'https://v1.handball.api-sports.io',
            'mma': 'https://v1.mma.api-sports.io',
            'formula-1': 'https://v1.formula-1.api-sports.io',
            'american-football': 'https://v1.american-football.api-sports.io',
            'tennis': 'https://v1.tennis.api-sports.io',
            'volleyball': 'https://v1.volleyball.api-sports.io',
        }
        
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for Platinum API commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
        else:
            logger.error(f"Error in Platinum API command: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.", ephemeral=True
            )

    async def make_api_request(self, sport: str, endpoint: str, params: dict) -> dict:
        """Make a request to the sports API."""
        try:
            api_key = self.bot.sports_api.api_key
            base_url = self.api_base_urls.get(sport)
            
            if not base_url:
                return {'error': f'Unsupported sport: {sport}'}
            
            # Special handling for odds endpoint
            if endpoint == 'odds':
                # Use the correct odds endpoint structure
                url = f"https://v1.{sport}.api-sports.io/odds"
            else:
                url = f"{base_url}/{endpoint}"
                
            headers = {
                'x-apisports-key': api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        return {'error': f'API request failed with status {response.status}: {error_text}'}
                        
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return {'error': f'Request failed: {str(e)}'}

    async def display_query_results(self, interaction: discord.Interaction, sport: str, query_type: str, result: dict):
        """Display the results of an API query."""
        if 'error' in result:
            embed = discord.Embed(
                title="❌ API Error",
                description=result['error'],
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if query_type == 'leagues':
            leagues = result.get('response', [])
            if not leagues:
                embed = discord.Embed(
                    title="🏆 Leagues Query",
                    description="No leagues found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🏆 {sport.title()} Leagues",
                description=f"Found {len(leagues)} leagues",
                color=0x9b59b6
            )
            for i, league in enumerate(leagues[:10]):
                league_info = league.get('league', {})
                name = league_info.get('name', 'Unknown')
                country = league_info.get('country', 'Unknown')
                type_name = league_info.get('type', 'Unknown')
                
                embed.add_field(
                    name=f"{i+1}. {name}",
                    value=f"Country: {country}\nType: {type_name}",
                    inline=True
                )
            if len(leagues) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(leagues)} leagues")
            await interaction.followup.send(embed=embed)

        elif query_type == 'players':
            players = result.get('response', [])
            if not players:
                embed = discord.Embed(
                    title="👥 Players Query",
                    description="No players found for the specified criteria.\n\n"
                               "**Try:**\n"
                               "• Use `/api_leagues` to find league IDs\n"
                               "• Use `/api_teams` to find team IDs\n"
                               "• Check if the season is valid for the league",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"👥 {sport.title()} Players",
                description=f"Found {len(players)} players",
                color=0x9b59b6
            )
            for i, player in enumerate(players[:10]):
                player_info = player.get('player', {})
                name = player_info.get('name', 'Unknown')
                age = player_info.get('age', 'Unknown')
                nationality = player_info.get('nationality', 'Unknown')
                
                embed.add_field(
                    name=f"{i+1}. {name}",
                    value=f"Age: {age}\nNationality: {nationality}",
                    inline=True
                )
            if len(players) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(players)} players")
            await interaction.followup.send(embed=embed)

        elif query_type == 'teams':
            teams = result.get('response', [])
            if not teams:
                embed = discord.Embed(
                    title="📋 Teams Query",
                    description="No teams found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🏈 {sport.title()} Teams",
                description=f"Found {len(teams)} teams",
                color=0x9b59b6
            )
            for i, team in enumerate(teams[:10]):
                team_info = team.get('team', {})
                name = team_info.get('name', 'Unknown')
                country = team_info.get('country', 'Unknown')
                founded = team_info.get('founded', 'Unknown')
                
                embed.add_field(
                    name=f"{i+1}. {name}",
                    value=f"Country: {country}\nFounded: {founded}",
                    inline=True
                )
            if len(teams) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(teams)} teams")
            await interaction.followup.send(embed=embed)

        elif query_type == 'fixtures':
            fixtures = result.get('response', [])
            if not fixtures:
                embed = discord.Embed(
                    title="📅 Fixtures Query",
                    description="No fixtures found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"📅 {sport.title()} Fixtures",
                description=f"Found {len(fixtures)} fixtures",
                color=0x9b59b6
            )
            for i, fixture in enumerate(fixtures[:10]):
                teams = fixture.get('teams', {})
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                fixture_info = fixture.get('fixture', {})
                date = fixture_info.get('date', 'Unknown')
                status = fixture_info.get('status', {}).get('short', 'Unknown')
                
                embed.add_field(
                    name=f"{i+1}. {home_team} vs {away_team}",
                    value=f"Date: {date}\nStatus: {status}",
                    inline=True
                )
            if len(fixtures) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(fixtures)} fixtures")
            await interaction.followup.send(embed=embed)

        elif query_type == 'odds':
            odds_data = result.get('response', [])
            if not odds_data:
                embed = discord.Embed(
                    title="💰 Odds Query",
                    description="No odds found for the specified criteria.\n\n"
                               "**Possible reasons:**\n"
                               "• No upcoming matches in this league/season\n"
                               "• Odds not yet available for these matches\n"
                               "• League doesn't provide odds data\n\n"
                               "**Try:**\n"
                               "• Use `/api_fixtures` to find recent/upcoming matches\n"
                               "• Use `/api_leagues` to find league IDs\n"
                               "• Check if the season is current",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"💰 {sport.title()} Odds",
                description=f"Found {len(odds_data)} odds entries",
                color=0x9b59b6
            )
            for i, odds in enumerate(odds_data[:5]):
                fixture_info = odds.get('fixture', {})
                teams = fixture_info.get('teams', {})
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                
                bookmakers = odds.get('bookmakers', [])
                if bookmakers:
                    bookmaker_name = bookmakers[0].get('name', 'Unknown')
                    bets = bookmakers[0].get('bets', [])
                    if bets:
                        bet_values = bets[0].get('values', [])
                        odds_text = ', '.join([f"{v.get('value', 'N/A')}: {v.get('odd', 'N/A')}" for v in bet_values[:3]])
                    else:
                        odds_text = "No odds available"
                else:
                    odds_text = "No bookmakers available"
                
                embed.add_field(
                    name=f"{i+1}. {home_team} vs {away_team}",
                    value=f"Bookmaker: {bookmaker_name}\nOdds: {odds_text}",
                    inline=False
                )
            if len(odds_data) > 5:
                embed.set_footer(text=f"Showing first 5 of {len(odds_data)} odds entries")
            await interaction.followup.send(embed=embed)

        elif query_type == 'live':
            live_matches = result.get('response', [])
            if not live_matches:
                embed = discord.Embed(
                    title="🔴 Live Matches",
                    description="No live matches currently playing.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🔴 Live {sport.title()} Matches",
                description=f"Found {len(live_matches)} live matches",
                color=0xff0000
            )
            for i, match in enumerate(live_matches[:10]):
                teams = match.get('teams', {})
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                
                goals = match.get('goals', {})
                home_goals = goals.get('home', 0)
                away_goals = goals.get('away', 0)
                
                fixture_info = match.get('fixture', {})
                status = fixture_info.get('status', {}).get('short', 'Unknown')
                elapsed = fixture_info.get('status', {}).get('elapsed', 0)
                
                embed.add_field(
                    name=f"{i+1}. {home_team} {home_goals} - {away_goals} {away_team}",
                    value=f"Status: {status}\nElapsed: {elapsed}'",
                    inline=True
                )
            if len(live_matches) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(live_matches)} live matches")
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="api", description="Interactive sports API query with dropdowns (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api(self, interaction: discord.Interaction):
        """Start the interactive API query flow."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="🔍 Sports API Query",
                description="Select a sport to start your query:",
                color=0x9b59b6
            )
            
            view = APIFlowView(self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the API query.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function for the Platinum API cog."""
    await bot.add_cog(PlatinumAPICog(bot))
    logger.info("PlatinumAPICog loaded successfully") 