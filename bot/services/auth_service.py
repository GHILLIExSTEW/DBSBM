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
from bot.data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

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
        self.secret_key = self._get_or_generate_secret_key()
        self.fernet = Fernet(self.secret_key)
        self.totp_issuer = "DBSBM"
        self.session_timeout = timedelta(hours=24)
        self.mfa_timeout = timedelta(minutes=5)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)

    async def start(self):
        """Start the authentication service."""
        logger.info("Starting AuthService...")
        await self._initialize_default_roles()
        logger.info("AuthService started successfully")

    async def stop(self):
        """Stop the authentication service."""
        logger.info("Stopping AuthService...")
        logger.info("AuthService stopped")

    @time_operation("auth_authenticate_user")
    async def authenticate_user(self, username: str, password: str, ip_address: str,
                              user_agent: str, guild_id: Optional[int] = None) -> AuthResult:
        """Authenticate a user with username and password."""
        try:
            # Check if account is locked
            if await self._is_account_locked(username):
                return AuthResult(
                    status=AuthStatus.LOCKED,
                    message="Account is temporarily locked due to failed login attempts"
                )

            # Get user by username
            user = await self._get_user_by_username(username)
            if not user:
                await self._record_failed_attempt(username, ip_address, user_agent)
                return AuthResult(
                    status=AuthStatus.FAILED,
                    message="Invalid username or password"
                )

            # Verify password
            if not await self._verify_password(password, user['password_hash']):
                await self._record_failed_attempt(username, ip_address, user_agent)
                await self._increment_failed_attempts(user['user_id'])
                return AuthResult(
                    status=AuthStatus.FAILED,
                    message="Invalid username or password"
                )

            # Check if MFA is required
            if await self._is_mfa_required(user['user_id']):
                mfa_method = await self._get_primary_mfa_method(user['user_id'])
                return AuthResult(
                    status=AuthStatus.MFA_REQUIRED,
                    user_id=user['user_id'],
                    message="Multi-factor authentication required",
                    mfa_required=True,
                    mfa_method=mfa_method
                )

            # Generate session token
            session_token = await self._generate_session_token(user['user_id'])

            # Get user permissions and roles
            permissions, roles = await self._get_user_permissions(user['user_id'], guild_id)

            # Update last login
            await self._update_last_login(user['user_id'], ip_address)

            # Record successful login
            await self._record_successful_login(user['user_id'], ip_address, user_agent)

            # Reset failed attempts
            await self._reset_failed_attempts(user['user_id'])

            record_metric("auth_successful_logins", 1)

            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=user['user_id'],
                message="Authentication successful",
                session_token=session_token,
                expires_at=datetime.utcnow() + self.session_timeout,
                permissions=permissions,
                roles=roles
            )

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            record_metric("auth_errors", 1)
            return AuthResult(
                status=AuthStatus.FAILED,
                message="Authentication service error"
            )

    @time_operation("auth_verify_mfa")
    async def verify_mfa(self, user_id: int, mfa_code: str, mfa_method: MFAMethod,
                        ip_address: str, user_agent: str) -> AuthResult:
        """Verify multi-factor authentication code."""
        try:
            # Get MFA device
            device = await self._get_mfa_device(user_id, mfa_method)
            if not device or not device.is_active:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    message="Invalid MFA device"
                )

            # Verify MFA code based on method
            if mfa_method == MFAMethod.TOTP:
                if not self._verify_totp_code(mfa_code, device.device_id):
                    await self._record_failed_mfa_attempt(user_id, ip_address, user_agent)
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        message="Invalid MFA code"
                    )
            elif mfa_method == MFAMethod.SMS:
                if not await self._verify_sms_code(user_id, mfa_code):
                    await self._record_failed_mfa_attempt(user_id, ip_address, user_agent)
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        message="Invalid SMS code"
                    )
            elif mfa_method == MFAMethod.EMAIL:
                if not await self._verify_email_code(user_id, mfa_code):
                    await self._record_failed_mfa_attempt(user_id, ip_address, user_agent)
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        message="Invalid email code"
                    )
            else:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    message="Unsupported MFA method"
                )

            # Update device last used
            await self._update_mfa_device_usage(device.id)

            # Generate session token
            session_token = await self._generate_session_token(user_id)

            # Get user permissions and roles
            permissions, roles = await self._get_user_permissions(user_id)

            record_metric("auth_mfa_successful", 1)

            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=user_id,
                message="MFA verification successful",
                session_token=session_token,
                expires_at=datetime.utcnow() + self.session_timeout,
                permissions=permissions,
                roles=roles
            )

        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            record_metric("auth_mfa_errors", 1)
            return AuthResult(
                status=AuthStatus.FAILED,
                message="MFA verification error"
            )

    @time_operation("auth_verify_session")
    async def verify_session(self, session_token: str, guild_id: Optional[int] = None) -> AuthResult:
        """Verify session token and return user information."""
        try:
            # Get session from cache
            session_data = await cache_get(f"session:{session_token}")
            if not session_data:
                return AuthResult(
                    status=AuthStatus.EXPIRED,
                    message="Session expired or invalid"
                )

            session = json.loads(session_data)
            user_id = session.get('user_id')
            expires_at = datetime.fromisoformat(session.get('expires_at'))

            # Check if session is expired
            if datetime.utcnow() > expires_at:
                await cache_get(f"session:{session_token}", delete=True)
                return AuthResult(
                    status=AuthStatus.EXPIRED,
                    message="Session expired"
                )

            # Get user permissions and roles
            permissions, roles = await self._get_user_permissions(user_id, guild_id)

            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_id=user_id,
                message="Session valid",
                session_token=session_token,
                expires_at=expires_at,
                permissions=permissions,
                roles=roles
            )

        except Exception as e:
            logger.error(f"Session verification error: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                message="Session verification error"
            )

    @time_operation("auth_logout")
    async def logout(self, session_token: str) -> bool:
        """Logout user by invalidating session token."""
        try:
            # Remove session from cache
            await cache_get(f"session:{session_token}", delete=True)
            record_metric("auth_logouts", 1)
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    @time_operation("auth_setup_mfa")
    async def setup_mfa(self, user_id: int, mfa_method: MFAMethod, device_name: str) -> Dict[str, Any]:
        """Setup multi-factor authentication for a user."""
        try:
            if mfa_method == MFAMethod.TOTP:
                return await self._setup_totp(user_id, device_name)
            elif mfa_method == MFAMethod.SMS:
                return await self._setup_sms(user_id, device_name)
            elif mfa_method == MFAMethod.EMAIL:
                return await self._setup_email(user_id, device_name)
            else:
                raise ValueError(f"Unsupported MFA method: {mfa_method}")

        except Exception as e:
            logger.error(f"MFA setup error: {e}")
            raise

    @time_operation("auth_remove_mfa")
    async def remove_mfa(self, user_id: int, device_id: int) -> bool:
        """Remove MFA device for a user."""
        try:
            query = """
                UPDATE mfa_devices
                SET is_active = FALSE
                WHERE id = %s AND user_id = %s
            """
            await self.db_manager.execute(query, (device_id, user_id))
            return True
        except Exception as e:
            logger.error(f"Remove MFA error: {e}")
            return False

    @time_operation("auth_get_user_roles")
    async def get_user_roles(self, user_id: int, guild_id: Optional[int] = None) -> List[Role]:
        """Get all roles assigned to a user."""
        try:
            query = """
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s AND ur.is_active = TRUE
                AND (ur.guild_id = %s OR ur.guild_id IS NULL)
                AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
            """
            rows = await self.db_manager.fetch_all(query, (user_id, guild_id))

            roles = []
            for row in rows:
                roles.append(Role(
                    id=row['id'],
                    role_name=row['role_name'],
                    display_name=row['display_name'],
                    description=row['description'],
                    permissions=json.loads(row['permissions']),
                    is_system_role=row['is_system_role'],
                    is_active=row['is_active']
                ))

            return roles
        except Exception as e:
            logger.error(f"Get user roles error: {e}")
            return []

    @time_operation("auth_assign_role")
    async def assign_role(self, user_id: int, role_name: str, assigned_by: int,
                         guild_id: Optional[int] = None, expires_at: Optional[datetime] = None) -> bool:
        """Assign a role to a user."""
        try:
            # Get role ID
            role_query = "SELECT id FROM roles WHERE role_name = %s AND is_active = TRUE"
            role_row = await self.db_manager.fetch_one(role_query, (role_name,))
            if not role_row:
                return False

            # Check if role is already assigned
            existing_query = """
                SELECT id FROM user_roles
                WHERE user_id = %s AND role_id = %s AND guild_id = %s AND is_active = TRUE
            """
            existing = await self.db_manager.fetch_one(existing_query, (user_id, role_row['id'], guild_id))
            if existing:
                return True  # Role already assigned

            # Assign role
            assign_query = """
                INSERT INTO user_roles (user_id, role_id, guild_id, assigned_by, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            await self.db_manager.execute(assign_query, (user_id, role_row['id'], guild_id, assigned_by, expires_at))

            # Log role assignment
            await self._log_role_assignment(user_id, role_name, assigned_by, guild_id)

            return True
        except Exception as e:
            logger.error(f"Assign role error: {e}")
            return False

    @time_operation("auth_revoke_role")
    async def revoke_role(self, user_id: int, role_name: str, revoked_by: int,
                         guild_id: Optional[int] = None) -> bool:
        """Revoke a role from a user."""
        try:
            # Get role ID
            role_query = "SELECT id FROM roles WHERE role_name = %s AND is_active = TRUE"
            role_row = await self.db_manager.fetch_one(role_query, (role_name,))
            if not role_row:
                return False

            # Revoke role
            revoke_query = """
                UPDATE user_roles
                SET is_active = FALSE
                WHERE user_id = %s AND role_id = %s AND guild_id = %s
            """
            await self.db_manager.execute(revoke_query, (user_id, role_row['id'], guild_id))

            # Log role revocation
            await self._log_role_revocation(user_id, role_name, revoked_by, guild_id)

            return True
        except Exception as e:
            logger.error(f"Revoke role error: {e}")
            return False

    @time_operation("auth_check_permission")
    async def check_permission(self, user_id: int, permission: str, guild_id: Optional[int] = None) -> bool:
        """Check if user has a specific permission."""
        try:
            permissions, _ = await self._get_user_permissions(user_id, guild_id)
            return permission in permissions or "*" in permissions
        except Exception as e:
            logger.error(f"Check permission error: {e}")
            return False

    # Private helper methods

    def _get_or_generate_secret_key(self) -> bytes:
        """Get or generate secret key for encryption."""
        # In production, this should be stored securely
        return Fernet.generate_key()

    async def _initialize_default_roles(self):
        """Initialize default system roles if they don't exist."""
        default_roles = [
            ("admin", "Administrator", "Full system administrator", ["*"]),
            ("moderator", "Moderator", "Guild moderator", ["guild.manage", "user.manage", "bet.view", "bet.moderate"]),
            ("user", "User", "Standard user", ["bet.create", "bet.view", "profile.manage"]),
            ("premium", "Premium User", "Premium user", ["bet.create", "bet.view", "profile.manage", "analytics.view", "ml.predictions"]),
            ("enterprise", "Enterprise User", "Enterprise user", ["bet.create", "bet.view", "profile.manage", "analytics.view", "ml.predictions", "enterprise.features", "compliance.view"])
        ]

        for role_name, display_name, description, permissions in default_roles:
            await self._create_role_if_not_exists(role_name, display_name, description, permissions)

    async def _create_role_if_not_exists(self, role_name: str, display_name: str,
                                       description: str, permissions: List[str]):
        """Create a role if it doesn't exist."""
        query = "SELECT id FROM roles WHERE role_name = %s"
        existing = await self.db_manager.fetch_one(query, (role_name,))

        if not existing:
            insert_query = """
                INSERT INTO roles (role_name, display_name, description, permissions, is_system_role)
                VALUES (%s, %s, %s, %s, TRUE)
            """
            await self.db_manager.execute(insert_query, (role_name, display_name, description, json.dumps(permissions)))

    async def _get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        query = "SELECT user_id, username, password_hash FROM users WHERE username = %s"
        return await self.db_manager.fetch_one(query, (username,))

    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    async def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts."""
        query = """
            SELECT account_locked, account_locked_until
            FROM user_settings us
            JOIN users u ON us.user_id = u.user_id
            WHERE u.username = %s
        """
        result = await self.db_manager.fetch_one(query, (username,))

        if result and result['account_locked']:
            if result['account_locked_until'] and datetime.utcnow() < result['account_locked_until']:
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
            WHERE u.username = %s
        """
        await self.db_manager.execute(query, (username,))

    async def _record_failed_attempt(self, username: str, ip_address: str, user_agent: str):
        """Record a failed login attempt."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            SELECT 'failed_login', u.user_id, %s, %s, %s, 0.5
            FROM users u WHERE u.username = %s
        """
        event_data = json.dumps({"username": username, "timestamp": datetime.utcnow().isoformat()})
        await self.db_manager.execute(query, (ip_address, user_agent, event_data, username))

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
            WHERE user_id = %s
        """
        await self.db_manager.execute(query, (self.max_failed_attempts, self.max_failed_attempts,
                                             int(self.lockout_duration.total_seconds() / 60), user_id))

    async def _reset_failed_attempts(self, user_id: int):
        """Reset failed login attempts for a user."""
        query = """
            UPDATE user_settings
            SET failed_login_attempts = 0, account_locked = FALSE, account_locked_until = NULL
            WHERE user_id = %s
        """
        await self.db_manager.execute(query, (user_id,))

    async def _is_mfa_required(self, user_id: int) -> bool:
        """Check if MFA is required for a user."""
        query = "SELECT mfa_enabled FROM user_settings WHERE user_id = %s"
        result = await self.db_manager.fetch_one(query, (user_id,))
        return result and result['mfa_enabled']

    async def _get_primary_mfa_method(self, user_id: int) -> Optional[MFAMethod]:
        """Get the primary MFA method for a user."""
        query = """
            SELECT device_type FROM mfa_devices
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at ASC LIMIT 1
        """
        result = await self.db_manager.fetch_one(query, (user_id,))
        return MFAMethod(result['device_type']) if result else None

    async def _generate_session_token(self, user_id: int) -> str:
        """Generate a new session token."""
        token = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + self.session_timeout).isoformat()
        }

        # Store session in cache
        await cache_set(f"session:{token}", json.dumps(session_data),
                       expire=int(self.session_timeout.total_seconds()))

        return token

    async def _get_user_permissions(self, user_id: int, guild_id: Optional[int] = None) -> Tuple[List[str], List[str]]:
        """Get user permissions and roles."""
        query = """
            SELECT DISTINCT r.role_name, r.permissions
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s AND ur.is_active = TRUE AND r.is_active = TRUE
            AND (ur.guild_id = %s OR ur.guild_id IS NULL)
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        """
        rows = await self.db_manager.fetch_all(query, (user_id, guild_id))

        permissions = set()
        roles = []

        for row in rows:
            roles.append(row['role_name'])
            perms = json.loads(row['permissions'])
            if isinstance(perms, list):
                permissions.update(perms)

        return list(permissions), roles

    async def _update_last_login(self, user_id: int, ip_address: str):
        """Update user's last login information."""
        query = """
            UPDATE user_settings
            SET last_login_ip = %s, last_login_time = NOW()
            WHERE user_id = %s
        """
        await self.db_manager.execute(query, (ip_address, user_id))

    async def _record_successful_login(self, user_id: int, ip_address: str, user_agent: str):
        """Record a successful login."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            VALUES ('successful_login', %s, %s, %s, %s, 0.0)
        """
        event_data = json.dumps({"timestamp": datetime.utcnow().isoformat()})
        await self.db_manager.execute(query, (user_id, ip_address, user_agent, event_data))

    async def _get_mfa_device(self, user_id: int, mfa_method: MFAMethod) -> Optional[MFADevice]:
        """Get MFA device for a user."""
        query = """
            SELECT * FROM mfa_devices
            WHERE user_id = %s AND device_type = %s AND is_active = TRUE
        """
        result = await self.db_manager.fetch_one(query, (user_id, mfa_method.value))

        if result:
            return MFADevice(
                id=result['id'],
                user_id=result['user_id'],
                device_type=MFAMethod(result['device_type']),
                device_id=result['device_id'],
                device_name=result['device_name'],
                is_active=result['is_active'],
                created_at=result['created_at'],
                last_used=result['last_used'],
                expires_at=result['expires_at']
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
        query = "UPDATE mfa_devices SET last_used = NOW() WHERE id = %s"
        await self.db_manager.execute(query, (device_id,))

    async def _record_failed_mfa_attempt(self, user_id: int, ip_address: str, user_agent: str):
        """Record a failed MFA attempt."""
        query = """
            INSERT INTO security_events (event_type, user_id, ip_address, user_agent, event_data, risk_score)
            VALUES ('failed_mfa', %s, %s, %s, %s, 0.7)
        """
        event_data = json.dumps({"timestamp": datetime.utcnow().isoformat()})
        await self.db_manager.execute(query, (user_id, ip_address, user_agent, event_data))

    async def _setup_totp(self, user_id: int, device_name: str) -> Dict[str, Any]:
        """Setup TOTP MFA."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code URL
        qr_url = totp.provisioning_uri(
            name=f"{user_id}@{self.totp_issuer}",
            issuer_name=self.totp_issuer
        )

        # Store device
        query = """
            INSERT INTO mfa_devices (user_id, device_type, device_id, device_name)
            VALUES (%s, %s, %s, %s)
        """
        await self.db_manager.execute(query, (user_id, MFAMethod.TOTP.value, secret, device_name))

        # Enable MFA for user
        await self.db_manager.execute(
            "UPDATE user_settings SET mfa_enabled = TRUE, mfa_method = %s WHERE user_id = %s",
            (MFAMethod.TOTP.value, user_id)
        )

        return {
            "secret": secret,
            "qr_url": qr_url,
            "backup_codes": self._generate_backup_codes()
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

    async def _log_role_assignment(self, user_id: int, role_name: str, assigned_by: int, guild_id: Optional[int]):
        """Log role assignment for audit."""
        query = """
            INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, action_data, ip_address)
            VALUES (%s, 'role_assigned', 'role', %s, %s, 'system')
        """
        action_data = json.dumps({
            "role_name": role_name,
            "assigned_by": assigned_by,
            "guild_id": guild_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.db_manager.execute(query, (user_id, role_name, action_data))

    async def _log_role_revocation(self, user_id: int, role_name: str, revoked_by: int, guild_id: Optional[int]):
        """Log role revocation for audit."""
        query = """
            INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, action_data, ip_address)
            VALUES (%s, 'role_revoked', 'role', %s, %s, 'system')
        """
        action_data = json.dumps({
            "role_name": role_name,
            "revoked_by": revoked_by,
            "guild_id": guild_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.db_manager.execute(query, (user_id, role_name, action_data))
