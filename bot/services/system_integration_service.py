"""
System Integration Service - Comprehensive System Integration & Microservices Architecture

This service provides comprehensive system integration capabilities including
microservices architecture, enterprise API management, service discovery,
load balancing, and deployment automation for the DBSBM system.

Features:
- Microservices architecture implementation
- Service discovery and registration
- Load balancing and health checks
- Enterprise API management and gateway
- Service mesh capabilities
- Deployment automation and orchestration
- Containerization support
- Service monitoring and metrics
- Circuit breaker patterns
- Distributed tracing
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp
import hashlib
import hmac
from pathlib import Path

from bot.services.performance_monitor import time_operation, record_metric
from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager

logger = logging.getLogger(__name__)

# System integration cache TTLs
SYSTEM_INTEGRATION_CACHE_TTLS = {
    'service_registry': 300,         # 5 minutes
    'service_health': 60,            # 1 minute
    'load_balancer': 30,             # 30 seconds
    'api_gateway': 180,              # 3 minutes
    'deployment_status': 120,        # 2 minutes
    'service_metrics': 60,           # 1 minute
    'circuit_breaker': 300,          # 5 minutes
    'distributed_tracing': 600,      # 10 minutes
    'service_mesh': 180,             # 3 minutes
    'orchestration': 120,            # 2 minutes
}


class ServiceStatus(Enum):
    """Service status types."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceType(Enum):
    """Service types for microservices architecture."""
    API_GATEWAY = "api_gateway"
    USER_SERVICE = "user_service"
    BETTING_SERVICE = "betting_service"
    ANALYTICS_SERVICE = "analytics_service"
    AI_SERVICE = "ai_service"
    INTEGRATION_SERVICE = "integration_service"
    ENTERPRISE_SERVICE = "enterprise_service"
    SECURITY_SERVICE = "security_service"
    COMPLIANCE_SERVICE = "compliance_service"
    CACHE_SERVICE = "cache_service"
    DATABASE_SERVICE = "database_service"
    MONITORING_SERVICE = "monitoring_service"


