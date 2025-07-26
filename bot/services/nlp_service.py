"""
Natural Language Processing Service for DBSBM System.
Implements AI-powered chatbot, sentiment analysis, and language processing features.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from data.db_manager import DatabaseManager
from data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Intent types for user interactions."""
    BET_PLACE = "bet_place"
    BET_QUERY = "bet_query"
    ODDS_QUERY = "odds_query"
    STATS_QUERY = "stats_query"
    HELP_REQUEST = "help_request"
    ACCOUNT_QUERY = "account_query"
    SETTINGS_CHANGE = "settings_change"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

class SentimentType(Enum):
    """Sentiment classification types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class LanguageType(Enum):
    """Supported languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"

@dataclass
class NLPResult:
    """NLP processing result."""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    sentiment: SentimentType
    sentiment_score: float
    language: LanguageType
    processed_text: str
    response: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)

@dataclass
class ConversationContext:
    """Conversation context for maintaining state."""
    conversation_id: str
    user_id: int
    guild_id: Optional[int]
    messages: List[Dict[str, Any]]
    current_intent: Optional[IntentType]
    entities: Dict[str, Any]
    language: LanguageType
    created_at: datetime
    last_updated: datetime

@dataclass
class ChatbotResponse:
    """Chatbot response with context."""
    message: str
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    suggestions: List[str]
    requires_action: bool
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None

