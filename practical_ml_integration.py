#!/usr/bin/env python3
"""
Practical ML Integration - Making ML Actually Useful for Users

This shows how to integrate ML models with real betting data and user actions.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional


class PracticalMLService:
    """ML service that actually helps users make betting decisions."""

    def __init__(self, db_manager, api_service):
        self.db_manager = db_manager
        self.api_service = api_service  # For live odds and game data

    async def analyze_upcoming_game(self, game_id: str, user_id: int) -> Dict:
        """Analyze a specific upcoming game for betting opportunities."""

        # 1. Get real game data
        game_data = await self.api_service.get_game_details(game_id)
        live_odds = await self.api_service.get_live_odds(game_id)
        team_stats = await self.api_service.get_team_stats(
            game_data["home_team"], game_data["away_team"]
        )

        # 2. Get user's betting history
        user_history = await self.db_manager.fetch_all(
            "SELECT * FROM bets WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
            (user_id,),
        )

        # 3. Generate actionable insights
        insights = {
            "game_info": {
                "home_team": game_data["home_team"],
                "away_team": game_data["away_team"],
                "start_time": game_data["start_time"],
                "league": game_data["league"],
            },
            "current_odds": live_odds,
            "recommendations": [],
            "risk_assessment": {},
            "optimal_bet_size": 0,
        }

        # 4. Use ML models with real data
        bet_outcome_prediction = await self._predict_bet_outcome(
            game_data, team_stats, live_odds
        )

        bankroll_recommendation = await self._calculate_optimal_bet_size(
            user_history, bet_outcome_prediction, live_odds
        )

        # 5. Generate user-friendly recommendations
        if bet_outcome_prediction["confidence"] > 0.7:
            insights["recommendations"].append(
                {
                    "type": "bet_recommendation",
                    "message": f"Strong {bet_outcome_prediction['prediction']} prediction for {game_data['home_team']}",
                    "confidence": f"{bet_outcome_prediction['confidence']:.1%}",
                    "recommended_odds": live_odds["home_win"],
                    "reasoning": "Based on team performance, recent form, and historical matchups",
                }
            )

        insights["optimal_bet_size"] = bankroll_recommendation["amount"]
        insights["risk_assessment"] = bankroll_recommendation["risk_level"]

        return insights

    async def get_daily_betting_opportunities(self, user_id: int) -> List[Dict]:
        """Get a list of today's best betting opportunities for the user."""

        # 1. Get today's games
        today_games = await self.api_service.get_todays_games()

        opportunities = []

        for game in today_games:
            # 2. Analyze each game
            analysis = await self.analyze_upcoming_game(game["id"], user_id)

            # 3. Only include high-confidence opportunities
            if analysis["recommendations"] and analysis["optimal_bet_size"] > 0:
                opportunities.append(
                    {
                        "game": analysis["game_info"],
                        "recommendation": analysis["recommendations"][0],
                        "bet_amount": analysis["optimal_bet_size"],
                        "risk_level": analysis["risk_assessment"],
                    }
                )

        # 4. Sort by confidence and return top 5
        opportunities.sort(
            key=lambda x: float(x["recommendation"]["confidence"].rstrip("%")),
            reverse=True,
        )
        return opportunities[:5]

    async def get_user_betting_insights(self, user_id: int) -> Dict:
        """Get personalized insights about user's betting patterns."""

        # 1. Analyze user's betting history
        user_bets = await self.db_manager.fetch_all(
            "SELECT * FROM bets WHERE user_id = %s ORDER BY created_at DESC LIMIT 100",
            (user_id,),
        )

        # 2. Use ML to analyze patterns
        behavior_analysis = await self._analyze_user_behavior(user_bets)

        # 3. Generate insights
        insights = {
            "betting_patterns": {
                "favorite_sports": behavior_analysis["preferred_sports"],
                "average_bet_size": behavior_analysis["avg_bet_size"],
                "success_rate": behavior_analysis["success_rate"],
                "risk_profile": behavior_analysis["risk_level"],
            },
            "recommendations": [
                f"You win {behavior_analysis['success_rate']:.1%} of your bets",
                f"Your average bet size is ${behavior_analysis['avg_bet_size']:.2f}",
                f"Consider focusing on {behavior_analysis['best_performing_sport']} for better results",
            ],
            "improvement_suggestions": behavior_analysis["suggestions"],
        }

        return insights

    async def _predict_bet_outcome(
        self, game_data: Dict, team_stats: Dict, odds: Dict
    ) -> Dict:
        """Use ML to predict bet outcome with real data."""

        # Prepare input data from real sources
        input_data = {
            "odds": odds["home_win"],
            "team_stats": {
                "home_wins": team_stats["home"]["wins"],
                "home_losses": team_stats["home"]["losses"],
                "away_wins": team_stats["away"]["wins"],
                "away_losses": team_stats["away"]["losses"],
            },
            "recent_form": {
                "home_last_5": team_stats["home"]["recent_form"],
                "away_last_5": team_stats["away"]["recent_form"],
            },
            "head_to_head": team_stats["head_to_head"],
            "venue": "home" if game_data["venue"] == game_data["home_team"] else "away",
        }

        # Use the ML model
        prediction = await self.predictive_service.generate_prediction(
            model_id="bet_outcome_predictor_v1",
            input_data=input_data,
            prediction_type="bet_outcome",
            user_id=user_id,
        )

        return {
            "prediction": prediction.prediction_result,
            "confidence": prediction.confidence_score,
        }

    async def _calculate_optimal_bet_size(
        self, user_history: List, prediction: Dict, odds: Dict
    ) -> Dict:
        """Calculate optimal bet size using Kelly Criterion."""

        # Calculate user's historical performance
        total_bets = len(user_history)
        wins = sum(1 for bet in user_history if bet["result"] == "win")
        win_rate = wins / total_bets if total_bets > 0 else 0.5

        # Use ML to get win probability
        win_probability = (
            prediction["confidence"]
            if prediction["prediction"] == "win"
            else 1 - prediction["confidence"]
        )

        # Kelly Criterion calculation
        kelly_fraction = (win_probability * odds["home_win"] - 1) / (
            odds["home_win"] - 1
        )
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25% of bankroll

        return {
            "amount": kelly_fraction * 1000,  # Assuming $1000 bankroll
            "risk_level": (
                "high"
                if kelly_fraction > 0.1
                else "medium" if kelly_fraction > 0.05 else "low"
            ),
        }

    async def _analyze_user_behavior(self, user_bets: List) -> Dict:
        """Analyze user's betting behavior patterns."""

        if not user_bets:
            return {
                "preferred_sports": [],
                "avg_bet_size": 0,
                "success_rate": 0,
                "risk_level": "unknown",
                "best_performing_sport": "none",
                "suggestions": ["Start betting to get personalized insights!"],
            }

        # Analyze patterns
        sports_count = {}
        bet_sizes = []
        wins = 0

        for bet in user_bets:
            sports_count[bet["sport"]] = sports_count.get(bet["sport"], 0) + 1
            bet_sizes.append(bet["amount"])
            if bet["result"] == "win":
                wins += 1

        # Calculate insights
        total_bets = len(user_bets)
        success_rate = wins / total_bets
        avg_bet_size = sum(bet_sizes) / len(bet_sizes)
        preferred_sports = sorted(
            sports_count.items(), key=lambda x: x[1], reverse=True
        )[:3]

        # Generate suggestions
        suggestions = []
        if success_rate < 0.5:
            suggestions.append("Consider reducing bet sizes and focusing on safer bets")
        if avg_bet_size > 100:
            suggestions.append("Your bet sizes are high - consider bankroll management")
        if len(preferred_sports) == 1:
            suggestions.append("Try diversifying across different sports")

        return {
            "preferred_sports": [sport for sport, count in preferred_sports],
            "avg_bet_size": avg_bet_size,
            "success_rate": success_rate,
            "risk_level": (
                "high"
                if avg_bet_size > 100
                else "medium" if avg_bet_size > 50 else "low"
            ),
            "best_performing_sport": (
                preferred_sports[0][0] if preferred_sports else "none"
            ),
            "suggestions": suggestions,
        }


# Example usage:
"""
# Instead of users providing JSON, they just ask:
await ml_service.analyze_upcoming_game("game_123", user_id=456)

# Returns:
{
    'game_info': {
        'home_team': 'Lakers',
        'away_team': 'Warriors',
        'start_time': '2024-01-15 19:30',
        'league': 'NBA'
    },
    'recommendations': [
        {
            'type': 'bet_recommendation',
            'message': 'Strong win prediction for Lakers',
            'confidence': '78.5%',
            'recommended_odds': 1.85,
            'reasoning': 'Based on team performance, recent form, and historical matchups'
        }
    ],
    'optimal_bet_size': 45.50,
    'risk_assessment': 'medium'
}
"""
