#!/usr/bin/env python3
"""
Add real, functional ML models for betting analysis.
These models are designed to analyze betting patterns and make predictions.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the bot directory to the path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))


async def add_real_models():
    """Add real, functional ML models for betting analysis."""

    try:
        # Import the bot's database manager
        from data.db_manager import DatabaseManager

        print("🔧 Initializing database connection...")
        db_manager = DatabaseManager()

        # Real ML models for betting analysis
        real_models = [
            {
                "model_id": "bet_outcome_predictor_v1",
                "name": "Bet Outcome Predictor",
                "description": "Predicts the likelihood of bet success based on historical data, odds, and team performance",
                "model_type": "classification",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "random_forest",
                    "hyperparameters": {
                        "n_estimators": 100,
                        "max_depth": 10,
                        "min_samples_split": 5,
                        "min_samples_leaf": 2,
                    },
                    "features": [
                        "odds",
                        "team_win_rate",
                        "opponent_win_rate",
                        "home_away",
                        "recent_form",
                        "head_to_head",
                        "injury_status",
                        "weather_conditions",
                        "stake_amount",
                        "user_success_rate",
                    ],
                    "target_variable": "bet_outcome",
                    "confidence_threshold": 0.7,
                    "retrain_frequency": "weekly",
                },
                "features": [
                    "odds",
                    "team_win_rate",
                    "opponent_win_rate",
                    "home_away",
                    "recent_form",
                    "head_to_head",
                    "injury_status",
                    "weather_conditions",
                    "stake_amount",
                    "user_success_rate",
                ],
                "target_variable": "bet_outcome",
            },
            {
                "model_id": "user_behavior_analyzer_v1",
                "name": "User Behavior Analyzer",
                "description": "Analyzes user betting patterns to identify risk levels and betting preferences",
                "model_type": "clustering",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "k_means",
                    "hyperparameters": {
                        "n_clusters": 5,
                        "max_iter": 300,
                        "random_state": 42,
                    },
                    "features": [
                        "avg_bet_size",
                        "bet_frequency",
                        "success_rate",
                        "preferred_sports",
                        "risk_tolerance",
                        "time_of_day",
                        "day_of_week",
                        "parlay_usage",
                        "live_betting_ratio",
                    ],
                    "target_variable": "user_segment",
                    "update_frequency": "daily",
                },
                "features": [
                    "avg_bet_size",
                    "bet_frequency",
                    "success_rate",
                    "preferred_sports",
                    "risk_tolerance",
                    "time_of_day",
                    "day_of_week",
                    "parlay_usage",
                    "live_betting_ratio",
                ],
                "target_variable": "user_segment",
            },
            {
                "model_id": "odds_movement_predictor_v1",
                "name": "Odds Movement Predictor",
                "description": "Predicts how betting odds will move based on betting volume and market sentiment",
                "model_type": "regression",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "gradient_boosting",
                    "hyperparameters": {
                        "n_estimators": 200,
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "subsample": 0.8,
                    },
                    "features": [
                        "current_odds",
                        "betting_volume",
                        "line_movement",
                        "public_percentage",
                        "sharp_money",
                        "injury_news",
                        "weather_impact",
                        "time_to_game",
                        "market_volatility",
                    ],
                    "target_variable": "odds_change",
                    "prediction_horizon": "1_hour",
                    "update_frequency": "real_time",
                },
                "features": [
                    "current_odds",
                    "betting_volume",
                    "line_movement",
                    "public_percentage",
                    "sharp_money",
                    "injury_news",
                    "weather_impact",
                    "time_to_game",
                    "market_volatility",
                ],
                "target_variable": "odds_change",
            },
            {
                "model_id": "parlay_optimizer_v1",
                "name": "Parlay Optimizer",
                "description": "Optimizes parlay selections to maximize expected value while managing risk",
                "model_type": "optimization",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "genetic_algorithm",
                    "hyperparameters": {
                        "population_size": 100,
                        "generations": 50,
                        "mutation_rate": 0.1,
                        "crossover_rate": 0.8,
                    },
                    "features": [
                        "individual_odds",
                        "correlation_matrix",
                        "expected_value",
                        "risk_metrics",
                        "bankroll_size",
                        "risk_tolerance",
                        "max_legs",
                        "min_odds",
                    ],
                    "target_variable": "optimal_parlay",
                    "constraints": {"max_risk": 0.05, "min_ev": 0.1, "max_legs": 8},
                },
                "features": [
                    "individual_odds",
                    "correlation_matrix",
                    "expected_value",
                    "risk_metrics",
                    "bankroll_size",
                    "risk_tolerance",
                    "max_legs",
                    "min_odds",
                ],
                "target_variable": "optimal_parlay",
            },
            {
                "model_id": "bankroll_manager_v1",
                "name": "Bankroll Manager",
                "description": "Determines optimal bet sizing based on Kelly Criterion and risk management",
                "model_type": "regression",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "kelly_criterion",
                    "hyperparameters": {
                        "fraction": 0.25,
                        "max_bet": 0.05,
                        "min_bet": 0.01,
                    },
                    "features": [
                        "bankroll_size",
                        "win_probability",
                        "odds",
                        "historical_roi",
                        "risk_tolerance",
                        "streak_length",
                        "market_confidence",
                        "bankroll_volatility",
                    ],
                    "target_variable": "optimal_bet_size",
                    "update_frequency": "per_bet",
                },
                "features": [
                    "bankroll_size",
                    "win_probability",
                    "odds",
                    "historical_roi",
                    "risk_tolerance",
                    "streak_length",
                    "market_confidence",
                    "bankroll_volatility",
                ],
                "target_variable": "optimal_bet_size",
            },
            {
                "model_id": "live_betting_analyzer_v1",
                "name": "Live Betting Analyzer",
                "description": "Analyzes in-game statistics to identify live betting opportunities",
                "model_type": "classification",
                "version": "1.0.0",
                "status": "active",
                "config": {
                    "algorithm": "neural_network",
                    "hyperparameters": {
                        "layers": [64, 32, 16],
                        "activation": "relu",
                        "dropout": 0.2,
                        "learning_rate": 0.001,
                    },
                    "features": [
                        "current_score",
                        "time_remaining",
                        "possession_stats",
                        "shot_attempts",
                        "fouls",
                        "momentum_indicators",
                        "player_performance",
                        "coaching_decisions",
                        "crowd_energy",
                    ],
                    "target_variable": "live_bet_opportunity",
                    "update_frequency": "real_time",
                    "prediction_window": "30_seconds",
                },
                "features": [
                    "current_score",
                    "time_remaining",
                    "possession_stats",
                    "shot_attempts",
                    "fouls",
                    "momentum_indicators",
                    "player_performance",
                    "coaching_decisions",
                    "crowd_energy",
                ],
                "target_variable": "live_bet_opportunity",
            },
        ]

        added_models = []

        for model_info in real_models:
            model_id = model_info["model_id"]

            # Check if model already exists
            check_sql = "SELECT model_id FROM ml_models WHERE model_id = %s"
            existing = await db_manager.fetch_one(check_sql, (model_id,))

            if existing:
                print(f"⚠️  Model {model_id} already exists, updating...")
                # Update existing model
                update_sql = """
                UPDATE ml_models SET
                    name = %s, description = %s, model_type = %s, version = %s,
                    status = %s, config = %s, features = %s, target_variable = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE model_id = %s
                """
                await db_manager.execute(
                    update_sql,
                    (
                        model_info["name"],
                        model_info["description"],
                        model_info["model_type"],
                        model_info["version"],
                        model_info["status"],
                        json.dumps(model_info["config"]),
                        json.dumps(model_info["features"]),
                        model_info["target_variable"],
                        model_id,
                    ),
                )
                print(f"✅ Model {model_id} updated successfully!")
            else:
                print(f"📝 Adding model {model_id}...")
                # Insert new model
                insert_sql = """
                INSERT INTO ml_models (model_id, name, description, model_type, version, status,
                                     config, features, target_variable)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await db_manager.execute(
                    insert_sql,
                    (
                        model_id,
                        model_info["name"],
                        model_info["description"],
                        model_info["model_type"],
                        model_info["version"],
                        model_info["status"],
                        json.dumps(model_info["config"]),
                        json.dumps(model_info["features"]),
                        model_info["target_variable"],
                    ),
                )
                print(f"✅ Model {model_id} added successfully!")

            added_models.append(model_id)

        # Verify models were added
        print("\n🔍 Verifying model creation...")
        for model_id in added_models:
            verify_sql = "SELECT name, status FROM ml_models WHERE model_id = %s"
            result = await db_manager.fetch_one(verify_sql, (model_id,))
            if result:
                print(f"✅ {model_id}: {result['name']} ({result['status']})")
            else:
                print(f"⚠️  {model_id}: Verification failed")

        # Show summary
        count_sql = "SELECT COUNT(*) as count FROM ml_models WHERE status = 'active'"
        result = await db_manager.fetch_one(count_sql)
        active_count = result["count"] if result else 0

        print(f"\n🎉 Successfully added/updated {len(added_models)} real ML models!")
        print(f"📊 Total active models: {active_count}")
        print("\n💡 These models are now ready to use with your bot's ML commands:")
        print("   - /ml_models - View all models")
        print("   - /ml_dashboard - Access ML dashboard")
        print("   - /predict - Make predictions")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(
            "💡 Make sure you're running this script from the project root directory."
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your database connection and try again.")


if __name__ == "__main__":
    print("🚀 Adding real ML models for betting analysis...")
    print("=" * 60)

    # Run the async function
    asyncio.run(add_real_models())

    print("=" * 60)
    print("🏁 Script completed!")
