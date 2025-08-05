"""
Predictive Analytics Commands

This module provides Discord commands for accessing predictive analytics
and machine learning features of the DBSBM system.
"""

import json
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class PredictiveCommands(commands.Cog):
    """Commands for predictive analytics and ML features."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="predict", description="Generate a prediction using ML models"
    )
    @app_commands.describe(
        model_type="Type of prediction to generate",
        input_data="JSON input data for prediction",
    )
    @app_commands.choices(
        model_type=[
            app_commands.Choice(name="Bet Outcome", value="bet_outcome"),
            app_commands.Choice(name="User Behavior", value="user_behavior"),
            app_commands.Choice(name="Revenue Forecast", value="revenue_forecast"),
            app_commands.Choice(name="Risk Assessment", value="risk_assessment"),
            app_commands.Choice(name="Churn Prediction", value="churn_prediction"),
            app_commands.Choice(name="Recommendation", value="recommendation"),
        ]
    )
    async def predict(
        self,
        interaction: discord.Interaction,
        model_type: str,
        input_data: Optional[str] = None,
    ):
        """Generate a prediction using ML models."""
        try:
            # Check if user has permission
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ You need administrator permissions to use predictive features.",
                    ephemeral=True,
                )
                return

            # Parse input data
            if input_data:
                try:
                    parsed_input = json.loads(input_data)
                except json.JSONDecodeError:
                    await interaction.response.send_message(
                        "❌ Invalid JSON format for input_data. Please provide valid JSON.",
                        ephemeral=True,
                    )
                    return
            else:
                # Use default test data
                parsed_input = {
                    "odds": 2.5,
                    "team_stats": {"wins": 10, "losses": 5},
                    "player_stats": {"avg_points": 20.5},
                    "historical_performance": 0.75,
                    "weather": "clear",
                    "venue": "home",
                }

            # Get prediction from service
            from services.predictive_service import PredictionType

            prediction_type_map = {
                "bet_outcome": PredictionType.BET_OUTCOME,
                "user_behavior": PredictionType.USER_BEHAVIOR,
                "revenue_forecast": PredictionType.REVENUE_FORECAST,
                "risk_assessment": PredictionType.RISK_ASSESSMENT,
                "churn_prediction": PredictionType.CHURN_PREDICTION,
                "recommendation": PredictionType.RECOMMENDATION,
            }

            prediction_type = prediction_type_map.get(model_type)
            if not prediction_type:
                await interaction.response.send_message(
                    f"❌ Invalid model type: {model_type}", ephemeral=True
                )
                return

            # Use default model for now
            model_id = "bet_outcome_predictor_v1"

            prediction = await self.bot.predictive_service.generate_prediction(
                model_id=model_id,
                input_data=parsed_input,
                prediction_type=prediction_type,
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
            )

            if prediction:
                embed = discord.Embed(
                    title="🤖 ML Prediction Generated",
                    description=f"**Model Type:** {model_type.replace('_', ' ').title()}",
                    color=discord.Color.green(),
                )

                embed.add_field(
                    name="Prediction Result",
                    value=str(prediction.prediction_result),
                    inline=False,
                )

                embed.add_field(
                    name="Confidence Score",
                    value=f"{prediction.confidence_score:.2%}",
                    inline=True,
                )

                embed.add_field(name="Model ID", value=prediction.model_id, inline=True)

                embed.add_field(
                    name="Input Data",
                    value=f"```json\n{json.dumps(parsed_input, indent=2)}```",
                    inline=False,
                )

                embed.set_footer(
                    text=f"Generated at {prediction.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Failed to generate prediction. Please try again later.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.error(f"Error in predict command: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}", ephemeral=True
            )

    @app_commands.command(
        name="ml_dashboard", description="View predictive analytics dashboard"
    )
    async def ml_dashboard(self, interaction: discord.Interaction):
        """View predictive analytics dashboard."""
        try:
            # Check if user has permission
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ You need administrator permissions to view the ML dashboard.",
                    ephemeral=True,
                )
                return

            # Get dashboard data
            dashboard_data = (
                await self.bot.predictive_service.get_predictive_dashboard_data()
            )

            embed = discord.Embed(
                title="📊 Predictive Analytics Dashboard",
                description="Machine Learning Model Overview",
                color=discord.Color.blue(),
            )

            # Model statistics
            if "model_statistics" in dashboard_data:
                stats = dashboard_data["model_statistics"]
                embed.add_field(
                    name="📈 Model Statistics",
                    value=f"**Total Models:** {stats.get('total_models', 0)}\n"
                    f"**Active Models:** {stats.get('active_models', 0)}\n"
                    f"**Model Types:** {len(stats.get('models_by_type', {}))}\n"
                    f"**Model Statuses:** {len(stats.get('models_by_status', {}))}",
                    inline=True,
                )

            # Performance summary
            if "performance_summary" in dashboard_data:
                perf = dashboard_data["performance_summary"]
                embed.add_field(
                    name="🎯 Performance Summary",
                    value=f"**Average Accuracy:** {perf.get('average_accuracy', 0):.2%}\n"
                    f"**Best Model:** {perf.get('best_performing_model', 'N/A')}\n"
                    f"**Models Needing Retraining:** {len(perf.get('models_needing_retraining', []))}",
                    inline=True,
                )

            # Recent predictions
            if "recent_predictions" in dashboard_data:
                recent = dashboard_data["recent_predictions"]
                embed.add_field(
                    name="🔄 Recent Activity",
                    value=f"**Recent Predictions:** {len(recent)}\n"
                    f"**Accuracy Trends:** {len(dashboard_data.get('accuracy_trends', []))} data points",
                    inline=True,
                )

            embed.set_footer(text="Predictive Analytics Dashboard")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in ml_dashboard command: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="ml_models", description="List available ML models")
    async def ml_models(self, interaction: discord.Interaction):
        """List available ML models."""
        try:
            # Check if user has permission
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ You need administrator permissions to view ML models.",
                    ephemeral=True,
                )
                return

            # Get model templates
            templates = await self.bot.predictive_service.get_model_templates()

            embed = discord.Embed(
                title="🤖 Available ML Models",
                description="Machine Learning Model Templates",
                color=discord.Color.purple(),
            )

            for template_id, template in templates.items():
                embed.add_field(
                    name=f"🔧 {template['name']}",
                    value=f"**Type:** {template['model_type'].value}\n"
                    f"**Description:** {template['description']}\n"
                    f"**Algorithm:** {template['algorithm']}\n"
                    f"**Features:** {len(template['features'])}",
                    inline=False,
                )

            embed.set_footer(text=f"Total Models: {len(templates)}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in ml_models command: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}", ephemeral=True
            )


async def setup(bot):
    """Set up the predictive commands cog."""
    await bot.add_cog(PredictiveCommands(bot))
    logger.info("Predictive commands cog loaded successfully")
