"""
SMS Service for sending text message notifications to phones.

This service integrates with Twilio to send SMS notifications to users' phone numbers.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

# Twilio imports
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio not installed. SMS functionality will be disabled.")

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS notifications via Twilio."""
    
    def __init__(self, bot, db_manager, twilio_account_sid: str = None, twilio_auth_token: str = None, twilio_phone_number: str = None):
        self.bot = bot
        self.db_manager = db_manager
        self.twilio_client = None
        self.twilio_phone_number = twilio_phone_number
        self.sms_cooldowns = {}  # Prevent SMS spam
        self.sms_logs = []  # Keep track of sent SMS
        
        # Initialize Twilio client if credentials provided
        if TWILIO_AVAILABLE and twilio_account_sid and twilio_auth_token:
            try:
                self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
                logger.info("Twilio SMS service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.twilio_client = None
        else:
            logger.warning("SMS service disabled - Twilio credentials not provided or Twilio not installed")
    
    async def start(self):
        """Initialize the SMS service."""
        logger.info("Starting SMS service...")
        
        # Create SMS tables if they don't exist
        await self.create_sms_tables()
        
        # Load user phone numbers from database
        await self.load_user_phones()
        
        logger.info("SMS service started successfully")
    
    async def create_sms_tables(self):
        """Create necessary database tables for SMS functionality."""
        try:
            # Table for storing user phone numbers
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS user_phone_numbers (
                    user_id BIGINT PRIMARY KEY,
                    phone_number VARCHAR(20) NOT NULL,
                    country_code VARCHAR(3) DEFAULT '+1',
                    verified BOOLEAN DEFAULT FALSE,
                    verification_code VARCHAR(6),
                    verification_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_phone_verified (verified),
                    INDEX idx_user_phone_number (phone_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Table for SMS logs
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS sms_logs (
                    sms_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    message_type VARCHAR(50) NOT NULL,
                    message_content TEXT NOT NULL,
                    twilio_sid VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP NULL,
                    error_message TEXT,
                    INDEX idx_sms_logs_user (user_id),
                    INDEX idx_sms_logs_status (status),
                    INDEX idx_sms_logs_time (sent_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            logger.info("SMS database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating SMS tables: {e}")
    
    async def load_user_phones(self):
        """Load user phone numbers from database."""
        try:
            phones = await self.db_manager.fetch_all(
                "SELECT user_id, phone_number, verified FROM user_phone_numbers WHERE verified = TRUE"
            )
            logger.info(f"Loaded {len(phones)} verified phone numbers")
        except Exception as e:
            logger.error(f"Error loading user phones: {e}")
    
    async def add_user_phone(self, user_id: int, phone_number: str, country_code: str = '+1') -> bool:
        """
        Add a phone number for a user.
        
        Args:
            user_id: Discord user ID
            phone_number: Phone number (without country code)
            country_code: Country code (default: +1 for US/Canada)
            
        Returns:
            bool: True if phone number added successfully
        """
        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number, country_code)
            
            # Generate verification code
            verification_code = self.generate_verification_code()
            verification_expires = datetime.now() + timedelta(minutes=10)
            
            # Store in database
            await self.db_manager.execute("""
                INSERT INTO user_phone_numbers (user_id, phone_number, country_code, verification_code, verification_expires)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    phone_number = VALUES(phone_number),
                    country_code = VALUES(country_code),
                    verification_code = VALUES(verification_code),
                    verification_expires = VALUES(verification_expires),
                    verified = FALSE
            """, (user_id, formatted_phone, country_code, verification_code, verification_expires))
            
            # Send verification SMS
            verification_sent = await self.send_verification_sms(formatted_phone, verification_code)
            
            if verification_sent:
                logger.info(f"Verification code sent to {formatted_phone} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to send verification SMS to {formatted_phone}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding user phone: {e}")
            return False
    
    async def verify_user_phone(self, user_id: int, verification_code: str) -> bool:
        """
        Verify a user's phone number with the provided code.
        
        Args:
            user_id: Discord user ID
            verification_code: 6-digit verification code
            
        Returns:
            bool: True if verification successful
        """
        try:
            # Check verification code
            result = await self.db_manager.fetch_one("""
                SELECT phone_number, verification_expires 
                FROM user_phone_numbers 
                WHERE user_id = %s AND verification_code = %s AND verified = FALSE
            """, (user_id, verification_code))
            
            if not result:
                return False
            
            # Check if code is expired
            if result['verification_expires'] < datetime.now():
                logger.warning(f"Verification code expired for user {user_id}")
                return False
            
            # Mark as verified
            await self.db_manager.execute("""
                UPDATE user_phone_numbers 
                SET verified = TRUE, verification_code = NULL, verification_expires = NULL
                WHERE user_id = %s
            """, (user_id,))
            
            logger.info(f"Phone number verified for user {user_id}: {result['phone_number']}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying user phone: {e}")
            return False
    
    async def send_sms_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "general",
        priority: str = "normal"
    ) -> bool:
        """
        Send an SMS notification to a user.
        
        Args:
            user_id: Discord user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            
        Returns:
            bool: True if SMS sent successfully
        """
        try:
            # Check if SMS service is available
            if not self.twilio_client:
                logger.warning("SMS service not available - Twilio not configured")
                return False
            
            # Get user's verified phone number
            phone_result = await self.db_manager.fetch_one("""
                SELECT phone_number FROM user_phone_numbers 
                WHERE user_id = %s AND verified = TRUE
            """, (user_id,))
            
            if not phone_result:
                logger.warning(f"No verified phone number found for user {user_id}")
                return False
            
            phone_number = phone_result['phone_number']
            
            # Check cooldown
            cooldown_key = f"sms_{user_id}"
            if cooldown_key in self.sms_cooldowns:
                last_sent = self.sms_cooldowns[cooldown_key]
                if datetime.now() - last_sent < timedelta(minutes=5):  # 5-minute cooldown
                    logger.info(f"SMS cooldown active for user {user_id}")
                    return False
            
            # Format SMS message
            sms_content = f"{title}\n\n{message}\n\n- Discord Bot"
            
            # Send SMS via Twilio
            try:
                message_obj = self.twilio_client.messages.create(
                    body=sms_content,
                    from_=self.twilio_phone_number,
                    to=phone_number
                )
                
                # Log the SMS
                await self.log_sms(
                    user_id=user_id,
                    phone_number=phone_number,
                    message_type=notification_type,
                    message_content=sms_content,
                    twilio_sid=message_obj.sid,
                    status='sent'
                )
                
                # Update cooldown
                self.sms_cooldowns[cooldown_key] = datetime.now()
                
                logger.info(f"SMS sent to user {user_id} ({phone_number}): {message_obj.sid}")
                return True
                
            except TwilioException as e:
                logger.error(f"Twilio error sending SMS to {phone_number}: {e}")
                
                # Log the error
                await self.log_sms(
                    user_id=user_id,
                    phone_number=phone_number,
                    message_type=notification_type,
                    message_content=sms_content,
                    status='error',
                    error_message=str(e)
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    async def send_verification_sms(self, phone_number: str, verification_code: str) -> bool:
        """Send verification SMS with code."""
        try:
            if not self.twilio_client:
                return False
            
            message_content = f"Your Discord Bot verification code is: {verification_code}\n\nThis code expires in 10 minutes."
            
            message_obj = self.twilio_client.messages.create(
                body=message_content,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"Verification SMS sent to {phone_number}: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification SMS: {e}")
            return False
    
    async def log_sms(
        self,
        user_id: int,
        phone_number: str,
        message_type: str,
        message_content: str,
        twilio_sid: str = None,
        status: str = 'pending',
        error_message: str = None
    ):
        """Log SMS to database."""
        try:
            await self.db_manager.execute("""
                INSERT INTO sms_logs (
                    user_id, phone_number, message_type, message_content, 
                    twilio_sid, status, error_message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, phone_number, message_type, message_content, twilio_sid, status, error_message))
            
        except Exception as e:
            logger.error(f"Error logging SMS: {e}")
    
    def format_phone_number(self, phone_number: str, country_code: str = '+1') -> str:
        """Format phone number for Twilio."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present
        if not phone_number.startswith('+'):
            return f"{country_code}{digits_only}"
        
        return phone_number
    
    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code."""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    async def get_user_phone_status(self, user_id: int) -> Dict[str, Any]:
        """Get phone number status for a user."""
        try:
            result = await self.db_manager.fetch_one("""
                SELECT phone_number, verified, created_at, updated_at
                FROM user_phone_numbers 
                WHERE user_id = %s
            """, (user_id,))
            
            if result:
                return {
                    "has_phone": True,
                    "phone_number": result['phone_number'],
                    "verified": result['verified'],
                    "created_at": result['created_at'],
                    "updated_at": result['updated_at']
                }
            else:
                return {
                    "has_phone": False,
                    "phone_number": None,
                    "verified": False
                }
                
        except Exception as e:
            logger.error(f"Error getting user phone status: {e}")
            return {"error": str(e)}
    
    async def get_sms_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get SMS statistics."""
        try:
            # Total SMS sent
            total_result = await self.db_manager.fetch_one("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
                       SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
                FROM sms_logs 
                WHERE sent_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            
            # Recent SMS
            recent_sms = await self.db_manager.fetch_all("""
                SELECT user_id, phone_number, message_type, status, sent_at
                FROM sms_logs 
                WHERE sent_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY sent_at DESC 
                LIMIT 10
            """, (days,))
            
            return {
                "total_sms": total_result['total'] or 0,
                "successful_sms": total_result['successful'] or 0,
                "failed_sms": total_result['failed'] or 0,
                "recent_sms": recent_sms
            }
            
        except Exception as e:
            logger.error(f"Error getting SMS stats: {e}")
            return {"error": str(e)}


async def create_sms_tables(db_manager):
    """Create SMS tables in database."""
    service = SMSService(None, db_manager)
    await service.create_sms_tables() 