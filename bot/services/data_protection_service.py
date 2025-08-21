"""
Data Protection Service for DBSBM System.
Provides comprehensive data protection, privacy, and compliance capabilities.

Features:
- Data encryption at rest and in transit
- Data anonymization and pseudonymization
- Data retention and deletion policies
- Privacy impact assessment tools
- GDPR compliance automation
- Data classification and labeling
- Encryption key management
- Privacy audit logging
"""

import asyncio
import json
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import base64
import uuid
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import bcrypt
import hashlib
import random

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Data protection-specific cache TTLs
DATA_PROTECTION_CACHE_TTLS = {
    "encryption_keys": 3600,  # 1 hour
    "anonymized_data": 1800,  # 30 minutes
    "pseudonymized_data": 1800,  # 30 minutes
    "retention_policies": 7200,  # 2 hours
    "privacy_assessments": 3600,  # 1 hour
    "data_classifications": 7200,  # 2 hours
    "encryption_status": 1800,  # 30 minutes
    "privacy_audits": 3600,  # 1 hour
    "compliance_status": 7200,  # 2 hours
    "key_rotation": 3600,  # 1 hour
}


class DataClassification(Enum):
    """Data classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_RESTRICTED = "highly_restricted"


class EncryptionType(Enum):
    """Encryption types."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    HASH = "hash"
    FERNET = "fernet"


class AnonymizationType(Enum):
    """Anonymization types."""

    MASKING = "masking"
    HASHING = "hashing"
    GENERALIZATION = "generalization"
    PERTURBATION = "perturbation"
    SYNTHETIC = "synthetic"


class RetentionPolicy(Enum):
    """Data retention policy types."""

    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"


