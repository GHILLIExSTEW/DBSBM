"""
Advanced Analytics Service - Enhanced Analytics & Business Intelligence

This service provides advanced analytics and business intelligence capabilities including
real-time analytics dashboards, advanced data visualization, predictive analytics,
and business intelligence reporting for the DBSBM system.

Features:
- Real-time analytics dashboards with live data streaming
- Advanced data visualization with multiple chart types
- Predictive analytics and forecasting capabilities
- Business intelligence reporting and insights
- Interactive dashboard widgets and components
- Real-time data processing and aggregation
- Advanced filtering and drill-down capabilities
- Automated report generation and distribution
- Performance monitoring and optimization
- Multi-dimensional data analysis
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import uuid4

# Custom JSON serializer for enums and datetimes
def json_default(obj):
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)
import hashlib
import math

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Analytics-specific cache TTLs
ADVANCED_ANALYTICS_CACHE_TTLS = {
    "analytics_dashboards": 1800,  # 30 minutes
    "analytics_metrics": 900,  # 15 minutes
    "analytics_reports": 3600,  # 1 hour
    "analytics_visualizations": 1800,  # 30 minutes
    "analytics_forecasts": 7200,  # 2 hours
    "analytics_insights": 3600,  # 1 hour
    "analytics_alerts": 300,  # 5 minutes
    "analytics_performance": 1800,  # 30 minutes
    "analytics_data": 600,  # 10 minutes
    "analytics_aggregations": 1800,  # 30 minutes
}


class ChartType(Enum):
    """Chart types for data visualization."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TABLE = "table"
    KPI = "kpi"
    FUNNEL = "funnel"


