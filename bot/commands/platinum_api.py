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
            'formula1': 'https://v1.formula-1.api-sports.io',
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

    async def make_api_request(self, sport: str, endpoint: str, params: dict) -> dict:
        """Make a request to the sports API."""
        try:
            api_key = self.bot.sports_api.api_key
            base_url = self.api_base_urls.get(sport)
            
            if not base_url:
                return {'error': f'Unsupported sport: {sport}'}
            
            url = f"{base_url}/{endpoint}"
            headers = {
                'x-rapidapi-key': api_key,
                'x-rapidapi-host': base_url.replace('https://', '')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {'error': f'API request failed with status {response.status}'}
                        
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return {'error': f'Request failed: {str(e)}'}

    @app_commands.command(name="api_teams", description="Query teams from sports API (Platinum only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def api_teams(
        self,
        interaction: Interaction,
        sport: str,
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
        sport: str,
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
        sport: str,
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
            endpoint = 'fixtures' if sport in ['football', 'basketball', 'baseball', 'hockey', 'rugby', 'handball'] else 'games'
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
        sport: str,
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
        sport: str,
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
        sport: str
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
            
            # Show first 10 live matches
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
            
        except Exception as e:
            logger.error(f"Error in api_live command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while querying live matches.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function for the Platinum API cog."""
    await bot.add_cog(PlatinumAPICog(bot))
    logger.info("PlatinumAPICog loaded successfully") 