class LoadBalancerType(Enum):
    """Load balancer types."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ServiceInstance:
    """Service instance information."""
    service_id: str
    service_type: ServiceType
    instance_id: str
    host: str
    port: int
    health_endpoint: str
    status: ServiceStatus
    load_balancer_weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ServiceRegistry:
    """Service registry entry."""
    service_id: str
    service_type: ServiceType
    instances: List[ServiceInstance]
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    load_balancer_type: LoadBalancerType = LoadBalancerType.ROUND_ROBIN
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class APIGateway:
    """API Gateway configuration."""
    gateway_id: str
    name: str
    base_url: str
    routes: List[Dict[str, Any]]
    rate_limits: Dict[str, int]
    authentication_required: bool = True
    cors_enabled: bool = True
    logging_enabled: bool = True
    monitoring_enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class LoadBalancer:
    """Load balancer configuration."""
    balancer_id: str
    name: str
    service_type: ServiceType
    balancer_type: LoadBalancerType
    instances: List[ServiceInstance]
    health_check_path: str = "/health"
    health_check_interval: int = 30
    session_sticky: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class CircuitBreaker:
    """Circuit breaker configuration."""
    breaker_id: str
    service_id: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    deployment_id: str
    service_type: ServiceType
    container_image: str
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    environment_vars: Dict[str, str] = None
    ports: List[int] = None
    volumes: List[Dict[str, str]] = None
    health_check: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.ports is None:
            self.ports = []
        if self.volumes is None:
            self.volumes = []


class SystemIntegrationService:
    """Comprehensive system integration and microservices architecture service."""

    def __init__(self, db_manager: DatabaseManager, 
                 enable_load_balancer_loop: bool = True,
                 load_balancer_update_interval: int = 30,
                 enable_verbose_logging: bool = False):
        """
        Initialize the system integration service.
        
        Args:
            db_manager: Database manager instance
            enable_load_balancer_loop: Whether to run the load balancer update loop
            load_balancer_update_interval: Seconds between load balancer updates
            enable_verbose_logging: Whether to enable verbose debug logging
        """
        self.db_manager = db_manager
        self.cache_manager = EnhancedCacheManager()
        
        # Configuration options
        self.enable_load_balancer_loop = enable_load_balancer_loop
        self.load_balancer_update_interval = load_balancer_update_interval
        self.enable_verbose_logging = enable_verbose_logging
        
        # Service configuration
        self.config = {
            'health_check_interval': 30,
            'service_timeout': 5,
            'max_retries': 3,
            'retry_delay': 1,
            'circuit_breaker_threshold': 5,
            'circuit_breaker_timeout': 60,
            'load_balancer_update_interval': load_balancer_update_interval,
            'service_discovery_interval': 60,
            'deployment_check_interval': 300
        }
        
        # Service state
        self.is_running = False
        self.session = None
        
        # Service registries
        self.service_registry: Dict[str, ServiceRegistry] = {}
        self.service_instances: Dict[str, ServiceInstance] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.api_gateways: Dict[str, APIGateway] = {}
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        
        # Background tasks
        self.health_check_task = None
        self.service_discovery_task = None
        self.load_balancer_task = None
        self.circuit_breaker_task = None
        self.deployment_automation_task = None

    async def start(self):
        """Start the system integration service."""
        try:
            # Initialize HTTP session
            self.session = aiohttp.ClientSession()

            # Load existing configurations
            await self._load_service_registry()
            await self._load_load_balancers()
            await self._load_circuit_breakers()
            await self._load_api_gateways()
            await self._load_deployment_configs()

            self.is_running = True

            # Start background tasks
            self.health_check_task = asyncio.create_task(
                self._health_check_loop())
            self.service_discovery_task = asyncio.create_task(
                self._service_discovery_loop())
            
            # Conditionally start load balancer task
            if self.enable_load_balancer_loop:
                self.load_balancer_task = asyncio.create_task(
                    self._load_balancer_loop())
                logger.info(f"Load balancer loop started (interval: {self.load_balancer_update_interval}s)")
            else:
                self.load_balancer_task = None
                logger.info("Load balancer loop disabled")
            
            # Start circuit breaker task
            self.circuit_breaker_task = asyncio.create_task(
                self._circuit_breaker_loop())
                
            self.deployment_automation_task = asyncio.create_task(
                self._deployment_automation_loop())

            logger.info("System integration service started successfully")

        except Exception as e:
            logger.error(f"Failed to start system integration service: {e}")
            raise

    async def stop(self):
        """Stop the system integration service."""
        self.is_running = False

        # Cancel background tasks
        tasks = [self.health_check_task, self.service_discovery_task,
                 self.load_balancer_task, self.circuit_breaker_task, self.deployment_automation_task]

        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close HTTP session
        if self.session:
            await self.session.close()

        logger.info("System integration service stopped")

    @time_operation("register_service")
    async def register_service(self, service_type: ServiceType, host: str, port: int,
                               health_endpoint: str = "/health", load_balancer_weight: int = 1,
                               max_connections: int = 100) -> Optional[str]:
        """Register a new service instance."""
        try:
            service_id = f"{service_type.value}_{uuid.uuid4().hex[:8]}"
            instance_id = f"{service_id}_instance_{uuid.uuid4().hex[:8]}"

            # Create service instance
            instance = ServiceInstance(
                service_id=service_id,
                service_type=service_type,
                instance_id=instance_id,
                host=host,
                port=port,
                health_endpoint=health_endpoint,
                status=ServiceStatus.STARTING,
                load_balancer_weight=load_balancer_weight,
                max_connections=max_connections
            )

            # Store in database
            await self._store_service_instance(instance)

            # Add to registry
            if service_id not in self.service_registry:
                self.service_registry[service_id] = ServiceRegistry(
                    service_id=service_id,
                    service_type=service_type,
                    instances=[instance]
                )
            else:
                self.service_registry[service_id].instances.append(instance)

            self.service_instances[instance_id] = instance

            # Create load balancer if needed
            await self._create_load_balancer(service_type, service_id)

            # Create circuit breaker
            await self._create_circuit_breaker(service_id)

            # Clear cache
            await self.cache_manager.clear_cache_by_pattern(f"service_registry:{service_id}")

            record_metric("services_registered", 1)
            logger.info(f"Service {service_id} registered successfully")

            return service_id

        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return None

    @time_operation("deregister_service")
    async def deregister_service(self, service_id: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        try:
            # Remove from registry
            if service_id in self.service_registry:
                self.service_registry[service_id].instances = [
                    inst for inst in self.service_registry[service_id].instances
                    if inst.instance_id != instance_id
                ]

                # Remove service if no instances remain
                if not self.service_registry[service_id].instances:
                    del self.service_registry[service_id]

            # Remove from instances
            if instance_id in self.service_instances:
                del self.service_instances[instance_id]

            # Update database
            await self._remove_service_instance(instance_id)

            # Clear cache
            await self.cache_manager.clear_cache_by_pattern(f"service_registry:{service_id}")

            record_metric("services_deregistered", 1)
            logger.info(
                f"Service instance {instance_id} deregistered successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            return False

    @time_operation("create_api_gateway")
    async def create_api_gateway(self, name: str, base_url: str, routes: List[Dict[str, Any]],
                                 rate_limits: Dict[str, int], authentication_required: bool = True,
                                 cors_enabled: bool = True) -> Optional[str]:
        """Create an API gateway."""
        try:
            gateway_id = f"gateway_{uuid.uuid4().hex[:8]}"

            gateway = APIGateway(
                gateway_id=gateway_id,
                name=name,
                base_url=base_url,
                routes=routes,
                rate_limits=rate_limits,
                authentication_required=authentication_required,
                cors_enabled=cors_enabled
            )

            # Store in database
            await self._store_api_gateway(gateway)

            # Add to memory
            self.api_gateways[gateway_id] = gateway

            # Clear cache
            await self.cache_manager.clear_cache_by_pattern("api_gateways:*")

            record_metric("api_gateways_created", 1)
            logger.info(f"API Gateway {gateway_id} created successfully")

            return gateway_id

        except Exception as e:
            logger.error(f"Failed to create API gateway: {e}")
            return None

    @time_operation("create_deployment_config")
    async def create_deployment_config(self, service_type: ServiceType, container_image: str,
                                       replicas: int = 1, cpu_limit: str = "500m",
                                       memory_limit: str = "512Mi", environment_vars: Dict[str, str] = None,
                                       ports: List[int] = None) -> Optional[str]:
        """Create a deployment configuration."""
        try:
            deployment_id = f"deployment_{uuid.uuid4().hex[:8]}"

            config = DeploymentConfig(
                deployment_id=deployment_id,
                service_type=service_type,
                container_image=container_image,
                replicas=replicas,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                environment_vars=environment_vars or {},
                ports=ports or []
            )

            # Store in database
            await self._store_deployment_config(config)

            # Add to memory
            self.deployment_configs[deployment_id] = config

            # Clear cache
            await self.cache_manager.clear_cache_by_pattern("deployment_configs:*")

            record_metric("deployment_configs_created", 1)
            logger.info(
                f"Deployment config {deployment_id} created successfully")

            return deployment_id

        except Exception as e:
            logger.error(f"Failed to create deployment config: {e}")
            return None

    @time_operation("deploy_service")
    async def deploy_service(self, deployment_id: str) -> bool:
        """Deploy a service using the specified configuration."""
        try:
            if deployment_id not in self.deployment_configs:
                logger.error(f"Deployment config {deployment_id} not found")
                return False

            config = self.deployment_configs[deployment_id]

            # Generate deployment manifest
            manifest = await self._generate_deployment_manifest(config)

            # Execute deployment
            success = await self._execute_deployment(manifest)

            if success:
                record_metric("services_deployed", 1)
                logger.info(f"Service {deployment_id} deployed successfully")
            else:
                logger.error(f"Failed to deploy service {deployment_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to deploy service: {e}")
            return False

    @time_operation("get_service_instances")
    async def get_service_instances(self, service_type: ServiceType) -> List[ServiceInstance]:
        """Get all instances of a service type."""
        try:
            cache_key = f"service_instances:{service_type.value}"
            cached = await self.cache_manager.get(cache_key)

            if cached:
                return [ServiceInstance(**inst) for inst in cached]

            instances = []
            for registry in self.service_registry.values():
                if registry.service_type == service_type:
                    instances.extend(registry.instances)

            # Cache result
            await self.cache_manager.set(cache_key, [asdict(inst) for inst in instances])

            return instances

        except Exception as e:
            logger.error(f"Failed to get service instances: {e}")
            return []

    @time_operation("get_healthy_instances")
    async def get_healthy_instances(self, service_type: ServiceType) -> List[ServiceInstance]:
        """Get healthy instances of a service type."""
        try:
            instances = await self.get_service_instances(service_type)
            return [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
        except Exception as e:
            logger.error(f"Failed to get healthy instances: {e}")
            return []

    @time_operation("route_request")
    async def route_request(self, service_type: ServiceType, path: str, method: str = "GET",
                            data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Route a request through the load balancer."""
        try:
            # Get healthy instances
            instances = await self.get_healthy_instances(service_type)

            if not instances:
                logger.error(
                    f"No healthy instances available for {service_type.value}")
                return None

            # Select instance based on load balancer type
            selected_instance = await self._select_instance(service_type, instances)

            if not selected_instance:
                logger.error(f"No instance selected for {service_type.value}")
                return None

            # Check circuit breaker
            if not await self._check_circuit_breaker(selected_instance.service_id):
                logger.warning(
                    f"Circuit breaker open for {selected_instance.service_id}")
                return None

            # Make request
            response = await self._make_service_request(selected_instance, path, method, data)

            # Update circuit breaker
            await self._update_circuit_breaker(selected_instance.service_id, response is not None)

            return response

        except Exception as e:
            logger.error(f"Failed to route request: {e}")
            return None

    async def _health_check_loop(self):
        """Background health check loop."""
        while self.is_running:
            try:
                for instance in self.service_instances.values():
                    await self._check_instance_health(instance)

                await asyncio.sleep(self.config['health_check_interval'])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)

    async def _service_discovery_loop(self):
        """Background service discovery loop."""
        while self.is_running:
            try:
                # Update service registry
                await self._update_service_registry()

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Service discovery loop error: {e}")
                await asyncio.sleep(10)

    async def _load_balancer_loop(self):
        """Background load balancer loop."""
        while self.is_running:
            try:
                # Update load balancer metrics (reduced logging)
                updated_count = 0
                for balancer in self.load_balancers.values():
                    if await self._update_load_balancer_metrics(balancer):
                        updated_count += 1
                
                # Only log if there were actual updates and verbose logging is enabled
                if updated_count > 0 and self.enable_verbose_logging:
                    logger.debug(f"Updated {updated_count} load balancer metrics")

                await asyncio.sleep(self.load_balancer_update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Load balancer loop error: {e}")
                await asyncio.sleep(5)

    async def _circuit_breaker_loop(self):
        """Background circuit breaker loop."""
        while self.is_running:
            try:
                # Only update circuit breakers that have changed state
                for breaker in self.circuit_breakers.values():
                    # Check if the breaker needs to transition from OPEN to HALF_OPEN
                    if (breaker.state == CircuitBreakerState.OPEN and 
                        breaker.last_failure_time and 
                        (datetime.utcnow() - breaker.last_failure_time).seconds > breaker.timeout_seconds):
                        
                        breaker.state = CircuitBreakerState.HALF_OPEN
                        breaker.updated_at = datetime.utcnow()
                        await self._update_circuit_breaker_state(breaker)
                        logger.debug(f"Circuit breaker {breaker.breaker_id} transitioned to HALF_OPEN")

                await asyncio.sleep(60)  # Check every 60 seconds instead of 10

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Circuit breaker loop error: {e}")
                await asyncio.sleep(5)

    async def _deployment_automation_loop(self):
        """Background deployment automation loop."""
        while self.is_running:
            try:
                # Check for deployment updates
                await self._check_deployment_updates()

                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Deployment automation loop error: {e}")
                await asyncio.sleep(30)

    async def _check_instance_health(self, instance: ServiceInstance):
        """Check health of a service instance."""
        try:
            url = f"http://{instance.host}:{instance.port}{instance.health_endpoint}"

            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    instance.status = ServiceStatus.HEALTHY
                else:
                    instance.status = ServiceStatus.UNHEALTHY

                instance.last_health_check = datetime.utcnow()
                instance.updated_at = datetime.utcnow()

                # Update database
                await self._update_service_instance(instance)

        except Exception as e:
            instance.status = ServiceStatus.UNHEALTHY
            instance.last_health_check = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

            # Update database
            await self._update_service_instance(instance)

            logger.warning(
                f"Health check failed for {instance.instance_id}: {e}")

    async def _select_instance(self, service_type: ServiceType, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select an instance based on load balancer type."""
        if not instances:
            return None

        # Get load balancer for service type
        balancer = None
        for lb in self.load_balancers.values():
            if lb.service_type == service_type:
                balancer = lb
                break

        if not balancer:
            # Use round robin as default
            return instances[0]

        # Apply load balancing strategy
        if balancer.balancer_type == LoadBalancerType.ROUND_ROBIN:
            return instances[0]  # Simplified round robin
        elif balancer.balancer_type == LoadBalancerType.LEAST_CONNECTIONS:
            return min(instances, key=lambda x: x.current_connections)
        elif balancer.balancer_type == LoadBalancerType.LEAST_RESPONSE_TIME:
            return min(instances, key=lambda x: x.response_time)
        else:
            return instances[0]

    async def _check_circuit_breaker(self, service_id: str) -> bool:
        """Check if circuit breaker allows requests."""
        if service_id not in self.circuit_breakers:
            return True

        breaker = self.circuit_breakers[service_id]

        if breaker.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if breaker.last_failure_time and (datetime.utcnow() - breaker.last_failure_time).seconds > breaker.timeout_seconds:
                breaker.state = CircuitBreakerState.HALF_OPEN
                return True
            return False

        return True

    async def _update_circuit_breaker(self, service_id: str, success: bool):
        """Update circuit breaker state."""
        if service_id not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[service_id]

        if success:
            breaker.failure_count = 0
            breaker.last_success_time = datetime.utcnow()
            if breaker.state == CircuitBreakerState.HALF_OPEN:
                breaker.state = CircuitBreakerState.CLOSED
        else:
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.utcnow()

            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitBreakerState.OPEN

        breaker.updated_at = datetime.utcnow()
        await self._update_circuit_breaker_db(breaker)

    async def _make_service_request(self, instance: ServiceInstance, path: str, method: str, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Make a request to a service instance."""
        try:
            url = f"http://{instance.host}:{instance.port}{path}"

            start_time = time.time()

            if method.upper() == "GET":
                async with self.session.get(url, timeout=self.config['service_timeout']) as response:
                    response_time = time.time() - start_time
                    instance.response_time = response_time
                    instance.current_connections += 1

                    if response.status == 200:
                        return await response.json()
                    else:
                        return None

            elif method.upper() == "POST":
                async with self.session.post(url, json=data, timeout=self.config['service_timeout']) as response:
                    response_time = time.time() - start_time
                    instance.response_time = response_time
                    instance.current_connections += 1

                    if response.status == 200:
                        return await response.json()
                    else:
                        return None

            return None

        except Exception as e:
            logger.error(f"Service request failed: {e}")
            return None

    async def _create_load_balancer(self, service_type: ServiceType, service_id: str):
        """Create a load balancer for a service."""
        balancer_id = f"lb_{service_type.value}_{uuid.uuid4().hex[:8]}"

        balancer = LoadBalancer(
            balancer_id=balancer_id,
            name=f"Load Balancer for {service_type.value}",
            service_type=service_type,
            balancer_type=LoadBalancerType.ROUND_ROBIN,
            instances=[]
        )

        self.load_balancers[balancer_id] = balancer
        await self._store_load_balancer(balancer)

    async def _create_circuit_breaker(self, service_id: str):
        """Create a circuit breaker for a service."""
        breaker_id = f"cb_{service_id}_{uuid.uuid4().hex[:8]}"

        breaker = CircuitBreaker(
            breaker_id=breaker_id,
            service_id=service_id
        )

        self.circuit_breakers[breaker_id] = breaker
        await self._store_circuit_breaker(breaker)

    async def _generate_deployment_manifest(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Generate deployment manifest for containerization."""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{config.service_type.value}-deployment",
                "labels": {
                    "app": config.service_type.value,
                    "deployment": config.deployment_id
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": config.service_type.value
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": config.service_type.value
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": config.service_type.value,
                            "image": config.container_image,
                            "ports": [{"containerPort": port} for port in config.ports],
                            "resources": {
                                "limits": {
                                    "cpu": config.cpu_limit,
                                    "memory": config.memory_limit
                                }
                            },
                            "env": [{"name": k, "value": v} for k, v in config.environment_vars.items()]
                        }]
                    }
                }
            }
        }

    async def _execute_deployment(self, manifest: Dict[str, Any]) -> bool:
        """Execute deployment (simulated)."""
        try:
            # In a real implementation, this would use Kubernetes API or Docker API
            logger.info(
                f"Deploying service with manifest: {manifest['metadata']['name']}")

            # Simulate deployment
            await asyncio.sleep(2)

            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    # Database operations
    async def _store_service_instance(self, instance: ServiceInstance):
        """Store service instance in database."""
        try:
            query = """
            INSERT INTO service_instances (
                service_id, service_type, instance_id, host, port, health_endpoint,
                status, load_balancer_weight, max_connections, current_connections,
                response_time, last_health_check, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                status = VALUES(status), current_connections = VALUES(current_connections),
                response_time = VALUES(response_time), last_health_check = VALUES(last_health_check),
                updated_at = VALUES(updated_at)
            """

            await self.db_manager.execute(query, (
                instance.service_id, instance.service_type.value, instance.instance_id,
                instance.host, instance.port, instance.health_endpoint, instance.status.value,
                instance.load_balancer_weight, instance.max_connections, instance.current_connections,
                instance.response_time, instance.last_health_check, instance.created_at,
                instance.updated_at
            ))

            logger.info(f"Stored service instance: {instance.instance_id}")

        except Exception as e:
            logger.error(f"Failed to store service instance: {e}")
            raise

    async def _update_service_instance(self, instance: ServiceInstance):
        """Update service instance in database."""
        try:
            query = """
            UPDATE service_instances SET
                status = %s, current_connections = %s, response_time = %s,
                last_health_check = %s, updated_at = %s
            WHERE instance_id = %s
            """

            await self.db_manager.execute(query, (
                instance.status.value, instance.current_connections, instance.response_time,
                instance.last_health_check, instance.updated_at, instance.instance_id
            ))

            logger.info(f"Updated service instance: {instance.instance_id}")

        except Exception as e:
            logger.error(f"Failed to update service instance: {e}")
            raise

    async def _remove_service_instance(self, instance_id: str):
        """Remove service instance from database."""
        try:
            query = "DELETE FROM service_instances WHERE instance_id = %s"
            await self.db_manager.execute(query, (instance_id,))
            logger.info(f"Removed service instance: {instance_id}")

        except Exception as e:
            logger.error(f"Failed to remove service instance: {e}")
            raise

    async def _store_api_gateway(self, gateway: APIGateway):
        """Store API gateway in database."""
        try:
            query = """
            INSERT INTO api_gateways (
                gateway_id, name, base_url, routes, rate_limits, authentication_required,
                cors_enabled, logging_enabled, monitoring_enabled, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                name = VALUES(name), base_url = VALUES(base_url), routes = VALUES(routes),
                rate_limits = VALUES(rate_limits), authentication_required = VALUES(authentication_required),
                cors_enabled = VALUES(cors_enabled), logging_enabled = VALUES(logging_enabled),
                monitoring_enabled = VALUES(monitoring_enabled), updated_at = VALUES(updated_at)
            """

            await self.db_manager.execute(query, (
                gateway.gateway_id, gateway.name, gateway.base_url, json.dumps(
                    gateway.routes),
                json.dumps(
                    gateway.rate_limits), gateway.authentication_required,
                gateway.cors_enabled, gateway.logging_enabled, gateway.monitoring_enabled,
                gateway.created_at, gateway.updated_at
            ))

            logger.info(f"Stored API gateway: {gateway.gateway_id}")

        except Exception as e:
            logger.error(f"Failed to store API gateway: {e}")
            raise

    async def _store_deployment_config(self, config: DeploymentConfig):
        """Store deployment configuration in database."""
        try:
            query = """
            INSERT INTO deployment_configs (
                deployment_id, service_type, container_image, replicas, cpu_limit,
                memory_limit, environment_vars, ports, volumes, health_check,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                container_image = VALUES(container_image), replicas = VALUES(replicas),
                cpu_limit = VALUES(cpu_limit), memory_limit = VALUES(memory_limit),
                environment_vars = VALUES(environment_vars), ports = VALUES(ports),
                volumes = VALUES(volumes), health_check = VALUES(health_check),
                updated_at = VALUES(updated_at)
            """

            await self.db_manager.execute(query, (
                config.deployment_id, config.service_type.value, config.container_image,
                config.replicas, config.cpu_limit, config.memory_limit,
                json.dumps(config.environment_vars), json.dumps(config.ports),
                json.dumps(config.volumes), json.dumps(
                    config.health_check or {}),
                config.created_at, config.updated_at
            ))

            logger.info(f"Stored deployment config: {config.deployment_id}")

        except Exception as e:
            logger.error(f"Failed to store deployment config: {e}")
            raise

    async def _store_load_balancer(self, balancer: LoadBalancer):
        """Store load balancer in database."""
        try:
            query = """
            INSERT INTO load_balancers (
                balancer_id, name, service_type, balancer_type, instances,
                health_check_path, health_check_interval, session_sticky,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                name = VALUES(name), service_type = VALUES(service_type),
                balancer_type = VALUES(balancer_type), instances = VALUES(instances),
                health_check_path = VALUES(health_check_path), health_check_interval = VALUES(health_check_interval),
                session_sticky = VALUES(session_sticky), updated_at = VALUES(updated_at)
            """

            # Convert instances to JSON-serializable format
            instances_data = []
            for instance in balancer.instances:
                instances_data.append({
                    'instance_id': instance.instance_id,
                    'host': instance.host,
                    'port': instance.port,
                    'status': instance.status.value
                })

            await self.db_manager.execute(query, (
                balancer.balancer_id, balancer.name, balancer.service_type.value,
                balancer.balancer_type.value, json.dumps(instances_data),
                balancer.health_check_path, balancer.health_check_interval,
                balancer.session_sticky, balancer.created_at, balancer.updated_at
            ))

            logger.info(f"Stored load balancer: {balancer.balancer_id}")

        except Exception as e:
            logger.error(f"Failed to store load balancer: {e}")
            raise

    async def _store_circuit_breaker(self, breaker: CircuitBreaker):
        """Store circuit breaker in database."""
        try:
            query = """
            INSERT INTO circuit_breakers (
                breaker_id, service_id, failure_threshold, timeout_seconds, state,
                failure_count, last_failure_time, last_success_time, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                failure_threshold = VALUES(failure_threshold), timeout_seconds = VALUES(timeout_seconds),
                state = VALUES(state), failure_count = VALUES(failure_count),
                last_failure_time = VALUES(last_failure_time), last_success_time = VALUES(last_success_time),
                updated_at = VALUES(updated_at)
            """

            await self.db_manager.execute(query, (
                breaker.breaker_id, breaker.service_id, breaker.failure_threshold,
                breaker.timeout_seconds, breaker.state.value, breaker.failure_count,
                breaker.last_failure_time, breaker.last_success_time,
                breaker.created_at, breaker.updated_at
            ))

            logger.info(f"Stored circuit breaker: {breaker.breaker_id}")

        except Exception as e:
            logger.error(f"Failed to store circuit breaker: {e}")
            raise

    async def _update_circuit_breaker_db(self, breaker: CircuitBreaker):
        """Update circuit breaker in database."""
        try:
            query = """
            UPDATE circuit_breakers SET
                state = %s, failure_count = %s, last_failure_time = %s,
                last_success_time = %s, updated_at = %s
            WHERE breaker_id = %s
            """

            await self.db_manager.execute(query, (
                breaker.state.value, breaker.failure_count, breaker.last_failure_time,
                breaker.last_success_time, breaker.updated_at, breaker.breaker_id
            ))

            logger.info(f"Updated circuit breaker: {breaker.breaker_id}")

        except Exception as e:
            logger.error(f"Failed to update circuit breaker: {e}")
            raise

    # Load methods
    async def _load_service_registry(self):
        """Load service registry from database."""
        try:
            query = "SELECT * FROM service_registry"
            registry_data = await self.db_manager.fetch_all(query)

            for row in registry_data:
                service_id = row['service_id']
                service_type = ServiceType(row['service_type'])

                # Get instances for this service
                instances_query = "SELECT * FROM service_instances WHERE service_id = %s"
                instances_data = await self.db_manager.fetch_all(instances_query, (service_id,))

                instances = []
                for instance_row in instances_data:
                    instance = ServiceInstance(
                        service_id=instance_row['service_id'],
                        service_type=ServiceType(instance_row['service_type']),
                        instance_id=instance_row['instance_id'],
                        host=instance_row['host'],
                        port=instance_row['port'],
                        health_endpoint=instance_row['health_endpoint'],
                        status=ServiceStatus(instance_row['status']),
                        load_balancer_weight=instance_row['load_balancer_weight'],
                        max_connections=instance_row['max_connections'],
                        current_connections=instance_row['current_connections'],
                        response_time=instance_row['response_time'],
                        last_health_check=instance_row['last_health_check'],
                        created_at=instance_row['created_at'],
                        updated_at=instance_row['updated_at']
                    )
                    instances.append(instance)

                registry = ServiceRegistry(
                    service_id=service_id,
                    service_type=service_type,
                    instances=instances,
                    health_check_interval=row['health_check_interval'],
                    circuit_breaker_threshold=row['circuit_breaker_threshold'],
                    circuit_breaker_timeout=row['circuit_breaker_timeout'],
                    load_balancer_type=LoadBalancerType(
                        row['load_balancer_type']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                self.service_registry[service_id] = registry

                # Store instances in memory
                for instance in instances:
                    self.service_instances[instance.instance_id] = instance

            logger.info(
                f"Loaded {len(self.service_registry)} services from registry")

        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")

    async def _load_load_balancers(self):
        """Load load balancers from database."""
        try:
            query = "SELECT * FROM load_balancers"
            balancers_data = await self.db_manager.fetch_all(query)

            for row in balancers_data:
                # Parse instances from JSON
                instances_data = json.loads(row['instances'])
                instances = []

                for instance_data in instances_data:
                    # Find the actual instance in memory
                    instance_id = instance_data['instance_id']
                    if instance_id in self.service_instances:
                        instances.append(self.service_instances[instance_id])

                balancer = LoadBalancer(
                    balancer_id=row['balancer_id'],
                    name=row['name'],
                    service_type=ServiceType(row['service_type']),
                    balancer_type=LoadBalancerType(row['balancer_type']),
                    instances=instances,
                    health_check_path=row['health_check_path'],
                    health_check_interval=row['health_check_interval'],
                    session_sticky=bool(row['session_sticky']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                self.load_balancers[row['balancer_id']] = balancer

            logger.info(f"Loaded {len(self.load_balancers)} load balancers")

        except Exception as e:
            logger.error(f"Failed to load load balancers: {e}")

    async def _load_circuit_breakers(self):
        """Load circuit breakers from database."""
        try:
            query = "SELECT * FROM circuit_breakers"
            breakers_data = await self.db_manager.fetch_all(query)

            for row in breakers_data:
                breaker = CircuitBreaker(
                    breaker_id=row['breaker_id'],
                    service_id=row['service_id'],
                    failure_threshold=row['failure_threshold'],
                    timeout_seconds=row['timeout_seconds'],
                    state=CircuitBreakerState(row['state']),
                    failure_count=row['failure_count'],
                    last_failure_time=row['last_failure_time'],
                    last_success_time=row['last_success_time'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                self.circuit_breakers[row['breaker_id']] = breaker

            logger.info(
                f"Loaded {len(self.circuit_breakers)} circuit breakers")

        except Exception as e:
            logger.error(f"Failed to load circuit breakers: {e}")

    async def _load_api_gateways(self):
        """Load API gateways from database."""
        try:
            query = "SELECT * FROM api_gateways"
            gateways_data = await self.db_manager.fetch_all(query)

            for row in gateways_data:
                gateway = APIGateway(
                    gateway_id=row['gateway_id'],
                    name=row['name'],
                    base_url=row['base_url'],
                    routes=json.loads(row['routes']),
                    rate_limits=json.loads(row['rate_limits']),
                    authentication_required=bool(
                        row['authentication_required']),
                    cors_enabled=bool(row['cors_enabled']),
                    logging_enabled=bool(row['logging_enabled']),
                    monitoring_enabled=bool(row['monitoring_enabled']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                self.api_gateways[row['gateway_id']] = gateway

            logger.info(f"Loaded {len(self.api_gateways)} API gateways")

        except Exception as e:
            logger.error(f"Failed to load API gateways: {e}")

    async def _load_deployment_configs(self):
        """Load deployment configurations from database."""
        try:
            query = "SELECT * FROM deployment_configs"
            configs_data = await self.db_manager.fetch_all(query)

            for row in configs_data:
                config = DeploymentConfig(
                    deployment_id=row['deployment_id'],
                    service_type=ServiceType(row['service_type']),
                    container_image=row['container_image'],
                    replicas=row['replicas'],
                    cpu_limit=row['cpu_limit'],
                    memory_limit=row['memory_limit'],
                    environment_vars=json.loads(row['environment_vars']),
                    ports=json.loads(row['ports']),
                    volumes=json.loads(row['volumes']),
                    health_check=json.loads(
                        row['health_check']) if row['health_check'] else None,
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                self.deployment_configs[row['deployment_id']] = config

            logger.info(
                f"Loaded {len(self.deployment_configs)} deployment configs")

        except Exception as e:
            logger.error(f"Failed to load deployment configs: {e}")

    # Update methods
    async def _update_service_registry(self):
        """Update service registry."""
        try:
            for service_id, registry in self.service_registry.items():
                query = """
                UPDATE service_registry
                SET health_check_interval = %s,
                    circuit_breaker_threshold = %s,
                    circuit_breaker_timeout = %s,
                    load_balancer_type = %s,
                    updated_at = %s
                WHERE service_id = %s
                """

                await self.db_manager.execute(query, (
                    registry.health_check_interval,
                    registry.circuit_breaker_threshold,
                    registry.circuit_breaker_timeout,
                    registry.load_balancer_type.value,
                    datetime.utcnow(),
                    service_id
                ))

            logger.debug("Updated service registry in database")

        except Exception as e:
            logger.error(f"Failed to update service registry: {e}")

    async def _update_load_balancer_metrics(self, balancer: LoadBalancer) -> bool:
        """Update load balancer metrics. Returns True if updated, False if no change."""
        try:
            query = """
            UPDATE load_balancers
            SET instances = %s, updated_at = %s
            WHERE balancer_id = %s
            """

            instances_json = json.dumps([asdict(inst)
                                        for inst in balancer.instances])

            # Check if there's actually a change before updating
            current_instances = await self._get_current_balancer_instances(balancer.balancer_id)
            if current_instances == instances_json:
                return False  # No change, don't log

            await self.db_manager.execute(query, (
                instances_json,
                datetime.utcnow(),
                balancer.balancer_id
            ))

            # Only log if there was an actual change
            logger.debug(f"Updated load balancer metrics for {balancer.balancer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update load balancer metrics: {e}")
            return False

    async def _get_current_balancer_instances(self, balancer_id: str) -> str:
        """Get current instances JSON for a load balancer."""
        try:
            query = "SELECT instances FROM load_balancers WHERE balancer_id = %s"
            result = await self.db_manager.fetch_one(query, (balancer_id,))
            return result['instances'] if result else '[]'
        except Exception:
            return '[]'

    async def _update_circuit_breaker_state(self, breaker: CircuitBreaker):
        """Update circuit breaker state."""
        try:
            await self._update_circuit_breaker_db(breaker)
            logger.debug(
                f"Updated circuit breaker state for {breaker.breaker_id}")

        except Exception as e:
            logger.error(f"Failed to update circuit breaker state: {e}")

    async def _check_deployment_updates(self):
        """Check for deployment updates."""
        try:
            # Check for any pending deployments
            query = """
            SELECT deployment_id, status FROM deployment_history
            WHERE status IN ('pending', 'in_progress')
            ORDER BY started_at DESC
            """

            pending_deployments = await self.db_manager.fetch_all(query)

            for deployment in pending_deployments:
                logger.info(
                    f"Found pending deployment: {deployment['deployment_id']}")
                # In a real implementation, this would trigger deployment execution

        except Exception as e:
            logger.error(f"Failed to check deployment updates: {e}")
