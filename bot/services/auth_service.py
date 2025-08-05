"""
Advanced Authentication Service for DBSBM System.
Implements enterprise-grade authentication and authorization features.
"""

import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import base64
import pyotp
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from data.db_manager import DatabaseManager
from utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Auth-specific cache TTLs
AUTH_CACHE_TTLS = {
    "user_sessions": 3600,  # 1 hour
    "user_roles": 1800,  # 30 minutes
    "user_permissions": 1800,  # 30 minutes
    "mfa_devices": 3600,  # 1 hour
    "failed_attempts": 300,  # 5 minutes
    "account_locks": 1800,  # 30 minutes
    "role_definitions": 7200,  # 2 hours
    "user_data": 900,  # 15 minutes
    "session_tokens": 3600,  # 1 hour
    "auth_events": 1800,  # 30 minutes
}


class MFAMethod(Enum):
    """Multi-factor authentication methods."""

    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    FIDO2 = "fido2"
    BIOMETRIC = "biometric"


class AuthStatus(Enum):
    """Authentication status."""

    SUCCESS = "success"
    FAILED = "failed"
    LOCKED = "locked"
    MFA_REQUIRED = "mfa_required"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass
class AuthResult:
    """Authentication result."""

    status: AuthStatus
    user_id: Optional[int] = None
    message: str = ""
    mfa_required: bool = False
    mfa_method: Optional[MFAMethod] = None
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    permissions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)


@dataclass
class MFADevice:
    """MFA device configuration."""

    id: int
    user_id: int
    device_type: MFAMethod
    device_id: str
    device_name: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class Role:
    """Role definition."""

    id: int
    role_name: str
    display_name: str
    description: str
    permissions: List[str]
    is_system_role: bool
    is_active: bool


