"""
NLP Service for DBSBM System.
Provides natural language processing capabilities for user interactions.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# NLP-specific cache TTLs
NLP_CACHE_TTLS = {
    'nlp_models': 3600,           # 1 hour
    'nlp_intents': 1800,          # 30 minutes
    'nlp_entities': 1800,          # 30 minutes
    'nlp_sentiments': 900,         # 15 minutes
    'nlp_responses': 1800,         # 30 minutes
    'nlp_patterns': 7200,          # 2 hours
    'nlp_training': 3600,          # 1 hour
    'nlp_accuracy': 1800,          # 30 minutes
    'nlp_usage': 600,              # 10 minutes
    'nlp_analytics': 3600,         # 1 hour
}

class IntentType(Enum):
    """NLP intent types."""
    BET_PLACEMENT = "bet_placement"
    BET_QUERY = "bet_query"
    BALANCE_CHECK = "balance_check"
    GAME_INFO = "game_info"
    HELP_REQUEST = "help_request"
    SETTINGS_CHANGE = "settings_change"
    STATISTICS_REQUEST = "statistics_request"
    GREETING = "greeting"
    FAREWELL = "farewell"
    UNKNOWN = "unknown"

class SentimentType(Enum):
    """Sentiment analysis types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class EntityType(Enum):
    """Entity extraction types."""
    TEAM_NAME = "team_name"
    PLAYER_NAME = "player_name"
    SPORT_TYPE = "sport_type"
    LEAGUE_NAME = "league_name"
    AMOUNT = "amount"
    ODDS = "odds"
    DATE_TIME = "date_time"
    LOCATION = "location"

@dataclass
class NLPIntent:
    """NLP intent classification."""
    id: int
    intent_type: IntentType
    confidence: float
    text: str
    user_id: int
    guild_id: int
    created_at: datetime

@dataclass
class NLPSentiment:
    """NLP sentiment analysis."""
    id: int
    sentiment_type: SentimentType
    confidence: float
    text: str
    user_id: int
    guild_id: int
    created_at: datetime

@dataclass
class NLPEntity:
    """NLP entity extraction."""
    id: int
    entity_type: EntityType
    value: str
    confidence: float
    text: str
    user_id: int
    guild_id: int
    created_at: datetime

