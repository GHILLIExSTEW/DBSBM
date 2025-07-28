"""
Test suite for Data Protection Service.
Tests all data protection and privacy features including encryption, anonymization,
pseudonymization, retention policies, and privacy impact assessments.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.data_protection_service import (
    AnonymizationType,
    AnonymizedData,
    DataClassification,
    DataProtectionService,
    EncryptionKey,
    EncryptionType,
    PrivacyImpactAssessment,
    PrivacyImpactLevel,
    PseudonymizedData,
)
from bot.services.data_protection_service import RetentionPolicy
from bot.services.data_protection_service import RetentionPolicy as RetentionPolicyEnum


class TestDataProtectionService:
    """Test cases for Data Protection Service."""

    @pytest.fixture
    async def data_protection_service(self):
        """Create a data protection service instance for testing."""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.execute = AsyncMock()
        db_manager.fetch_one = AsyncMock()
        db_manager.fetch_all = AsyncMock()

        service = DataProtectionService(db_manager)
        return service

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111",
            "ip_address": "192.168.1.1",
            "zip_code": "12345",
            "normal_text": "This is normal text",
        }

    @pytest.mark.asyncio
    async def test_service_initialization(self, data_protection_service):
        """Test service initialization."""
        assert data_protection_service.db_manager is not None
        assert data_protection_service.cache_manager is not None
        assert data_protection_service.master_key is not None
        assert len(data_protection_service.encryption_keys) == 0
        assert data_protection_service.key_rotation_interval == 90
        assert data_protection_service.anonymization_salt is not None
        assert data_protection_service.pseudonymization_salt is not None

    @pytest.mark.asyncio
    async def test_service_start_stop(self, data_protection_service):
        """Test service start and stop functionality."""
        # Test start
        await data_protection_service.start()
        assert data_protection_service.is_running is True
        assert data_protection_service.key_rotation_task is not None
        assert data_protection_service.retention_cleanup_task is not None

        # Test stop
        await data_protection_service.stop()
        assert data_protection_service.is_running is False

    @pytest.mark.asyncio
    async def test_data_encryption_symmetric(
        self, data_protection_service, sample_data
    ):
        """Test symmetric data encryption."""
        # Mock encryption key
        mock_key = EncryptionKey(
            key_id="test-key-1",
            key_type=EncryptionType.SYMMETRIC,
            key_data=b"test-key-data",
            created_at=datetime.utcnow(),
        )

        with patch.object(
            data_protection_service, "_get_encryption_key", return_value=mock_key
        ):
            with patch.object(data_protection_service, "_store_encryption_metadata"):
                encrypted = await data_protection_service.encrypt_data(
                    sample_data["email"], DataClassification.CONFIDENTIAL
                )

                assert encrypted is not None
                assert isinstance(encrypted, str)
                assert encrypted != sample_data["email"]

    @pytest.mark.asyncio
    async def test_data_encryption_asymmetric(
        self, data_protection_service, sample_data
    ):
        """Test asymmetric data encryption."""
        # Mock asymmetric encryption key
        mock_key = EncryptionKey(
            key_id="test-key-2",
            key_type=EncryptionType.ASYMMETRIC,
            key_data={
                "private_key": b"test-private-key",
                "public_key": b"test-public-key",
            },
            created_at=datetime.utcnow(),
        )

        with patch.object(
            data_protection_service, "_get_encryption_key", return_value=mock_key
        ):
            with patch.object(data_protection_service, "_store_encryption_metadata"):
                encrypted = await data_protection_service.encrypt_data(
                    sample_data["ssn"], DataClassification.HIGHLY_RESTRICTED
                )

                assert encrypted is not None
                assert isinstance(encrypted, str)
                assert encrypted != sample_data["ssn"]

    @pytest.mark.asyncio
    async def test_data_decryption_symmetric(
        self, data_protection_service, sample_data
    ):
        """Test symmetric data decryption."""
        # Mock encryption key and metadata
        mock_key = EncryptionKey(
            key_id="test-key-1",
            key_type=EncryptionType.SYMMETRIC,
            key_data=b"test-key-data",
            created_at=datetime.utcnow(),
        )

        mock_metadata = {"key_id": "test-key-1", "classification": "confidential"}

        with patch.object(
            data_protection_service,
            "_get_encryption_metadata",
            return_value=mock_metadata,
        ):
            with patch.object(
                data_protection_service,
                "_get_encryption_key_by_id",
                return_value=mock_key,
            ):
                decrypted = await data_protection_service.decrypt_data(
                    "encrypted-data", DataClassification.CONFIDENTIAL
                )

                assert decrypted is not None
                assert isinstance(decrypted, str)

    @pytest.mark.asyncio
    async def test_data_anonymization_hashing(
        self, data_protection_service, sample_data
    ):
        """Test data anonymization using hashing."""
        with patch.object(data_protection_service, "_store_anonymized_data"):
            anonymized = await data_protection_service.anonymize_data(
                sample_data["email"], "email", AnonymizationType.HASHING
            )

            assert anonymized is not None
            assert isinstance(anonymized, AnonymizedData)
            assert anonymized.anonymized_id is not None
            assert anonymized.anonymized_value != sample_data["email"]
            assert anonymized.anonymization_type == AnonymizationType.HASHING
            assert anonymized.data_type == "email"

    @pytest.mark.asyncio
    async def test_data_anonymization_masking(
        self, data_protection_service, sample_data
    ):
        """Test data anonymization using masking."""
        with patch.object(data_protection_service, "_store_anonymized_data"):
            anonymized = await data_protection_service.anonymize_data(
                sample_data["phone"], "phone", AnonymizationType.MASKING
            )

            assert anonymized is not None
            assert isinstance(anonymized, AnonymizedData)
            assert anonymized.anonymized_value != sample_data["phone"]
            assert anonymized.anonymization_type == AnonymizationType.MASKING

    @pytest.mark.asyncio
    async def test_data_anonymization_generalization(
        self, data_protection_service, sample_data
    ):
        """Test data anonymization using generalization."""
        with patch.object(data_protection_service, "_store_anonymized_data"):
            anonymized = await data_protection_service.anonymize_data(
                sample_data["email"], "email", AnonymizationType.GENERALIZATION
            )

            assert anonymized is not None
            assert isinstance(anonymized, AnonymizedData)
            assert anonymized.anonymized_value != sample_data["email"]
            assert anonymized.anonymization_type == AnonymizationType.GENERALIZATION

    @pytest.mark.asyncio
    async def test_data_pseudonymization(self, data_protection_service, sample_data):
        """Test data pseudonymization."""
        with patch.object(data_protection_service, "_store_pseudonymized_data"):
            pseudonymized = await data_protection_service.pseudonymize_data(
                sample_data["email"], "email"
            )

            assert pseudonymized is not None
            assert isinstance(pseudonymized, PseudonymizedData)
            assert pseudonymized.pseudonym_id is not None
            assert pseudonymized.pseudonym_value != sample_data["email"]
            assert pseudonymized.reversible is True
            assert pseudonymized.data_type == "email"

    @pytest.mark.asyncio
    async def test_create_retention_policy(self, data_protection_service):
        """Test retention policy creation."""
        with patch.object(data_protection_service, "_store_retention_policy"):
            policy = await data_protection_service.create_retention_policy(
                data_type="user_data",
                classification=DataClassification.CONFIDENTIAL,
                retention_period=365,
                retention_type=RetentionPolicyEnum.MEDIUM_TERM,
                auto_delete=True,
                archive_before_delete=False,
            )

            assert policy is not None
            assert isinstance(policy, RetentionPolicy)
            assert policy.policy_id is not None
            assert policy.data_type == "user_data"
            assert policy.classification == DataClassification.CONFIDENTIAL
            assert policy.retention_period == 365
            assert policy.retention_type == RetentionPolicyEnum.MEDIUM_TERM
            assert policy.auto_delete is True
            assert policy.archive_before_delete is False

    @pytest.mark.asyncio
    async def test_delete_expired_data(self, data_protection_service):
        """Test deletion of expired data."""
        # Mock retention policies and expired data
        mock_policy = RetentionPolicy(
            policy_id="test-policy-1",
            data_type="user_data",
            classification=DataClassification.CONFIDENTIAL,
            retention_period=30,
            retention_type=RetentionPolicyEnum.SHORT_TERM,
            auto_delete=True,
            archive_before_delete=False,
        )

        mock_expired_data = [
            {
                "id": 1,
                "data_type": "user_data",
                "created_at": datetime.utcnow() - timedelta(days=31),
            },
            {
                "id": 2,
                "data_type": "user_data",
                "created_at": datetime.utcnow() - timedelta(days=32),
            },
        ]

        with patch.object(
            data_protection_service,
            "_get_retention_policies",
            return_value=[mock_policy],
        ):
            with patch.object(
                data_protection_service,
                "_get_expired_data",
                return_value=mock_expired_data,
            ):
                with patch.object(data_protection_service, "_delete_data_item"):
                    deleted_count = await data_protection_service.delete_expired_data(
                        "user_data"
                    )

                    assert deleted_count == 2

    @pytest.mark.asyncio
    async def test_create_privacy_impact_assessment(self, data_protection_service):
        """Test privacy impact assessment creation."""
        with patch.object(data_protection_service, "_store_privacy_assessment"):
            assessment = await data_protection_service.create_privacy_impact_assessment(
                data_type="user_profile",
                processing_purpose="user_analytics",
                data_subjects=["users", "customers"],
                data_categories=["personal_identifiers", "contact_info"],
                risk_factors=["large_scale", "automated_decision"],
            )

            assert assessment is not None
            assert isinstance(assessment, PrivacyImpactAssessment)
            assert assessment.assessment_id is not None
            assert assessment.data_type == "user_profile"
            assert assessment.processing_purpose == "user_analytics"
            assert assessment.data_subjects == ["users", "customers"]
            assert assessment.data_categories == [
                "personal_identifiers",
                "contact_info",
            ]
            assert assessment.risk_factors == ["large_scale", "automated_decision"]
            assert assessment.impact_level in [
                PrivacyImpactLevel.HIGH,
                PrivacyImpactLevel.CRITICAL,
            ]
            assert len(assessment.mitigation_measures) > 0

    @pytest.mark.asyncio
    async def test_data_classification(self, data_protection_service, sample_data):
        """Test data classification based on content patterns."""
        # Test highly restricted data
        classification = await data_protection_service.classify_data(sample_data["ssn"])
        assert classification == DataClassification.HIGHLY_RESTRICTED

        classification = await data_protection_service.classify_data(
            sample_data["credit_card"]
        )
        assert classification == DataClassification.HIGHLY_RESTRICTED

        # Test restricted data
        classification = await data_protection_service.classify_data(
            sample_data["zip_code"]
        )
        assert classification == DataClassification.RESTRICTED

        # Test confidential data
        classification = await data_protection_service.classify_data(
            sample_data["ip_address"]
        )
        assert classification == DataClassification.CONFIDENTIAL

        # Test normal data
        classification = await data_protection_service.classify_data(
            sample_data["normal_text"]
        )
        assert classification == DataClassification.INTERNAL

    @pytest.mark.asyncio
    async def test_encryption_key_rotation(self, data_protection_service):
        """Test encryption key rotation."""
        with patch.object(data_protection_service, "_update_key_metadata"):
            rotated_count = await data_protection_service.rotate_encryption_keys()

            assert rotated_count > 0
            assert len(data_protection_service.encryption_keys) > 0

    @pytest.mark.asyncio
    async def test_get_data_protection_report(self, data_protection_service):
        """Test data protection report generation."""
        with patch.object(
            data_protection_service, "_get_encryption_statistics", return_value={}
        ):
            with patch.object(
                data_protection_service,
                "_get_anonymization_statistics",
                return_value={},
            ):
                with patch.object(
                    data_protection_service,
                    "_get_retention_statistics",
                    return_value={},
                ):
                    with patch.object(
                        data_protection_service,
                        "_get_privacy_assessment_statistics",
                        return_value={},
                    ):
                        with patch.object(
                            data_protection_service,
                            "_get_compliance_status",
                            return_value={},
                        ):
                            with patch.object(
                                data_protection_service,
                                "_generate_data_protection_recommendations",
                                return_value=[],
                            ):
                                report = await data_protection_service.get_data_protection_report(
                                    days=30
                                )

                                assert report is not None
                                assert isinstance(report, dict)
                                assert "period" in report
                                assert "encryption" in report
                                assert "anonymization" in report
                                assert "retention" in report
                                assert "privacy" in report
                                assert "compliance_status" in report
                                assert "recommendations" in report

    @pytest.mark.asyncio
    async def test_encryption_key_management(self, data_protection_service):
        """Test encryption key management functionality."""
        # Test key generation
        key = await data_protection_service._generate_encryption_key(
            DataClassification.CONFIDENTIAL
        )
        assert key is not None
        assert isinstance(key, EncryptionKey)
        assert key.key_id is not None
        assert key.key_type in [EncryptionType.SYMMETRIC, EncryptionType.ASYMMETRIC]
        assert key.key_data is not None
        assert key.created_at is not None

    @pytest.mark.asyncio
    async def test_anonymization_methods(self, data_protection_service, sample_data):
        """Test different anonymization methods."""
        # Test hashing
        hashed = data_protection_service._hash_data(sample_data["email"], "test-salt")
        assert hashed != sample_data["email"]
        assert len(hashed) == 64  # SHA256 hash length

        # Test masking
        masked = data_protection_service._mask_data(sample_data["phone"])
        assert masked != sample_data["phone"]
        assert "*" in masked

        # Test generalization
        generalized = data_protection_service._generalize_data(
            sample_data["email"], "email"
        )
        assert generalized != sample_data["email"]
        assert "***" in generalized

        # Test perturbation
        perturbed = data_protection_service._perturb_data("12345")
        assert perturbed != "12345"
        assert perturbed.isdigit()

    @pytest.mark.asyncio
    async def test_pseudonym_generation(self, data_protection_service, sample_data):
        """Test pseudonym generation."""
        pseudonym = data_protection_service._generate_pseudonym(
            sample_data["email"], "test-salt"
        )
        assert pseudonym != sample_data["email"]
        assert len(pseudonym) == 16  # First 16 characters of hash

    @pytest.mark.asyncio
    async def test_privacy_impact_calculation(self, data_protection_service):
        """Test privacy impact level calculation."""
        # Test high impact
        high_risk_categories = ["personal_identifiers", "financial_data"]
        high_risk_factors = ["large_scale", "automated_decision"]

        impact_level = await data_protection_service._calculate_privacy_impact_level(
            high_risk_categories, high_risk_factors
        )
        assert impact_level in [PrivacyImpactLevel.HIGH, PrivacyImpactLevel.CRITICAL]

        # Test low impact
        low_risk_categories = ["public_data"]
        low_risk_factors = []

        impact_level = await data_protection_service._calculate_privacy_impact_level(
            low_risk_categories, low_risk_factors
        )
        assert impact_level == PrivacyImpactLevel.LOW

    @pytest.mark.asyncio
    async def test_mitigation_measures_generation(self, data_protection_service):
        """Test mitigation measures generation."""
        # Test high impact measures
        measures = await data_protection_service._generate_mitigation_measures(
            PrivacyImpactLevel.HIGH, ["personal_identifiers", "financial_data"]
        )
        assert len(measures) > 0
        assert "Implement strong encryption" in measures
        assert "Implement data anonymization" in measures
        assert "Comply with PCI DSS requirements" in measures

    @pytest.mark.asyncio
    async def test_error_handling_encryption(
        self, data_protection_service, sample_data
    ):
        """Test error handling in encryption operations."""
        with patch.object(
            data_protection_service,
            "_get_encryption_key",
            side_effect=Exception("Key error"),
        ):
            with pytest.raises(Exception):
                await data_protection_service.encrypt_data(sample_data["email"])

    @pytest.mark.asyncio
    async def test_error_handling_decryption(self, data_protection_service):
        """Test error handling in decryption operations."""
        with patch.object(
            data_protection_service, "_get_encryption_metadata", return_value=None
        ):
            with pytest.raises(ValueError, match="Encryption metadata not found"):
                await data_protection_service.decrypt_data("encrypted-data")

    @pytest.mark.asyncio
    async def test_error_handling_anonymization(
        self, data_protection_service, sample_data
    ):
        """Test error handling in anonymization operations."""
        with patch.object(
            data_protection_service,
            "_store_anonymized_data",
            side_effect=Exception("DB error"),
        ):
            with pytest.raises(Exception):
                await data_protection_service.anonymize_data(
                    sample_data["email"], "email"
                )

    @pytest.mark.asyncio
    async def test_background_tasks(self, data_protection_service):
        """Test background tasks functionality."""
        # Start service
        await data_protection_service.start()

        # Verify background tasks are running
        assert data_protection_service.key_rotation_task is not None
        assert data_protection_service.retention_cleanup_task is not None

        # Stop service
        await data_protection_service.stop()

        # Verify tasks are cancelled
        assert data_protection_service.is_running is False

    @pytest.mark.asyncio
    async def test_cache_integration(self, data_protection_service):
        """Test cache integration for encryption keys."""
        # Mock cache operations
        data_protection_service.cache_manager.enhanced_cache_get = AsyncMock(
            return_value=None
        )
        data_protection_service.cache_manager.enhanced_cache_set = AsyncMock()

        # Test key caching
        mock_key = EncryptionKey(
            key_id="test-key",
            key_type=EncryptionType.SYMMETRIC,
            key_data=b"test-data",
            created_at=datetime.utcnow(),
        )

        with patch.object(
            data_protection_service, "_get_encryption_key", return_value=mock_key
        ):
            key = await data_protection_service._get_encryption_key(
                DataClassification.CONFIDENTIAL
            )
            assert key is not None

    @pytest.mark.asyncio
    async def test_database_operations(self, data_protection_service):
        """Test database operations for data protection."""
        # Test encryption metadata storage
        await data_protection_service._store_encryption_metadata(
            "original-data", "encrypted-data", DataClassification.CONFIDENTIAL, "key-id"
        )
        data_protection_service.db_manager.execute.assert_called_once()

        # Test anonymized data storage
        anonymized_data = AnonymizedData(
            original_id="orig-1",
            anonymized_id="anon-1",
            data_type="email",
            anonymization_type=AnonymizationType.HASHING,
            original_hash="hash123",
            anonymized_value="anon-value",
            created_at=datetime.utcnow(),
        )

        await data_protection_service._store_anonymized_data(anonymized_data)
        data_protection_service.db_manager.execute.assert_called()

    @pytest.mark.asyncio
    async def test_comprehensive_data_protection_workflow(
        self, data_protection_service, sample_data
    ):
        """Test comprehensive data protection workflow."""
        # 1. Classify data
        classification = await data_protection_service.classify_data(sample_data["ssn"])
        assert classification == DataClassification.HIGHLY_RESTRICTED

        # 2. Encrypt data
        with patch.object(
            data_protection_service, "_get_encryption_key"
        ) as mock_get_key:
            mock_key = EncryptionKey(
                key_id="test-key",
                key_type=EncryptionType.ASYMMETRIC,
                key_data={"private_key": b"test", "public_key": b"test"},
                created_at=datetime.utcnow(),
            )
            mock_get_key.return_value = mock_key

            with patch.object(data_protection_service, "_store_encryption_metadata"):
                encrypted = await data_protection_service.encrypt_data(
                    sample_data["ssn"], classification
                )
                assert encrypted is not None

        # 3. Anonymize data
        with patch.object(data_protection_service, "_store_anonymized_data"):
            anonymized = await data_protection_service.anonymize_data(
                sample_data["email"], "email"
            )
            assert anonymized is not None

        # 4. Create retention policy
        with patch.object(data_protection_service, "_store_retention_policy"):
            policy = await data_protection_service.create_retention_policy(
                "user_data", classification, 365, RetentionPolicyEnum.MEDIUM_TERM
            )
            assert policy is not None

        # 5. Create privacy assessment
        with patch.object(data_protection_service, "_store_privacy_assessment"):
            assessment = await data_protection_service.create_privacy_impact_assessment(
                "user_data", "analytics", ["users"], ["personal_identifiers"]
            )
            assert assessment is not None

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, data_protection_service, sample_data):
        """Test performance monitoring integration."""
        # Mock performance monitoring
        with patch("bot.services.performance_monitor.record_metric") as mock_record:
            with patch.object(data_protection_service, "_get_encryption_key"):
                with patch.object(
                    data_protection_service, "_store_encryption_metadata"
                ):
                    await data_protection_service.encrypt_data(sample_data["email"])
                    mock_record.assert_called_with("data_encrypted", 1)

    def test_data_classification_patterns(self, data_protection_service):
        """Test data classification patterns."""
        patterns = data_protection_service.classification_patterns

        # Test highly restricted patterns
        assert len(patterns[DataClassification.HIGHLY_RESTRICTED]) > 0
        assert any(
            "SSN" in str(pattern)
            for pattern in patterns[DataClassification.HIGHLY_RESTRICTED]
        )
        assert any(
            "credit card" in str(pattern)
            for pattern in patterns[DataClassification.HIGHLY_RESTRICTED]
        )

        # Test restricted patterns
        assert len(patterns[DataClassification.RESTRICTED]) > 0
        assert any(
            "ZIP" in str(pattern) for pattern in patterns[DataClassification.RESTRICTED]
        )

        # Test confidential patterns
        assert len(patterns[DataClassification.CONFIDENTIAL]) > 0
        assert any(
            "IP" in str(pattern)
            for pattern in patterns[DataClassification.CONFIDENTIAL]
        )

    @pytest.mark.asyncio
    async def test_service_integration_with_cache(self, data_protection_service):
        """Test service integration with enhanced cache manager."""
        # Mock cache operations
        data_protection_service.cache_manager.enhanced_cache_get = AsyncMock(
            return_value=None
        )
        data_protection_service.cache_manager.enhanced_cache_set = AsyncMock()
        data_protection_service.cache_manager.clear_cache_by_pattern = AsyncMock()

        # Test cache integration
        assert data_protection_service.cache_manager is not None
        assert data_protection_service.cache_ttls is not None
        assert "encryption_keys" in data_protection_service.cache_ttls
        assert "anonymized_data" in data_protection_service.cache_ttls

    @pytest.mark.asyncio
    async def test_compliance_reporting(self, data_protection_service):
        """Test compliance reporting functionality."""
        compliance_status = await data_protection_service._get_compliance_status()

        assert compliance_status is not None
        assert isinstance(compliance_status, dict)
        assert "gdpr_compliant" in compliance_status
        assert "encryption_enabled" in compliance_status
        assert "retention_policies_active" in compliance_status
        assert "privacy_assessments_current" in compliance_status
        assert "data_minimization_practiced" in compliance_status

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, data_protection_service):
        """Test data protection recommendations generation."""
        recommendations = (
            await data_protection_service._generate_data_protection_recommendations()
        )

        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("encryption" in rec.lower() for rec in recommendations)
        assert any("audit" in rec.lower() for rec in recommendations)


if __name__ == "__main__":
    pytest.main([__file__])
