#!/usr/bin/env python3
"""
Test script for Predictive Service

This script tests the basic functionality of the predictive service
to ensure it's working correctly.
"""

import asyncio
import logging
import os
import sys

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.data.db_manager import DatabaseManager
from bot.services.predictive_service import ModelType, PredictionType, PredictiveService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_predictive_service():
    """Test the predictive service functionality."""
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()

        # Initialize predictive service
        predictive_service = PredictiveService(db_manager)
        await predictive_service.initialize()

        logger.info("✅ Predictive service initialized successfully")

        # Test getting model templates
        templates = await predictive_service.get_model_templates()
        logger.info(f"✅ Retrieved {len(templates)} model templates")

        # Test creating a simple prediction
        test_input = {
            "odds": 2.5,
            "team_stats": {"wins": 10, "losses": 5},
            "player_stats": {"avg_points": 20.5},
            "historical_performance": 0.75,
            "weather": "clear",
            "venue": "home",
        }

        # Use one of the default models
        model_id = "bet_outcome_predictor_v1"

        prediction = await predictive_service.generate_prediction(
            model_id=model_id,
            input_data=test_input,
            prediction_type=PredictionType.BET_OUTCOME,
            user_id=12345,
            guild_id=67890,
        )

        if prediction:
            logger.info(f"✅ Generated prediction: {prediction.prediction_result}")
            logger.info(f"✅ Confidence score: {prediction.confidence_score}")
        else:
            logger.warning(
                "⚠️ No prediction generated (this is expected for mock models)"
            )

        # Test dashboard data
        dashboard_data = await predictive_service.get_predictive_dashboard_data()
        logger.info(f"✅ Retrieved dashboard data with {len(dashboard_data)} sections")

        # Test feature importance analysis
        feature_importances = await predictive_service.analyze_feature_importance(
            model_id
        )
        logger.info(
            f"✅ Analyzed feature importance: {len(feature_importances)} features"
        )

        # Cleanup
        await predictive_service.cleanup()
        await db_manager.close()

        logger.info("✅ All tests completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


async def main():
    """Main test function."""
    logger.info("Starting Predictive Service tests...")
    await test_predictive_service()
    logger.info("Predictive Service tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
