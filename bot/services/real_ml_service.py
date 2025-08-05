#!/usr/bin/env python3
"""
Real ML Service - Making ML Actually Useful with Live API Data

This integrates ML models with your existing API-Sports system to provide
real betting insights based on live data.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from api.sports_api import APISportsFetcher, SportsAPI
from data.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class RealMLService:
    """ML service that uses real API data to provide actionable betting insights."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        sports_api: SportsAPI,
        predictive_service=None,
    ):
        self.db_manager = db_manager
        self.sports_api = sports_api
        self.fetcher = APISportsFetcher()
        self.predictive_service = predictive_service

    async def analyze_todays_games(self, user_id: int) -> List[Dict]:
        """Analyze today's games using real API data and ML predictions."""

        try:
            # 1. Get today's games from API
            today = datetime.now().strftime("%Y-%m-%d")
            games = await self._get_todays_games_from_api(today)

            if not games:
                return []

            # 2. Analyze each game with ML
            analyzed_games = []

            for game in games[:10]:  # Limit to top 10 games
                analysis = await self._analyze_single_game(game, user_id)
                if analysis and analysis.get("confidence", 0) > 0.6:
                    analyzed_games.append(analysis)

            # 3. Sort by confidence and return top 5
            analyzed_games.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            return analyzed_games[:5]

        except Exception as e:
            logger.error(f"Error analyzing today's games: {e}")
            return []

    async def analyze_specific_game(
        self, home_team: str, away_team: str, sport: str, user_id: int
    ) -> Optional[Dict]:
        """Analyze a specific game using real API data."""

        try:
            # 1. Find the game in API data
            game = await self._find_game_in_api(home_team, away_team, sport)
            if not game:
                return None

            # 2. Get detailed game data
            game_details = await self._get_game_details(game["id"], sport)
            if not game_details:
                return None

            # 3. Analyze with ML
            return await self._analyze_single_game(game_details, user_id)

        except Exception as e:
            logger.error(f"Error analyzing specific game: {e}")
            return None

    async def get_user_betting_insights(self, user_id: int) -> Dict:
        """Get personalized insights based on user's betting history."""

        try:
            # 1. Get user's betting history
            user_bets = await self.db_manager.fetch_all(
                "SELECT * FROM bets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            )

            if not user_bets:
                return {
                    "message": "No betting history found. Start betting to get personalized insights!",
                    "recommendations": [
                        "Try analyzing today's games with /analyze_today"
                    ],
                }

            # 2. Analyze patterns
            patterns = await self._analyze_betting_patterns(user_bets)

            # 3. Get recommendations based on patterns
            recommendations = await self._generate_personalized_recommendations(
                patterns, user_id
            )

            return {
                "betting_patterns": patterns,
                "recommendations": recommendations,
                "improvement_tips": await self._get_improvement_tips(patterns),
            }

        except Exception as e:
            logger.error(f"Error getting user insights: {e}")
            return {"error": "Failed to get insights"}

    async def _get_todays_games_from_api(self, date: str) -> List[Dict]:
        """Get today's games from API-Sports."""

        games = []

        # Get games from major sports
        sports = ["football", "basketball", "baseball", "hockey", "american-football"]

        for sport in sports:
            try:
                # Get leagues for this sport
                leagues = await self._get_sport_leagues(sport)

                for league in leagues[:3]:  # Top 3 leagues per sport
                    league_games = await self._get_league_games(
                        sport, league["id"], date
                    )
                    games.extend(league_games)

            except Exception as e:
                logger.warning(f"Failed to get games for {sport}: {e}")
                continue

        return games

    async def _get_sport_leagues(self, sport: str) -> List[Dict]:
        """Get leagues for a specific sport."""

        try:
            async with self.fetcher:
                data = await self.fetcher.fetch_data(sport, "leagues", {})

                if data and "response" in data:
                    return data["response"][:5]  # Top 5 leagues
                return []

        except Exception as e:
            logger.error(f"Error getting leagues for {sport}: {e}")
            return []

    async def _get_league_games(
        self, sport: str, league_id: int, date: str
    ) -> List[Dict]:
        """Get games for a specific league and date."""

        try:
            async with self.fetcher:
                params = {"league": league_id, "date": date}

                data = await self.fetcher.fetch_data(sport, "fixtures", params)

                if data and "response" in data:
                    return data["response"]
                return []

        except Exception as e:
            logger.error(f"Error getting games for league {league_id}: {e}")
            return []

    async def _find_game_in_api(
        self, home_team: str, away_team: str, sport: str
    ) -> Optional[Dict]:
        """Find a specific game in API data."""

        try:
            # Search in recent games
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            for date in [today, tomorrow]:
                games = await self._get_todays_games_from_api(date)

                for game in games:
                    home = game.get("teams", {}).get("home", {}).get("name", "").lower()
                    away = game.get("teams", {}).get("away", {}).get("name", "").lower()

                    if (home_team.lower() in home or home in home_team.lower()) and (
                        away_team.lower() in away or away in away_team.lower()
                    ):
                        return game

            return None

        except Exception as e:
            logger.error(f"Error finding game: {e}")
            return None

    async def _get_game_details(self, game_id: int, sport: str) -> Optional[Dict]:
        """Get detailed information about a specific game."""

        try:
            async with self.fetcher:
                # Get fixture details
                fixture_data = await self.fetcher.fetch_data(
                    sport, "fixtures", {"id": game_id}
                )

                if fixture_data and "response" in fixture_data:
                    game = fixture_data["response"][0]

                    # Get team statistics
                    home_team_id = game["teams"]["home"]["id"]
                    away_team_id = game["teams"]["away"]["id"]

                    home_stats = await self._get_team_stats(sport, home_team_id)
                    away_stats = await self._get_team_stats(sport, away_team_id)

                    game["team_stats"] = {"home": home_stats, "away": away_stats}

                    return game

                return None

        except Exception as e:
            logger.error(f"Error getting game details: {e}")
            return None

    async def _get_team_stats(self, sport: str, team_id: int) -> Dict:
        """Get team statistics."""

        try:
            async with self.fetcher:
                # Get team standings
                standings_data = await self.fetcher.fetch_data(
                    sport, "standings", {"team": team_id}
                )

                if standings_data and "response" in standings_data:
                    return standings_data["response"][0]

                return {}

        except Exception as e:
            logger.error(f"Error getting team stats: {e}")
            return {}

    async def _analyze_single_game(self, game: Dict, user_id: int) -> Optional[Dict]:
        """Analyze a single game using ML models."""

        try:
            # Extract game information
            home_team = game["teams"]["home"]["name"]
            away_team = game["teams"]["away"]["name"]
            sport = game.get("league", {}).get("type", "football")

            # Get odds (if available)
            odds = await self._get_game_odds(game.get("fixture", {}).get("id"))

            # Prepare input data for ML
            input_data = await self._prepare_ml_input(game, odds)

            # Use ML model to predict outcome
            prediction = await self._make_ml_prediction(input_data, user_id)

            if not prediction:
                return None

            # Calculate optimal bet size
            bet_size = await self._calculate_optimal_bet_size(user_id, prediction, odds)

            return {
                "game_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "sport": sport,
                    "date": game["fixture"]["date"],
                    "league": game["league"]["name"],
                },
                "prediction": prediction["result"],
                "confidence": prediction["confidence"],
                "reasoning": prediction["reasoning"],
                "recommended_bet": bet_size["amount"],
                "risk_level": bet_size["risk_level"],
                "odds": odds,
            }

        except Exception as e:
            logger.error(f"Error analyzing single game: {e}")
            return None

    async def _get_game_odds(self, fixture_id: int) -> Dict:
        """Get odds for a specific game."""

        try:
            # Try to get odds from API
            async with self.fetcher:
                odds_data = await self.fetcher.fetch_data(
                    "football", "odds", {"fixture": fixture_id}
                )

                if odds_data and "response" in odds_data:
                    return odds_data["response"][0]

                # Return default odds if not available
                return {"home_win": 2.0, "away_win": 2.0, "draw": 3.0}

        except Exception as e:
            logger.warning(f"Could not get odds for fixture {fixture_id}: {e}")
            return {"home_win": 2.0, "away_win": 2.0, "draw": 3.0}

    async def _prepare_ml_input(self, game: Dict, odds: Dict) -> Dict:
        """Prepare input data for ML model."""

        try:
            home_stats = game.get("team_stats", {}).get("home", {})
            away_stats = game.get("team_stats", {}).get("away", {})

            # Extract relevant features
            input_data = {
                "odds": odds.get("home_win", 2.0),
                "team_stats": {
                    "home_wins": home_stats.get("all", {}).get("win", 0),
                    "home_losses": home_stats.get("all", {}).get("lose", 0),
                    "home_draws": home_stats.get("all", {}).get("draw", 0),
                    "away_wins": away_stats.get("all", {}).get("win", 0),
                    "away_losses": away_stats.get("all", {}).get("lose", 0),
                    "away_draws": away_stats.get("all", {}).get("draw", 0),
                },
                "recent_form": {
                    "home_form": home_stats.get("form", ""),
                    "away_form": away_stats.get("form", ""),
                },
                "venue": "home",
                "league_importance": game.get("league", {})
                .get("country", {})
                .get("name", "Unknown"),
            }

            return input_data

        except Exception as e:
            logger.error(f"Error preparing ML input: {e}")
            return {}

    async def _make_ml_prediction(
        self, input_data: Dict, user_id: int
    ) -> Optional[Dict]:
        """Make prediction using ML model."""

        try:
            # Use the existing predictive service
            from services.predictive_service import PredictionType

            prediction = await self.predictive_service.generate_prediction(
                model_id="bet_outcome_predictor_v1",
                input_data=input_data,
                prediction_type=PredictionType.BET_OUTCOME,
                user_id=user_id,
            )

            if prediction:
                # Generate reasoning based on input data
                reasoning = await self._generate_reasoning(
                    input_data, prediction.prediction_result
                )

                return {
                    "result": prediction.prediction_result,
                    "confidence": prediction.confidence_score,
                    "reasoning": reasoning,
                }

            return None

        except Exception as e:
            logger.error(f"Error making ML prediction: {e}")
            return None

    async def _generate_reasoning(self, input_data: Dict, prediction: str) -> str:
        """Generate human-readable reasoning for the prediction."""

        home_stats = input_data.get("team_stats", {})
        away_stats = input_data.get("team_stats", {})

        home_wins = home_stats.get("home_wins", 0)
        home_losses = home_stats.get("home_losses", 0)
        away_wins = away_stats.get("away_wins", 0)
        away_losses = away_stats.get("away_losses", 0)

        if prediction == "win":
            if home_wins > away_wins:
                return f"Home team has better record ({home_wins}-{home_losses} vs {away_wins}-{away_losses})"
            else:
                return "ML model predicts home advantage will be decisive"
        elif prediction == "loss":
            if away_wins > home_wins:
                return f"Away team has better record ({away_wins}-{away_losses} vs {home_wins}-{home_losses})"
            else:
                return "ML model predicts away team will overcome home advantage"
        else:
            return "Teams are evenly matched, likely to end in draw"

    async def _calculate_optimal_bet_size(
        self, user_id: int, prediction: Dict, odds: Dict
    ) -> Dict:
        """Calculate optimal bet size using Kelly Criterion."""

        try:
            # Get user's betting history
            user_bets = await self.db_manager.fetch_all(
                "SELECT * FROM bets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 50",
                (user_id,),
            )

            # Calculate user's win rate
            total_bets = len(user_bets)
            wins = sum(1 for bet in user_bets if bet["result"] == "win")
            win_rate = wins / total_bets if total_bets > 0 else 0.5

            # Use ML confidence as win probability
            win_probability = prediction["confidence"]

            # Kelly Criterion calculation
            kelly_fraction = (win_probability * odds["home_win"] - 1) / (
                odds["home_win"] - 1
            )
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

            # Calculate bet amount (assuming $1000 bankroll)
            bet_amount = kelly_fraction * 1000

            # Determine risk level
            if kelly_fraction > 0.1:
                risk_level = "high"
            elif kelly_fraction > 0.05:
                risk_level = "medium"
            else:
                risk_level = "low"

            return {
                "amount": bet_amount,
                "risk_level": risk_level,
                "kelly_fraction": kelly_fraction,
            }

        except Exception as e:
            logger.error(f"Error calculating bet size: {e}")
            return {"amount": 0, "risk_level": "unknown", "kelly_fraction": 0}

    async def _analyze_betting_patterns(self, user_bets: List[Dict]) -> Dict:
        """Analyze user's betting patterns."""

        if not user_bets:
            return {}

        # Analyze patterns
        sports_count = {}
        bet_sizes = []
        wins = 0
        total_wagered = 0

        for bet in user_bets:
            sport = bet.get("sport", "unknown")
            sports_count[sport] = sports_count.get(sport, 0) + 1
            bet_sizes.append(bet.get("amount", 0))
            total_wagered += bet.get("amount", 0)

            if bet.get("result") == "win":
                wins += 1

        total_bets = len(user_bets)
        success_rate = wins / total_bets
        avg_bet_size = sum(bet_sizes) / len(bet_sizes)
        preferred_sports = sorted(
            sports_count.items(), key=lambda x: x[1], reverse=True
        )[:3]

        return {
            "total_bets": total_bets,
            "success_rate": success_rate,
            "avg_bet_size": avg_bet_size,
            "total_wagered": total_wagered,
            "preferred_sports": [sport for sport, count in preferred_sports],
            "risk_profile": (
                "high"
                if avg_bet_size > 100
                else "medium" if avg_bet_size > 50 else "low"
            ),
        }

    async def _generate_personalized_recommendations(
        self, patterns: Dict, user_id: int
    ) -> List[str]:
        """Generate personalized recommendations based on betting patterns."""

        recommendations = []

        if patterns.get("success_rate", 0) < 0.5:
            recommendations.append(
                "Consider reducing bet sizes and focusing on safer bets"
            )

        if patterns.get("avg_bet_size", 0) > 100:
            recommendations.append(
                "Your bet sizes are high - consider bankroll management"
            )

        if len(patterns.get("preferred_sports", [])) == 1:
            recommendations.append("Try diversifying across different sports")

        # Get today's best opportunities for user's preferred sports
        preferred_sports = patterns.get("preferred_sports", [])
        if preferred_sports:
            recommendations.append(
                f"Check today's {preferred_sports[0]} games for opportunities"
            )

        return recommendations

    async def _get_improvement_tips(self, patterns: Dict) -> List[str]:
        """Get improvement tips based on betting patterns."""

        tips = []

        if patterns.get("success_rate", 0) < 0.4:
            tips.append("Focus on games with higher confidence predictions")

        if patterns.get("avg_bet_size", 0) > 150:
            tips.append("Never bet more than 5% of your bankroll on a single bet")

        if patterns.get("total_bets", 0) < 20:
            tips.append("Place more bets to get better statistical insights")

        return tips