class NLPService:
    """Natural Language Processing service for AI-powered interactions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.nlp_models = {}
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.response_templates = self._load_response_templates()
        self.conversation_contexts = {}
        self.max_context_age = timedelta(hours=1)

        # Initialize NLP models
        self._initialize_models()

    async def start(self):
        """Start the NLP service."""
        logger.info("Starting NLPService...")

        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")

        # Initialize spaCy model
        try:
            self.spacy_model = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, downloading...")
            try:
                spacy.cli.download("en_core_web_sm")
                self.spacy_model = spacy.load("en_core_web_sm")
            except Exception as e:
                logger.error(f"Could not load spaCy model: {e}")
                self.spacy_model = None

        logger.info("NLPService started successfully")

    async def stop(self):
        """Stop the NLP service."""
        logger.info("Stopping NLPService...")
        # Clear conversation contexts
        self.conversation_contexts.clear()
        logger.info("NLPService stopped")

    @time_operation("nlp_process_message")
    async def process_message(self, user_id: int, message: str, guild_id: Optional[int] = None,
                            conversation_id: Optional[str] = None) -> NLPResult:
        """Process a user message and return NLP analysis."""
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # Detect language
            language = self._detect_language(message)

            # Preprocess text
            processed_text = self._preprocess_text(message, language)

            # Detect intent
            intent, confidence = self._detect_intent(processed_text, language)

            # Extract entities
            entities = self._extract_entities(processed_text, intent, language)

            # Analyze sentiment
            sentiment, sentiment_score = self._analyze_sentiment(processed_text, language)

            # Store conversation
            await self._store_conversation(user_id, guild_id, conversation_id, message,
                                         intent, entities, language)

            # Update conversation context
            self._update_conversation_context(user_id, guild_id, conversation_id,
                                            intent, entities, language)

            record_metric("nlp_messages_processed", 1)

            return NLPResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                language=language,
                processed_text=processed_text
            )

        except Exception as e:
            logger.error(f"NLP processing error: {e}")
            record_metric("nlp_errors", 1)
            return NLPResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                sentiment=SentimentType.NEUTRAL,
                sentiment_score=0.0,
                language=LanguageType.ENGLISH,
                processed_text=message
            )

    @time_operation("nlp_generate_response")
    async def generate_response(self, user_id: int, nlp_result: NLPResult,
                              guild_id: Optional[int] = None) -> ChatbotResponse:
        """Generate an appropriate response based on NLP analysis."""
        try:
            # Get conversation context
            context = self._get_conversation_context(user_id, guild_id)

            # Generate response based on intent
            response = await self._generate_intent_response(nlp_result, context)

            # Generate suggestions
            suggestions = self._generate_suggestions(nlp_result.intent, nlp_result.entities)

            # Determine if action is required
            requires_action, action_type, action_data = self._determine_action_required(nlp_result)

            record_metric("nlp_responses_generated", 1)

            return ChatbotResponse(
                message=response,
                intent=nlp_result.intent,
                confidence=nlp_result.confidence,
                entities=nlp_result.entities,
                suggestions=suggestions,
                requires_action=requires_action,
                action_type=action_type,
                action_data=action_data
            )

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return ChatbotResponse(
                message="I'm sorry, I didn't understand that. Could you please rephrase?",
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                suggestions=["Try asking about placing a bet", "Ask about odds", "Request help"],
                requires_action=False
            )

    @time_operation("nlp_analyze_sentiment")
    async def analyze_sentiment(self, text: str, language: LanguageType = LanguageType.ENGLISH) -> Tuple[SentimentType, float]:
        """Analyze sentiment of text."""
        try:
            sentiment, score = self._analyze_sentiment(text, language)
            return sentiment, score
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return SentimentType.NEUTRAL, 0.0

    @time_operation("nlp_extract_entities")
    async def extract_entities(self, text: str, intent: IntentType,
                             language: LanguageType = LanguageType.ENGLISH) -> Dict[str, Any]:
        """Extract entities from text."""
        try:
            processed_text = self._preprocess_text(text, language)
            entities = self._extract_entities(processed_text, intent, language)
            return entities
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {}

    @time_operation("nlp_get_conversation_history")
    async def get_conversation_history(self, user_id: int, guild_id: Optional[int] = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        try:
            query = """
                SELECT * FROM nlp_conversations
                WHERE user_id = %s AND guild_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            rows = await self.db_manager.fetch_all(query, (user_id, guild_id, limit))

            conversations = []
            for row in rows:
                conversations.append({
                    'conversation_id': row['conversation_id'],
                    'message_content': row['message_content'],
                    'intent_recognized': row['intent_recognized'],
                    'entities_extracted': json.loads(row['entities_extracted']) if row['entities_extracted'] else {},
                    'response_generated': row['response_generated'],
                    'confidence_score': row['confidence_score'],
                    'sentiment_score': row['sentiment_score'],
                    'timestamp': row['timestamp']
                })

            return conversations
        except Exception as e:
            logger.error(f"Get conversation history error: {e}")
            return []

    @time_operation("nlp_get_user_sentiment_trends")
    async def get_user_sentiment_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get sentiment trends for a user over time."""
        try:
            query = """
                SELECT
                    DATE(timestamp) as date,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as message_count,
                    AVG(confidence_score) as avg_confidence
                FROM nlp_conversations
                WHERE user_id = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
            rows = await self.db_manager.fetch_all(query, (user_id, days))

            trends = {
                'dates': [],
                'sentiment_scores': [],
                'message_counts': [],
                'confidence_scores': [],
                'overall_sentiment': 'neutral',
                'total_messages': 0
            }

            total_sentiment = 0
            total_messages = 0

            for row in rows:
                trends['dates'].append(row['date'].isoformat())
                trends['sentiment_scores'].append(float(row['avg_sentiment']))
                trends['message_counts'].append(row['message_count'])
                trends['confidence_scores'].append(float(row['avg_confidence']))

                total_sentiment += float(row['avg_sentiment']) * row['message_count']
                total_messages += row['message_count']

            if total_messages > 0:
                overall_sentiment = total_sentiment / total_messages
                if overall_sentiment > 0.1:
                    trends['overall_sentiment'] = 'positive'
                elif overall_sentiment < -0.1:
                    trends['overall_sentiment'] = 'negative'
                else:
                    trends['overall_sentiment'] = 'neutral'

            trends['total_messages'] = total_messages

            return trends
        except Exception as e:
            logger.error(f"Get sentiment trends error: {e}")
            return {}

    # Private helper methods

    def _initialize_models(self):
        """Initialize NLP models."""
        try:
            # Initialize sentiment analysis model
            self.sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

            # Initialize intent classification model (placeholder)
            # In production, use a fine-tuned model for intent classification
            self.intent_model = None

        except Exception as e:
            logger.warning(f"Could not initialize some NLP models: {e}")

    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load intent recognition patterns."""
        return {
            IntentType.BET_PLACE: [
                r'\b(bet|wager|place|put|make)\b.*\b(on|for)\b',
                r'\b(betting|gambling)\b.*\b(odds|chances)\b',
                r'\b(win|lose|earn|make money)\b.*\b(bet|wager)\b'
            ],
            IntentType.BET_QUERY: [
                r'\b(my|current|active)\b.*\b(bets|wagers)\b',
                r'\b(bet history|betting history|past bets)\b',
                r'\b(how much|what)\b.*\b(bet|wager)\b'
            ],
            IntentType.ODDS_QUERY: [
                r'\b(odds|chances|probability)\b.*\b(for|of)\b',
                r'\b(what are|show me|get)\b.*\b(odds)\b',
                r'\b(betting odds|game odds|match odds)\b'
            ],
            IntentType.STATS_QUERY: [
                r'\b(stats|statistics|record|performance)\b',
                r'\b(how good|how well)\b.*\b(team|player)\b',
                r'\b(win rate|success rate|performance)\b'
            ],
            IntentType.HELP_REQUEST: [
                r'\b(help|support|assist|guide)\b',
                r'\b(how to|what is|explain)\b',
                r'\b(problem|issue|trouble|error)\b'
            ],
            IntentType.ACCOUNT_QUERY: [
                r'\b(account|profile|balance|money)\b',
                r'\b(my|personal)\b.*\b(info|information|details)\b',
                r'\b(settings|preferences|options)\b'
            ],
            IntentType.GREETING: [
                r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
                r'\b(how are you|how\'s it going|what\'s up)\b'
            ],
            IntentType.GOODBYE: [
                r'\b(goodbye|bye|see you|farewell|take care)\b',
                r'\b(thanks|thank you|appreciate it)\b'
            ]
        }

    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load entity extraction patterns."""
        return {
            'team': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b.*\b(team|club|squad)\b',
                r'\b(team|club)\b.*\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            ],
            'player': [
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b.*\b(player|athlete|star)\b',
                r'\b(player|athlete)\b.*\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
            ],
            'amount': [
                r'\b(\$?\d+(?:\.\d{2})?)\b',
                r'\b(\d+)\b.*\b(dollars|bucks|money)\b'
            ],
            'sport': [
                r'\b(football|soccer|basketball|baseball|hockey|tennis|golf|racing)\b',
                r'\b(NFL|NBA|MLB|NHL|MLS|EPL|La Liga|Bundesliga)\b'
            ],
            'game': [
                r'\b(game|match|contest|fixture)\b.*\b(\d+|\w+)\b',
                r'\b(\w+)\b.*\b(vs|versus|against)\b.*\b(\w+)\b'
            ]
        }

    def _load_response_templates(self) -> Dict[IntentType, List[str]]:
        """Load response templates for different intents."""
        return {
            IntentType.BET_PLACE: [
                "I can help you place a bet! What team or player would you like to bet on?",
                "Sure! To place a bet, I'll need to know what you want to bet on and how much.",
                "Great! Let's place that bet. What are the details?"
            ],
            IntentType.BET_QUERY: [
                "Let me check your current bets for you.",
                "I'll look up your betting history right away.",
                "Here's what I found about your bets:"
            ],
            IntentType.ODDS_QUERY: [
                "I can help you find the latest odds. What game or event are you interested in?",
                "Let me get the current odds for you. Which team or player?",
                "Here are the current odds:"
            ],
            IntentType.STATS_QUERY: [
                "I can provide you with detailed statistics. What would you like to know?",
                "Let me get those stats for you. Which team or player?",
                "Here are the statistics you requested:"
            ],
            IntentType.HELP_REQUEST: [
                "I'm here to help! What can I assist you with?",
                "Sure! I can help with betting, odds, statistics, and more. What do you need?",
                "I'd be happy to help! What's your question?"
            ],
            IntentType.ACCOUNT_QUERY: [
                "I can help you with your account information. What would you like to know?",
                "Let me check your account details for you.",
                "Here's your account information:"
            ],
            IntentType.GREETING: [
                "Hello! How can I help you today?",
                "Hi there! I'm here to assist with your betting needs.",
                "Greetings! What can I do for you?"
            ],
            IntentType.GOODBYE: [
                "Goodbye! Have a great day!",
                "See you later! Feel free to ask if you need anything else.",
                "Take care! Come back anytime for betting assistance."
            ],
            IntentType.UNKNOWN: [
                "I'm not sure I understood that. Could you please rephrase?",
                "I didn't quite catch that. Can you try asking in a different way?",
                "I'm still learning! Could you be more specific?"
            ]
        }

    def _detect_language(self, text: str) -> LanguageType:
        """Detect the language of the text."""
        try:
            # Simple language detection based on common words
            text_lower = text.lower()

            # Spanish
            if any(word in text_lower for word in ['hola', 'gracias', 'por favor', 'sí', 'no']):
                return LanguageType.SPANISH

            # French
            if any(word in text_lower for word in ['bonjour', 'merci', 's\'il vous plaît', 'oui', 'non']):
                return LanguageType.FRENCH

            # German
            if any(word in text_lower for word in ['hallo', 'danke', 'bitte', 'ja', 'nein']):
                return LanguageType.GERMAN

            # Default to English
            return LanguageType.ENGLISH
        except Exception:
            return LanguageType.ENGLISH

    def _preprocess_text(self, text: str, language: LanguageType) -> str:
        """Preprocess text for NLP analysis."""
        try:
            # Convert to lowercase
            text = text.lower()

            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Remove special characters but keep important ones
            text = re.sub(r'[^\w\s\$\.,!?]', '', text)

            # Tokenize and lemmatize if spaCy is available
            if self.spacy_model and language == LanguageType.ENGLISH:
                doc = self.spacy_model(text)
                tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
                text = ' '.join(tokens)

            return text
        except Exception as e:
            logger.warning(f"Text preprocessing error: {e}")
            return text.lower().strip()

    def _detect_intent(self, text: str, language: LanguageType) -> Tuple[IntentType, float]:
        """Detect intent from text."""
        try:
            best_intent = IntentType.UNKNOWN
            best_confidence = 0.0

            # Pattern matching
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        confidence = len(matches) / len(text.split())
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent

            # Use ML model if available
            if self.intent_model:
                # Placeholder for ML-based intent detection
                pass

            # Minimum confidence threshold
            if best_confidence < 0.1:
                best_intent = IntentType.UNKNOWN
                best_confidence = 0.0

            return best_intent, min(best_confidence, 1.0)

        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            return IntentType.UNKNOWN, 0.0

    def _extract_entities(self, text: str, intent: IntentType, language: LanguageType) -> Dict[str, Any]:
        """Extract entities from text."""
        try:
            entities = {}

            # Pattern-based entity extraction
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        entities[entity_type] = matches

            # Use spaCy for named entity recognition if available
            if self.spacy_model and language == LanguageType.ENGLISH:
                doc = self.spacy_model(text)
                for ent in doc.ents:
                    if ent.label_ not in entities:
                        entities[ent.label_.lower()] = []
                    entities[ent.label_.lower()].append(ent.text)

            return entities

        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {}

    def _analyze_sentiment(self, text: str, language: LanguageType) -> Tuple[SentimentType, float]:
        """Analyze sentiment of text."""
        try:
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity

            # Use ML model if available
            if self.sentiment_model and language == LanguageType.ENGLISH:
                result = self.sentiment_model(text)
                if result:
                    # Map model output to our sentiment types
                    label = result[0]['label']
                    score = result[0]['score']

                    if label == 'POS':
                        sentiment_score = score
                    elif label == 'NEG':
                        sentiment_score = -score
                    else:
                        sentiment_score = 0.0

            # Classify sentiment
            if sentiment_score > 0.1:
                sentiment = SentimentType.POSITIVE
            elif sentiment_score < -0.1:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL

            return sentiment, sentiment_score

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return SentimentType.NEUTRAL, 0.0

    async def _store_conversation(self, user_id: int, guild_id: Optional[int], conversation_id: str,
                                message: str, intent: IntentType, entities: Dict[str, Any],
                                language: LanguageType):
        """Store conversation in database."""
        try:
            query = """
                INSERT INTO nlp_conversations
                (user_id, guild_id, conversation_id, message_type, message_content,
                 intent_recognized, entities_extracted, language_detected, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            await self.db_manager.execute(query, (
                user_id, guild_id, conversation_id, 'user_input', message,
                intent.value, json.dumps(entities), language.value
            ))
        except Exception as e:
            logger.error(f"Store conversation error: {e}")

    def _update_conversation_context(self, user_id: int, guild_id: Optional[int],
                                   conversation_id: str, intent: IntentType,
                                   entities: Dict[str, Any], language: LanguageType):
        """Update conversation context."""
        try:
            context_key = f"{user_id}:{guild_id or 'global'}"

            if context_key not in self.conversation_contexts:
                self.conversation_contexts[context_key] = ConversationContext(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    guild_id=guild_id,
                    messages=[],
                    current_intent=None,
                    entities={},
                    language=language,
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )

            context = self.conversation_contexts[context_key]
            context.last_updated = datetime.utcnow()
            context.current_intent = intent
            context.entities.update(entities)
            context.language = language

            # Clean old contexts
            self._cleanup_old_contexts()

        except Exception as e:
            logger.error(f"Update conversation context error: {e}")

    def _get_conversation_context(self, user_id: int, guild_id: Optional[int]) -> Optional[ConversationContext]:
        """Get conversation context for a user."""
        try:
            context_key = f"{user_id}:{guild_id or 'global'}"
            context = self.conversation_contexts.get(context_key)

            if context and (datetime.utcnow() - context.last_updated) < self.max_context_age:
                return context

            return None
        except Exception as e:
            logger.error(f"Get conversation context error: {e}")
            return None

    def _cleanup_old_contexts(self):
        """Clean up old conversation contexts."""
        try:
            current_time = datetime.utcnow()
            keys_to_remove = []

            for key, context in self.conversation_contexts.items():
                if (current_time - context.last_updated) > self.max_context_age:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.conversation_contexts[key]

        except Exception as e:
            logger.error(f"Cleanup contexts error: {e}")

    async def _generate_intent_response(self, nlp_result: NLPResult,
                                      context: Optional[ConversationContext]) -> str:
        """Generate response based on intent."""
        try:
            templates = self.response_templates.get(nlp_result.intent, [])

            if not templates:
                return "I'm not sure how to respond to that."

            # Select template based on context and entities
            template = templates[0]  # Simple selection for now

            # Customize response based on entities
            if nlp_result.entities:
                if 'team' in nlp_result.entities:
                    template = template.replace("What team or player", f"What about {nlp_result.entities['team'][0]}")
                if 'amount' in nlp_result.entities:
                    template = template.replace("how much", f"${nlp_result.entities['amount'][0]}")

            return template

        except Exception as e:
            logger.error(f"Generate intent response error: {e}")
            return "I'm sorry, I didn't understand that."

    def _generate_suggestions(self, intent: IntentType, entities: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on intent and entities."""
        try:
            suggestions = []

            if intent == IntentType.BET_PLACE:
                suggestions = [
                    "What team would you like to bet on?",
                    "How much would you like to bet?",
                    "What type of bet would you prefer?"
                ]
            elif intent == IntentType.ODDS_QUERY:
                suggestions = [
                    "Which game are you interested in?",
                    "What team's odds would you like to see?",
                    "Would you like to see live odds?"
                ]
            elif intent == IntentType.STATS_QUERY:
                suggestions = [
                    "Which team's stats would you like to see?",
                    "What type of statistics are you looking for?",
                    "Would you like recent performance data?"
                ]
            elif intent == IntentType.HELP_REQUEST:
                suggestions = [
                    "I can help you place bets",
                    "I can show you odds and statistics",
                    "I can help with your account"
                ]
            else:
                suggestions = [
                    "Try asking about placing a bet",
                    "Ask about current odds",
                    "Request help or support"
                ]

            return suggestions[:3]  # Limit to 3 suggestions

        except Exception as e:
            logger.error(f"Generate suggestions error: {e}")
            return ["Try asking for help"]

    def _determine_action_required(self, nlp_result: NLPResult) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Determine if an action is required based on NLP result."""
        try:
            if nlp_result.intent == IntentType.BET_PLACE:
                return True, "place_bet", nlp_result.entities
            elif nlp_result.intent == IntentType.ODDS_QUERY:
                return True, "get_odds", nlp_result.entities
            elif nlp_result.intent == IntentType.STATS_QUERY:
                return True, "get_stats", nlp_result.entities
            elif nlp_result.intent == IntentType.BET_QUERY:
                return True, "get_bets", nlp_result.entities
            else:
                return False, None, None

        except Exception as e:
            logger.error(f"Determine action required error: {e}")
            return False, None, None