@dataclass
class UserRole:
    """User role assignment."""

    id: int
    user_id: int
    role_id: int
    guild_id: Optional[int]
    assigned_by: Optional[int]
    assigned_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class AuthService:
    """Advanced authentication and authorization service."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = AUTH_CACHE_TTLS

        # Encryption key for sensitive data
        self.secret_key = self._get_or_generate_secret_key()
        self.cipher_suite = Fernet(self.secret_key)

        # Configuration
        self.max_failed_attempts = 5
        self.lockout_duration = 1800  # 30 minutes
        self.session_timeout = 3600  # 1 hour
        self.mfa_timeout = 300  # 5 minutes

        # Background tasks
        self.cleanup_task = None
        self.is_running = False

    async def start(self):
        """Start the authentication service."""
        try:
            await self._initialize_default_roles()
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("Authentication service started successfully")
        except Exception as e:
            logger.error(f"Failed to start authentication service: {e}")
            raise

    async def stop(self):
        """Stop the authentication service."""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("Authentication service stopped")

    @time_operation("auth_authenticate_user")
    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str,
        guild_id: Optional[int] = None,
    ) -> AuthResult:
        """Authenticate a user with username and password."""
        try:
            # Check if account is locked
            if await self._is_account_locked(username):
                return AuthResult(
                    status=AuthStatus.LOCKED,
                    message="Account is temporarily locked due to multiple failed attempts",
                )

            # Get user from cache or database
            cache_key = f"user_data:{username}"
            user_data = await self.cache_manager.enhanced_cache_get(cache_key)

            if not user_data:
                user_data = await self._get_user_by_username(username)
                if user_data:
                    await self.cache_manager.enhanced_cache_set(
                        cache_key, user_data, ttl=self.cache_ttls["user_data"]
                    )

            if not user_data:
                await self._record_failed_attempt(username, ip_address, user_agent)
                return AuthResult(
                    status=AuthStatus.FAILED, message="Invalid username or password"
                )

            # Verify password
            if not await self._verify_password(password, user_data["password_hash"]):
                await self._record_failed_attempt(username, ip_address, user_agent)
                await self._increment_failed_attempts(user_data["id"])
                return AuthResult(
                    status=AuthStatus.FAILED, message="Invalid username or password"
                )

            # Reset failed attempts on successful login
            await self._reset_failed_attempts(user_data["id"])

            # Check if MFA is required
            if await self._is_mfa_required(user_data["id"]):
                primary_mfa = await self._get_primary_mfa_method(user_data["id"])
                return AuthResult(
                    status=AuthStatus.MFA_REQUIRED,
                    user_id=user_data["id"],
                    message="Multi-factor authentication required",
                    mfa_required=True,
                    mfa_method=primary_mfa,
                )

            # Generate session token
            session_token = await self._generate_session_token(user_data["id"])

            # Get user permissions and roles
            permissions, roles = await self._get_user_permissions(
                user_data["id"], guild_id
            )

            # Update last login
            await self._update_last_login(user_data["id"], ip_address)
            await self._record_successful_login(user_data["id"], ip_address, user_agent)

            # Cache session data
            session_data = {
                "user_id": user_data["id"],
                "username": user_data["username"],
                "permissions": permissions,
                "roles": roles,
                "expires_at": datetime.utcnow()
                + timedelta(seconds=self.session_timeout),
            }

            await self.cache_manager.enhanced_cache_set(
                f"session:{session_token}",
                session_data,
                ttl=self.cache_ttls["session_tokens"],
            )

            record_metric("auth_successful_logins", 1)
            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=user_data["id"],
                message="Authentication successful",
                session_token=session_token,
                expires_at=datetime.utcnow() + timedelta(seconds=self.session_timeout),
                permissions=permissions,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                message="Authentication failed due to system error",
            )

    @time_operation("auth_verify_mfa")
    async def verify_mfa(
        self,
        user_id: int,
        mfa_code: str,
        mfa_method: MFAMethod,
        ip_address: str,
        user_agent: str,
    ) -> AuthResult:
        """Verify multi-factor authentication code."""
        try:
            # Get MFA device from cache or database
            cache_key = f"mfa_device:{user_id}:{mfa_method.value}"
            mfa_device_data = await self.cache_manager.enhanced_cache_get(cache_key)

            if not mfa_device_data:
                mfa_device = await self._get_mfa_device(user_id, mfa_method)
                if mfa_device:
                    mfa_device_data = {
                        "id": mfa_device.id,
                        "user_id": mfa_device.user_id,
                        "device_type": mfa_device.device_type.value,
                        "device_id": mfa_device.device_id,
                        "device_name": mfa_device.device_name,
                        "is_active": mfa_device.is_active,
                        "created_at": mfa_device.created_at.isoformat(),
                        "last_used": (
                            mfa_device.last_used.isoformat()
                            if mfa_device.last_used
                            else None
                        ),
                        "expires_at": (
                            mfa_device.expires_at.isoformat()
                            if mfa_device.expires_at
                            else None
                        ),
                    }
                    await self.cache_manager.enhanced_cache_set(
                        cache_key, mfa_device_data, ttl=self.cache_ttls["mfa_devices"]
                    )

            if not mfa_device_data:
                return AuthResult(
                    status=AuthStatus.FAILED, message="MFA device not found"
                )

            # Verify MFA code based on method
            is_valid = False
            if mfa_method == MFAMethod.TOTP:
                is_valid = self._verify_totp_code(
                    mfa_code, mfa_device_data["device_id"]
                )
            elif mfa_method == MFAMethod.SMS:
                is_valid = await self._verify_sms_code(user_id, mfa_code)
            elif mfa_method == MFAMethod.EMAIL:
                is_valid = await self._verify_email_code(user_id, mfa_code)

            if not is_valid:
                await self._record_failed_mfa_attempt(user_id, ip_address, user_agent)
                return AuthResult(status=AuthStatus.FAILED, message="Invalid MFA code")

            # Update MFA device usage
            await self._update_mfa_device_usage(mfa_device_data["id"])

            # Generate session token
            session_token = await self._generate_session_token(user_id)

            # Get user permissions and roles
            permissions, roles = await self._get_user_permissions(user_id)

            # Cache session data
            session_data = {
                "user_id": user_id,
                "permissions": permissions,
                "roles": roles,
                "expires_at": datetime.utcnow()
                + timedelta(seconds=self.session_timeout),
            }

            await self.cache_manager.enhanced_cache_set(
                f"session:{session_token}",
                session_data,
                ttl=self.cache_ttls["session_tokens"],
            )

            record_metric("auth_mfa_successful", 1)
            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=user_id,
                message="MFA verification successful",
                session_token=session_token,
                expires_at=datetime.utcnow() + timedelta(seconds=self.session_timeout),
                permissions=permissions,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                message="MFA verification failed due to system error",
            )

    @time_operation("auth_verify_session")
    async def verify_session(
        self, session_token: str, guild_id: Optional[int] = None
    ) -> AuthResult:
        """Verify a session token."""
        try:
            # Get session data from cache
            session_data = await self.cache_manager.enhanced_cache_get(
                f"session:{session_token}"
            )

            if not session_data:
                return AuthResult(
                    status=AuthStatus.EXPIRED,
                    message="Session token expired or invalid",
                )

            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                # Remove expired session
                await self.cache_manager.enhanced_cache_delete(
                    f"session:{session_token}"
                )
                return AuthResult(
                    status=AuthStatus.EXPIRED, message="Session token expired"
                )

            # Get fresh permissions for the specific guild
            permissions, roles = await self._get_user_permissions(
                session_data["user_id"], guild_id
            )

            # Update session with fresh permissions
            session_data["permissions"] = permissions
            session_data["roles"] = roles

            await self.cache_manager.enhanced_cache_set(
                f"session:{session_token}",
                session_data,
                ttl=self.cache_ttls["session_tokens"],
            )

            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=session_data["user_id"],
                message="Session verified successfully",
                session_token=session_token,
                expires_at=expires_at,
                permissions=permissions,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"Session verification error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, message="Session verification failed"
            )

    @time_operation("auth_logout")
    async def logout(self, session_token: str) -> bool:
        """Logout a user by invalidating their session."""
        try:
            # Remove session from cache
            await self.cache_manager.enhanced_cache_delete(f"session:{session_token}")
            record_metric("auth_logouts", 1)
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    @time_operation("auth_setup_mfa")
    async def setup_mfa(
        self, user_id: int, mfa_method: MFAMethod, device_name: str
    ) -> Dict[str, Any]:
        """Setup multi-factor authentication for a user."""
        try:
            if mfa_method == MFAMethod.TOTP:
                return await self._setup_totp(user_id, device_name)
            elif mfa_method == MFAMethod.SMS:
                return await self._setup_sms(user_id, device_name)
            elif mfa_method == MFAMethod.EMAIL:
                return await self._setup_email(user_id, device_name)
            else:
                return {"error": "Unsupported MFA method"}

        except Exception as e:
            logger.error(f"MFA setup error: {e}")
            return {"error": "Failed to setup MFA"}

    @time_operation("auth_remove_mfa")
    async def remove_mfa(self, user_id: int, device_id: int) -> bool:
        """Remove an MFA device for a user."""
        try:
            # Remove from database
            query = (
                "DELETE FROM mfa_devices WHERE id = :device_id AND user_id = :user_id"
            )
            await self.db_manager.execute(
                query, {"device_id": device_id, "user_id": user_id}
            )

            # Clear related cache entries
            await self.cache_manager.clear_cache_by_pattern(f"mfa_device:{user_id}:*")

            return True
        except Exception as e:
            logger.error(f"Remove MFA error: {e}")
            return False

    @time_operation("auth_get_user_roles")
    async def get_user_roles(
        self, user_id: int, guild_id: Optional[int] = None
    ) -> List[Role]:
        """Get roles assigned to a user."""
        try:
            # Try to get cached roles
            cache_key = f"user_roles:{user_id}:{guild_id or 'global'}"
            cached_roles = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_roles:
                return [Role(**role) for role in cached_roles]

            # Get roles from database
            query = """
            SELECT r.* FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = :user_id AND ur.is_active = 1
            AND (ur.guild_id = :guild_id OR ur.guild_id IS NULL)
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
            """

            results = await self.db_manager.fetch_all(
                query, {"user_id": user_id, "guild_id": guild_id}
            )

            roles = [Role(**row) for row in results]

            # Cache roles
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [asdict(role) for role in roles],
                ttl=self.cache_ttls["user_roles"],
            )

            return roles

        except Exception as e:
            logger.error(f"Get user roles error: {e}")
            return []

    @time_operation("auth_assign_role")
    async def assign_role(
        self,
        user_id: int,
        role_name: str,
        assigned_by: int,
        guild_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Assign a role to a user."""
        try:
            # Get role ID
            role_query = (
                "SELECT id FROM roles WHERE role_name = :role_name AND is_active = 1"
            )
            role_result = await self.db_manager.fetch_one(
                role_query, {"role_name": role_name}
            )

            if not role_result:
                return False

            # Check if role is already assigned
            existing_query = """
            SELECT id FROM user_roles
            WHERE user_id = :user_id AND role_id = :role_id
            AND (guild_id = :guild_id OR (guild_id IS NULL AND :guild_id IS NULL))
            AND is_active = 1
            """

            existing = await self.db_manager.fetch_one(
                existing_query,
                {
                    "user_id": user_id,
                    "role_id": role_result["id"],
                    "guild_id": guild_id,
                },
            )

            if existing:
                return True  # Role already assigned

            # Assign role
            insert_query = """
            INSERT INTO user_roles (user_id, role_id, guild_id, assigned_by, assigned_at, expires_at, is_active)
            VALUES (:user_id, :role_id, :guild_id, :assigned_by, NOW(), :expires_at, 1)
            """

            await self.db_manager.execute(
                insert_query,
                {
                    "user_id": user_id,
                    "role_id": role_result["id"],
                    "guild_id": guild_id,
                    "assigned_by": assigned_by,
                    "expires_at": expires_at,
                },
            )

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"user_roles:{user_id}:*")
            await self.cache_manager.clear_cache_by_pattern(
                f"user_permissions:{user_id}:*"
            )

            # Log role assignment
            await self._log_role_assignment(user_id, role_name, assigned_by, guild_id)

            return True

        except Exception as e:
            logger.error(f"Assign role error: {e}")
            return False

    @time_operation("auth_revoke_role")
    async def revoke_role(
        self,
        user_id: int,
        role_name: str,
        revoked_by: int,
        guild_id: Optional[int] = None,
    ) -> bool:
        """Revoke a role from a user."""
        try:
            # Get role ID
            role_query = (
                "SELECT id FROM roles WHERE role_name = :role_name AND is_active = 1"
            )
            role_result = await self.db_manager.fetch_one(
                role_query, {"role_name": role_name}
            )

            if not role_result:
                return False

            # Revoke role
            update_query = """
            UPDATE user_roles
            SET is_active = 0, revoked_by = :revoked_by, revoked_at = NOW()
            WHERE user_id = :user_id AND role_id = :role_id
            AND (guild_id = :guild_id OR (guild_id IS NULL AND :guild_id IS NULL))
            AND is_active = 1
            """

            result = await self.db_manager.execute(
                update_query,
                {
                    "user_id": user_id,
                    "role_id": role_result["id"],
                    "guild_id": guild_id,
                    "revoked_by": revoked_by,
                },
            )

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"user_roles:{user_id}:*")
            await self.cache_manager.clear_cache_by_pattern(
                f"user_permissions:{user_id}:*"
            )

            # Log role revocation
            await self._log_role_revocation(user_id, role_name, revoked_by, guild_id)

            return True

        except Exception as e:
            logger.error(f"Revoke role error: {e}")
            return False

    @time_operation("auth_check_permission")
    async def check_permission(
        self, user_id: int, permission: str, guild_id: Optional[int] = None
    ) -> bool:
        """Check if a user has a specific permission."""
        try:
            permissions, _ = await self._get_user_permissions(user_id, guild_id)
            return permission in permissions
        except Exception as e:
            logger.error(f"Check permission error: {e}")
            return False

    async def clear_auth_cache(self):
        """Clear all authentication-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("user_data:*")
            await self.cache_manager.clear_cache_by_pattern("user_roles:*")
            await self.cache_manager.clear_cache_by_pattern("user_permissions:*")
            await self.cache_manager.clear_cache_by_pattern("mfa_device:*")
            await self.cache_manager.clear_cache_by_pattern("session:*")
            await self.cache_manager.clear_cache_by_pattern("failed_attempts:*")
            await self.cache_manager.clear_cache_by_pattern("account_locks:*")
            logger.info("Auth cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear auth cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get authentication service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    # Private helper methods

    def _get_or_generate_secret_key(self) -> bytes:
        """Get or generate secret key for encryption."""
        # In production, this should be stored securely
        return Fernet.generate_key()

    async def _initialize_default_roles(self):
        """Initialize default system roles if they don't exist."""
        default_roles = [
            ("admin", "Administrator", "Full system administrator", ["*"]),
            (
                "moderator",
                "Moderator",
                "Guild moderator",
                ["guild.manage", "user.manage", "bet.view", "bet.moderate"],
            ),
            (
                "user",
                "User",
                "Standard user",
                ["bet.create", "bet.view", "profile.manage"],
            ),
            (
                "premium",
                "Premium User",
                "Premium user",
                [
                    "bet.create",
                    "bet.view",
                    "profile.manage",
                    "analytics.view",
                    "ml.predictions",
                ],
            ),
            (
                "enterprise",
                "Enterprise User",
                "Enterprise user",
                [
                    "bet.create",
                    "bet.view",
                    "profile.manage",
                    "analytics.view",
                    "ml.predictions",
                    "enterprise.features",
                    "compliance.view",
                ],
            ),
        ]

        for role_name, display_name, description, permissions in default_roles:
            await self._create_role_if_not_exists(
                role_name, display_name, description, permissions
            )

    async def _create_role_if_not_exists(
        self,
        role_name: str,
        display_name: str,
        description: str,
        permissions: List[str],
    ):
        """Create a role if it doesn't exist."""
        query = "SELECT id FROM roles WHERE role_name = $1"
        existing = await self.db_manager.fetch_one(query, (role_name,))

        if not existing:
            insert_query = """
                INSERT INTO roles (role_name, display_name, description, permissions, is_system_role)
                VALUES ($1, $2, $3, $4, TRUE)
            """
            await self.db_manager.execute(
                insert_query,
                (role_name, display_name, description, json.dumps(permissions)),
            )

    async def _get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        query = "SELECT user_id, username, password_hash FROM users WHERE username = $1"
        return await self.db_manager.fetch_one(query, (username,))

    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception:
            return False

    async def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts."""
        query = """
            SELECT account_locked, account_locked_until
            FROM user_settings us
            JOIN users u ON us.user_id = u.user_id
            WHERE u.username = $1
        """
        result = await self.db_manager.fetch_one(query, (username,))

        if result and result["account_locked"]:
            if (
                result["account_locked_until"]
                and datetime.utcnow() < result["account_locked_until"]
            ):
                return True
            else:
                # Unlock account if lock period has expired
                await self._unlock_account(username)

        return False

    async def _unlock_account(self, username: str):
        """Unlock a locked account."""
        query = """
            UPDATE user_settings us
            JOIN users u ON us.user_id = u.user_id
            SET account_locked = FALSE, account_locked_until = NULL, failed_login_attempts = 0
            WHERE u.username = $1
        """
        await self.db_manager.execute(query, (username,))

    async def _record_failed_attempt(
        self, username: str, ip_address: str, user_agent: str
    ):
        """Record a failed login attempt."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            SELECT 'failed_login', u.user_id, $1, $2, $3, 0.5
            FROM users u WHERE u.username = $1
        """
        event_data = json.dumps(
            {"username": username, "timestamp": datetime.utcnow().isoformat()}
        )
        await self.db_manager.execute(
            query, (ip_address, user_agent, event_data, username)
        )

    async def _increment_failed_attempts(self, user_id: int):
        """Increment failed login attempts for a user."""
        query = """
            UPDATE user_settings
            SET failed_login_attempts = failed_login_attempts + 1,
                account_locked = (failed_login_attempts + 1 >= %s),
                account_locked_until = CASE
                    WHEN (failed_login_attempts + 1 >= %s) THEN DATE_ADD(NOW(), INTERVAL %s MINUTE)
                    ELSE account_locked_until
                END
            WHERE user_id = $1
        """
        await self.db_manager.execute(
            query,
            (
                self.max_failed_attempts,
                self.max_failed_attempts,
                int(self.lockout_duration / 60),
                user_id,
            ),
        )

    async def _reset_failed_attempts(self, user_id: int):
        """Reset failed login attempts for a user."""
        query = """
            UPDATE user_settings
            SET failed_login_attempts = 0, account_locked = FALSE, account_locked_until = NULL
            WHERE user_id = $1
        """
        await self.db_manager.execute(query, (user_id,))

    async def _is_mfa_required(self, user_id: int) -> bool:
        """Check if MFA is required for a user."""
        query = "SELECT mfa_enabled FROM user_settings WHERE user_id = $1"
        result = await self.db_manager.fetch_one(query, (user_id,))
        return result and result["mfa_enabled"]

    async def _get_primary_mfa_method(self, user_id: int) -> Optional[MFAMethod]:
        """Get the primary MFA method for a user."""
        query = """
            SELECT device_type FROM mfa_devices
            WHERE user_id = $1 AND is_active = TRUE
            ORDER BY created_at ASC LIMIT 1
        """
        result = await self.db_manager.fetch_one(query, (user_id,))
        return MFAMethod(result["device_type"]) if result else None

    async def _generate_session_token(self, user_id: int) -> str:
        """Generate a new session token."""
        token = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(seconds=self.session_timeout)
            ).isoformat(),
        }

        # Store session in cache
        await self.cache_manager.enhanced_cache_set(
            f"session:{token}", session_data, ttl=self.cache_ttls["session_tokens"]
        )

        return token

    async def _get_user_permissions(
        self, user_id: int, guild_id: Optional[int] = None
    ) -> Tuple[List[str], List[str]]:
        """Get user permissions and roles."""
        query = """
            SELECT DISTINCT r.role_name, r.permissions
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = $1 AND ur.is_active = TRUE AND r.is_active = TRUE
            AND (ur.guild_id = %s OR ur.guild_id IS NULL)
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        """
        rows = await self.db_manager.fetch_all(query, (user_id, guild_id))

        permissions = set()
        roles = []

        for row in rows:
            roles.append(row["role_name"])
            perms = json.loads(row["permissions"])
            if isinstance(perms, list):
                permissions.update(perms)

        return list(permissions), roles

    async def _update_last_login(self, user_id: int, ip_address: str):
        """Update user's last login information."""
        query = """
            UPDATE user_settings
            SET last_login_ip = $1, last_login_time = NOW()
            WHERE user_id = $1
        """
        await self.db_manager.execute(query, (ip_address, user_id))

    async def _record_successful_login(
        self, user_id: int, ip_address: str, user_agent: str
    ):
        """Record a successful login."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            VALUES ('successful_login', $1, $2, $3, $4, 0.0)
        """
        event_data = json.dumps({"timestamp": datetime.utcnow().isoformat()})
        await self.db_manager.execute(
            query, (user_id, ip_address, user_agent, event_data)
        )

    async def _get_mfa_device(
        self, user_id: int, mfa_method: MFAMethod
    ) -> Optional[MFADevice]:
        """Get MFA device for a user."""
        query = """
            SELECT * FROM mfa_devices
            WHERE user_id = $1 AND device_type = $2 AND is_active = TRUE
        """
        result = await self.db_manager.fetch_one(query, (user_id, mfa_method.value))

        if result:
            return MFADevice(
                id=result["id"],
                user_id=result["user_id"],
                device_type=MFAMethod(result["device_type"]),
                device_id=result["device_id"],
                device_name=result["device_name"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                last_used=result["last_used"],
                expires_at=result["expires_at"],
            )
        return None

    def _verify_totp_code(self, code: str, secret: str) -> bool:
        """Verify TOTP code."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        except Exception:
            return False

    async def _verify_sms_code(self, user_id: int, code: str) -> bool:
        """Verify SMS code (placeholder implementation)."""
        # In production, implement SMS verification logic
        return False

    async def _verify_email_code(self, user_id: int, code: str) -> bool:
        """Verify email code (placeholder implementation)."""
        # In production, implement email verification logic
        return False

    async def _update_mfa_device_usage(self, device_id: int):
        """Update MFA device last used timestamp."""
        query = "UPDATE mfa_devices SET last_used = NOW() WHERE id = $1"
        await self.db_manager.execute(query, (device_id,))

    async def _record_failed_mfa_attempt(
        self, user_id: int, ip_address: str, user_agent: str
    ):
        """Record a failed MFA attempt."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            VALUES ('failed_mfa', $1, $2, $3, $4, 0.7)
        """
        event_data = json.dumps({"timestamp": datetime.utcnow().isoformat()})
        await self.db_manager.execute(
            query, (user_id, ip_address, user_agent, event_data)
        )

    async def _setup_totp(self, user_id: int, device_name: str) -> Dict[str, Any]:
        """Setup TOTP MFA."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code URL
        qr_url = totp.provisioning_uri(
            name=f"{user_id}@{self.totp_issuer}", issuer_name=self.totp_issuer
        )

        # Store device
        query = """
            INSERT INTO mfa_devices (user_id, device_type, device_id, device_name)
            VALUES ($1, $2, $3, $4)
        """
        await self.db_manager.execute(
            query, (user_id, MFAMethod.TOTP.value, secret, device_name)
        )

        # Enable MFA for user
        await self.db_manager.execute(
            "UPDATE user_settings SET mfa_enabled = TRUE, mfa_method = $1 WHERE user_id = $2",
            (MFAMethod.TOTP.value, user_id),
        )

        return {
            "secret": secret,
            "qr_url": qr_url,
            "backup_codes": self._generate_backup_codes(),
        }

    async def _setup_sms(self, user_id: int, device_name: str) -> Dict[str, Any]:
        """Setup SMS MFA (placeholder implementation)."""
        # In production, implement SMS setup logic
        raise NotImplementedError("SMS MFA not implemented")

    async def _setup_email(self, user_id: int, device_name: str) -> Dict[str, Any]:
        """Setup email MFA (placeholder implementation)."""
        # In production, implement email setup logic
        raise NotImplementedError("Email MFA not implemented")

    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes for MFA."""
        return [secrets.token_hex(4).upper() for _ in range(10)]

    async def _log_role_assignment(
        self, user_id: int, role_name: str, assigned_by: int, guild_id: Optional[int]
    ):
        """Log role assignment for audit."""
        query = """
            INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, action_data, ip_address)
            VALUES ($1, 'role_assigned', 'role', $2, $3, 'system')
        """
        action_data = json.dumps(
            {
                "role_name": role_name,
                "assigned_by": assigned_by,
                "guild_id": guild_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        await self.db_manager.execute(query, (user_id, role_name, action_data))

    async def _log_role_revocation(
        self, user_id: int, role_name: str, revoked_by: int, guild_id: Optional[int]
    ):
        """Log role revocation for audit."""
        query = """
            INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, action_data, ip_address)
            VALUES ($1, 'role_revoked', 'role', $2, $3, 'system')
        """
        action_data = json.dumps(
            {
                "role_name": role_name,
                "revoked_by": revoked_by,
                "guild_id": guild_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        await self.db_manager.execute(query, (user_id, role_name, action_data))
