#!/usr/bin/env python3
"""
Real ML Commands - Discord Commands with Live API Integration (Platinum Only)

These commands use real sports data from API-Sports to provide actionable
betting insights powered by ML models. Available only to Platinum servers.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class SportDropdown(discord.ui.Select):
    """Dropdown for selecting sports."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label="⚽ Football (Soccer)",
                value="football",
                description="Soccer leagues worldwide",
            ),
            discord.SelectOption(
                label="🏀 Basketball",
                value="basketball",
                description="NBA, WNBA, EuroLeague",
            ),
            discord.SelectOption(
                label="⚾ Baseball", value="baseball", description="MLB, NPB, KBO"
            ),
            discord.SelectOption(
                label="🏈 American Football",
                value="american-football",
                description="NFL, NCAA",
            ),
            discord.SelectOption(
                label="🏒 Hockey", value="hockey", description="NHL, KHL"
            ),
            discord.SelectOption(
                label="🎾 Tennis", value="tennis", description="ATP, WTA, Grand Slams"
            ),
            discord.SelectOption(
                label="🥊 MMA", value="mma", description="UFC, Bellator"
            ),
            discord.SelectOption(
                label="🏎️ Formula 1", value="formula-1", description="F1 Championship"
            ),
            discord.SelectOption(
                label="🏉 Rugby", value="rugby", description="Super Rugby, Six Nations"
            ),
            discord.SelectOption(
                label="🏐 Volleyball",
                value="volleyball",
                description="FIVB World League",
            ),
        ]
        super().__init__(
            placeholder="Select a sport...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        sport = self.values[0]
        await self.parent_view.on_sport_selected(interaction, sport)


class LeagueDropdown(discord.ui.Select):
    """Dropdown for selecting leagues within a sport."""

    def __init__(self, parent_view, sport: str):
        self.parent_view = parent_view
        self.sport = sport

        # Define leagues for each sport
        leagues = {
            "football": [
                ("Premier League", "EPL"),
                ("La Liga", "LaLiga"),
                ("Bundesliga", "Bundesliga"),
                ("Serie A", "SerieA"),
                ("Ligue 1", "Ligue1"),
                ("MLS", "MLS"),
                ("Champions League", "ChampionsLeague"),
                ("Europa League", "EuropaLeague"),
                ("Brazil Serie A", "Brazil_Serie_A"),
                ("World Cup", "WorldCup"),
            ],
            "basketball": [
                ("NBA", "NBA"),
                ("WNBA", "WNBA"),
                ("EuroLeague", "EuroLeague"),
            ],
            "baseball": [
                ("MLB", "MLB"),
                ("NPB", "NPB"),
                ("KBO", "KBO"),
            ],
            "hockey": [
                ("NHL", "NHL"),
                ("KHL", "KHL"),
            ],
            "american-football": [
                ("NFL", "NFL"),
                ("NCAA", "NCAA"),
            ],
            "tennis": [
                ("ATP", "ATP"),
                ("WTA", "WTA"),
                ("Grand Slam", "GrandSlam"),
            ],
            "mma": [
                ("UFC", "UFC"),
            ],
            "formula-1": [
                ("F1", "Formula-1"),
            ],
            "rugby": [
                ("Super Rugby", "SuperRugby"),
                ("Six Nations", "SixNations"),
            ],
            "volleyball": [
                ("FIVB", "FIVB"),
            ],
        }

        sport_leagues = leagues.get(sport, [])
        options = []

        for league_name, league_key in sport_leagues:
            options.append(
                discord.SelectOption(
                    label=league_name,
                    value=league_key,
                    description=f"{sport.title()} • {league_name}",
                )
            )

        super().__init__(
            placeholder="Select a league...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        league = self.values[0]
        await self.parent_view.on_league_selected(interaction, self.sport, league)


class TeamDropdown(discord.ui.Select):
    """Dropdown for selecting teams."""

    def __init__(self, parent_view, sport: str, league: str, teams: List[str]):
        self.parent_view = parent_view
        self.sport = sport
        self.league = league

        options = []
        for team in teams[:25]:  # Discord limit
            options.append(
                discord.SelectOption(
                    label=team,
                    value=team,
                    description=f"{league} • {sport.title()}",
                )
            )

        super().__init__(
            placeholder="Select a team...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        team = self.values[0]
        await self.parent_view.on_team_selected(
            interaction, self.sport, self.league, team
        )


class MLCommandView(discord.ui.View):
    """Base view for ML commands with dropdowns."""

    def __init__(self, bot, command_type: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.command_type = command_type
        self.sport = None
        self.league = None
        self.team = None
        self.home_team = None
        self.away_team = None

    async def on_sport_selected(self, interaction: discord.Interaction, sport: str):
        """Handle sport selection."""
        self.sport = sport
        self.clear_items()
        self.add_item(LeagueDropdown(self, sport))
        await interaction.response.edit_message(
            content=f"🎯 **{self.command_type}** - Selected: **{sport.title()}**\n"
            f"Now select a league:",
            view=self,
        )

    async def on_league_selected(
        self, interaction: discord.Interaction, sport: str, league: str
    ):
        """Handle league selection."""
        self.league = league

        if self.command_type == "Team Stats":
            # For team stats, show team dropdown
            teams = await self._get_teams_for_league(sport, league)
            if teams:
                self.clear_items()
                self.add_item(TeamDropdown(self, sport, league, teams))
                await interaction.response.edit_message(
                    content=f"🎯 **{self.command_type}** - {sport.title()} • {league}\n"
                    f"Select a team:",
                    view=self,
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ No teams found for {league}", view=None
                )
        elif self.command_type == "Analyze Game":
            # For game analysis, show team dropdowns
            teams = await self._get_teams_for_league(sport, league)
            if teams:
                self.clear_items()
                self.add_item(TeamDropdown(self, sport, league, teams))
                await interaction.response.edit_message(
                    content=f"🎯 **{self.command_type}** - {sport.title()} • {league}\n"
                    f"Select home team:",
                    view=self,
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ No teams found for {league}", view=None
                )
        else:
            # For other commands, execute directly
            await self._execute_command(interaction)

    async def on_team_selected(
        self, interaction: discord.Interaction, sport: str, league: str, team: str
    ):
        """Handle team selection."""
        if self.command_type == "Team Stats":
            await self._execute_team_stats(interaction, sport, league, team)
        elif self.command_type == "Analyze Game":
            if not self.home_team:
                self.home_team = team
                teams = await self._get_teams_for_league(sport, league)
                # Remove the selected home team
                teams = [t for t in teams if t != team]
                self.clear_items()
                self.add_item(TeamDropdown(self, sport, league, teams))
                await interaction.response.edit_message(
                    content=f"🎯 **{self.command_type}** - {sport.title()} • {league}\n"
                    f"Home team: **{team}**\n"
                    f"Select away team:",
                    view=self,
                )
            else:
                self.away_team = team
                await self._execute_analyze_game(
                    interaction, sport, league, self.home_team, team
                )

    async def _get_teams_for_league(self, sport: str, league: str) -> List[str]:
        """Get teams for a specific league."""
        try:
            # This is a simplified version - in practice you'd fetch from API
            # For now, return some common teams based on league
            common_teams = {
                "NBA": ["Lakers", "Warriors", "Celtics", "Bulls", "Heat", "Knicks"],
                "NFL": [
                    "Patriots",
                    "Cowboys",
                    "Packers",
                    "Steelers",
                    "49ers",
                    "Chiefs",
                ],
                "EPL": [
                    "Manchester United",
                    "Liverpool",
                    "Arsenal",
                    "Chelsea",
                    "Manchester City",
                    "Tottenham",
                ],
                "LaLiga": [
                    "Real Madrid",
                    "Barcelona",
                    "Atletico Madrid",
                    "Sevilla",
                    "Valencia",
                    "Athletic Bilbao",
                ],
                "MLB": ["Yankees", "Red Sox", "Dodgers", "Giants", "Cubs", "Cardinals"],
                "NHL": [
                    "Maple Leafs",
                    "Canadiens",
                    "Bruins",
                    "Rangers",
                    "Blackhawks",
                    "Red Wings",
                ],
            }
            return common_teams.get(league, ["Team 1", "Team 2", "Team 3", "Team 4"])
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []

    async def _execute_command(self, interaction: discord.Interaction):
        """Execute the command based on type."""
        if self.command_type == "Analyze Today":
            await self._execute_analyze_today(interaction)
        elif self.command_type == "My Insights":
            await self._execute_my_insights(interaction)
        elif self.command_type == "Live Odds":
            await self._execute_live_odds(interaction)

    async def _execute_analyze_today(self, interaction: discord.Interaction):
        """Execute analyze today command."""
        await interaction.response.defer()

        try:
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return

            opportunities = await self.bot.real_ml_service.analyze_todays_games(
                interaction.user.id
            )

            if not opportunities:
                embed = discord.Embed(
                    title="📅 No High-Confidence Opportunities Today",
                    description="No games with strong ML predictions found for today.\n"
                    "💡 Try again later or use `/analyze_game` for specific games.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title="🎯 Today's Best Betting Opportunities",
                description=f"ML-powered analysis using real sports data\n"
                f"Found {len(opportunities)} high-confidence opportunities",
                color=discord.Color.green(),
                timestamp=datetime.now(),
            )

            for i, opp in enumerate(opportunities[:3], 1):
                game_info = opp["game_info"]
                embed.add_field(
                    name=f"{i}. {game_info['home_team']} vs {game_info['away_team']}",
                    value=f"**Sport:** {game_info['sport'].title()}\n"
                    f"**League:** {game_info['league']}\n"
                    f"**Prediction:** {opp['prediction']}\n"
                    f"**Confidence:** {opp['confidence']}%\n"
                    f"**Recommended Bet:** {opp['recommended_bet']}",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing today's games: {str(e)}"
            )

    async def _execute_my_insights(self, interaction: discord.Interaction):
        """Execute my insights command."""
        await interaction.response.defer()

        try:
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return

            insights = await self.bot.real_ml_service.get_user_betting_insights(
                interaction.user.id
            )

            embed = discord.Embed(
                title="🧠 Your Personalized Betting Insights",
                description="ML analysis of your betting patterns and recommendations",
                color=discord.Color.blue(),
                timestamp=datetime.now(),
            )

            embed.add_field(
                name="📊 Performance Analysis",
                value=insights.get("performance_analysis", "No data available"),
                inline=False,
            )

            embed.add_field(
                name="🎯 Recommendations",
                value=insights.get("recommendations", "No recommendations available"),
                inline=False,
            )

            embed.add_field(
                name="💡 Improvement Tips",
                value=insights.get("improvement_tips", "No tips available"),
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting insights: {str(e)}")

    async def _execute_live_odds(self, interaction: discord.Interaction):
        """Execute live odds command."""
        await interaction.response.defer()

        try:
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return

            odds_data = await self.bot.real_ml_service.get_live_odds()

            if not odds_data:
                embed = discord.Embed(
                    title="📊 No Live Odds Available",
                    description="No live odds data found for today's games.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title="💰 Live Odds Analysis",
                description="Current odds for today's games with ML insights",
                color=discord.Color.gold(),
                timestamp=datetime.now(),
            )

            for i, game in enumerate(odds_data[:5], 1):
                embed.add_field(
                    name=f"{i}. {game['home_team']} vs {game['away_team']}",
                    value=f"**Sport:** {game['sport'].title()}\n"
                    f"**League:** {game['league']}\n"
                    f"**Home:** {game['home_odds']}\n"
                    f"**Away:** {game['away_odds']}\n"
                    f"**Draw:** {game.get('draw_odds', 'N/A')}\n"
                    f"**ML Value:** {game.get('ml_value', 'N/A')}",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting live odds: {str(e)}")

    async def _execute_team_stats(
        self, interaction: discord.Interaction, sport: str, league: str, team: str
    ):
        """Execute team stats command."""
        await interaction.response.defer()

        try:
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return

            stats = await self.bot.real_ml_service.get_team_statistics(team, sport)

            if not stats:
                embed = discord.Embed(
                    title="📊 No Team Statistics Available",
                    description=f"No statistics found for {team} in {league}.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"📊 {team} Statistics",
                description=f"Team performance data for {league}",
                color=discord.Color.blue(),
                timestamp=datetime.now(),
            )

            for stat_name, stat_value in stats.items():
                embed.add_field(
                    name=stat_name.replace("_", " ").title(),
                    value=str(stat_value),
                    inline=True,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting team stats: {str(e)}")

    async def _execute_analyze_game(
        self,
        interaction: discord.Interaction,
        sport: str,
        league: str,
        home_team: str,
        away_team: str,
    ):
        """Execute analyze game command."""
        await interaction.response.defer()

        try:
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return

            analysis = await self.bot.real_ml_service.analyze_specific_game(
                home_team, away_team, sport, interaction.user.id
            )

            if not analysis:
                embed = discord.Embed(
                    title="❌ Game Analysis Failed",
                    description=f"Could not analyze {home_team} vs {away_team}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"🎯 {home_team} vs {away_team} Analysis",
                description=f"ML-powered analysis for {league} game",
                color=discord.Color.green(),
                timestamp=datetime.now(),
            )

            embed.add_field(
                name="📊 Prediction",
                value=analysis.get("prediction", "No prediction available"),
                inline=False,
            )

            embed.add_field(
                name="🎯 Confidence",
                value=f"{analysis.get('confidence', 0)}%",
                inline=True,
            )

            embed.add_field(
                name="💰 Recommended Bet",
                value=analysis.get("recommended_bet", "No recommendation"),
                inline=True,
            )

            embed.add_field(
                name="📈 Reasoning",
                value=analysis.get("reasoning", "No reasoning available"),
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error analyzing game: {str(e)}")


class RealMLCommands(commands.Cog):
    """Real ML commands that use live API data (Platinum servers only)."""

    def __init__(self, bot):
        self.bot = bot

    async def check_platinum_guild(self, interaction: discord.Interaction) -> bool:
        """Check if the guild has Platinum subscription."""
        try:
            # First check if guild_settings table exists and has the guild
            result = await self.bot.db_manager.fetch_one(
                "SELECT subscription_level FROM guild_settings WHERE guild_id = %s",
                interaction.guild_id,
            )

            if not result:
                # Create default guild settings if they don't exist
                await self.bot.db_manager.execute(
                    """
                    INSERT IGNORE INTO guild_settings
                    (guild_id, guild_name, subscription_level, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                    """,
                    interaction.guild_id,
                    interaction.guild.name if interaction.guild else "Unknown Guild",
                    "free",  # Default to free tier
                )
                result = {"subscription_level": "free"}

            is_platinum = result.get("subscription_level") == "platinum"

            if not is_platinum:
                embed = discord.Embed(
                    title="🔒 Platinum Feature Required",
                    description="This feature is only available to Platinum tier servers.\n"
                    "Contact your server administrator to upgrade to Platinum.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking Platinum status: {e}")
            await interaction.response.send_message(
                "❌ Error checking server subscription level.", ephemeral=True
            )
            return False

    @app_commands.command(
        name="analyze_today",
        description="Get today's best betting opportunities using real sports data (Platinum)",
    )
    async def analyze_today(self, interaction: discord.Interaction):
        """Analyze today's games using real API data and ML predictions (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        view = MLCommandView(self.bot, "Analyze Today")
        view.add_item(SportDropdown(view))

        await interaction.response.send_message(
            "🎯 **Analyze Today** - Select a sport to get today's best betting opportunities:",
            view=view,
        )

    @app_commands.command(
        name="analyze_game",
        description="Analyze a specific game using real sports data (Platinum)",
    )
    async def analyze_game(self, interaction: discord.Interaction):
        """Analyze a specific game using real API data and ML predictions (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        view = MLCommandView(self.bot, "Analyze Game")
        view.add_item(SportDropdown(view))

        await interaction.response.send_message(
            "🎯 **Analyze Game** - Select a sport to analyze a specific game:",
            view=view,
        )

    @app_commands.command(
        name="my_insights",
        description="Get personalized betting insights based on your history (Platinum)",
    )
    async def my_insights(self, interaction: discord.Interaction):
        """Get personalized betting insights (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        view = MLCommandView(self.bot, "My Insights")
        view.add_item(SportDropdown(view))

        await interaction.response.send_message(
            "🧠 **My Insights** - Select a sport to get personalized insights:",
            view=view,
        )

    @app_commands.command(
        name="live_odds", description="Get live odds for today's games (Platinum)"
    )
    async def live_odds(self, interaction: discord.Interaction):
        """Get live odds analysis (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        view = MLCommandView(self.bot, "Live Odds")
        view.add_item(SportDropdown(view))

        await interaction.response.send_message(
            "💰 **Live Odds** - Select a sport to get live odds analysis:", view=view
        )

    @app_commands.command(
        name="team_stats",
        description="Get team statistics and recent performance (Platinum)",
    )
    async def team_stats(self, interaction: discord.Interaction):
        """Get team statistics (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        view = MLCommandView(self.bot, "Team Stats")
        view.add_item(SportDropdown(view))

        await interaction.response.send_message(
            "📊 **Team Stats** - Select a sport to get team statistics:", view=view
        )

    @app_commands.command(
        name="manual", description="Manual betting entry with ML analysis (Platinum)"
    )
    async def manual(self, interaction: discord.Interaction):
        """Manual betting entry with ML analysis (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        embed = discord.Embed(
            title="📝 Manual Betting Entry",
            description="Use this command to manually enter bets and get ML analysis.\n\n"
            "**Available Commands:**\n"
            "• `/manual bet` - Enter a manual bet\n"
            "• `/manual analyze` - Analyze a manual game\n"
            "• `/manual history` - View manual bet history",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="manual_bet", description="Enter a manual bet with ML analysis (Platinum)"
    )
    @app_commands.describe(
        home_team="Home team name",
        away_team="Away team name",
        bet_type="Type of bet (moneyline, spread, total)",
        bet_selection="Your bet selection",
        bet_amount="Amount to bet",
        odds="Odds for your bet",
    )
    async def manual_bet(
        self,
        interaction: discord.Interaction,
        home_team: str,
        away_team: str,
        bet_type: str,
        bet_selection: str,
        bet_amount: float,
        odds: float,
    ):
        """Enter a manual bet with ML analysis (Platinum only)."""
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Store the manual bet
            await self.bot.db_manager.execute(
                """
                INSERT INTO bets (user_id, guild_id, home_team, away_team, bet_type,
                                bet_selection, bet_amount, odds, is_manual, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
                """,
                interaction.user.id,
                interaction.guild_id,
                home_team,
                away_team,
                bet_type,
                bet_selection,
                bet_amount,
                odds,
            )

            # Get ML analysis for the manual bet
            if self.bot.real_ml_service:
                analysis = await self.bot.real_ml_service.analyze_specific_game(
                    home_team, away_team, "manual", interaction.user.id
                )
            else:
                analysis = None

            embed = discord.Embed(
                title="📝 Manual Bet Recorded",
                description=f"Your manual bet has been recorded and analyzed.",
                color=discord.Color.green(),
                timestamp=datetime.now(),
            )

            embed.add_field(
                name="🏈 Game",
                value=f"{home_team} vs {away_team}",
                inline=False,
            )

            embed.add_field(
                name="💰 Bet Details",
                value=f"**Type:** {bet_type}\n"
                f"**Selection:** {bet_selection}\n"
                f"**Amount:** ${bet_amount:.2f}\n"
                f"**Odds:** {odds}",
                inline=True,
            )

            if analysis:
                embed.add_field(
                    name="🧠 ML Analysis",
                    value=f"**Prediction:** {analysis.get('prediction', 'N/A')}\n"
                    f"**Confidence:** {analysis.get('confidence', 0)}%\n"
                    f"**Recommendation:** {analysis.get('recommended_bet', 'N/A')}",
                    inline=True,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error recording manual bet: {str(e)}")


async def setup(bot):
    """Set up the RealMLCommands cog."""
    await bot.add_cog(RealMLCommands(bot))