@dataclass
class NLPResponse:
    """NLP response template."""
    id: int
    intent_type: IntentType
    response_text: str
    response_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class NLPService:
    """NLP service for natural language processing capabilities."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = NLP_CACHE_TTLS

        # NLP patterns and keywords
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.sentiment_keywords = self._load_sentiment_keywords()

        # Background tasks
        self.training_task = None
        self.is_running = False

    async def start(self):
        """Start the NLP service."""
        try:
            await self._load_nlp_models()
            self.is_running = True
            self.training_task = asyncio.create_task(self._periodic_model_training())
            logger.info("NLP service started successfully")
        except Exception as e:
            logger.error(f"Failed to start NLP service: {e}")
            raise

    async def stop(self):
        """Stop the NLP service."""
        self.is_running = False
        if self.training_task:
            self.training_task.cancel()
        logger.info("NLP service stopped")

    @time_operation("nlp_classify_intent")
    async def classify_intent(self, text: str, user_id: int, guild_id: int) -> Optional[NLPIntent]:
        """Classify the intent of user input."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_intent:{hashlib.md5(text.encode()).hexdigest()}:{user_id}:{guild_id}"
            cached_intent = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_intent:
                return NLPIntent(**cached_intent)

            # Perform intent classification
            intent_type, confidence = self._classify_intent_pattern(text)

            # Create intent record
            query = """
            INSERT INTO nlp_intents (intent_type, confidence, text, user_id, guild_id, created_at)
            VALUES (:intent_type, :confidence, :text, :user_id, :guild_id, NOW())
            """

            result = await self.db_manager.execute(query, {
                'intent_type': intent_type.value,
                'confidence': confidence,
                'text': text,
                'user_id': user_id,
                'guild_id': guild_id
            })

            intent_id = result.lastrowid

            intent = NLPIntent(
                id=intent_id,
                intent_type=intent_type,
                confidence=confidence,
                text=text,
                user_id=user_id,
                guild_id=guild_id,
                created_at=datetime.utcnow()
            )

            # Cache intent
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': intent.id,
                    'intent_type': intent.intent_type.value,
                    'confidence': intent.confidence,
                    'text': intent.text,
                    'user_id': intent.user_id,
                    'guild_id': intent.guild_id,
                    'created_at': intent.created_at.isoformat()
                },
                ttl=self.cache_ttls['nlp_intents']
            )

            record_metric("nlp_intents_classified", 1)
            return intent

        except Exception as e:
            logger.error(f"Failed to classify intent: {e}")
            return None

    @time_operation("nlp_analyze_sentiment")
    async def analyze_sentiment(self, text: str, user_id: int, guild_id: int) -> Optional[NLPSentiment]:
        """Analyze the sentiment of user input."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_sentiment:{hashlib.md5(text.encode()).hexdigest()}:{user_id}:{guild_id}"
            cached_sentiment = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_sentiment:
                return NLPSentiment(**cached_sentiment)

            # Perform sentiment analysis
            sentiment_type, confidence = self._analyze_sentiment_pattern(text)

            # Create sentiment record
            query = """
            INSERT INTO nlp_sentiments (sentiment_type, confidence, text, user_id, guild_id, created_at)
            VALUES (:sentiment_type, :confidence, :text, :user_id, :guild_id, NOW())
            """

            result = await self.db_manager.execute(query, {
                'sentiment_type': sentiment_type.value,
                'confidence': confidence,
                'text': text,
                'user_id': user_id,
                'guild_id': guild_id
            })

            sentiment_id = result.lastrowid

            sentiment = NLPSentiment(
                id=sentiment_id,
                sentiment_type=sentiment_type,
                confidence=confidence,
                text=text,
                user_id=user_id,
                guild_id=guild_id,
                created_at=datetime.utcnow()
            )

            # Cache sentiment
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': sentiment.id,
                    'sentiment_type': sentiment.sentiment_type.value,
                    'confidence': sentiment.confidence,
                    'text': sentiment.text,
                    'user_id': sentiment.user_id,
                    'guild_id': sentiment.guild_id,
                    'created_at': sentiment.created_at.isoformat()
                },
                ttl=self.cache_ttls['nlp_sentiments']
            )

            record_metric("nlp_sentiments_analyzed", 1)
            return sentiment

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return None

    @time_operation("nlp_extract_entities")
    async def extract_entities(self, text: str, user_id: int, guild_id: int) -> List[NLPEntity]:
        """Extract entities from user input."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_entities:{hashlib.md5(text.encode()).hexdigest()}:{user_id}:{guild_id}"
            cached_entities = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_entities:
                return [NLPEntity(**entity) for entity in cached_entities]

            # Extract entities
            entities = self._extract_entities_pattern(text)

            # Create entity records
            created_entities = []
            for entity_type, value, confidence in entities:
                query = """
                INSERT INTO nlp_entities (entity_type, value, confidence, text, user_id, guild_id, created_at)
                VALUES (:entity_type, :value, :confidence, :text, :user_id, :guild_id, NOW())
                """

                result = await self.db_manager.execute(query, {
                    'entity_type': entity_type.value,
                    'value': value,
                    'confidence': confidence,
                    'text': text,
                    'user_id': user_id,
                    'guild_id': guild_id
                })

                entity_id = result.lastrowid

                entity = NLPEntity(
                    id=entity_id,
                    entity_type=entity_type,
                    value=value,
                    confidence=confidence,
                    text=text,
                    user_id=user_id,
                    guild_id=guild_id,
                    created_at=datetime.utcnow()
                )
                created_entities.append(entity)

            # Cache entities
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': e.id,
                    'entity_type': e.entity_type.value,
                    'value': e.value,
                    'confidence': e.confidence,
                    'text': e.text,
                    'user_id': e.user_id,
                    'guild_id': e.guild_id,
                    'created_at': e.created_at.isoformat()
                } for e in created_entities],
                ttl=self.cache_ttls['nlp_entities']
            )

            record_metric("nlp_entities_extracted", len(created_entities))
            return created_entities

        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            return []

    @time_operation("nlp_get_response")
    async def get_response(self, intent_type: IntentType, user_id: int, guild_id: int) -> Optional[str]:
        """Get appropriate response for an intent."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_response:{intent_type.value}:{user_id}:{guild_id}"
            cached_response = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_response:
                return cached_response

            # Get response from database
            query = """
            SELECT response_text FROM nlp_responses
            WHERE intent_type = :intent_type AND is_active = 1
            ORDER BY RAND()
            LIMIT 1
            """

            result = await self.db_manager.fetch_one(query, {'intent_type': intent_type.value})

            if not result:
                return None

            response_text = result['response_text']

            # Cache response
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                response_text,
                ttl=self.cache_ttls['nlp_responses']
            )

            return response_text

        except Exception as e:
            logger.error(f"Failed to get response: {e}")
            return None

    @time_operation("nlp_process_message")
    async def process_message(self, text: str, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Process a complete message with intent, sentiment, and entities."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_message:{hashlib.md5(text.encode()).hexdigest()}:{user_id}:{guild_id}"
            cached_result = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_result:
                return cached_result

            # Process message components
            intent = await self.classify_intent(text, user_id, guild_id)
            sentiment = await self.analyze_sentiment(text, user_id, guild_id)
            entities = await self.extract_entities(text, user_id, guild_id)
            response = await self.get_response(intent.intent_type, user_id, guild_id) if intent else None

            result = {
                'intent': {
                    'type': intent.intent_type.value if intent else None,
                    'confidence': intent.confidence if intent else 0.0
                },
                'sentiment': {
                    'type': sentiment.sentiment_type.value if sentiment else None,
                    'confidence': sentiment.confidence if sentiment else 0.0
                },
                'entities': [{
                    'type': e.entity_type.value,
                    'value': e.value,
                    'confidence': e.confidence
                } for e in entities],
                'response': response,
                'processed_at': datetime.utcnow().isoformat()
            }

            # Cache result
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                result,
                ttl=self.cache_ttls['nlp_responses']
            )

            record_metric("nlp_messages_processed", 1)
            return result

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return {}

    @time_operation("nlp_get_analytics")
    async def get_analytics(self, guild_id: int, days: int = 30) -> Dict[str, Any]:
        """Get NLP analytics for a guild."""
        try:
            # Try to get from cache first
            cache_key = f"nlp_analytics:{guild_id}:{days}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return cached_analytics

            # Get intent statistics
            intent_query = """
            SELECT intent_type, COUNT(*) as count
            FROM nlp_intents
            WHERE guild_id = :guild_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY intent_type
            """

            intent_results = await self.db_manager.fetch_all(intent_query, {
                'guild_id': guild_id,
                'days': days
            })

            # Get sentiment statistics
            sentiment_query = """
            SELECT sentiment_type, COUNT(*) as count
            FROM nlp_sentiments
            WHERE guild_id = :guild_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY sentiment_type
            """

            sentiment_results = await self.db_manager.fetch_all(sentiment_query, {
                'guild_id': guild_id,
                'days': days
            })

            # Get entity statistics
            entity_query = """
            SELECT entity_type, COUNT(*) as count
            FROM nlp_entities
            WHERE guild_id = :guild_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY entity_type
            """

            entity_results = await self.db_manager.fetch_all(entity_query, {
                'guild_id': guild_id,
                'days': days
            })

            analytics = {
                'intent_distribution': {row['intent_type']: row['count'] for row in intent_results},
                'sentiment_distribution': {row['sentiment_type']: row['count'] for row in sentiment_results},
                'entity_distribution': {row['entity_type']: row['count'] for row in entity_results},
                'total_messages': sum(row['count'] for row in intent_results),
                'most_common_intent': max(intent_results, key=lambda x: x['count'])['intent_type'] if intent_results else None,
                'most_common_sentiment': max(sentiment_results, key=lambda x: x['count'])['sentiment_type'] if sentiment_results else None,
                'most_common_entity': max(entity_results, key=lambda x: x['count'])['entity_type'] if entity_results else None
            }

            # Cache analytics
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                analytics,
                ttl=self.cache_ttls['nlp_analytics']
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get NLP analytics: {e}")
            return {}

    async def clear_nlp_cache(self):
        """Clear all NLP-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("nlp_intents:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_sentiments:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_entities:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_responses:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_patterns:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_training:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_accuracy:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_usage:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("nlp_models:*")
            logger.info("NLP cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear NLP cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get NLP service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
