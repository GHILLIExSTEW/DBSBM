"""
BI Service for DBSBM System.
Provides business intelligence and reporting capabilities.
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# BI-specific cache TTLs
BI_CACHE_TTLS = {
    'bi_reports': 3600,            # 1 hour
    'bi_dashboards': 1800,          # 30 minutes
    'bi_metrics': 900,              # 15 minutes
    'bi_analytics': 7200,           # 2 hours
    'bi_insights': 3600,            # 1 hour
    'bi_forecasts': 1800,           # 30 minutes
    'bi_exports': 600,              # 10 minutes
    'bi_schedules': 3600,           # 1 hour
    'bi_alerts': 300,               # 5 minutes
    'bi_performance': 1800,         # 30 minutes
}

class ReportType(Enum):
    """BI report types."""
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_ANALYSIS = "weekly_analysis"
    MONTHLY_REPORT = "monthly_report"
    QUARTERLY_REVIEW = "quarterly_review"
    CUSTOM_REPORT = "custom_report"

class DashboardType(Enum):
    """BI dashboard types."""
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    ANALYTICAL = "analytical"
    CUSTOM = "custom"

class MetricType(Enum):
    """BI metric types."""
    REVENUE = "revenue"
    USERS = "users"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    CUSTOM = "custom"

@dataclass
class BIReport:
    """BI report configuration."""
    id: int
    tenant_id: int
    name: str
    report_type: ReportType
    parameters: Dict[str, Any]
    schedule: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class BIDashboard:
    """BI dashboard configuration."""
    id: int
    tenant_id: int
    name: str
    dashboard_type: DashboardType
    widgets: List[Dict[str, Any]]
    layout: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class BIMetric:
    """BI metric definition."""
    id: int
    tenant_id: int
    name: str
    metric_type: MetricType
    calculation: str
    parameters: Dict[str, Any]
    is_active: bool
    created_at: datetime

@dataclass
class BIAnalytics:
    """BI analytics result."""
    id: int
    tenant_id: int
    analysis_type: str
    data: Dict[str, Any]
    insights: List[str]
    created_at: datetime

class BIService:
    """BI service for business intelligence and reporting."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = BI_CACHE_TTLS

        # Background tasks
        self.report_generation_task = None
        self.analytics_task = None
        self.is_running = False

    async def start(self):
        """Start the BI service."""
        try:
            self.is_running = True
            self.report_generation_task = asyncio.create_task(self._generate_scheduled_reports())
            self.analytics_task = asyncio.create_task(self._run_analytics())
            logger.info("BI service started successfully")
        except Exception as e:
            logger.error(f"Failed to start BI service: {e}")
            raise

    async def stop(self):
        """Stop the BI service."""
        self.is_running = False
        if self.report_generation_task:
            self.report_generation_task.cancel()
        if self.analytics_task:
            self.analytics_task.cancel()
        logger.info("BI service stopped")

    @time_operation("bi_create_report")
    async def create_report(self, tenant_id: int, name: str, report_type: ReportType,
                          parameters: Dict[str, Any], schedule: Optional[str] = None) -> Optional[BIReport]:
        """Create a new BI report."""
        try:
            query = """
            INSERT INTO bi_reports (tenant_id, name, report_type, parameters, schedule,
                                   is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :report_type, :parameters, :schedule,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'name': name,
                'report_type': report_type.value,
                'parameters': json.dumps(parameters),
                'schedule': schedule
            })

            report_id = result.lastrowid

            # Get created report
            report = await self.get_report_by_id(report_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"bi_reports:{tenant_id}:*")

            record_metric("bi_reports_created", 1)
            return report

        except Exception as e:
            logger.error(f"Failed to create BI report: {e}")
            return None

    @time_operation("bi_get_report")
    async def get_report_by_id(self, report_id: int) -> Optional[BIReport]:
        """Get BI report by ID."""
        try:
            # Try to get from cache first
            cache_key = f"bi_report:{report_id}"
            cached_report = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_report:
                return BIReport(**cached_report)

            # Get from database
            query = """
            SELECT * FROM bi_reports WHERE id = :report_id
            """

            result = await self.db_manager.fetch_one(query, {'report_id': report_id})

            if not result:
                return None

            report = BIReport(
                id=result['id'],
                tenant_id=result['tenant_id'],
                name=result['name'],
                report_type=ReportType(result['report_type']),
                parameters=json.loads(result['parameters']) if result['parameters'] else {},
                schedule=result['schedule'],
                is_active=result['is_active'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache report
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': report.id,
                    'tenant_id': report.tenant_id,
                    'name': report.name,
                    'report_type': report.report_type.value,
                    'parameters': report.parameters,
                    'schedule': report.schedule,
                    'is_active': report.is_active,
                    'created_at': report.created_at.isoformat(),
                    'updated_at': report.updated_at.isoformat()
                },
                ttl=self.cache_ttls['bi_reports']
            )

            return report

        except Exception as e:
            logger.error(f"Failed to get BI report: {e}")
            return None

    @time_operation("bi_get_reports")
    async def get_reports_by_tenant(self, tenant_id: int, report_type: Optional[ReportType] = None) -> List[BIReport]:
        """Get BI reports for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"bi_reports:{tenant_id}:{report_type.value if report_type else 'all'}"
            cached_reports = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_reports:
                return [BIReport(**report) for report in cached_reports]

            # Build query
            query = "SELECT * FROM bi_reports WHERE tenant_id = :tenant_id"
            params = {'tenant_id': tenant_id}

            if report_type:
                query += " AND report_type = :report_type"
                params['report_type'] = report_type.value

            results = await self.db_manager.fetch_all(query, params)

            reports = []
            for row in results:
                report = BIReport(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    name=row['name'],
                    report_type=ReportType(row['report_type']),
                    parameters=json.loads(row['parameters']) if row['parameters'] else {},
                    schedule=row['schedule'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                reports.append(report)

            # Cache reports
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': r.id,
                    'tenant_id': r.tenant_id,
                    'name': r.name,
                    'report_type': r.report_type.value,
                    'parameters': r.parameters,
                    'schedule': r.schedule,
                    'is_active': r.is_active,
                    'created_at': r.created_at.isoformat(),
                    'updated_at': r.updated_at.isoformat()
                } for r in reports],
                ttl=self.cache_ttls['bi_reports']
            )

            return reports

        except Exception as e:
            logger.error(f"Failed to get BI reports: {e}")
            return []

    @time_operation("bi_generate_report")
    async def generate_report(self, report_id: int, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Generate a BI report."""
        try:
            # Get report configuration
            report = await self.get_report_by_id(report_id)
            if not report:
                return None

            # Try to get from cache first
            cache_key = f"bi_report_data:{report_id}:{hashlib.md5(str(parameters).encode()).hexdigest()}"
            cached_data = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_data:
                return cached_data

            # Generate report data based on type
            report_data = await self._generate_report_data(report, parameters or {})

            # Cache report data
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                report_data,
                ttl=self.cache_ttls['bi_reports']
            )

            record_metric("bi_reports_generated", 1)
            return report_data

        except Exception as e:
            logger.error(f"Failed to generate BI report: {e}")
            return None

    @time_operation("bi_create_dashboard")
    async def create_dashboard(self, tenant_id: int, name: str, dashboard_type: DashboardType,
                             widgets: List[Dict[str, Any]], layout: Dict[str, Any]) -> Optional[BIDashboard]:
        """Create a new BI dashboard."""
        try:
            query = """
            INSERT INTO bi_dashboards (tenant_id, name, dashboard_type, widgets, layout,
                                      is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :dashboard_type, :widgets, :layout,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'name': name,
                'dashboard_type': dashboard_type.value,
                'widgets': json.dumps(widgets),
                'layout': json.dumps(layout)
            })

            dashboard_id = result.lastrowid

            # Get created dashboard
            dashboard = await self.get_dashboard_by_id(dashboard_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"bi_dashboards:{tenant_id}:*")

            record_metric("bi_dashboards_created", 1)
            return dashboard

        except Exception as e:
            logger.error(f"Failed to create BI dashboard: {e}")
            return None

    @time_operation("bi_get_dashboard")
    async def get_dashboard_by_id(self, dashboard_id: int) -> Optional[BIDashboard]:
        """Get BI dashboard by ID."""
        try:
            # Try to get from cache first
            cache_key = f"bi_dashboard:{dashboard_id}"
            cached_dashboard = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_dashboard:
                return BIDashboard(**cached_dashboard)

            # Get from database
            query = """
            SELECT * FROM bi_dashboards WHERE id = :dashboard_id
            """

            result = await self.db_manager.fetch_one(query, {'dashboard_id': dashboard_id})

            if not result:
                return None

            dashboard = BIDashboard(
                id=result['id'],
                tenant_id=result['tenant_id'],
                name=result['name'],
                dashboard_type=DashboardType(result['dashboard_type']),
                widgets=json.loads(result['widgets']) if result['widgets'] else [],
                layout=json.loads(result['layout']) if result['layout'] else {},
                is_active=result['is_active'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache dashboard
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': dashboard.id,
                    'tenant_id': dashboard.tenant_id,
                    'name': dashboard.name,
                    'dashboard_type': dashboard.dashboard_type.value,
                    'widgets': dashboard.widgets,
                    'layout': dashboard.layout,
                    'is_active': dashboard.is_active,
                    'created_at': dashboard.created_at.isoformat(),
                    'updated_at': dashboard.updated_at.isoformat()
                },
                ttl=self.cache_ttls['bi_dashboards']
            )

            return dashboard

        except Exception as e:
            logger.error(f"Failed to get BI dashboard: {e}")
            return None

    @time_operation("bi_get_dashboards")
    async def get_dashboards_by_tenant(self, tenant_id: int, dashboard_type: Optional[DashboardType] = None) -> List[BIDashboard]:
        """Get BI dashboards for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"bi_dashboards:{tenant_id}:{dashboard_type.value if dashboard_type else 'all'}"
            cached_dashboards = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_dashboards:
                return [BIDashboard(**dashboard) for dashboard in cached_dashboards]

            # Build query
            query = "SELECT * FROM bi_dashboards WHERE tenant_id = :tenant_id"
            params = {'tenant_id': tenant_id}

            if dashboard_type:
                query += " AND dashboard_type = :dashboard_type"
                params['dashboard_type'] = dashboard_type.value

            results = await self.db_manager.fetch_all(query, params)

            dashboards = []
            for row in results:
                dashboard = BIDashboard(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    name=row['name'],
                    dashboard_type=DashboardType(row['dashboard_type']),
                    widgets=json.loads(row['widgets']) if row['widgets'] else [],
                    layout=json.loads(row['layout']) if row['layout'] else {},
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                dashboards.append(dashboard)

            # Cache dashboards
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': d.id,
                    'tenant_id': d.tenant_id,
                    'name': d.name,
                    'dashboard_type': d.dashboard_type.value,
                    'widgets': d.widgets,
                    'layout': d.layout,
                    'is_active': d.is_active,
                    'created_at': d.created_at.isoformat(),
                    'updated_at': d.updated_at.isoformat()
                } for d in dashboards],
                ttl=self.cache_ttls['bi_dashboards']
            )

            return dashboards

        except Exception as e:
            logger.error(f"Failed to get BI dashboards: {e}")
            return []

    @time_operation("bi_create_metric")
    async def create_metric(self, tenant_id: int, name: str, metric_type: MetricType,
                          calculation: str, parameters: Dict[str, Any]) -> Optional[BIMetric]:
        """Create a new BI metric."""
        try:
            query = """
            INSERT INTO bi_metrics (tenant_id, name, metric_type, calculation, parameters,
                                   is_active, created_at)
            VALUES (:tenant_id, :name, :metric_type, :calculation, :parameters,
                    1, NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'name': name,
                'metric_type': metric_type.value,
                'calculation': calculation,
                'parameters': json.dumps(parameters)
            })

            metric_id = result.lastrowid

            # Get created metric
            metric = await self.get_metric_by_id(metric_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"bi_metrics:{tenant_id}:*")

            record_metric("bi_metrics_created", 1)
            return metric

        except Exception as e:
            logger.error(f"Failed to create BI metric: {e}")
            return None

    @time_operation("bi_get_metric")
    async def get_metric_by_id(self, metric_id: int) -> Optional[BIMetric]:
        """Get BI metric by ID."""
        try:
            # Try to get from cache first
            cache_key = f"bi_metric:{metric_id}"
            cached_metric = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_metric:
                return BIMetric(**cached_metric)

            # Get from database
            query = """
            SELECT * FROM bi_metrics WHERE id = :metric_id
            """

            result = await self.db_manager.fetch_one(query, {'metric_id': metric_id})

            if not result:
                return None

            metric = BIMetric(
                id=result['id'],
                tenant_id=result['tenant_id'],
                name=result['name'],
                metric_type=MetricType(result['metric_type']),
                calculation=result['calculation'],
                parameters=json.loads(result['parameters']) if result['parameters'] else {},
                is_active=result['is_active'],
                created_at=result['created_at']
            )

            # Cache metric
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': metric.id,
                    'tenant_id': metric.tenant_id,
                    'name': metric.name,
                    'metric_type': metric.metric_type.value,
                    'calculation': metric.calculation,
                    'parameters': metric.parameters,
                    'is_active': metric.is_active,
                    'created_at': metric.created_at.isoformat()
                },
                ttl=self.cache_ttls['bi_metrics']
            )

            return metric

        except Exception as e:
            logger.error(f"Failed to get BI metric: {e}")
            return None

    @time_operation("bi_calculate_metric")
    async def calculate_metric(self, metric_id: int, parameters: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """Calculate a BI metric value."""
        try:
            # Get metric configuration
            metric = await self.get_metric_by_id(metric_id)
            if not metric:
                return None

            # Try to get from cache first
            cache_key = f"bi_metric_value:{metric_id}:{hashlib.md5(str(parameters).encode()).hexdigest()}"
            cached_value = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_value is not None:
                return cached_value

            # Calculate metric value
            value = await self._calculate_metric_value(metric, parameters or {})

            # Cache metric value
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                value,
                ttl=self.cache_ttls['bi_metrics']
            )

            return value

        except Exception as e:
            logger.error(f"Failed to calculate BI metric: {e}")
            return None

    @time_operation("bi_get_analytics")
    async def get_analytics(self, tenant_id: int, analysis_type: str, parameters: Dict[str, Any]) -> Optional[BIAnalytics]:
        """Get BI analytics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"bi_analytics:{tenant_id}:{analysis_type}:{hashlib.md5(str(parameters).encode()).hexdigest()}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return BIAnalytics(**cached_analytics)

            # Generate analytics
            analytics_data = await self._generate_analytics(tenant_id, analysis_type, parameters)

            # Create analytics record
            query = """
            INSERT INTO bi_analytics (tenant_id, analysis_type, data, insights, created_at)
            VALUES (:tenant_id, :analysis_type, :data, :insights, NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'analysis_type': analysis_type,
                'data': json.dumps(analytics_data['data']),
                'insights': json.dumps(analytics_data['insights'])
            })

            analytics_id = result.lastrowid

            analytics = BIAnalytics(
                id=analytics_id,
                tenant_id=tenant_id,
                analysis_type=analysis_type,
                data=analytics_data['data'],
                insights=analytics_data['insights'],
                created_at=datetime.utcnow()
            )

            # Cache analytics
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': analytics.id,
                    'tenant_id': analytics.tenant_id,
                    'analysis_type': analytics.analysis_type,
                    'data': analytics.data,
                    'insights': analytics.insights,
                    'created_at': analytics.created_at.isoformat()
                },
                ttl=self.cache_ttls['bi_analytics']
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get BI analytics: {e}")
            return None

    async def clear_bi_cache(self):
        """Clear all BI-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("bi_reports:*")
            await self.cache_manager.clear_cache_by_pattern("bi_dashboards:*")
            await self.cache_manager.clear_cache_by_pattern("bi_metrics:*")
            await self.cache_manager.clear_cache_by_pattern("bi_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("bi_insights:*")
            await self.cache_manager.clear_cache_by_pattern("bi_forecasts:*")
            await self.cache_manager.clear_cache_by_pattern("bi_exports:*")
            await self.cache_manager.clear_cache_by_pattern("bi_schedules:*")
            await self.cache_manager.clear_cache_by_pattern("bi_alerts:*")
            await self.cache_manager.clear_cache_by_pattern("bi_performance:*")
            logger.info("BI cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear BI cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get BI service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
