"""
Test cases for Advanced Analytics Service
Tests the advanced analytics and business intelligence capabilities.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.advanced_analytics_service import (
    AdvancedAnalyticsService,
    AnalyticsAlert,
    AnalyticsDashboard,
    AnalyticsForecast,
    AnalyticsInsight,
    AnalyticsMetric,
    AnalyticsReport,
    AnalyticsWidget,
    ChartType,
    DashboardType,
    MetricType,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager


class TestAdvancedAnalyticsService:
    """Test cases for Advanced Analytics Service."""

    @pytest.fixture
    async def service(self):
        """Create a test instance of AdvancedAnalyticsService."""
        db_manager = DatabaseManager()
        cache_manager = EnhancedCacheManager()

        # Mock database and cache connections
        with patch.object(db_manager, "connect", new_callable=AsyncMock), patch.object(
            cache_manager, "connect", new_callable=AsyncMock
        ):

            service = AdvancedAnalyticsService(db_manager, cache_manager)
            return service

    def test_chart_type_enum(self):
        """Test ChartType enum values."""
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.PIE.value == "pie"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.AREA.value == "area"
        assert ChartType.HEATMAP.value == "heatmap"
        assert ChartType.GAUGE.value == "gauge"
        assert ChartType.TABLE.value == "table"
        assert ChartType.KPI.value == "kpi"
        assert ChartType.FUNNEL.value == "funnel"

    def test_metric_type_enum(self):
        """Test MetricType enum values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"
        assert MetricType.PERCENTILE.value == "percentile"
        assert MetricType.RATE.value == "rate"
        assert MetricType.DELTA.value == "delta"

    def test_dashboard_type_enum(self):
        """Test DashboardType enum values."""
        assert DashboardType.REAL_TIME.value == "real_time"
        assert DashboardType.HISTORICAL.value == "historical"
        assert DashboardType.PREDICTIVE.value == "predictive"
        assert DashboardType.OPERATIONAL.value == "operational"
        assert DashboardType.EXECUTIVE.value == "executive"
        assert DashboardType.TECHNICAL.value == "technical"

    def test_analytics_metric_dataclass(self):
        """Test AnalyticsMetric dataclass."""
        metric = AnalyticsMetric(
            metric_id="metric-001",
            name="system_performance",
            metric_type=MetricType.GAUGE,
            value=85.5,
            unit="%",
            timestamp=datetime.now(),
            tags={"component": "system", "type": "performance"},
        )

        assert metric.metric_id == "metric-001"
        assert metric.name == "system_performance"
        assert metric.metric_type == MetricType.GAUGE
        assert metric.value == 85.5
        assert metric.unit == "%"
        assert metric.tags == {"component": "system", "type": "performance"}

    def test_analytics_dashboard_dataclass(self):
        """Test AnalyticsDashboard dataclass."""
        dashboard = AnalyticsDashboard(
            dashboard_id="dashboard-001",
            name="Real-Time Analytics",
            dashboard_type=DashboardType.REAL_TIME,
            description="Real-time system performance monitoring",
            widgets=[],
            layout={"type": "grid", "columns": 12, "rows": 8},
            refresh_interval=30,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert dashboard.dashboard_id == "dashboard-001"
        assert dashboard.name == "Real-Time Analytics"
        assert dashboard.dashboard_type == DashboardType.REAL_TIME
        assert dashboard.description == "Real-time system performance monitoring"
        assert dashboard.refresh_interval == 30
        assert dashboard.is_active is True

    def test_analytics_widget_dataclass(self):
        """Test AnalyticsWidget dataclass."""
        widget = AnalyticsWidget(
            widget_id="widget-001",
            name="System Performance",
            chart_type=ChartType.GAUGE,
            data_source="system_metrics",
            query="SELECT AVG(performance) FROM system_metrics",
            config={"min": 0, "max": 100},
            position={"x": 0, "y": 0},
            size={"width": 4, "height": 3},
            refresh_interval=30,
            is_active=True,
            created_at=datetime.now(),
        )

        assert widget.widget_id == "widget-001"
        assert widget.name == "System Performance"
        assert widget.chart_type == ChartType.GAUGE
        assert widget.data_source == "system_metrics"
        assert widget.query == "SELECT AVG(performance) FROM system_metrics"
        assert widget.config == {"min": 0, "max": 100}
        assert widget.refresh_interval == 30
        assert widget.is_active is True

    def test_analytics_report_dataclass(self):
        """Test AnalyticsReport dataclass."""
        report = AnalyticsReport(
            report_id="report-001",
            name="Daily Performance Report",
            report_type="daily",
            description="Daily system performance summary",
            data={"performance": 85.5, "user_activity": 150},
            charts=[],
            insights=["System performance is excellent"],
            recommendations=["Continue monitoring"],
            generated_at=datetime.now(),
            scheduled=False,
        )

        assert report.report_id == "report-001"
        assert report.name == "Daily Performance Report"
        assert report.report_type == "daily"
        assert report.description == "Daily system performance summary"
        assert report.data == {"performance": 85.5, "user_activity": 150}
        assert report.insights == ["System performance is excellent"]
        assert report.recommendations == ["Continue monitoring"]
        assert report.scheduled is False

    def test_analytics_forecast_dataclass(self):
        """Test AnalyticsForecast dataclass."""
        forecast = AnalyticsForecast(
            forecast_id="forecast-001",
            metric_name="user_activity",
            forecast_type="linear_regression",
            predictions=[155, 160, 165, 170],
            confidence_intervals=[[150, 160], [155, 165], [160, 170], [165, 175]],
            timestamps=[datetime.now() for _ in range(4)],
            accuracy=0.85,
            model_used="linear_regression",
            created_at=datetime.now(),
        )

        assert forecast.forecast_id == "forecast-001"
        assert forecast.metric_name == "user_activity"
        assert forecast.forecast_type == "linear_regression"
        assert forecast.predictions == [155, 160, 165, 170]
        assert forecast.confidence_intervals == [
            [150, 160],
            [155, 165],
            [160, 170],
            [165, 175],
        ]
        assert forecast.accuracy == 0.85
        assert forecast.model_used == "linear_regression"

    def test_analytics_insight_dataclass(self):
        """Test AnalyticsInsight dataclass."""
        insight = AnalyticsInsight(
            insight_id="insight-001",
            title="Performance Trending Upward",
            description="System performance has shown consistent improvement",
            insight_type="trend",
            severity="positive",
            confidence=0.85,
            data_points=[{"timestamp": datetime.now(), "value": 85.5}],
            recommendations=["Continue monitoring", "Document improvements"],
            created_at=datetime.now(),
        )

        assert insight.insight_id == "insight-001"
        assert insight.title == "Performance Trending Upward"
        assert (
            insight.description == "System performance has shown consistent improvement"
        )
        assert insight.insight_type == "trend"
        assert insight.severity == "positive"
        assert insight.confidence == 0.85
        assert len(insight.data_points) == 1
        assert len(insight.recommendations) == 2

    def test_analytics_alert_dataclass(self):
        """Test AnalyticsAlert dataclass."""
        alert = AnalyticsAlert(
            alert_id="alert-001",
            name="High Error Rate Alert",
            condition="error_rate > 0.05",
            threshold=0.05,
            current_value=0.025,
            severity="medium",
            status="normal",
            triggered_at=datetime.now(),
        )

        assert alert.alert_id == "alert-001"
        assert alert.name == "High Error Rate Alert"
        assert alert.condition == "error_rate > 0.05"
        assert alert.threshold == 0.05
        assert alert.current_value == 0.025
        assert alert.severity == "medium"
        assert alert.status == "normal"

    @pytest.mark.asyncio
    async def test_create_dashboard(self, service):
        """Test creating an analytics dashboard."""
        with patch.object(
            service, "_save_dashboard_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            dashboard = await service.create_dashboard(
                name="Test Dashboard",
                dashboard_type=DashboardType.REAL_TIME,
                description="Test dashboard for unit testing",
            )

            assert dashboard.name == "Test Dashboard"
            assert dashboard.dashboard_type == DashboardType.REAL_TIME
            assert dashboard.description == "Test dashboard for unit testing"
            assert dashboard.is_active is True
            assert dashboard.refresh_interval == 30

    @pytest.mark.asyncio
    async def test_create_widget(self, service):
        """Test creating an analytics widget."""
        with patch.object(
            service, "_save_widget_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            widget = await service.create_widget(
                name="Test Widget",
                chart_type=ChartType.LINE,
                data_source="test_metrics",
                query="SELECT * FROM test_metrics",
                config={"responsive": True},
            )

            assert widget.name == "Test Widget"
            assert widget.chart_type == ChartType.LINE
            assert widget.data_source == "test_metrics"
            assert widget.query == "SELECT * FROM test_metrics"
            assert widget.config == {"responsive": True}
            assert widget.is_active is True

    @pytest.mark.asyncio
    async def test_record_metric(self, service):
        """Test recording an analytics metric."""
        with patch.object(
            service, "_save_metric_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            metric = await service.record_metric(
                name="test_metric",
                metric_type=MetricType.GAUGE,
                value=85.5,
                unit="%",
                tags={"component": "test"},
            )

            assert metric.name == "test_metric"
            assert metric.metric_type == MetricType.GAUGE
            assert metric.value == 85.5
            assert metric.unit == "%"
            assert metric.tags == {"component": "test"}

    @pytest.mark.asyncio
    async def test_generate_report(self, service):
        """Test generating an analytics report."""
        with patch.object(
            service, "_save_report_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            data = {"performance": 85.5, "user_activity": 150}
            report = await service.generate_report(
                name="Test Report", report_type="daily", data=data
            )

            assert report.name == "Test Report"
            assert report.report_type == "daily"
            assert report.data == data
            assert len(report.insights) > 0
            assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_create_forecast(self, service):
        """Test creating an analytics forecast."""
        with patch.object(
            service, "_save_forecast_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            historical_data = [100, 110, 120, 130, 140]
            forecast = await service.create_forecast(
                metric_name="user_activity",
                forecast_type="linear_regression",
                historical_data=historical_data,
                periods=5,
            )

            assert forecast.metric_name == "user_activity"
            assert forecast.forecast_type == "linear_regression"
            assert len(forecast.predictions) == 5
            assert len(forecast.confidence_intervals) == 5
            assert forecast.accuracy > 0

    @pytest.mark.asyncio
    async def test_create_insight(self, service):
        """Test creating an analytics insight."""
        with patch.object(
            service, "_save_insight_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            data_points = [{"timestamp": datetime.now(), "value": 85.5}]
            insight = await service.create_insight(
                title="Test Insight",
                description="Test insight description",
                insight_type="trend",
                data_points=data_points,
                confidence=0.8,
            )

            assert insight.title == "Test Insight"
            assert insight.description == "Test insight description"
            assert insight.insight_type == "trend"
            assert insight.confidence == 0.8
            assert insight.data_points == data_points
            assert len(insight.recommendations) > 0

    @pytest.mark.asyncio
    async def test_create_alert(self, service):
        """Test creating an analytics alert."""
        with patch.object(
            service, "_save_alert_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            alert = await service.create_alert(
                name="Test Alert",
                condition="value > 100",
                threshold=100.0,
                current_value=85.5,
                severity="medium",
            )

            assert alert.name == "Test Alert"
            assert alert.condition == "value > 100"
            assert alert.threshold == 100.0
            assert alert.current_value == 85.5
            assert alert.severity == "medium"
            assert alert.status == "normal"  # Since current_value < threshold

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, service):
        """Test getting dashboard data."""
        # Create a dashboard first
        with patch.object(
            service, "_save_dashboard_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            dashboard = await service.create_dashboard(
                name="Test Dashboard",
                dashboard_type=DashboardType.REAL_TIME,
                description="Test dashboard",
            )

            # Add dashboard to service
            service.dashboards[dashboard.dashboard_id] = dashboard

            # Test getting dashboard data
            with patch.object(
                service, "_get_widget_data", new_callable=AsyncMock
            ) as mock_widget_data:
                mock_widget_data.return_value = {
                    "widget_id": "test-widget",
                    "name": "Test Widget",
                    "data": {"labels": [], "datasets": []},
                }

                dashboard_data = await service.get_dashboard_data(
                    dashboard.dashboard_id
                )

                assert (
                    dashboard_data["dashboard"]["dashboard_id"]
                    == dashboard.dashboard_id
                )
                assert "last_updated" in dashboard_data

    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, service):
        """Test getting analytics summary."""
        summary = await service.get_analytics_summary()

        assert "total_metrics" in summary
        assert "total_dashboards" in summary
        assert "total_reports" in summary
        assert "total_insights" in summary
        assert "total_alerts" in summary
        assert "active_alerts" in summary
        assert "recent_insights" in summary
        assert "performance_stats" in summary
        assert "last_updated" in summary

    @pytest.mark.asyncio
    async def test_service_start_stop(self, service):
        """Test service start and stop methods."""
        with patch.object(
            service, "_load_analytics_data", new_callable=AsyncMock
        ), patch.object(
            service, "_initialize_dashboards", new_callable=AsyncMock
        ), patch.object(
            service, "_save_analytics_data", new_callable=AsyncMock
        ):

            await service.start()
            await service.stop()

            # Verify methods were called
            service._load_analytics_data.assert_called_once()
            service._initialize_dashboards.assert_called_once()
            service._save_analytics_data.assert_called_once()

    def test_update_analytics_stats(self, service):
        """Test updating analytics statistics."""
        # Add some test data
        service.metrics["metric-1"] = AnalyticsMetric(
            metric_id="metric-1",
            name="test",
            metric_type=MetricType.GAUGE,
            value=1.0,
            unit="",
            timestamp=datetime.now(),
            tags={},
        )
        service.dashboards["dashboard-1"] = AnalyticsDashboard(
            dashboard_id="dashboard-1",
            name="test",
            dashboard_type=DashboardType.REAL_TIME,
            description="",
            widgets=[],
            layout={},
            refresh_interval=30,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service._update_analytics_stats()

        assert service.analytics_stats["total_metrics"] == 1
        assert service.analytics_stats["total_dashboards"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