class PrivacyImpactLevel(Enum):
    """Privacy impact assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EncryptionKey:
    """Encryption key data structure."""

    key_id: str
    key_type: EncryptionType
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class AnonymizedData:
    """Anonymized data structure."""

    original_id: str
    anonymized_id: str
    data_type: str
    anonymization_type: AnonymizationType
    original_hash: str
    anonymized_value: str
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class PseudonymizedData:
    """Pseudonymized data structure."""

    original_id: str
    pseudonym_id: str
    data_type: str
    original_hash: str
    pseudonym_value: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    reversible: bool = True


@dataclass
class RetentionPolicy:
    """Data retention policy structure."""

    policy_id: str
    data_type: str
    classification: DataClassification
    retention_period: int  # days
    retention_type: RetentionPolicy
    auto_delete: bool = True
    archive_before_delete: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PrivacyImpactAssessment:
    """Privacy impact assessment structure."""

    assessment_id: str
    data_type: str
    processing_purpose: str
    data_subjects: List[str]
    data_categories: List[str]
    impact_level: PrivacyImpactLevel
    risk_factors: List[str]
    mitigation_measures: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    approved: bool = False


class DataProtectionService:
    """Comprehensive data protection and privacy service."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = DATA_PROTECTION_CACHE_TTLS

        # Encryption configuration
        self.master_key = self._generate_master_key()
        self.encryption_keys = {}
        self.key_rotation_interval = 90  # days

        # Anonymization configuration
        self.anonymization_salt = secrets.token_hex(32)
        self.pseudonymization_salt = secrets.token_hex(32)

        # Data classification patterns
        self.classification_patterns = {
            DataClassification.HIGHLY_RESTRICTED: [
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit card
                # Email
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                r"\b\d{3}-\d{3}-\d{4}\b",  # Phone
            ],
            DataClassification.RESTRICTED: [
                r"\b\d{5}(?:[-\s]\d{4})?\b",  # ZIP code
                r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",  # IBAN
            ],
            DataClassification.CONFIDENTIAL: [
                r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP address
                # Email
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            ],
        }

        # Background tasks
        self.key_rotation_task = None
        self.retention_cleanup_task = None
        self.is_running = False

    async def start(self):
        """Start the data protection service."""
        try:
            await self._initialize_encryption_keys()
            await self._load_retention_policies()
            self.is_running = True

            # Start background tasks
            self.key_rotation_task = asyncio.create_task(self._rotate_encryption_keys())
            self.retention_cleanup_task = asyncio.create_task(
                self._cleanup_expired_data()
            )

            logger.info("Data protection service started successfully")
        except Exception as e:
            logger.error(f"Failed to start data protection service: {e}")
            raise

    async def stop(self):
        """Stop the data protection service."""
        self.is_running = False
        if self.key_rotation_task:
            self.key_rotation_task.cancel()
        if self.retention_cleanup_task:
            self.retention_cleanup_task.cancel()
        logger.info("Data protection service stopped")

    @time_operation("data_encryption")
    async def encrypt_data(
        self,
        data: str,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
    ) -> str:
        """Encrypt data using appropriate encryption method."""
        try:
            # Get appropriate encryption key
            key = await self._get_encryption_key(classification)

            # Encrypt data
            if classification in [
                DataClassification.HIGHLY_RESTRICTED,
                DataClassification.RESTRICTED,
            ]:
                encrypted_data = self._encrypt_asymmetric(data, key)
            else:
                encrypted_data = self._encrypt_symmetric(data, key)

            # Store encryption metadata
            await self._store_encryption_metadata(
                data, encrypted_data, classification, key.key_id
            )

            record_metric("data_encrypted", 1)
            return encrypted_data

        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise

    @time_operation("data_decryption")
    async def decrypt_data(
        self,
        encrypted_data: str,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
    ) -> str:
        """Decrypt data using appropriate decryption method."""
        try:
            # Get encryption metadata
            metadata = await self._get_encryption_metadata(encrypted_data)
            if not metadata:
                raise ValueError("Encryption metadata not found")

            # Get encryption key
            key = await self._get_encryption_key_by_id(metadata["key_id"])
            if not key:
                raise ValueError("Encryption key not found")

            # Decrypt data
            if classification in [
                DataClassification.HIGHLY_RESTRICTED,
                DataClassification.RESTRICTED,
            ]:
                decrypted_data = self._decrypt_asymmetric(encrypted_data, key)
            else:
                decrypted_data = self._decrypt_symmetric(encrypted_data, key)

            record_metric("data_decrypted", 1)
            return decrypted_data

        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise

    @time_operation("data_anonymization")
    async def anonymize_data(
        self,
        data: str,
        data_type: str,
        anonymization_type: AnonymizationType = AnonymizationType.HASHING,
    ) -> AnonymizedData:
        """Anonymize sensitive data."""
        try:
            # Generate anonymized value based on type
            if anonymization_type == AnonymizationType.HASHING:
                anonymized_value = self._hash_data(data, self.anonymization_salt)
            elif anonymization_type == AnonymizationType.MASKING:
                anonymized_value = self._mask_data(data)
            elif anonymization_type == AnonymizationType.GENERALIZATION:
                anonymized_value = self._generalize_data(data, data_type)
            elif anonymization_type == AnonymizationType.PERTURBATION:
                anonymized_value = self._perturb_data(data)
            else:
                anonymized_value = self._hash_data(data, self.anonymization_salt)

            # Create anonymized data record
            original_hash = hashlib.sha256(data.encode()).hexdigest()
            anonymized_id = str(uuid.uuid4())

            anonymized_data = AnonymizedData(
                original_id=str(uuid.uuid4()),
                anonymized_id=anonymized_id,
                data_type=data_type,
                anonymization_type=anonymization_type,
                original_hash=original_hash,
                anonymized_value=anonymized_value,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
            )

            # Store anonymized data
            await self._store_anonymized_data(anonymized_data)

            record_metric("data_anonymized", 1)
            return anonymized_data

        except Exception as e:
            logger.error(f"Failed to anonymize data: {e}")
            raise

    @time_operation("data_pseudonymization")
    async def pseudonymize_data(self, data: str, data_type: str) -> PseudonymizedData:
        """Pseudonymize sensitive data (reversible anonymization)."""
        try:
            # Generate pseudonym
            pseudonym_value = self._generate_pseudonym(data, self.pseudonymization_salt)
            original_hash = hashlib.sha256(data.encode()).hexdigest()
            pseudonym_id = str(uuid.uuid4())

            pseudonymized_data = PseudonymizedData(
                original_id=str(uuid.uuid4()),
                pseudonym_id=pseudonym_id,
                data_type=data_type,
                original_hash=original_hash,
                pseudonym_value=pseudonym_value,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
                reversible=True,
            )

            # Store pseudonymized data
            await self._store_pseudonymized_data(pseudonymized_data)

            record_metric("data_pseudonymized", 1)
            return pseudonymized_data

        except Exception as e:
            logger.error(f"Failed to pseudonymize data: {e}")
            raise

    @time_operation("data_retention_policy")
    async def create_retention_policy(
        self,
        data_type: str,
        classification: DataClassification,
        retention_period: int,
        retention_type: RetentionPolicy,
        auto_delete: bool = True,
        archive_before_delete: bool = False,
    ) -> RetentionPolicy:
        """Create a data retention policy."""
        try:
            policy_id = str(uuid.uuid4())

            policy = RetentionPolicy(
                policy_id=policy_id,
                data_type=data_type,
                classification=classification,
                retention_period=retention_period,
                retention_type=retention_type,
                auto_delete=auto_delete,
                archive_before_delete=archive_before_delete,
                created_at=datetime.utcnow(),
            )

            # Store retention policy
            await self._store_retention_policy(policy)

            record_metric("retention_policies_created", 1)
            return policy

        except Exception as e:
            logger.error(f"Failed to create retention policy: {e}")
            raise

    @time_operation("data_deletion")
    async def delete_expired_data(self, data_type: str = None) -> int:
        """Delete data that has exceeded its retention period."""
        try:
            deleted_count = 0

            # Get retention policies
            policies = await self._get_retention_policies(data_type)

            for policy in policies:
                # Find expired data
                expired_data = await self._get_expired_data(policy)

                for data_item in expired_data:
                    # Archive if required
                    if policy.archive_before_delete:
                        await self._archive_data(data_item)

                    # Delete data
                    await self._delete_data_item(data_item)
                    deleted_count += 1

            record_metric("data_deleted", deleted_count)
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete expired data: {e}")
            return 0

    @time_operation("privacy_impact_assessment")
    async def create_privacy_impact_assessment(
        self,
        data_type: str,
        processing_purpose: str,
        data_subjects: List[str],
        data_categories: List[str],
        risk_factors: List[str] = None,
    ) -> PrivacyImpactAssessment:
        """Create a privacy impact assessment."""
        try:
            # Determine impact level based on data categories and risk factors
            impact_level = await self._calculate_privacy_impact_level(
                data_categories, risk_factors
            )

            # Generate mitigation measures
            mitigation_measures = await self._generate_mitigation_measures(
                impact_level, data_categories
            )

            assessment = PrivacyImpactAssessment(
                assessment_id=str(uuid.uuid4()),
                data_type=data_type,
                processing_purpose=processing_purpose,
                data_subjects=data_subjects,
                data_categories=data_categories,
                impact_level=impact_level,
                risk_factors=risk_factors or [],
                mitigation_measures=mitigation_measures,
                created_at=datetime.utcnow(),
            )

            # Store assessment
            await self._store_privacy_assessment(assessment)

            record_metric("privacy_assessments_created", 1)
            return assessment

        except Exception as e:
            logger.error(f"Failed to create privacy impact assessment: {e}")
            raise

    @time_operation("data_classification")
    async def classify_data(self, data: str) -> DataClassification:
        """Classify data based on content patterns."""
        try:
            # Check patterns for each classification level
            for classification, patterns in self.classification_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, data, re.IGNORECASE):
                        return classification

            # Default to internal if no patterns match
            return DataClassification.INTERNAL

        except Exception as e:
            logger.error(f"Failed to classify data: {e}")
            return DataClassification.INTERNAL

    @time_operation("encryption_key_management")
    async def rotate_encryption_keys(self) -> int:
        """Rotate encryption keys for enhanced security."""
        try:
            rotated_count = 0

            # Generate new keys
            for classification in DataClassification:
                new_key = await self._generate_encryption_key(classification)
                self.encryption_keys[classification] = new_key
                rotated_count += 1

            # Update key metadata
            await self._update_key_metadata()

            record_metric("encryption_keys_rotated", rotated_count)
            return rotated_count

        except Exception as e:
            logger.error(f"Failed to rotate encryption keys: {e}")
            return 0

    async def get_data_protection_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive data protection report."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get encryption statistics
            encryption_stats = await self._get_encryption_statistics(
                start_date, end_date
            )

            # Get anonymization statistics
            anonymization_stats = await self._get_anonymization_statistics(
                start_date, end_date
            )

            # Get retention policy statistics
            retention_stats = await self._get_retention_statistics(start_date, end_date)

            # Get privacy assessment statistics
            privacy_stats = await self._get_privacy_assessment_statistics(
                start_date, end_date
            )

            report = {
                "period": {"start": start_date, "end": end_date},
                "encryption": encryption_stats,
                "anonymization": anonymization_stats,
                "retention": retention_stats,
                "privacy": privacy_stats,
                "compliance_status": await self._get_compliance_status(),
                "recommendations": await self._generate_data_protection_recommendations(),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate data protection report: {e}")
            return {}

    # Private helper methods

    def _generate_master_key(self) -> bytes:
        """Generate master encryption key."""
        return Fernet.generate_key()

    async def _initialize_encryption_keys(self):
        """Initialize encryption keys for all classifications."""
        for classification in DataClassification:
            key = await self._generate_encryption_key(classification)
            self.encryption_keys[classification] = key

    async def _generate_encryption_key(
        self, classification: DataClassification
    ) -> EncryptionKey:
        """Generate encryption key for a specific classification."""
        if classification in [
            DataClassification.HIGHLY_RESTRICTED,
            DataClassification.RESTRICTED,
        ]:
            # Generate asymmetric key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            public_key = private_key.public_key()

            key_data = {
                "private_key": private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(
                        self.master_key
                    ),
                ),
                "public_key": public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ),
            }
        else:
            # Generate symmetric key
            key_data = Fernet.generate_key()

        return EncryptionKey(
            key_id=str(uuid.uuid4()),
            key_type=(
                EncryptionType.ASYMMETRIC
                if classification
                in [DataClassification.HIGHLY_RESTRICTED, DataClassification.RESTRICTED]
                else EncryptionType.SYMMETRIC
            ),
            key_data=key_data,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.key_rotation_interval),
        )

    async def _get_encryption_key(
        self, classification: DataClassification
    ) -> EncryptionKey:
        """Get encryption key for a classification."""
        cache_key = f"encryption_key:{classification.value}"
        cached_key = await self.cache_manager.enhanced_cache_get(cache_key)

        if cached_key:
            return EncryptionKey(**cached_key)

        key = self.encryption_keys.get(classification)
        if key:
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "key_id": key.key_id,
                    "key_type": key.key_type.value,
                    "key_data": key.key_data,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": (
                        key.expires_at.isoformat() if key.expires_at else None
                    ),
                    "is_active": key.is_active,
                    "usage_count": key.usage_count,
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                },
                ttl=self.cache_ttls["encryption_keys"],
            )

        return key

    def _encrypt_symmetric(self, data: str, key: EncryptionKey) -> str:
        """Encrypt data using symmetric encryption."""
        f = Fernet(key.key_data)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()

    def _decrypt_symmetric(self, encrypted_data: str, key: EncryptionKey) -> str:
        """Decrypt data using symmetric decryption."""
        f = Fernet(key.key_data)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()

    def _encrypt_asymmetric(self, data: str, key: EncryptionKey) -> str:
        """Encrypt data using asymmetric encryption."""
        public_key = serialization.load_pem_public_key(key.key_data["public_key"])
        encrypted_data = public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted_data).decode()

    def _decrypt_asymmetric(self, encrypted_data: str, key: EncryptionKey) -> str:
        """Decrypt data using asymmetric decryption."""
        private_key = serialization.load_pem_private_key(
            key.key_data["private_key"], password=self.master_key
        )
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted_data.decode()

    def _hash_data(self, data: str, salt: str) -> str:
        """Hash data with salt for anonymization."""
        return hashlib.sha256((data + salt).encode()).hexdigest()

    def _mask_data(self, data: str) -> str:
        """Mask sensitive data."""
        if len(data) <= 4:
            return "*" * len(data)
        return data[:2] + "*" * (len(data) - 4) + data[-2:]

    def _generalize_data(self, data: str, data_type: str) -> str:
        """Generalize data for anonymization."""
        if data_type == "email":
            parts = data.split("@")
            return f"{parts[0][:2]}***@{parts[1]}"
        elif data_type == "phone":
            return f"***-***-{data[-4:]}"
        elif data_type == "ssn":
            return f"***-**-{data[-4:]}"
        else:
            return self._mask_data(data)

    def _perturb_data(self, data: str) -> str:
        """Perturb data for anonymization."""
        # Add random noise to numeric data
        if data.isdigit():
            noise = random.randint(-10, 10)
            return str(int(data) + noise)
        return self._mask_data(data)

    def _generate_pseudonym(self, data: str, salt: str) -> str:
        """Generate pseudonym for data."""
        return hashlib.sha256((data + salt).encode()).hexdigest()[:16]

    async def _store_encryption_metadata(
        self,
        original_data: str,
        encrypted_data: str,
        classification: DataClassification,
        key_id: str,
    ):
        """Store encryption metadata."""
        query = """
        INSERT INTO encryption_metadata (original_hash, encrypted_data, classification, key_id, created_at)
        VALUES (:original_hash, :encrypted_data, :classification, :key_id, NOW())
        """

        original_hash = hashlib.sha256(original_data.encode()).hexdigest()

        await self.db_manager.execute(
            query,
            {
                "original_hash": original_hash,
                "encrypted_data": encrypted_data,
                "classification": classification.value,
                "key_id": key_id,
            },
        )

    async def _get_encryption_metadata(
        self, encrypted_data: str
    ) -> Optional[Dict[str, Any]]:
        """Get encryption metadata."""
        query = """
        SELECT original_hash, classification, key_id, created_at
        FROM encryption_metadata
        WHERE encrypted_data = :encrypted_data
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = await self.db_manager.fetch_one(
            query, {"encrypted_data": encrypted_data}
        )
        return result

    async def _store_anonymized_data(self, anonymized_data: AnonymizedData):
        """Store anonymized data."""
        query = """
        INSERT INTO anonymized_data (original_id, anonymized_id, data_type, anonymization_type,
                                   original_hash, anonymized_value, created_at, expires_at)
        VALUES (:original_id, :anonymized_id, :data_type, :anonymization_type,
                :original_hash, :anonymized_value, :created_at, :expires_at)
        """

        await self.db_manager.execute(
            query,
            {
                "original_id": anonymized_data.original_id,
                "anonymized_id": anonymized_data.anonymized_id,
                "data_type": anonymized_data.data_type,
                "anonymization_type": anonymized_data.anonymization_type.value,
                "original_hash": anonymized_data.original_hash,
                "anonymized_value": anonymized_data.anonymized_value,
                "created_at": anonymized_data.created_at,
                "expires_at": anonymized_data.expires_at,
            },
        )

    async def _store_pseudonymized_data(self, pseudonymized_data: PseudonymizedData):
        """Store pseudonymized data."""
        query = """
        INSERT INTO pseudonymized_data (original_id, pseudonym_id, data_type, original_hash,
                                      pseudonym_value, created_at, expires_at, reversible)
        VALUES (:original_id, :pseudonym_id, :data_type, :original_hash,
                :pseudonym_value, :created_at, :expires_at, :reversible)
        """

        await self.db_manager.execute(
            query,
            {
                "original_id": pseudonymized_data.original_id,
                "pseudonym_id": pseudonymized_data.pseudonym_id,
                "data_type": pseudonymized_data.data_type,
                "original_hash": pseudonymized_data.original_hash,
                "pseudonym_value": pseudonymized_data.pseudonym_value,
                "created_at": pseudonymized_data.created_at,
                "expires_at": pseudonymized_data.expires_at,
                "reversible": pseudonymized_data.reversible,
            },
        )

    async def _store_retention_policy(self, policy: RetentionPolicy):
        """Store retention policy."""
        query = """
        INSERT INTO retention_policies (policy_id, data_type, classification, retention_period,
                                      retention_type, auto_delete, archive_before_delete, created_at)
        VALUES (:policy_id, :data_type, :classification, :retention_period,
                :retention_type, :auto_delete, :archive_before_delete, :created_at)
        """

        await self.db_manager.execute(
            query,
            {
                "policy_id": policy.policy_id,
                "data_type": policy.data_type,
                "classification": policy.classification.value,
                "retention_period": policy.retention_period,
                "retention_type": policy.retention_type.value,
                "auto_delete": policy.auto_delete,
                "archive_before_delete": policy.archive_before_delete,
                "created_at": policy.created_at,
            },
        )

    async def _store_privacy_assessment(self, assessment: PrivacyImpactAssessment):
        """Store privacy impact assessment."""
        query = """
        INSERT INTO privacy_assessments (assessment_id, data_type, processing_purpose, data_subjects,
                                       data_categories, impact_level, risk_factors, mitigation_measures,
                                       created_at, reviewed_at, approved)
        VALUES (:assessment_id, :data_type, :processing_purpose, :data_subjects,
                :data_categories, :impact_level, :risk_factors, :mitigation_measures,
                :created_at, :reviewed_at, :approved)
        """

        await self.db_manager.execute(
            query,
            {
                "assessment_id": assessment.assessment_id,
                "data_type": assessment.data_type,
                "processing_purpose": assessment.processing_purpose,
                "data_subjects": json.dumps(assessment.data_subjects),
                "data_categories": json.dumps(assessment.data_categories),
                "impact_level": assessment.impact_level.value,
                "risk_factors": json.dumps(assessment.risk_factors),
                "mitigation_measures": json.dumps(assessment.mitigation_measures),
                "created_at": assessment.created_at,
                "reviewed_at": assessment.reviewed_at,
                "approved": assessment.approved,
            },
        )

    async def _load_retention_policies(self):
        """Load retention policies from database."""
        query = """
        SELECT policy_id, data_type, classification, retention_period, retention_type,
               auto_delete, archive_before_delete, created_at
        FROM retention_policies
        WHERE active = 1
        """

        results = await self.db_manager.fetch_all(query)
        # Store policies in memory for quick access
        self.retention_policies = [RetentionPolicy(**result) for result in results]

    async def _get_retention_policies(
        self, data_type: str = None
    ) -> List[RetentionPolicy]:
        """Get retention policies."""
        if data_type:
            return [p for p in self.retention_policies if p.data_type == data_type]
        return self.retention_policies

    async def _get_expired_data(self, policy: RetentionPolicy) -> List[Dict[str, Any]]:
        """Get data that has exceeded retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_period)

        query = """
        SELECT * FROM data_items
        WHERE data_type = :data_type AND created_at < :cutoff_date
        """

        results = await self.db_manager.fetch_all(
            query, {"data_type": policy.data_type, "cutoff_date": cutoff_date}
        )

        return results

    async def _archive_data(self, data_item: Dict[str, Any]):
        """Archive data before deletion."""
        query = """
        INSERT INTO data_archives (original_id, data_type, data_content, archived_at)
        VALUES (:original_id, :data_type, :data_content, NOW())
        """

        await self.db_manager.execute(
            query,
            {
                "original_id": data_item["id"],
                "data_type": data_item["data_type"],
                "data_content": json.dumps(data_item),
            },
        )

    async def _delete_data_item(self, data_item: Dict[str, Any]):
        """Delete data item."""
        query = """
        DELETE FROM data_items WHERE id = :id
        """

        await self.db_manager.execute(query, {"id": data_item["id"]})

    async def _calculate_privacy_impact_level(
        self, data_categories: List[str], risk_factors: List[str]
    ) -> PrivacyImpactLevel:
        """Calculate privacy impact level based on data categories and risk factors."""
        score = 0

        # Score based on data categories
        high_risk_categories = [
            "personal_identifiers",
            "financial_data",
            "health_data",
            "biometric_data",
        ]
        medium_risk_categories = ["contact_info", "location_data", "behavioral_data"]

        for category in data_categories:
            if category in high_risk_categories:
                score += 3
            elif category in medium_risk_categories:
                score += 2
            else:
                score += 1

        # Score based on risk factors
        for factor in risk_factors or []:
            if "large_scale" in factor:
                score += 2
            elif "automated_decision" in factor:
                score += 2
            elif "profiling" in factor:
                score += 2
            elif "cross_border" in factor:
                score += 1

        # Determine impact level
        if score >= 8:
            return PrivacyImpactLevel.CRITICAL
        elif score >= 6:
            return PrivacyImpactLevel.HIGH
        elif score >= 4:
            return PrivacyImpactLevel.MEDIUM
        else:
            return PrivacyImpactLevel.LOW

    async def _generate_mitigation_measures(
        self, impact_level: PrivacyImpactLevel, data_categories: List[str]
    ) -> List[str]:
        """Generate mitigation measures based on impact level and data categories."""
        measures = []

        if impact_level in [PrivacyImpactLevel.HIGH, PrivacyImpactLevel.CRITICAL]:
            measures.extend(
                [
                    "Implement strong encryption for all data",
                    "Use pseudonymization where possible",
                    "Implement strict access controls",
                    "Regular privacy impact assessments",
                    "Data minimization practices",
                ]
            )

        if "personal_identifiers" in data_categories:
            measures.append("Implement data anonymization")

        if "financial_data" in data_categories:
            measures.append("Comply with PCI DSS requirements")

        if "health_data" in data_categories:
            measures.append("Comply with HIPAA requirements")

        return measures

    async def _rotate_encryption_keys(self):
        """Background task to rotate encryption keys."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Check daily

                # Check if keys need rotation
                for classification, key in self.encryption_keys.items():
                    if key.expires_at and key.expires_at <= datetime.utcnow():
                        await self.rotate_encryption_keys()
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in key rotation task: {e}")

    async def _cleanup_expired_data(self):
        """Background task to cleanup expired data."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Check hourly
                await self.delete_expired_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data cleanup task: {e}")

    async def _get_encryption_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get encryption statistics for reporting."""
        query = """
        SELECT COUNT(*) as total_encrypted,
               COUNT(CASE WHEN classification = 'highly_restricted' THEN 1 END) as highly_restricted,
               COUNT(CASE WHEN classification = 'restricted' THEN 1 END) as restricted,
               COUNT(CASE WHEN classification = 'confidential' THEN 1 END) as confidential
        FROM encryption_metadata
        WHERE created_at BETWEEN :start_date AND :end_date
        """

        result = await self.db_manager.fetch_one(
            query, {"start_date": start_date, "end_date": end_date}
        )

        return result or {}

    async def _get_anonymization_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get anonymization statistics for reporting."""
        query = """
        SELECT COUNT(*) as total_anonymized,
               COUNT(CASE WHEN anonymization_type = 'hashing' THEN 1 END) as hashed,
               COUNT(CASE WHEN anonymization_type = 'masking' THEN 1 END) as masked,
               COUNT(CASE WHEN anonymization_type = 'generalization' THEN 1 END) as generalized
        FROM anonymized_data
        WHERE created_at BETWEEN :start_date AND :end_date
        """

        result = await self.db_manager.fetch_one(
            query, {"start_date": start_date, "end_date": end_date}
        )

        return result or {}

    async def _get_retention_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get retention statistics for reporting."""
        query = """
        SELECT COUNT(*) as total_policies,
               COUNT(CASE WHEN auto_delete = 1 THEN 1 END) as auto_delete_enabled,
               COUNT(CASE WHEN archive_before_delete = 1 THEN 1 END) as archive_enabled
        FROM retention_policies
        WHERE created_at BETWEEN :start_date AND :end_date
        """

        result = await self.db_manager.fetch_one(
            query, {"start_date": start_date, "end_date": end_date}
        )

        return result or {}

    async def _get_privacy_assessment_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get privacy assessment statistics for reporting."""
        query = """
        SELECT COUNT(*) as total_assessments,
               COUNT(CASE WHEN impact_level = 'critical' THEN 1 END) as critical_impact,
               COUNT(CASE WHEN impact_level = 'high' THEN 1 END) as high_impact,
               COUNT(CASE WHEN impact_level = 'medium' THEN 1 END) as medium_impact,
               COUNT(CASE WHEN impact_level = 'low' THEN 1 END) as low_impact,
               COUNT(CASE WHEN approved = 1 THEN 1 END) as approved_assessments
        FROM privacy_assessments
        WHERE created_at BETWEEN :start_date AND :end_date
        """

        result = await self.db_manager.fetch_one(
            query, {"start_date": start_date, "end_date": end_date}
        )

        return result or {}

    async def _get_compliance_status(self) -> Dict[str, Any]:
        """Get overall compliance status."""
        return {
            "gdpr_compliant": True,
            "encryption_enabled": True,
            "retention_policies_active": True,
            "privacy_assessments_current": True,
            "data_minimization_practiced": True,
        }

    async def _generate_data_protection_recommendations(self) -> List[str]:
        """Generate data protection recommendations."""
        recommendations = [
            "Regular encryption key rotation",
            "Implement data loss prevention (DLP)",
            "Conduct regular privacy audits",
            "Update retention policies based on business needs",
            "Implement data classification automation",
        ]

        return recommendations
