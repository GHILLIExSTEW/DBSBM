"""
Experimental Systems Integration Service

This service integrates all experimental systems including:
- Advanced AI Service
- Advanced Analytics Service
- System Integration Service
- Compliance Automation Service
- Data Protection Service
- Security Incident Response Service

Provides unified access and coordination between all experimental systems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from bot.services.advanced_ai_service import AdvancedAIService
from bot.services.advanced_analytics_service import AdvancedAnalyticsService
from bot.services.system_integration_service import SystemIntegrationService
from bot.services.compliance_automation_service import ComplianceAutomationService
from bot.services.data_protection_service import DataProtectionService
from bot.services.security_incident_response import SecurityIncidentResponseService
from bot.services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """Status of experimental systems."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class SystemHealth:
    """System health information."""

    system_name: str
    status: SystemStatus
    last_check: datetime
    error_count: int = 0
    performance_score: float = 0.0
    uptime: timedelta = timedelta(0)
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExperimentalSystemsIntegration:
    """Integration service for all experimental systems."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: EnhancedCacheManager
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager

        # Initialize all experimental services
        self.advanced_ai_service = AdvancedAIService(db_manager, cache_manager)
        self.advanced_analytics_service = AdvancedAnalyticsService(
            db_manager, cache_manager
        )
        self.system_integration_service = SystemIntegrationService(db_manager)
        self.compliance_automation_service = ComplianceAutomationService(
            db_manager, cache_manager
        )
        self.data_protection_service = DataProtectionService(db_manager, cache_manager)
        self.security_incident_response = SecurityIncidentResponseService(
            db_manager, cache_manager
        )

        # System health tracking
        self.system_health: Dict[str, SystemHealth] = {}
        self.is_running = False

        # Background tasks
        self.health_monitor_task = None
        self.performance_optimizer_task = None
        self.data_sync_task = None

        logger.info("Experimental Systems Integration initialized")

    async def start(self):
        """Start all experimental systems."""
        try:
            self.is_running = True

            # Start all services
            await self._start_all_services()

            # Start background tasks
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            self.performance_optimizer_task = asyncio.create_task(
                self._performance_optimizer_loop()
            )
            self.data_sync_task = asyncio.create_task(self._data_sync_loop())

            logger.info("All experimental systems started successfully")

        except Exception as e:
            logger.error(f"Failed to start experimental systems: {e}")
            raise

    async def stop(self):
        """Stop all experimental systems."""
        try:
            self.is_running = False

            # Cancel background tasks
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
            if self.performance_optimizer_task:
                self.performance_optimizer_task.cancel()
            if self.data_sync_task:
                self.data_sync_task.cancel()

            # Stop all services
            await self._stop_all_services()

            logger.info("All experimental systems stopped")

        except Exception as e:
            logger.error(f"Failed to stop experimental systems: {e}")
            raise

    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all experimental systems."""
        try:
            status = {
                "overall_status": (
                    "healthy"
                    if all(
                        h.status == SystemStatus.ACTIVE
                        for h in self.system_health.values()
                    )
                    else "degraded"
                ),
                "systems": {},
                "total_systems": len(self.system_health),
                "active_systems": len(
                    [
                        h
                        for h in self.system_health.values()
                        if h.status == SystemStatus.ACTIVE
                    ]
                ),
                "error_systems": len(
                    [
                        h
                        for h in self.system_health.values()
                        if h.status == SystemStatus.ERROR
                    ]
                ),
                "last_updated": datetime.now().isoformat(),
            }

            for system_name, health in self.system_health.items():
                status["systems"][system_name] = {
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "error_count": health.error_count,
                    "performance_score": health.performance_score,
                    "uptime": str(health.uptime),
                    "metadata": health.metadata,
                }

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    @time_operation("experimental_systems_ai_prediction")
    async def make_ai_prediction(
        self, model_type: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a prediction using the advanced AI system."""
        try:
            # Get the appropriate model type
            from bot.services.advanced_ai_service import ModelType

            model_type_enum = None
            for mt in ModelType:
                if mt.value == model_type:
                    model_type_enum = mt
                    break

            if not model_type_enum:
                raise ValueError(f"Unknown model type: {model_type}")

            # Find active model for this type
            active_model_id = self.advanced_ai_service.active_models.get(
                model_type_enum
            )
            if not active_model_id:
                raise ValueError(f"No active model found for type: {model_type}")

            # Make prediction
            prediction = await self.advanced_ai_service.predict(
                active_model_id, input_data
            )

            # Record analytics
            await self.advanced_analytics_service.record_metric(
                name="ai_predictions_made",
                metric_type="counter",
                value=1.0,
                unit="predictions",
            )

            return {
                "prediction_id": prediction.prediction_id,
                "model_id": prediction.model_id,
                "prediction": prediction.prediction,
                "confidence": prediction.confidence,
                "processing_time": prediction.processing_time,
                "timestamp": prediction.prediction_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to make AI prediction: {e}")
            raise

    @time_operation("experimental_systems_analytics_dashboard")
    async def create_analytics_dashboard(
        self, name: str, dashboard_type: str, widgets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create an analytics dashboard."""
        try:
            from bot.services.advanced_analytics_service import DashboardType

            dashboard_type_enum = None
            for dt in DashboardType:
                if dt.value == dashboard_type:
                    dashboard_type_enum = dt
                    break

            if not dashboard_type_enum:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")

            dashboard = await self.advanced_analytics_service.create_dashboard(
                name=name,
                dashboard_type=dashboard_type_enum,
                description=f"Dashboard for {name}",
                widgets=widgets,
            )

            return {
                "dashboard_id": dashboard.dashboard_id,
                "name": dashboard.name,
                "dashboard_type": dashboard.dashboard_type.value,
                "widgets_count": len(dashboard.widgets),
                "created_at": dashboard.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create analytics dashboard: {e}")
            raise

    @time_operation("experimental_systems_service_registration")
    async def register_service(
        self, service_type: str, host: str, port: int
    ) -> Dict[str, Any]:
        """Register a service with the system integration service."""
        try:
            from bot.services.system_integration_service import ServiceType

            service_type_enum = None
            for st in ServiceType:
                if st.value == service_type:
                    service_type_enum = st
                    break

            if not service_type_enum:
                raise ValueError(f"Unknown service type: {service_type}")

            instance_id = await self.system_integration_service.register_service(
                service_type=service_type_enum, host=host, port=port
            )

            return {
                "instance_id": instance_id,
                "service_type": service_type,
                "host": host,
                "port": port,
                "status": "registered",
            }

        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise

    @time_operation("experimental_systems_compliance_check")
    async def run_compliance_check(
        self, framework: str, check_type: str
    ) -> Dict[str, Any]:
        """Run a compliance check."""
        try:
            result = await self.compliance_automation_service.run_compliance_check(
                framework=framework, check_type=check_type
            )

            return {
                "check_id": result.get("check_id"),
                "framework": framework,
                "check_type": check_type,
                "status": result.get("status"),
                "findings": result.get("findings", []),
                "compliance_score": result.get("compliance_score", 0.0),
            }

        except Exception as e:
            logger.error(f"Failed to run compliance check: {e}")
            raise

    @time_operation("experimental_systems_data_protection")
    async def process_data_protection(
        self, data_type: str, action: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process data protection operations."""
        try:
            if action == "anonymize":
                result = await self.data_protection_service.anonymize_data(
                    data_type=data_type, data=data
                )
            elif action == "pseudonymize":
                result = await self.data_protection_service.pseudonymize_data(
                    data_type=data_type, data=data
                )
            elif action == "encrypt":
                result = await self.data_protection_service.encrypt_data(
                    data_type=data_type, data=data
                )
            else:
                raise ValueError(f"Unknown data protection action: {action}")

            return {
                "action": action,
                "data_type": data_type,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to process data protection: {e}")
            raise

    @time_operation("experimental_systems_security_incident")
    async def report_security_incident(
        self, incident_type: str, severity: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Report a security incident."""
        try:
            incident = await self.security_incident_response.create_incident(
                incident_type=incident_type,
                severity=severity,
                description=details.get("description", ""),
                affected_users=details.get("affected_users", []),
                evidence=details.get("evidence", {}),
            )

            return {
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "status": incident.status,
                "created_at": incident.created_at.isoformat(),
                "response_actions": incident.response_actions,
            }

        except Exception as e:
            logger.error(f"Failed to report security incident: {e}")
            raise

    async def _start_all_services(self):
        """Start all experimental services."""
        try:
            # Start Advanced AI Service
            await self.advanced_ai_service.start()
            self.system_health["advanced_ai"] = SystemHealth(
                system_name="Advanced AI Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            # Start Advanced Analytics Service
            await self.advanced_analytics_service.start()
            self.system_health["advanced_analytics"] = SystemHealth(
                system_name="Advanced Analytics Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            # Start System Integration Service
            await self.system_integration_service.start()
            self.system_health["system_integration"] = SystemHealth(
                system_name="System Integration Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            # Start Compliance Automation Service
            await self.compliance_automation_service.start()
            self.system_health["compliance_automation"] = SystemHealth(
                system_name="Compliance Automation Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            # Start Data Protection Service
            await self.data_protection_service.start()
            self.system_health["data_protection"] = SystemHealth(
                system_name="Data Protection Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            # Start Security Incident Response Service
            await self.security_incident_response.start()
            self.system_health["security_incident_response"] = SystemHealth(
                system_name="Security Incident Response Service",
                status=SystemStatus.ACTIVE,
                last_check=datetime.now(),
            )

            logger.info("All experimental services started")

        except Exception as e:
            logger.error(f"Failed to start all services: {e}")
            raise

    async def _stop_all_services(self):
        """Stop all experimental services."""
        try:
            # Stop all services
            await self.advanced_ai_service.stop()
            await self.advanced_analytics_service.stop()
            await self.system_integration_service.stop()
            await self.compliance_automation_service.stop()
            await self.data_protection_service.stop()
            await self.security_incident_response.stop()

            logger.info("All experimental services stopped")

        except Exception as e:
            logger.error(f"Failed to stop all services: {e}")
            raise

    async def _health_monitor_loop(self):
        """Monitor health of all experimental systems."""
        while self.is_running:
            try:
                for system_name, health in self.system_health.items():
                    # Update last check time
                    health.last_check = datetime.now()

                    # Check system health (simplified for now)
                    try:
                        if system_name == "advanced_ai":
                            # Check AI service health
                            if len(self.advanced_ai_service.models) > 0:
                                health.status = SystemStatus.ACTIVE
                                health.performance_score = 0.9
                            else:
                                health.status = SystemStatus.ERROR
                                health.error_count += 1

                        elif system_name == "advanced_analytics":
                            # Check analytics service health
                            if len(self.advanced_analytics_service.dashboards) > 0:
                                health.status = SystemStatus.ACTIVE
                                health.performance_score = 0.85
                            else:
                                health.status = SystemStatus.ERROR
                                health.error_count += 1

                        elif system_name == "system_integration":
                            # Check system integration health
                            if (
                                len(self.system_integration_service.service_registry)
                                > 0
                            ):
                                health.status = SystemStatus.ACTIVE
                                health.performance_score = 0.95
                            else:
                                health.status = SystemStatus.ERROR
                                health.error_count += 1

                        # Update uptime
                        health.uptime = datetime.now() - health.last_check

                    except Exception as e:
                        health.status = SystemStatus.ERROR
                        health.error_count += 1
                        health.metadata["last_error"] = str(e)
                        logger.error(f"Health check failed for {system_name}: {e}")

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _performance_optimizer_loop(self):
        """Optimize performance of experimental systems."""
        while self.is_running:
            try:
                # Optimize cache usage
                await self.cache_manager.optimize_cache()

                # Record performance metrics
                for system_name, health in self.system_health.items():
                    if health.status == SystemStatus.ACTIVE:
                        await self.advanced_analytics_service.record_metric(
                            name=f"{system_name}_performance",
                            metric_type="gauge",
                            value=health.performance_score,
                            unit="score",
                        )

                await asyncio.sleep(300)  # Optimize every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance optimizer loop: {e}")
                await asyncio.sleep(600)  # Wait longer on error

    async def _data_sync_loop(self):
        """Sync data between experimental systems."""
        while self.is_running:
            try:
                # Sync AI predictions to analytics
                if hasattr(self.advanced_ai_service, "prediction_stats"):
                    stats = self.advanced_ai_service.prediction_stats
                    await self.advanced_analytics_service.record_metric(
                        name="ai_total_predictions",
                        metric_type="counter",
                        value=stats.get("total_predictions", 0),
                        unit="predictions",
                    )

                # Sync system integration metrics
                if hasattr(self.system_integration_service, "service_registry"):
                    service_count = len(
                        self.system_integration_service.service_registry
                    )
                    await self.advanced_analytics_service.record_metric(
                        name="registered_services",
                        metric_type="gauge",
                        value=service_count,
                        unit="services",
                    )

                await asyncio.sleep(60)  # Sync every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data sync loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error
