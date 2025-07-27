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


class RealMLCommands(commands.Cog):
    """Real ML commands that use live API data (Platinum servers only)."""

    def __init__(self, bot):
        self.bot = bot

    async def check_platinum_guild(self, interaction: discord.Interaction) -> bool:
        """Check if the guild has Platinum subscription."""
        try:
            is_platinum = await self.bot.platinum_service.is_platinum_guild(
                interaction.guild_id
            )
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

        # Check Platinum access
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Use the bot's real ML service
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return
            real_ml_service = self.bot.real_ml_service

            # Get today's opportunities
            opportunities = await real_ml_service.analyze_todays_games(
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

            # Create embed with opportunities
            embed = discord.Embed(
                title="🎯 Today's Best Betting Opportunities",
                description=f"ML-powered analysis using real sports data\n"
                f"Found {len(opportunities)} high-confidence opportunities",
                color=discord.Color.green(),
                timestamp=datetime.now(),
            )

            for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
                game_info = opp["game_info"]

                embed.add_field(
                    name=f"{i}. {game_info['home_team']} vs {game_info['away_team']}",
                    value=f"**Sport:** {game_info['sport'].title()}\n"
                    f"**League:** {game_info['league']}\n"
                    f"**Prediction:** {opp['prediction'].title()}\n"
                    f"**Confidence:** {opp['confidence']:.1%}\n"
                    f"**Recommended Bet:** ${opp['recommended_bet']:.2f}\n"
                    f"**Risk Level:** {opp['risk_level'].title()}\n"
                    f"**Reasoning:** {opp['reasoning']}",
                    inline=False,
                )

            embed.set_footer(text="Use /analyze_game for detailed analysis of any game")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing today's games: {str(e)}"
            )

    @app_commands.command(
        name="analyze_game",
        description="Analyze a specific game using real sports data (Platinum)",
    )
    @app_commands.describe(
        home_team="Home team name (e.g., Lakers, Manchester United)",
        away_team="Away team name (e.g., Warriors, Chelsea)",
        sport="Sport (football, basketball, baseball, hockey, american-football)",
    )
    async def analyze_game(
        self,
        interaction: discord.Interaction,
        home_team: str,
        away_team: str,
        sport: str = "football",
    ):
        """Analyze a specific game using real API data and ML (Platinum only)."""

        # Check Platinum access
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Use the bot's real ML service
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return
            real_ml_service = self.bot.real_ml_service

            # Analyze the specific game
            analysis = await real_ml_service.analyze_specific_game(
                home_team, away_team, sport, interaction.user.id
            )

            if not analysis:
                embed = discord.Embed(
                    title="❌ Game Not Found",
                    description=f"Could not find {home_team} vs {away_team} in {sport} data.\n"
                    "💡 Make sure the team names are correct and the game is scheduled.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

            # Create detailed analysis embed
            game_info = analysis["game_info"]

            embed = discord.Embed(
                title=f"🎯 {home_team} vs {away_team} Analysis",
                description=f"ML-powered analysis using real {sport} data",
                color=discord.Color.blue(),
                timestamp=datetime.now(),
            )

            # Game information
            embed.add_field(
                name="📊 Game Info",
                value=f"**Sport:** {game_info['sport'].title()}\n"
                f"**League:** {game_info['league']}\n"
                f"**Date:** {game_info['date']}",
                inline=False,
            )

            # ML prediction
            embed.add_field(
                name="🤖 ML Prediction",
                value=f"**Prediction:** {analysis['prediction'].title()}\n"
                f"**Confidence:** {analysis['confidence']:.1%}\n"
                f"**Reasoning:** {analysis['reasoning']}",
                inline=False,
            )

            # Betting recommendations
            embed.add_field(
                name="💰 Betting Advice",
                value=f"**Recommended Bet:** ${analysis['recommended_bet']:.2f}\n"
                f"**Risk Level:** {analysis['risk_level'].title()}\n"
                f"**Current Odds:** {analysis['odds'].get('home_win', 'N/A')}",
                inline=True,
            )

            # Set color based on confidence
            if analysis["confidence"] > 0.8:
                embed.color = discord.Color.green()
            elif analysis["confidence"] > 0.6:
                embed.color = discord.Color.blue()
            else:
                embed.color = discord.Color.orange()

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error analyzing game: {str(e)}")

    @app_commands.command(
        name="my_insights",
        description="Get personalized betting insights based on your history (Platinum)",
    )
    async def my_insights(self, interaction: discord.Interaction):
        """Get personalized insights based on user's betting history (Platinum only)."""

        # Check Platinum access
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Use the bot's real ML service
            if not self.bot.real_ml_service:
                await interaction.followup.send("❌ Real ML service not available")
                return
            real_ml_service = self.bot.real_ml_service

            # Get user insights
            insights = await real_ml_service.get_user_betting_insights(
                interaction.user.id
            )

            if "error" in insights:
                await interaction.followup.send(f"❌ {insights['error']}")
                return

            if "message" in insights:
                # No betting history
                embed = discord.Embed(
                    title="📊 Your Betting Insights",
                    description=insights["message"],
                    color=discord.Color.blue(),
                )

                if insights.get("recommendations"):
                    embed.add_field(
                        name="💡 Recommendations",
                        value="\n".join(
                            f"• {rec}" for rec in insights["recommendations"]
                        ),
                        inline=False,
                    )

                await interaction.followup.send(embed=embed)
                return

            # Create insights embed
            patterns = insights["betting_patterns"]

            embed = discord.Embed(
                title="📊 Your Betting Insights",
                description="Personalized analysis of your betting patterns",
                color=discord.Color.purple(),
                timestamp=datetime.now(),
            )

            # Betting patterns
            embed.add_field(
                name="📈 Your Patterns",
                value=f"**Total Bets:** {patterns['total_bets']}\n"
                f"**Success Rate:** {patterns['success_rate']:.1%}\n"
                f"**Average Bet:** ${patterns['avg_bet_size']:.2f}\n"
                f"**Total Wagered:** ${patterns['total_wagered']:.2f}\n"
                f"**Risk Profile:** {patterns['risk_profile'].title()}\n"
                f"**Favorite Sports:** {', '.join(patterns['preferred_sports'][:3])}",
                inline=False,
            )

            # Recommendations
            if insights.get("recommendations"):
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(f"• {rec}" for rec in insights["recommendations"]),
                    inline=False,
                )

            # Improvement tips
            if insights.get("improvement_tips"):
                embed.add_field(
                    name="🚀 Improvement Tips",
                    value="\n".join(f"• {tip}" for tip in insights["improvement_tips"]),
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting insights: {str(e)}")

    @app_commands.command(
        name="live_odds", description="Get live odds for today's games (Platinum)"
    )
    async def live_odds(self, interaction: discord.Interaction):
        """Get live odds for today's major games (Platinum only)."""

        # Check Platinum access
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Get today's games with odds
            today = datetime.now().strftime("%Y-%m-%d")
            games_with_odds = await self._get_todays_games_with_odds(today)

            if not games_with_odds:
                embed = discord.Embed(
                    title="📊 No Live Odds Available",
                    description="No games with live odds found for today.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed)
                return

            # Create odds embed
            embed = discord.Embed(
                title="📊 Live Odds - Today's Games",
                description=f"Current betting odds for today's major games\n"
                f"Found {len(games_with_odds)} games with odds",
                color=discord.Color.gold(),
                timestamp=datetime.now(),
            )

            for i, game in enumerate(games_with_odds[:5], 1):  # Show top 5
                embed.add_field(
                    name=f"{i}. {game['home_team']} vs {game['away_team']}",
                    value=f"**Sport:** {game['sport'].title()}\n"
                    f"**League:** {game['league']}\n"
                    f"**Home Win:** {game['odds']['home_win']:.2f}\n"
                    f"**Away Win:** {game['odds']['away_win']:.2f}\n"
                    f"**Draw:** {game['odds'].get('draw', 'N/A')}\n"
                    f"**Time:** {game['time']}",
                    inline=False,
                )

            embed.set_footer(
                text="Use /analyze_game to get ML predictions for any game"
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting live odds: {str(e)}")

    @app_commands.command(
        name="team_stats",
        description="Get team statistics and recent performance (Platinum)",
    )
    @app_commands.describe(
        team_name="Team name (e.g., Lakers, Manchester United)",
        sport="Sport (football, basketball, baseball, hockey, american-football)",
    )
    async def team_stats(
        self, interaction: discord.Interaction, team_name: str, sport: str = "football"
    ):
        """Get team statistics and recent performance (Platinum only)."""

        # Check Platinum access
        if not await self.check_platinum_guild(interaction):
            return

        await interaction.response.defer()

        try:
            # Get team stats from API
            team_stats = await self._get_team_statistics(team_name, sport)

            if not team_stats:
                embed = discord.Embed(
                    title="❌ Team Not Found",
                    description=f"Could not find {team_name} in {sport} data.\n"
                    "💡 Make sure the team name is correct.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

            # Create team stats embed
            embed = discord.Embed(
                title=f"📊 {team_name} Statistics",
                description=f"Team performance data for {sport}",
                color=discord.Color.blue(),
                timestamp=datetime.now(),
            )

            # Basic stats
            embed.add_field(
                name="📈 Season Stats",
                value=f"**Wins:** {team_stats.get('wins', 'N/A')}\n"
                f"**Losses:** {team_stats.get('losses', 'N/A')}\n"
                f"**Draws:** {team_stats.get('draws', 'N/A')}\n"
                f"**Win Rate:** {team_stats.get('win_rate', 'N/A')}",
                inline=True,
            )

            # Recent form
            embed.add_field(
                name="🔥 Recent Form",
                value=f"**Last 5:** {team_stats.get('recent_form', 'N/A')}\n"
                f"**Home Record:** {team_stats.get('home_record', 'N/A')}\n"
                f"**Away Record:** {team_stats.get('away_record', 'N/A')}",
                inline=True,
            )

            # League info
            embed.add_field(
                name="🏆 League Info",
                value=f"**League:** {team_stats.get('league', 'N/A')}\n"
                f"**Position:** {team_stats.get('position', 'N/A')}\n"
                f"**Points:** {team_stats.get('points', 'N/A')}",
                inline=True,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting team stats: {str(e)}")

    async def _get_todays_games_with_odds(self, date: str) -> List[Dict]:
        """Get today's games with live odds."""

        try:
            if not self.bot.real_ml_service:
                return []

            # Get today's games
            games = await self.bot.real_ml_service._get_todays_games_from_api(date)

            games_with_odds = []

            for game in games[:10]:  # Limit to 10 games
                try:
                    # Get odds for this game
                    odds = await self.bot.real_ml_service._get_game_odds(
                        game.get("fixture", {}).get("id")
                    )

                    if odds and odds.get("home_win"):
                        games_with_odds.append(
                            {
                                "home_team": game["teams"]["home"]["name"],
                                "away_team": game["teams"]["away"]["name"],
                                "sport": game.get("league", {}).get("type", "football"),
                                "league": game["league"]["name"],
                                "odds": odds,
                                "time": game["fixture"]["date"],
                            }
                        )
                except Exception as e:
                    continue

            return games_with_odds

        except Exception as e:
            logger.error(f"Error getting games with odds: {e}")
            return []

    async def _get_team_statistics(self, team_name: str, sport: str) -> Optional[Dict]:
        """Get team statistics from API."""

        try:
            if not self.bot.real_ml_service:
                return None

            # Search for team in API data
            team_data = await self.bot.real_ml_service._find_team_in_api(
                team_name, sport
            )

            if not team_data:
                return None

            # Get detailed team stats
            team_stats = await self.bot.real_ml_service._get_team_stats(
                sport, team_data["id"]
            )

            if not team_stats:
                return None

            # Format stats for display
            return {
                "wins": team_stats.get("all", {}).get("win", "N/A"),
                "losses": team_stats.get("all", {}).get("lose", "N/A"),
                "draws": team_stats.get("all", {}).get("draw", "N/A"),
                "win_rate": f"{team_stats.get('all', {}).get('win', 0) / max(team_stats.get('all', {}).get('played', 1), 1) * 100:.1f}%",
                "recent_form": team_stats.get("form", "N/A"),
                "home_record": f"{team_stats.get('home', {}).get('win', 0)}-{team_stats.get('home', {}).get('lose', 0)}-{team_stats.get('home', {}).get('draw', 0)}",
                "away_record": f"{team_stats.get('away', {}).get('win', 0)}-{team_stats.get('away', {}).get('lose', 0)}-{team_stats.get('away', {}).get('draw', 0)}",
                "league": team_stats.get("league", {}).get("name", "N/A"),
                "position": team_stats.get("rank", "N/A"),
                "points": team_stats.get("points", "N/A"),
            }

        except Exception as e:
            logger.error(f"Error getting team statistics: {e}")
            return None


async def setup(bot):
    await bot.add_cog(RealMLCommands(bot))
