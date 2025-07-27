#!/usr/bin/env python3
"""
User-Friendly ML Commands - Making ML Accessible to Real Users

These commands let users interact with ML without knowing JSON or technical details.
"""

import asyncio

import discord
from discord import app_commands
from discord.ext import commands


class UserFriendlyMLCommands(commands.Cog):
    """User-friendly ML commands that don't require technical knowledge."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="analyze_game",
        description="Analyze a specific game for betting opportunities",
    )
    @app_commands.describe(
        home_team="Home team name",
        away_team="Away team name",
        sport="Sport (NBA, NFL, MLB, etc.)",
    )
    async def analyze_game(
        self,
        interaction: discord.Interaction,
        home_team: str,
        away_team: str,
        sport: str = "NBA",
    ):
        """Analyze a game for betting opportunities."""

        await interaction.response.defer()

        try:
            # Find the game in our database
            game = await self.bot.db_manager.fetch_one(
                "SELECT * FROM games WHERE home_team LIKE %s AND away_team LIKE %s AND sport = %s",
                (f"%{home_team}%", f"%{away_team}%", sport),
            )

            if not game:
                await interaction.followup.send(
                    f"❌ Game not found: {home_team} vs {away_team} ({sport})\n"
                    f"💡 Try using `/games` to see available games."
                )
                return

            # Analyze the game using ML
            analysis = await self.bot.practical_ml_service.analyze_upcoming_game(
                game["id"], interaction.user.id
            )

            # Create user-friendly embed
            embed = discord.Embed(
                title=f"🎯 {home_team} vs {away_team} Analysis",
                description=f"ML-powered betting analysis for {sport}",
                color=discord.Color.blue(),
            )

            # Game info
            embed.add_field(
                name="📊 Game Info",
                value=f"**League:** {analysis['game_info']['league']}\n"
                f"**Start Time:** {analysis['game_info']['start_time']}\n"
                f"**Current Odds:** {analysis['current_odds']['home_win']:.2f}",
                inline=False,
            )

            # Recommendations
            if analysis["recommendations"]:
                rec = analysis["recommendations"][0]
                embed.add_field(
                    name="🤖 ML Recommendation",
                    value=f"**{rec['message']}**\n"
                    f"**Confidence:** {rec['confidence']}\n"
                    f"**Reasoning:** {rec['reasoning']}",
                    inline=False,
                )

                # Bet sizing
                embed.add_field(
                    name="💰 Bet Sizing",
                    value=f"**Recommended Bet:** ${analysis['optimal_bet_size']:.2f}\n"
                    f"**Risk Level:** {analysis['risk_assessment'].title()}",
                    inline=True,
                )

                embed.color = discord.Color.green()
            else:
                embed.add_field(
                    name="⚠️ No Strong Prediction",
                    value="ML model doesn't have enough confidence for a recommendation.\n"
                    "Consider waiting for more data or different betting options.",
                    inline=False,
                )
                embed.color = discord.Color.orange()

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error analyzing game: {str(e)}")

    @app_commands.command(
        name="daily_opportunities", description="Get today's best betting opportunities"
    )
    async def daily_opportunities(self, interaction: discord.Interaction):
        """Get today's best betting opportunities."""

        await interaction.response.defer()

        try:
            opportunities = (
                await self.bot.practical_ml_service.get_daily_betting_opportunities(
                    interaction.user.id
                )
            )

            if not opportunities:
                await interaction.followup.send(
                    "📅 No high-confidence betting opportunities found for today.\n"
                    "💡 Check back later or try `/analyze_game` for specific games."
                )
                return

            embed = discord.Embed(
                title="🎯 Today's Best Betting Opportunities",
                description="ML-powered recommendations for today's games",
                color=discord.Color.green(),
            )

            for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
                game = opp["game"]
                rec = opp["recommendation"]

                embed.add_field(
                    name=f"{i}. {game['home_team']} vs {game['away_team']}",
                    value=f"**{rec['message']}**\n"
                    f"**Confidence:** {rec['confidence']}\n"
                    f"**Recommended Bet:** ${opp['bet_amount']:.2f}\n"
                    f"**Risk:** {opp['risk_level'].title()}\n"
                    f"**League:** {game['league']}",
                    inline=False,
                )

            embed.set_footer(text="Use /analyze_game for detailed analysis of any game")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting opportunities: {str(e)}")

    @app_commands.command(
        name="my_insights",
        description="Get personalized insights about your betting patterns",
    )
    async def my_insights(self, interaction: discord.Interaction):
        """Get personalized betting insights."""

        await interaction.response.defer()

        try:
            insights = await self.bot.practical_ml_service.get_user_betting_insights(
                interaction.user.id
            )

            embed = discord.Embed(
                title="📊 Your Betting Insights",
                description="Personalized analysis of your betting patterns",
                color=discord.Color.purple(),
            )

            # Betting patterns
            patterns = insights["betting_patterns"]
            embed.add_field(
                name="📈 Your Patterns",
                value=f"**Success Rate:** {patterns['success_rate']:.1%}\n"
                f"**Average Bet:** ${patterns['avg_bet_size']:.2f}\n"
                f"**Risk Profile:** {patterns['risk_profile'].title()}\n"
                f"**Favorite Sports:** {', '.join(patterns['favorite_sports'][:3])}",
                inline=False,
            )

            # Recommendations
            if insights["recommendations"]:
                embed.add_field(
                    name="💡 Key Insights",
                    value="\n".join(f"• {rec}" for rec in insights["recommendations"]),
                    inline=False,
                )

            # Improvement suggestions
            if insights["improvement_suggestions"]:
                embed.add_field(
                    name="🚀 Improvement Tips",
                    value="\n".join(
                        f"• {suggestion}"
                        for suggestion in insights["improvement_suggestions"]
                    ),
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error getting insights: {str(e)}")

    @app_commands.command(
        name="compare_teams", description="Compare two teams for betting analysis"
    )
    @app_commands.describe(
        team1="First team name",
        team2="Second team name",
        sport="Sport (NBA, NFL, MLB, etc.)",
    )
    async def compare_teams(
        self,
        interaction: discord.Interaction,
        team1: str,
        team2: str,
        sport: str = "NBA",
    ):
        """Compare two teams for betting analysis."""

        await interaction.response.defer()

        try:
            # Get team stats
            team1_stats = await self.bot.api_service.get_team_stats(team1, sport)
            team2_stats = await self.bot.api_service.get_team_stats(team2, sport)

            # Use ML to predict head-to-head
            prediction = await self.bot.practical_ml_service._predict_head_to_head(
                team1, team2, team1_stats, team2_stats
            )

            embed = discord.Embed(
                title=f"⚔️ {team1} vs {team2} Comparison",
                description=f"Head-to-head analysis for {sport}",
                color=discord.Color.blue(),
            )

            # Team 1 stats
            embed.add_field(
                name=f"🏀 {team1}",
                value=f"**Record:** {team1_stats['wins']}-{team1_stats['losses']}\n"
                f"**Recent Form:** {team1_stats['recent_form']}\n"
                f"**Home Record:** {team1_stats['home_record']}\n"
                f"**Away Record:** {team1_stats['away_record']}",
                inline=True,
            )

            # Team 2 stats
            embed.add_field(
                name=f"🏀 {team2}",
                value=f"**Record:** {team2_stats['wins']}-{team2_stats['losses']}\n"
                f"**Recent Form:** {team2_stats['recent_form']}\n"
                f"**Home Record:** {team2_stats['home_record']}\n"
                f"**Away Record:** {team2_stats['away_record']}",
                inline=True,
            )

            # ML prediction
            embed.add_field(
                name="🤖 ML Prediction",
                value=f"**{prediction['winner']}** is predicted to win\n"
                f"**Confidence:** {prediction['confidence']:.1%}\n"
                f"**Key Factor:** {prediction['key_factor']}",
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error comparing teams: {str(e)}")

    @app_commands.command(
        name="bankroll_advice",
        description="Get personalized bankroll management advice",
    )
    async def bankroll_advice(self, interaction: discord.Interaction):
        """Get personalized bankroll management advice."""

        await interaction.response.defer()

        try:
            # Get user's betting history
            user_bets = await self.bot.db_manager.fetch_all(
                "SELECT * FROM bets WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
                (interaction.user.id,),
            )

            if not user_bets:
                await interaction.followup.send(
                    "💡 You haven't placed any bets yet!\n"
                    "Start betting to get personalized bankroll advice."
                )
                return

            # Calculate bankroll metrics
            total_bets = len(user_bets)
            total_wagered = sum(bet["amount"] for bet in user_bets)
            total_won = sum(
                bet["amount"] for bet in user_bets if bet["result"] == "win"
            )
            avg_bet = total_wagered / total_bets

            # Calculate Kelly Criterion recommendation
            win_rate = len([b for b in user_bets if b["result"] == "win"]) / total_bets
            avg_odds = 2.0  # Assuming average odds of 2.0

            kelly_fraction = (win_rate * avg_odds - 1) / (avg_odds - 1)
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

            embed = discord.Embed(
                title="💰 Bankroll Management Advice",
                description="Personalized recommendations for your betting strategy",
                color=discord.Color.gold(),
            )

            # Current stats
            embed.add_field(
                name="📊 Your Stats",
                value=f"**Total Bets:** {total_bets}\n"
                f"**Total Wagered:** ${total_wagered:.2f}\n"
                f"**Win Rate:** {win_rate:.1%}\n"
                f"**Average Bet:** ${avg_bet:.2f}",
                inline=False,
            )

            # Kelly Criterion advice
            if kelly_fraction > 0:
                recommended_bet = kelly_fraction * 1000  # Assuming $1000 bankroll
                embed.add_field(
                    name="🎯 Kelly Criterion",
                    value=f"**Recommended Bet Size:** {kelly_fraction:.1%} of bankroll\n"
                    f"**For $1000 bankroll:** ${recommended_bet:.2f}\n"
                    f"**Current average:** ${avg_bet:.2f}",
                    inline=False,
                )

                if avg_bet > recommended_bet * 1.5:
                    embed.add_field(
                        name="⚠️ Warning",
                        value="Your bet sizes are larger than recommended.\n"
                        "Consider reducing bet sizes for better bankroll management.",
                        inline=False,
                    )
                    embed.color = discord.Color.red()
                elif avg_bet < recommended_bet * 0.5:
                    embed.add_field(
                        name="💡 Opportunity",
                        value="You could increase bet sizes slightly.\n"
                        "Your win rate supports larger bets.",
                        inline=False,
                    )
                    embed.color = discord.Color.green()
            else:
                embed.add_field(
                    name="⚠️ Kelly Criterion",
                    value="Your win rate doesn't support positive expected value betting.\n"
                    "Consider improving your betting strategy before increasing bet sizes.",
                    inline=False,
                )
                embed.color = discord.Color.orange()

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error getting bankroll advice: {str(e)}"
            )


async def setup(bot):
    await bot.add_cog(UserFriendlyMLCommands(bot))
