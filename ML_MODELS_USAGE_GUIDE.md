# 🤖 ML Models Usage Guide

Your betting bot now has **6 powerful ML models** ready to help you make better betting decisions! Here's how to use them:

## 🎯 **Available Models**

### 1. **Bet Outcome Predictor** (`bet_outcome_predictor_v1`)
- **Purpose**: Predicts if a bet will win, lose, or draw
- **Best for**: Game outcome predictions
- **Algorithm**: Random Forest Classification

### 2. **User Behavior Analyzer** (`user_behavior_analyzer_v1`)
- **Purpose**: Analyzes user betting patterns and segments users
- **Best for**: Understanding user preferences and risk tolerance
- **Algorithm**: K-Means Clustering

### 3. **Odds Movement Predictor** (`odds_movement_predictor_v1`)
- **Purpose**: Predicts how betting odds will move
- **Best for**: Timing your bets for better odds
- **Algorithm**: Gradient Boosting Regression

### 4. **Parlay Optimizer** (`parlay_optimizer_v1`)
- **Purpose**: Optimizes parlay selections for maximum value
- **Best for**: Building profitable parlays
- **Algorithm**: Genetic Algorithm Optimization

### 5. **Bankroll Manager** (`bankroll_manager_v1`)
- **Purpose**: Determines optimal bet sizing using Kelly Criterion
- **Best for**: Managing your bankroll and risk
- **Algorithm**: Kelly Criterion Regression

### 6. **Live Betting Analyzer** (`live_betting_analyzer_v1`)
- **Purpose**: Analyzes in-game statistics for live betting opportunities
- **Best for**: Live betting decisions
- **Algorithm**: Neural Network Classification

## 🚀 **How to Use the Models**

### **Method 1: Discord Commands (Recommended)**

Your bot has these ML commands available in Discord:

#### **📊 View All Models:**
```
/ml_models
```
Shows all available models with descriptions and status.

#### **🤖 Make Predictions:**
```
/predict model_type:bet_outcome input_data:{"odds": 2.5, "team_stats": {"wins": 10, "losses": 5}}
```

**Available model types:**
- `bet_outcome` - Predicts bet success
- `user_behavior` - Analyzes user patterns
- `revenue_forecast` - Forecasts revenue
- `risk_assessment` - Assesses risk
- `churn_prediction` - Predicts user churn
- `recommendation` - Provides recommendations

#### **📈 View ML Dashboard:**
```
/ml_dashboard
```
Shows model performance metrics and recent predictions.

### **Method 2: Example Usage Scenarios**

#### **Example 1: Bet Outcome Prediction**
```json
{
  "odds": 2.15,
  "team_stats": {
    "wins": 12,
    "losses": 8,
    "home_record": "8-2",
    "recent_form": "W-W-L-W-W"
  },
  "opponent_stats": {
    "wins": 10,
    "losses": 10,
    "away_record": "3-7",
    "recent_form": "L-W-L-L-W"
  },
  "weather": "clear",
  "venue": "home",
  "injury_status": "healthy",
  "stake_amount": 50.0
}
```

#### **Example 2: Bankroll Management**
```json
{
  "bankroll_size": 1000.0,
  "win_probability": 0.65,
  "odds": 2.10,
  "historical_roi": 0.12,
  "risk_tolerance": "conservative",
  "streak_length": 3,
  "market_confidence": 0.75,
  "bankroll_volatility": 0.08
}
```

#### **Example 3: Live Betting Analysis**
```json
{
  "current_score": "24-18",
  "time_remaining": "Q3 8:45",
  "possession_stats": {"home": 0.52, "away": 0.48},
  "shot_attempts": {"home": 45, "away": 42},
  "fouls": {"home": 8, "away": 12},
  "momentum_indicators": "home_team_heating_up",
  "player_performance": "star_player_hot",
  "coaching_decisions": "timeout_called",
  "crowd_energy": "high"
}
```

## 🎯 **Model Features & Inputs**

### **Bet Outcome Predictor Features:**
- `odds` - Betting odds
- `team_stats` - Team performance statistics
- `opponent_stats` - Opponent performance statistics
- `weather` - Weather conditions
- `venue` - Home/away venue
- `injury_status` - Team injury status
- `stake_amount` - Bet amount

### **Bankroll Manager Features:**
- `bankroll_size` - Current bankroll
- `win_probability` - Estimated win probability
- `odds` - Betting odds
- `historical_roi` - Historical return on investment
- `risk_tolerance` - Risk tolerance level
- `streak_length` - Current winning/losing streak
- `market_confidence` - Market confidence level
- `bankroll_volatility` - Bankroll volatility

### **Live Betting Analyzer Features:**
- `current_score` - Current game score
- `time_remaining` - Time remaining in game
- `possession_stats` - Possession statistics
- `shot_attempts` - Shot attempts by team
- `fouls` - Foul counts
- `momentum_indicators` - Game momentum
- `player_performance` - Key player performance
- `coaching_decisions` - Recent coaching decisions
- `crowd_energy` - Crowd energy level

## 📊 **Understanding Model Outputs**

### **Prediction Results:**
- **Classification Models** (Bet Outcome, Live Betting): Return `win`, `loss`, or `draw`
- **Regression Models** (Odds Movement, Bankroll): Return numerical values
- **Clustering Models** (User Behavior): Return user segments like `high_risk`, `moderate`, `conservative`

### **Confidence Scores:**
- **0.0 - 1.0** scale (0% - 100%)
- **High confidence** (0.8+): Very reliable prediction
- **Medium confidence** (0.6-0.8): Reasonably reliable
- **Low confidence** (<0.6): Less reliable, use with caution

## 🔧 **Advanced Usage**

### **Batch Predictions:**
You can make multiple predictions at once for efficiency.

### **Model Performance Monitoring:**
The system automatically tracks:
- Prediction accuracy
- Model performance trends
- Confidence score distributions
- Model retraining needs

### **Feature Importance Analysis:**
Understand which factors most influence predictions.

## ⚠️ **Important Notes**

1. **Model Status**: All models are currently `active` and ready to use
2. **Input Flexibility**: Models can handle missing features with default values
3. **Real-time Updates**: Models are continuously learning from new data
4. **Confidence Thresholds**: Consider confidence scores when making decisions
5. **Risk Management**: Always use proper bankroll management regardless of predictions

## 🎯 **Getting Started**

1. **Start with simple predictions** using the `/predict` command
2. **Experiment with different input data** to see how predictions change
3. **Monitor the ML dashboard** to track performance
4. **Use multiple models** for different aspects of your betting strategy
5. **Combine predictions** with your own analysis for best results

## 🚀 **Example Workflow**

1. **Analyze a game** using the Bet Outcome Predictor
2. **Check odds movement** with the Odds Movement Predictor
3. **Determine bet size** using the Bankroll Manager
4. **Monitor live betting opportunities** with the Live Betting Analyzer
5. **Track your patterns** with the User Behavior Analyzer

---

**🎉 Your ML models are now ready to help you make smarter betting decisions!**

Start with `/ml_models` to see all available models, then try `/predict` to make your first prediction!