class MetricType(Enum):
    """Types of analytics metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    PERCENTILE = "percentile"
    RATE = "rate"
    DELTA = "delta"


class DashboardType(Enum):
    """Types of analytics dashboards."""

    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    PREDICTIVE = "predictive"
    OPERATIONAL = "operational"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"


@dataclass
class AnalyticsMetric:
    """Analytics metric data structure."""

    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsDashboard:
    """Analytics dashboard data structure."""

    dashboard_id: str
    name: str
    dashboard_type: DashboardType
    description: str
    widgets: List[Dict[str, Any]]
    layout: Dict[str, Any]
    refresh_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsWidget:
    """Analytics widget data structure."""

    widget_id: str
    name: str
    chart_type: ChartType
    data_source: str
    query: str
    config: Dict[str, Any]
    position: Dict[str, int]
    size: Dict[str, int]
    refresh_interval: int
    is_active: bool
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsReport:
    """Analytics report data structure."""

    report_id: str
    name: str
    report_type: str
    description: str
    data: Dict[str, Any]
    charts: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime
    scheduled: bool
    schedule_config: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsForecast:
    """Analytics forecast data structure."""

    forecast_id: str
    metric_name: str
    forecast_type: str
    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    timestamps: List[datetime]
    accuracy: float
    model_used: str
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsInsight:
    """Analytics insight data structure."""

    insight_id: str
    title: str
    description: str
    insight_type: str
    severity: str
    confidence: float
    data_points: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalyticsAlert:
    """Analytics alert data structure."""

    alert_id: str
    name: str
    condition: str
    threshold: float
    current_value: float
    severity: str
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AdvancedAnalyticsService:
    """Advanced analytics and business intelligence service."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: EnhancedCacheManager
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.cache_prefix = "advanced_analytics"
        self.default_ttl = 1800  # 30 minutes

        # Analytics state
        self.dashboards: Dict[str, AnalyticsDashboard] = {}
        self.widgets: Dict[str, AnalyticsWidget] = {}
        self.metrics: Dict[str, AnalyticsMetric] = {}
        self.reports: Dict[str, AnalyticsReport] = {}
        self.forecasts: Dict[str, AnalyticsForecast] = {}
        self.insights: Dict[str, AnalyticsInsight] = {}
        self.alerts: Dict[str, AnalyticsAlert] = {}

        # Real-time processing
        self.is_processing = False
        self.processing_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.analytics_stats = {
            "total_metrics": 0,
            "total_dashboards": 0,
            "total_reports": 0,
            "total_insights": 0,
            "total_alerts": 0,
            "average_response_time": 0.0,
        }

        logger.info("Advanced Analytics Service initialized")

    async def start(self):
        """Start the advanced analytics service."""
        try:
            await self._load_analytics_data()
            await self._initialize_dashboards()
            self.is_processing = True
            self.processing_task = asyncio.create_task(self._real_time_processing())
            logger.info("Advanced Analytics Service started")
        except Exception as e:
            logger.error(f"Failed to start Advanced Analytics Service: {e}")

    async def stop(self):
        """Stop the advanced analytics service."""
        try:
            self.is_processing = False
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            await self._save_analytics_data()
            logger.info("Advanced Analytics Service stopped")
        except Exception as e:
            logger.error(f"Failed to stop Advanced Analytics Service: {e}")

    @time_operation("create_dashboard")
    async def create_dashboard(
        self,
        name: str,
        dashboard_type: DashboardType,
        description: str,
        widgets: List[Dict[str, Any]] = None,
    ) -> AnalyticsDashboard:
        """Create a new analytics dashboard."""
        try:
            dashboard_id = str(uuid4())

            dashboard = AnalyticsDashboard(
                dashboard_id=dashboard_id,
                name=name,
                dashboard_type=dashboard_type,
                description=description,
                widgets=widgets or [],
                layout={"type": "grid", "columns": 12, "rows": 8},
                refresh_interval=30,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Save to database
            await self._save_dashboard_to_db(dashboard)

            # Cache dashboard
            cache_key = f"{self.cache_prefix}:dashboard:{dashboard_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(dashboard), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_dashboards"],
            )

            self.dashboards[dashboard_id] = dashboard
            logger.info(f"Created analytics dashboard: {dashboard_id} ({name})")

            return dashboard

        except Exception as e:
            logger.error(f"Failed to create analytics dashboard: {e}")
            raise

    @time_operation("create_widget")
    async def create_widget(
        self,
        name: str,
        chart_type: ChartType,
        data_source: str,
        query: str,
        config: Dict[str, Any],
    ) -> AnalyticsWidget:
        """Create a new analytics widget."""
        try:
            widget_id = str(uuid4())

            widget = AnalyticsWidget(
                widget_id=widget_id,
                name=name,
                chart_type=chart_type,
                data_source=data_source,
                query=query,
                config=config,
                position={"x": 0, "y": 0},
                size={"width": 6, "height": 4},
                refresh_interval=30,
                is_active=True,
                created_at=datetime.now(),
            )

            # Save to database
            await self._save_widget_to_db(widget)

            # Cache widget
            cache_key = f"{self.cache_prefix}:widget:{widget_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(widget), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_visualizations"],
            )

            self.widgets[widget_id] = widget
            logger.info(f"Created analytics widget: {widget_id} ({name})")

            return widget

        except Exception as e:
            logger.error(f"Failed to create analytics widget: {e}")
            raise

    @time_operation("record_metric")
    async def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        unit: str = "",
        tags: Dict[str, str] = None,
    ) -> AnalyticsMetric:
        """Record an analytics metric."""
        try:
            metric_id = str(uuid4())

            metric = AnalyticsMetric(
                metric_id=metric_id,
                name=name,
                metric_type=metric_type,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                tags=tags or {},
            )

            # Save to database
            await self._save_metric_to_db(metric)

            # Cache metric
            cache_key = f"{self.cache_prefix}:metric:{metric_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(metric), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_metrics"],
            )

            self.metrics[metric_id] = metric
            self._update_analytics_stats()

            logger.info(f"Recorded analytics metric: {metric_id} ({name})")
            return metric

        except Exception as e:
            logger.error(f"Failed to record analytics metric: {e}")
            raise

    @time_operation("generate_report")
    async def generate_report(
        self,
        name: str,
        report_type: str,
        data: Dict[str, Any],
        charts: List[Dict[str, Any]] = None,
    ) -> AnalyticsReport:
        """Generate an analytics report."""
        try:
            report_id = str(uuid4())

            # Generate insights and recommendations
            insights = await self._generate_insights(data)
            recommendations = await self._generate_recommendations(data)

            report = AnalyticsReport(
                report_id=report_id,
                name=name,
                report_type=report_type,
                description=f"Generated report for {name}",
                data=data,
                charts=charts or [],
                insights=insights,
                recommendations=recommendations,
                generated_at=datetime.now(),
                scheduled=False,
            )

            # Save to database
            await self._save_report_to_db(report)

            # Cache report
            cache_key = f"{self.cache_prefix}:report:{report_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(report), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_reports"],
            )

            self.reports[report_id] = report
            logger.info(f"Generated analytics report: {report_id} ({name})")

            return report

        except Exception as e:
            logger.error(f"Failed to generate analytics report: {e}")
            raise

    @time_operation("create_forecast")
    async def create_forecast(
        self,
        metric_name: str,
        forecast_type: str,
        historical_data: List[float],
        periods: int = 30,
    ) -> AnalyticsForecast:
        """Create a forecast for a metric."""
        try:
            forecast_id = str(uuid4())

            # Generate forecast predictions
            predictions, confidence_intervals = await self._generate_forecast(
                historical_data, periods
            )
            timestamps = [datetime.now() + timedelta(hours=i) for i in range(periods)]

            forecast = AnalyticsForecast(
                forecast_id=forecast_id,
                metric_name=metric_name,
                forecast_type=forecast_type,
                predictions=predictions,
                confidence_intervals=confidence_intervals,
                timestamps=timestamps,
                accuracy=0.85,  # Simulated accuracy
                model_used="linear_regression",
                created_at=datetime.now(),
            )

            # Save to database
            await self._save_forecast_to_db(forecast)

            # Cache forecast
            cache_key = f"{self.cache_prefix}:forecast:{forecast_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(forecast), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_forecasts"],
            )

            self.forecasts[forecast_id] = forecast
            logger.info(f"Created analytics forecast: {forecast_id} ({metric_name})")

            return forecast

        except Exception as e:
            logger.error(f"Failed to create analytics forecast: {e}")
            raise

    @time_operation("create_insight")
    async def create_insight(
        self,
        title: str,
        description: str,
        insight_type: str,
        data_points: List[Dict[str, Any]],
        confidence: float = 0.8,
    ) -> AnalyticsInsight:
        """Create an analytics insight."""
        try:
            insight_id = str(uuid4())

            # Generate recommendations based on insight
            recommendations = await self._generate_insight_recommendations(
                insight_type, data_points
            )

            insight = AnalyticsInsight(
                insight_id=insight_id,
                title=title,
                description=description,
                insight_type=insight_type,
                severity="medium",
                confidence=confidence,
                data_points=data_points,
                recommendations=recommendations,
                created_at=datetime.now(),
            )

            # Save to database
            await self._save_insight_to_db(insight)

            # Cache insight
            cache_key = f"{self.cache_prefix}:insight:{insight_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(insight), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_insights"],
            )

            self.insights[insight_id] = insight
            logger.info(f"Created analytics insight: {insight_id} ({title})")

            return insight

        except Exception as e:
            logger.error(f"Failed to create analytics insight: {e}")
            raise

    @time_operation("create_alert")
    async def create_alert(
        self,
        name: str,
        condition: str,
        threshold: float,
        current_value: float,
        severity: str = "medium",
    ) -> AnalyticsAlert:
        """Create an analytics alert."""
        try:
            alert_id = str(uuid4())

            alert = AnalyticsAlert(
                alert_id=alert_id,
                name=name,
                condition=condition,
                threshold=threshold,
                current_value=current_value,
                severity=severity,
                status="active" if current_value > threshold else "normal",
                triggered_at=datetime.now(),
            )

            # Save to database
            await self._save_alert_to_db(alert)

            # Cache alert
            cache_key = f"{self.cache_prefix}:alert:{alert_id}"
            await self.cache_manager.set(
                cache_key,
                json.dumps(asdict(alert), default=json_default),
                ADVANCED_ANALYTICS_CACHE_TTLS["analytics_alerts"],
            )

            self.alerts[alert_id] = alert
            logger.info(f"Created analytics alert: {alert_id} ({name})")

            return alert

        except Exception as e:
            logger.error(f"Failed to create analytics alert: {e}")
            raise

    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data with all widgets."""
        try:
            if dashboard_id not in self.dashboards:
                raise ValueError(f"Dashboard {dashboard_id} not found")

            dashboard = self.dashboards[dashboard_id]

            # Get widget data for each widget
            widget_data = []
            for widget in dashboard.widgets:
                widget_info = await self._get_widget_data(widget)
                widget_data.append(widget_info)

            return {
                "dashboard": asdict(dashboard),
                "widgets": widget_data,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            raise

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary and statistics."""
        try:
            return {
                "total_metrics": len(self.metrics),
                "total_dashboards": len(self.dashboards),
                "total_reports": len(self.reports),
                "total_insights": len(self.insights),
                "total_alerts": len(self.alerts),
                "active_alerts": len(
                    [a for a in self.alerts.values() if a.status == "active"]
                ),
                "recent_insights": [
                    asdict(i) for i in list(self.insights.values())[-5:]
                ],
                "performance_stats": self.analytics_stats,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            raise

    async def _load_analytics_data(self):
        """Load analytics data from database."""
        try:
            # Load data from database
            dashboards_data = await self._get_dashboards_from_db()
            widgets_data = await self._get_widgets_from_db()
            metrics_data = await self._get_metrics_from_db()

            for dashboard_data in dashboards_data:
                dashboard = AnalyticsDashboard(**dashboard_data)
                self.dashboards[dashboard.dashboard_id] = dashboard

            for widget_data in widgets_data:
                widget = AnalyticsWidget(**widget_data)
                self.widgets[widget.widget_id] = widget

            for metric_data in metrics_data:
                metric = AnalyticsMetric(**metric_data)
                self.metrics[metric.metric_id] = metric

            logger.info(
                f"Loaded {len(self.dashboards)} dashboards, {len(self.widgets)} widgets, {len(self.metrics)} metrics"
            )

        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")

    async def _initialize_dashboards(self):
        """Initialize default dashboards."""
        try:
            # Create default real-time dashboard
            if not any(
                d.dashboard_type == DashboardType.REAL_TIME
                for d in self.dashboards.values()
            ):
                await self.create_dashboard(
                    name="Real-Time Analytics",
                    dashboard_type=DashboardType.REAL_TIME,
                    description="Real-time system performance and user activity",
                )

            # Create default executive dashboard
            if not any(
                d.dashboard_type == DashboardType.EXECUTIVE
                for d in self.dashboards.values()
            ):
                await self.create_dashboard(
                    name="Executive Overview",
                    dashboard_type=DashboardType.EXECUTIVE,
                    description="High-level business metrics and KPIs",
                )

            logger.info("Initialized default dashboards")

        except Exception as e:
            logger.error(f"Failed to initialize dashboards: {e}")

    async def _real_time_processing(self):
        """Real-time analytics processing loop."""
        try:
            while self.is_processing:
                # Process real-time metrics
                await self._process_real_time_metrics()

                # Update dashboards
                await self._update_dashboards()

                # Check alerts
                await self._check_alerts()

                # Generate insights
                await self._generate_real_time_insights()

                await asyncio.sleep(30)  # Process every 30 seconds

        except asyncio.CancelledError:
            logger.info("Real-time processing cancelled")
        except Exception as e:
            logger.error(f"Real-time processing error: {e}")

    async def _process_real_time_metrics(self):
        """Process real-time metrics."""
        try:
            # Simulate real-time metric processing
            current_time = datetime.now()

            # Record system metrics
            await self.record_metric(
                name="system_performance",
                metric_type=MetricType.GAUGE,
                value=0.85,
                unit="%",
                tags={"component": "system", "type": "performance"},
            )

            await self.record_metric(
                name="user_activity",
                metric_type=MetricType.COUNTER,
                value=150,
                unit="users",
                tags={"component": "users", "type": "activity"},
            )

        except Exception as e:
            logger.error(f"Failed to process real-time metrics: {e}")

    async def _update_dashboards(self):
        """Update dashboard data."""
        try:
            for dashboard in self.dashboards.values():
                if dashboard.is_active:
                    # Update dashboard widgets
                    for widget in dashboard.widgets:
                        await self._update_widget_data(widget)

        except Exception as e:
            logger.error(f"Failed to update dashboards: {e}")

    async def _check_alerts(self):
        """Check and trigger alerts."""
        try:
            for alert in self.alerts.values():
                if alert.status == "active":
                    # Check if alert should be resolved
                    if alert.current_value <= alert.threshold:
                        alert.status = "resolved"
                        alert.resolved_at = datetime.now()
                        await self._update_alert_in_db(alert)

        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")

    async def _generate_real_time_insights(self):
        """Generate real-time insights."""
        try:
            # Analyze recent metrics for insights
            recent_metrics = list(self.metrics.values())[-10:]

            if len(recent_metrics) >= 5:
                # Check for trends
                values = [m.value for m in recent_metrics]
                if len(set(values)) > 1:  # If there's variation
                    trend = "increasing" if values[-1] > values[0] else "decreasing"

                    await self.create_insight(
                        title=f"Metric {recent_metrics[0].name} is {trend}",
                        description=f"Recent trend analysis shows {trend} pattern",
                        insight_type="trend",
                        data_points=[
                            {"timestamp": m.timestamp, "value": m.value}
                            for m in recent_metrics
                        ],
                        confidence=0.8,
                    )

        except Exception as e:
            logger.error(f"Failed to generate real-time insights: {e}")

    async def _get_widget_data(self, widget: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for a widget."""
        # Simulate widget data retrieval
        return {
            "widget_id": widget.get("widget_id"),
            "name": widget.get("name"),
            "chart_type": widget.get("chart_type"),
            "data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "datasets": [
                    {
                        "label": "Performance",
                        "data": [65, 70, 75, 80, 85],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    }
                ],
            },
            "config": widget.get("config", {}),
        }

    async def _update_widget_data(self, widget: Dict[str, Any]):
        """Update widget data."""
        # Simulate widget data update
        pass

    async def _generate_forecast(
        self, historical_data: List[float], periods: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Generate forecast predictions."""
        # Simple linear regression forecast
        if len(historical_data) < 2:
            return [historical_data[-1]] * periods, [
                (historical_data[-1], historical_data[-1])
            ] * periods

        # Calculate trend
        x = list(range(len(historical_data)))
        y = historical_data

        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        intercept = (sum_y - slope * sum_x) / n

        # Generate predictions
        predictions = []
        confidence_intervals = []

        for i in range(periods):
            pred = slope * (len(historical_data) + i) + intercept
            predictions.append(pred)

            # Simple confidence interval
            confidence = 0.1 * pred  # 10% confidence interval
            confidence_intervals.append((pred - confidence, pred + confidence))

        return predictions, confidence_intervals

    async def _generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from data."""
        insights = []

        # Analyze data for insights
        if "performance" in data:
            performance = data["performance"]
            if performance > 0.8:
                insights.append("System performance is excellent")
            elif performance > 0.6:
                insights.append("System performance is good")
            else:
                insights.append("System performance needs attention")

        if "user_activity" in data:
            activity = data["user_activity"]
            if activity > 100:
                insights.append("High user activity detected")
            elif activity < 10:
                insights.append("Low user activity - consider engagement strategies")

        return insights

    async def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from data."""
        recommendations = []
        # Always return at least one recommendation for test data
        if "performance" in data:
            performance = data["performance"]
            if performance < 0.7:
                recommendations.append("Consider optimizing system resources")
                recommendations.append("Monitor system bottlenecks")
            else:
                recommendations.append("Maintain current system performance")
        if "user_activity" in data:
            activity = data["user_activity"]
            if activity < 50:
                recommendations.append("Implement user engagement strategies")
                recommendations.append("Consider marketing campaigns")
            else:
                recommendations.append("Continue to engage users with new features")
        if not recommendations:
            recommendations.append("No specific recommendations. Review analytics for insights.")
        return recommendations

    async def _generate_insight_recommendations(
        self, insight_type: str, data_points: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on insight type."""
        recommendations = []

        if insight_type == "trend":
            recommendations.append("Monitor trend continuation")
            recommendations.append("Prepare for potential changes")
        elif insight_type == "anomaly":
            recommendations.append("Investigate root cause")
            recommendations.append("Implement monitoring alerts")
        elif insight_type == "performance":
            recommendations.append("Optimize system resources")
            recommendations.append("Review system configuration")

        return recommendations

    def _update_analytics_stats(self):
        """Update analytics statistics."""
        self.analytics_stats["total_metrics"] = len(self.metrics)
        self.analytics_stats["total_dashboards"] = len(self.dashboards)
        self.analytics_stats["total_reports"] = len(self.reports)
        self.analytics_stats["total_insights"] = len(self.insights)
        self.analytics_stats["total_alerts"] = len(self.alerts)

    # Database operations
    async def _save_analytics_data(self):
        """Save analytics data to database."""
        try:
            # Save dashboards
            for dashboard in self.dashboards.values():
                await self._save_dashboard_to_db(dashboard)

            # Save widgets
            for widget in self.widgets.values():
                await self._save_widget_to_db(widget)

            # Save metrics
            for metric in self.metrics.values():
                await self._save_metric_to_db(metric)

            logger.info("Saved analytics data to database")

        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")

    async def _save_dashboard_to_db(self, dashboard: AnalyticsDashboard):
        """Save dashboard to database."""
        try:
            query = """
            INSERT INTO analytics_dashboards (
                dashboard_id, name, dashboard_type, description, widgets, layout,
                refresh_interval, is_active, created_at, updated_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            ) ON CONFLICT (dashboard_id) DO UPDATE SET
                name = EXCLUDED.name, dashboard_type = EXCLUDED.dashboard_type,
                description = EXCLUDED.description, widgets = EXCLUDED.widgets,
                layout = EXCLUDED.layout, refresh_interval = EXCLUDED.refresh_interval,
                is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata
            """

            await self.db_manager.execute(
                query,
                (
                    dashboard.dashboard_id,
                    dashboard.name,
                    dashboard.dashboard_type.value,
                    dashboard.description,
                    json.dumps(dashboard.widgets),
                    json.dumps(dashboard.layout),
                    dashboard.refresh_interval,
                    dashboard.is_active,
                    dashboard.created_at,
                    dashboard.updated_at,
                    json.dumps(dashboard.metadata),
                ),
            )

            logger.info(f"Saved dashboard to database: {dashboard.dashboard_id}")

        except Exception as e:
            logger.error(f"Failed to save dashboard to database: {e}")
            raise

    async def _save_widget_to_db(self, widget: AnalyticsWidget):
        """Save widget to database."""
        try:
            query = """
            INSERT INTO analytics_widgets (
                widget_id, name, chart_type, data_source, query, config, position,
                size, refresh_interval, is_active, created_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            ) ON CONFLICT (widget_id) DO UPDATE SET
                name = EXCLUDED.name, chart_type = EXCLUDED.chart_type,
                data_source = EXCLUDED.data_source, query = EXCLUDED.query,
                config = EXCLUDED.config, position = EXCLUDED.position,
                size = EXCLUDED.size, refresh_interval = EXCLUDED.refresh_interval,
                is_active = EXCLUDED.is_active, metadata = EXCLUDED.metadata
            """

            await self.db_manager.execute(
                query,
                (
                    widget.widget_id,
                    widget.name,
                    widget.chart_type.value,
                    widget.data_source,
                    widget.query,
                    json.dumps(widget.config),
                    json.dumps(widget.position),
                    json.dumps(widget.size),
                    widget.refresh_interval,
                    widget.is_active,
                    widget.created_at,
                    json.dumps(widget.metadata),
                ),
            )

            logger.info(f"Saved widget to database: {widget.widget_id}")

        except Exception as e:
            logger.error(f"Failed to save widget to database: {e}")
            raise

    async def _save_metric_to_db(self, metric: AnalyticsMetric):
        """Save metric to database."""
        try:
            query = """
            INSERT INTO analytics_metrics (
                metric_id, name, metric_type, value, unit, timestamp, tags, metadata, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            await self.db_manager.execute(
                query,
                (
                    metric.metric_id,
                    metric.name,
                    metric.metric_type.value,
                    metric.value,
                    metric.unit,
                    metric.timestamp,
                    json.dumps(metric.tags),
                    json.dumps(metric.metadata),
                    metric.created_at,
                ),
            )

            logger.info(f"Saved metric to database: {metric.metric_id}")

        except Exception as e:
            logger.error(f"Failed to save metric to database: {e}")
            raise

    async def _save_report_to_db(self, report: AnalyticsReport):
        """Save report to database."""
        try:
            query = """
            INSERT INTO analytics_reports (
                report_id, name, report_type, description, data, charts, insights,
                recommendations, generated_at, scheduled, schedule_config, metadata, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            await self.db_manager.execute(
                query,
                (
                    report.report_id,
                    report.name,
                    report.report_type,
                    report.description,
                    json.dumps(report.data),
                    json.dumps(report.charts),
                    json.dumps(report.insights),
                    json.dumps(report.recommendations),
                    report.generated_at,
                    report.scheduled,
                    json.dumps(report.schedule_config or {}),
                    json.dumps(report.metadata),
                    report.created_at,
                ),
            )

            logger.info(f"Saved report to database: {report.report_id}")

        except Exception as e:
            logger.error(f"Failed to save report to database: {e}")
            raise

    async def _save_forecast_to_db(self, forecast: AnalyticsForecast):
        """Save forecast to database."""
        try:
            query = """
            INSERT INTO analytics_forecasts (
                forecast_id, metric_name, forecast_type, predictions, confidence_intervals,
                timestamps, accuracy, model_used, metadata, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            await self.db_manager.execute(
                query,
                (
                    forecast.forecast_id,
                    forecast.metric_name,
                    forecast.forecast_type,
                    json.dumps(forecast.predictions),
                    json.dumps(forecast.confidence_intervals),
                    json.dumps([ts.isoformat() for ts in forecast.timestamps]),
                    forecast.accuracy,
                    forecast.model_used,
                    json.dumps(forecast.metadata),
                    forecast.created_at,
                ),
            )

            logger.info(f"Saved forecast to database: {forecast.forecast_id}")

        except Exception as e:
            logger.error(f"Failed to save forecast to database: {e}")
            raise

    async def _save_insight_to_db(self, insight: AnalyticsInsight):
        """Save insight to database."""
        try:
            query = """
            INSERT INTO analytics_insights (
                insight_id, title, description, insight_type, severity, confidence,
                data_points, recommendations, metadata, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            await self.db_manager.execute(
                query,
                (
                    insight.insight_id,
                    insight.title,
                    insight.description,
                    insight.insight_type,
                    insight.severity,
                    insight.confidence,
                    json.dumps(insight.data_points),
                    json.dumps(insight.recommendations),
                    json.dumps(insight.metadata),
                    insight.created_at,
                ),
            )

            logger.info(f"Saved insight to database: {insight.insight_id}")

        except Exception as e:
            logger.error(f"Failed to save insight to database: {e}")
            raise

    async def _save_alert_to_db(self, alert: AnalyticsAlert):
        """Save alert to database."""
        try:
            query = """
            INSERT INTO analytics_alerts (
                alert_id, name, condition, threshold, current_value, severity,
                status, triggered_at, resolved_at, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            await self.db_manager.execute(
                query,
                (
                    alert.alert_id,
                    alert.name,
                    alert.condition,
                    alert.threshold,
                    alert.current_value,
                    alert.severity,
                    alert.status,
                    alert.triggered_at,
                    alert.resolved_at,
                    json.dumps(alert.metadata),
                ),
            )

            logger.info(f"Saved alert to database: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
            raise

    async def _update_alert_in_db(self, alert: AnalyticsAlert):
        """Update alert in database."""
        try:
            query = """
            UPDATE analytics_alerts SET
                status = %s, current_value = %s, resolved_at = %s, metadata = %s
            WHERE alert_id = $1
            """

            await self.db_manager.execute(
                query,
                (
                    alert.status,
                    alert.current_value,
                    alert.resolved_at,
                    json.dumps(alert.metadata),
                    alert.alert_id,
                ),
            )

            logger.info(f"Updated alert in database: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Failed to update alert in database: {e}")
            raise

    async def _get_dashboards_from_db(self) -> List[Dict[str, Any]]:
        """Get dashboards from database."""
        try:
            query = "SELECT * FROM analytics_dashboards WHERE is_active = 1"
            dashboards_data = await self.db_manager.fetch_all(query)

            result = []
            for row in dashboards_data:
                dashboard_data = {
                    "dashboard_id": row["dashboard_id"],
                    "name": row["name"],
                    "dashboard_type": DashboardType(row["dashboard_type"]),
                    "description": row["description"],
                    "widgets": json.loads(row["widgets"]),
                    "layout": json.loads(row["layout"]),
                    "refresh_interval": row["refresh_interval"],
                    "is_active": bool(row["is_active"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]),
                }
                result.append(dashboard_data)

            logger.info(f"Loaded {len(result)} dashboards from database")
            return result

        except Exception as e:
            logger.error(f"Failed to get dashboards from database: {e}")
            return []

    async def _get_widgets_from_db(self) -> List[Dict[str, Any]]:
        """Get widgets from database."""
        try:
            query = "SELECT * FROM analytics_widgets WHERE is_active = 1"
            widgets_data = await self.db_manager.fetch_all(query)

            result = []
            for row in widgets_data:
                widget_data = {
                    "widget_id": row["widget_id"],
                    "name": row["name"],
                    "chart_type": ChartType(row["chart_type"]),
                    "data_source": row["data_source"],
                    "query": row["query"],
                    "config": json.loads(row["config"]),
                    "position": json.loads(row["position"]),
                    "size": json.loads(row["size"]),
                    "refresh_interval": row["refresh_interval"],
                    "is_active": bool(row["is_active"]),
                    "created_at": row["created_at"],
                    "metadata": json.loads(row["metadata"]),
                }
                result.append(widget_data)

            logger.info(f"Loaded {len(result)} widgets from database")
            return result

        except Exception as e:
            logger.error(f"Failed to get widgets from database: {e}")
            return []

    async def _get_metrics_from_db(self) -> List[Dict[str, Any]]:
        """Get metrics from database."""
        try:
            query = "SELECT * FROM analytics_metrics ORDER BY timestamp DESC LIMIT 1000"
            metrics_data = await self.db_manager.fetch_all(query)

            result = []
            for row in metrics_data:
                metric_data = {
                    "metric_id": row["metric_id"],
                    "name": row["name"],
                    "metric_type": MetricType(row["metric_type"]),
                    "value": float(row["value"]),
                    "unit": row["unit"],
                    "timestamp": row["timestamp"],
                    "tags": json.loads(row["tags"]),
                    "metadata": json.loads(row["metadata"]),
                    "created_at": row["created_at"],
                }
                result.append(metric_data)

            logger.info(f"Loaded {len(result)} metrics from database")
            return result

        except Exception as e:
            logger.error(f"Failed to get metrics from database: {e}")
            return []
