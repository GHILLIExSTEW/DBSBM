import logging
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from typing import Optional, List
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
            'formula1': 'https://v1.formula1.api-sports.io',
            'nfl': 'https://v1.american-football.api-sports.io',
            'afl': 'https://v1.afl.api-sports.io',
            'nba': 'https://v2.nba.api-sports.io',

        }
        
    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
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

    async def make_api_request(self, sport: str, endpoint: str, params: dict = None) -> dict:
        """Make a request to the sports API."""
        try:
            base_url = self.api_base_urls.get(sport)
            if not base_url:
                return {"error": f"Sport '{sport}' not supported"}
            
            url = f"{base_url}/{endpoint}"
            headers = {
                'x-rapidapi-key': self.bot.config.get('API_KEY'),
                'x-rapidapi-host': f'{sport}.api-sports.io'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"API request failed: {response.status}"}
                        
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {"error": f"Request failed: {str(e)}"}

    @app_commands.command(name="api_teams", description="Query teams from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_teams(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                app_commands.Choice(name="Football", value="football"),
                app_commands.Choice(name="Basketball", value="basketball"),
                app_commands.Choice(name="Baseball", value="baseball"),
                app_commands.Choice(name="Hockey", value="hockey"),
                app_commands.Choice(name="Rugby", value="rugby"),
                app_commands.Choice(name="Handball", value="handball"),
                app_commands.Choice(name="MMA", value="mma"),
                app_commands.Choice(name="Formula 1", value="formula1"),
                app_commands.Choice(name="NFL", value="nfl"),
                app_commands.Choice(name="AFL", value="afl")
            ]
        ),
        league: Optional[int] = None,
        country: Optional[str] = None,
        season: Optional[int] = None
    ):
        """Query teams from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Build parameters
            params = {}
            if league:
                params['league'] = league
            if country:
                params['country'] = country
            if season:
                params['season'] = season
            
            # Make API request
            result = await self.make_api_request(sport, 'teams', params)
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            teams = result.get('response', [])
            if not teams:
                embed = discord.Embed(
                    title="📋 Teams Query",
                    description="No teams found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with team information
            embed = discord.Embed(
                title=f"🏈 {sport.title()} Teams",
                description=f"Found {len(teams)} teams",
                color=0x9b59b6
            )
            
            # Show first 10 teams
            for i, team in enumerate(teams[:10]):
                team_info = team.get('team', {})
                embed.add_field(
                    name=f"{i+1}. {team_info.get('name', 'Unknown')}",
                    value=f"ID: {team_info.get('id', 'N/A')}\n"
                          f"Country: {team_info.get('country', 'N/A')}\n"
                          f"Founded: {team_info.get('founded', 'N/A')}",
                    inline=True
                )
            
            if len(teams) > 10:
                embed.add_field(
                    name="More Results",
                    value=f"... and {len(teams) - 10} more teams",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_teams command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying teams.", ephemeral=True
            )

    @app_commands.command(name="api_players", description="Query players from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_players(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                "football", "basketball", "baseball", "hockey", "rugby",
                "handball", "mma", "formula1", "nfl", "afl"
            ]
        ),
        team: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        search: Optional[str] = None
    ):
        """Query players from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Build parameters
            params = {}
            if team:
                params['team'] = team
            if league:
                params['league'] = league
            if season:
                params['season'] = season
            if search:
                params['search'] = search
            
            # Make API request
            result = await self.make_api_request(sport, 'players', params)
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            players = result.get('response', [])
            if not players:
                embed = discord.Embed(
                    title="👥 Players Query",
                    description="No players found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with player information
            embed = discord.Embed(
                title=f"👥 {sport.title()} Players",
                description=f"Found {len(players)} players",
                color=0x9b59b6
            )
            
            # Show first 10 players
            for i, player in enumerate(players[:10]):
                player_info = player.get('player', {})
                stats = player.get('statistics', [{}])[0] if player.get('statistics') else {}
                
                embed.add_field(
                    name=f"{i+1}. {player_info.get('name', 'Unknown')}",
                    value=f"Age: {player_info.get('age', 'N/A')}\n"
                          f"Height: {player_info.get('height', 'N/A')}\n"
                          f"Weight: {player_info.get('weight', 'N/A')}\n"
                          f"Position: {stats.get('games', {}).get('position', 'N/A')}",
                    inline=True
                )
            
            if len(players) > 10:
                embed.add_field(
                    name="More Results",
                    value=f"... and {len(players) - 10} more players",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_players command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying players.", ephemeral=True
            )

    @app_commands.command(name="api_fixtures", description="Query fixtures/matches from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_fixtures(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                "football", "basketball", "baseball", "hockey", "rugby",
                "handball", "mma", "formula1", "nfl", "afl"
            ]
        ),
        league: Optional[int] = None,
        team: Optional[int] = None,
        season: Optional[int] = None,
        date: Optional[str] = None
    ):
        """Query fixtures/matches from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Build parameters
            params = {}
            if league:
                params['league'] = league
            if team:
                params['team'] = team
            if season:
                params['season'] = season
            if date:
                params['date'] = date
            else:
                # Default to today
                params['date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Make API request
            endpoint = 'fixtures' if sport in ['football', 'basketball', 'baseball', 'hockey', 'rugby', 'handball'] else 'matches'
            result = await self.make_api_request(sport, endpoint, params)
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            fixtures = result.get('response', [])
            if not fixtures:
                embed = discord.Embed(
                    title="📅 Fixtures Query",
                    description="No fixtures found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with fixture information
            embed = discord.Embed(
                title=f"📅 {sport.title()} Fixtures",
                description=f"Found {len(fixtures)} fixtures",
                color=0x9b59b6
            )
            
            # Show first 10 fixtures
            for i, fixture in enumerate(fixtures[:10]):
                teams = fixture.get('teams', {})
                goals = fixture.get('goals', {})
                score = fixture.get('score', {})
                
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                home_score = score.get('halftime', {}).get('home', 'N/A')
                away_score = score.get('halftime', {}).get('away', 'N/A')
                
                embed.add_field(
                    name=f"{i+1}. {home_team} vs {away_team}",
                    value=f"Score: {home_score} - {away_score}\n"
                          f"Date: {fixture.get('fixture', {}).get('date', 'N/A')}\n"
                          f"Status: {fixture.get('fixture', {}).get('status', {}).get('long', 'N/A')}",
                    inline=True
                )
            
            if len(fixtures) > 10:
                embed.add_field(
                    name="More Results",
                    value=f"... and {len(fixtures) - 10} more fixtures",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_fixtures command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying fixtures.", ephemeral=True
            )

    @app_commands.command(name="api_odds", description="Query odds from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_odds(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                "football", "basketball", "baseball", "hockey", "rugby",
                "handball", "mma", "formula1", "nfl", "afl"
            ]
        ),
        fixture: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        bookmaker: Optional[int] = None
    ):
        """Query odds from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Build parameters
            params = {}
            if fixture:
                params['fixture'] = fixture
            if league:
                params['league'] = league
            if season:
                params['season'] = season
            if bookmaker:
                params['bookmaker'] = bookmaker
            
            # Make API request
            result = await self.make_api_request(sport, 'odds', params)
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            odds_data = result.get('response', [])
            if not odds_data:
                embed = discord.Embed(
                    title="💰 Odds Query",
                    description="No odds found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with odds information
            embed = discord.Embed(
                title=f"💰 {sport.title()} Odds",
                description=f"Found {len(odds_data)} odds entries",
                color=0x9b59b6
            )
            
            # Show first 5 odds entries
            for i, odds in enumerate(odds_data[:5]):
                fixture_info = odds.get('fixture', {})
                bookmaker_info = odds.get('bookmakers', [{}])[0] if odds.get('bookmakers') else {}
                bet_info = bookmaker_info.get('bets', [{}])[0] if bookmaker_info.get('bets') else {}
                
                embed.add_field(
                    name=f"{i+1}. {fixture_info.get('teams', {}).get('home', {}).get('name', 'Unknown')} vs {fixture_info.get('teams', {}).get('away', {}).get('name', 'Unknown')}",
                    value=f"Bookmaker: {bookmaker_info.get('name', 'N/A')}\n"
                          f"Bet Type: {bet_info.get('name', 'N/A')}\n"
                          f"Last Update: {odds.get('update', 'N/A')}",
                    inline=True
                )
            
            if len(odds_data) > 5:
                embed.add_field(
                    name="More Results",
                    value=f"... and {len(odds_data) - 5} more odds entries",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_odds command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying odds.", ephemeral=True
            )

    @app_commands.command(name="api_leagues", description="Query leagues from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_leagues(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                "football", "basketball", "baseball", "hockey", "rugby",
                "handball", "mma", "formula1", "nfl", "afl"
            ]
        ),
        country: Optional[str] = None,
        season: Optional[int] = None
    ):
        """Query leagues from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Build parameters
            params = {}
            if country:
                params['country'] = country
            if season:
                params['season'] = season
            
            # Make API request
            result = await self.make_api_request(sport, 'leagues', params)
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            leagues = result.get('response', [])
            if not leagues:
                embed = discord.Embed(
                    title="🏆 Leagues Query",
                    description="No leagues found for the specified criteria.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with league information
            embed = discord.Embed(
                title=f"🏆 {sport.title()} Leagues",
                description=f"Found {len(leagues)} leagues",
                color=0x9b59b6
            )
            
            # Show first 10 leagues
            for i, league in enumerate(leagues[:10]):
                league_info = league.get('league', {})
                country_info = league.get('country', {})
                
                embed.add_field(
                    name=f"{i+1}. {league_info.get('name', 'Unknown')}",
                    value=f"Country: {country_info.get('name', 'N/A')}\n"
                          f"Type: {league_info.get('type', 'N/A')}\n"
                          f"Season: {league_info.get('season', 'N/A')}",
                    inline=True
                )
            
            if len(leagues) > 10:
                embed.add_field(
                    name="More Results",
                    value=f"... and {len(leagues) - 10} more leagues",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_leagues command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying leagues.", ephemeral=True
            )

    @app_commands.command(name="api_live", description="Query live matches from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_live(
        self,
        interaction: Interaction,
        sport: str = app_commands.Choice(
            name="Sport",
            choices=[
                "football", "basketball", "baseball", "hockey", "rugby",
                "handball", "mma", "formula1", "nfl", "afl"
            ]
        )
    ):
        """Query live matches from the sports API."""
        try:
            guild_id = interaction.guild_id
            
            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Make API request for live matches
            result = await self.make_api_request(sport, 'fixtures', {'live': 'all'})
            
            if 'error' in result:
                embed = discord.Embed(
                    title="❌ API Error",
                    description=result['error'],
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Process results
            live_matches = result.get('response', [])
            if not live_matches:
                embed = discord.Embed(
                    title="🔴 Live Matches",
                    description="No live matches currently playing.",
                    color=0x9b59b6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create embed with live match information
            embed = discord.Embed(
                title=f"🔴 Live {sport.title()} Matches",
                description=f"Found {len(live_matches)} live matches",
                color=0xff0000
            )
            
            # Show all live matches
            for i, match in enumerate(live_matches):
                teams = match.get('teams', {})
                score = match.get('score', {})
                fixture = match.get('fixture', {})
                
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                home_score = score.get('fulltime', {}).get('home', 'N/A')
                away_score = score.get('fulltime', {}).get('away', 'N/A')
                elapsed = fixture.get('status', {}).get('elapsed', 'N/A')
                
                embed.add_field(
                    name=f"{i+1}. {home_team} vs {away_team}",
                    value=f"Score: {home_score} - {away_score}\n"
                          f"Elapsed: {elapsed} min\n"
                          f"Status: {fixture.get('status', {}).get('long', 'N/A')}",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in api_live command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying live matches.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Set up the Platinum API cog."""
    await bot.add_cog(PlatinumAPICog(bot))
    logger.info("Platinum API cog loaded successfully") 