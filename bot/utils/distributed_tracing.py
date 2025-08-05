"""
Distributed Tracing System for DBSBM using OpenTelemetry.
Provides comprehensive request tracing across all services and components.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.span import Span
    from opentelemetry.context import Context
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.mysql import MySQLInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    Status = None
    StatusCode = None
    Span = None
    Context = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    Resource = None
    AsyncioInstrumentor = None
    AioHttpClientInstrumentor = None
    MySQLInstrumentor = None
    RedisInstrumentor = None

from utils.enhanced_cache_manager import EnhancedCacheManager

logger = logging.getLogger(__name__)


class TraceLevel(Enum):
    """Trace levels for different types of operations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TraceSpan:
    """Represents a trace span."""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "ok"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    user_id: Optional[int] = None
    guild_id: Optional[int] = None
    service_name: str = "dbsbm"


@dataclass
class TraceContext:
    """Trace context for propagating trace information."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    user_id: Optional[int] = None
    guild_id: Optional[int] = None
    service_name: str = "dbsbm"


class DistributedTracing:
    """Comprehensive distributed tracing system using OpenTelemetry."""

    def __init__(self, service_name: str = "dbsbm", enable_console_export: bool = True):
        """Initialize the distributed tracing system."""
        self.service_name = service_name
        self.cache_manager = EnhancedCacheManager()

        # Trace storage
        self.traces: Dict[str, List[TraceSpan]] = {}
        self.active_spans: Dict[str, TraceSpan] = {}

        # Configuration
        self.enabled = OPENTELEMETRY_AVAILABLE
        self.sampling_rate = 1.0  # 100% sampling
        self.max_trace_duration = timedelta(hours=24)

        # OpenTelemetry setup
        if self.enabled:
            self._setup_opentelemetry(enable_console_export)
        else:
            logger.warning("OpenTelemetry not available. Tracing will be disabled.")

        logger.info(f"Distributed tracing initialized for service: {service_name}")

    def _setup_opentelemetry(self, enable_console_export: bool = True) -> None:
        """Set up OpenTelemetry tracing."""
        try:
            # Create tracer provider
            resource = Resource.create({"service.name": self.service_name})
            provider = TracerProvider(resource=resource)

            # Add console exporter for development
            if enable_console_export:
                console_exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(console_exporter))

            # Set the global tracer provider
            trace.set_tracer_provider(provider)

            # Get the tracer
            self.tracer = trace.get_tracer(self.service_name)

            # Instrument libraries
            AsyncioInstrumentor().instrument()
            AioHttpClientInstrumentor().instrument()
            MySQLInstrumentor().instrument()
            RedisInstrumentor().instrument()

            logger.info("OpenTelemetry tracing setup completed")

        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            self.enabled = False

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        trace_level: TraceLevel = TraceLevel.MEDIUM,
    ) -> str:
        """Start a new trace span."""
        if not self.enabled:
            return str(uuid.uuid4())

        try:
            # Create span attributes
            span_attributes = attributes or {}
            if user_id:
                span_attributes["user.id"] = user_id
            if guild_id:
                span_attributes["guild.id"] = guild_id
            span_attributes["trace.level"] = trace_level.value

            # Start span with OpenTelemetry
            span = self.tracer.start_span(name, attributes=span_attributes)
            span_id = str(span.get_span_context().span_id)
            trace_id = str(span.get_span_context().trace_id)

            # Create trace span record
            trace_span = TraceSpan(
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=None,  # Will be set by context
                name=name,
                start_time=datetime.now(),
                attributes=span_attributes,
                user_id=user_id,
                guild_id=guild_id,
                service_name=self.service_name,
            )

            # Store active span
            self.active_spans[span_id] = trace_span

            # Store in trace collection
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            self.traces[trace_id].append(trace_span)

            return span_id

        except Exception as e:
            logger.error(f"Failed to start span: {e}")
            return str(uuid.uuid4())

    def end_span(
        self,
        span_id: str,
        status: str = "ok",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End a trace span."""
        if not self.enabled or span_id not in self.active_spans:
            return

        try:
            # Get the span
            span = trace.get_current_span()
            if span:
                # Set status
                if status == "error":
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))

                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # End the span
                span.end()

            # Update trace span record
            trace_span = self.active_spans[span_id]
            trace_span.end_time = datetime.now()
            trace_span.duration_ms = (
                trace_span.end_time - trace_span.start_time
            ).total_seconds() * 1000
            trace_span.status = status

            if attributes:
                trace_span.attributes.update(attributes)

            # Remove from active spans
            del self.active_spans[span_id]

        except Exception as e:
            logger.error(f"Failed to end span: {e}")

    def add_event(
        self, span_id: str, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an event to a span."""
        if not self.enabled or span_id not in self.active_spans:
            return

        try:
            # Add event to OpenTelemetry span
            span = trace.get_current_span()
            if span:
                span.add_event(name, attributes or {})

            # Add event to trace span record
            trace_span = self.active_spans[span_id]
            event = {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
            trace_span.events.append(event)

        except Exception as e:
            logger.error(f"Failed to add event to span: {e}")

    def add_attribute(self, span_id: str, key: str, value: Any) -> None:
        """Add an attribute to a span."""
        if not self.enabled or span_id not in self.active_spans:
            return

        try:
            # Add attribute to OpenTelemetry span
            span = trace.get_current_span()
            if span:
                span.set_attribute(key, value)

            # Add attribute to trace span record
            trace_span = self.active_spans[span_id]
            trace_span.attributes[key] = value

        except Exception as e:
            logger.error(f"Failed to add attribute to span: {e}")

    @asynccontextmanager
    async def trace_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        trace_level: TraceLevel = TraceLevel.MEDIUM,
    ):
        """Context manager for tracing spans."""
        span_id = self.start_span(name, attributes, user_id, guild_id, trace_level)
        try:
            yield span_id
        except Exception as e:
            self.add_attribute(span_id, "error", str(e))
            self.end_span(span_id, "error")
            raise
        else:
            self.end_span(span_id, "ok")

    def trace_function(
        self, name: Optional[str] = None, trace_level: TraceLevel = TraceLevel.MEDIUM
    ):
        """Decorator to trace function execution."""

        def decorator(func):
            func_name = name or func.__name__

            async def async_wrapper(*args, **kwargs):
                # Extract user_id and guild_id from kwargs
                user_id = kwargs.get("user_id")
                guild_id = kwargs.get("guild_id")

                async with self.trace_span(
                    func_name,
                    user_id=user_id,
                    guild_id=guild_id,
                    trace_level=trace_level,
                ):
                    return await func(*args, **kwargs)

            def sync_wrapper(*args, **kwargs):
                # Extract user_id and guild_id from kwargs
                user_id = kwargs.get("user_id")
                guild_id = kwargs.get("guild_id")

                span_id = self.start_span(
                    func_name,
                    user_id=user_id,
                    guild_id=guild_id,
                    trace_level=trace_level,
                )
                try:
                    result = func(*args, **kwargs)
                    self.end_span(span_id, "ok")
                    return result
                except Exception as e:
                    self.add_attribute(span_id, "error", str(e))
                    self.end_span(span_id, "error")
                    raise

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def get_trace_context(self) -> Optional[TraceContext]:
        """Get current trace context."""
        if not self.enabled:
            return None

        try:
            span = trace.get_current_span()
            if span:
                context = span.get_span_context()
                return TraceContext(
                    trace_id=str(context.trace_id),
                    span_id=str(context.span_id),
                    service_name=self.service_name,
                )
        except Exception as e:
            logger.error(f"Failed to get trace context: {e}")

        return None

    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for propagation."""
        if not self.enabled:
            return headers

        try:
            context = trace.get_current_span().get_span_context()
            headers["X-Trace-ID"] = str(context.trace_id)
            headers["X-Span-ID"] = str(context.span_id)
            headers["X-Service-Name"] = self.service_name
        except Exception as e:
            logger.error(f"Failed to inject trace context: {e}")

        return headers

    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from headers."""
        if not self.enabled:
            return None

        try:
            trace_id = headers.get("X-Trace-ID")
            span_id = headers.get("X-Span-ID")
            service_name = headers.get("X-Service-Name", self.service_name)

            if trace_id and span_id:
                return TraceContext(
                    trace_id=trace_id, span_id=span_id, service_name=service_name
                )
        except Exception as e:
            logger.error(f"Failed to extract trace context: {e}")

        return None

    def get_trace_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a trace."""
        if trace_id not in self.traces:
            return None

        spans = self.traces[trace_id]
        if not spans:
            return None

        # Calculate trace statistics
        start_time = min(span.start_time for span in spans)
        end_time = max(span.end_time or span.start_time for span in spans)
        total_duration = (end_time - start_time).total_seconds() * 1000

        successful_spans = sum(1 for span in spans if span.status == "ok")
        error_spans = len(spans) - successful_spans

        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_ms": total_duration,
            "successful_spans": successful_spans,
            "error_spans": error_spans,
            "success_rate": (successful_spans / len(spans)) * 100 if spans else 0,
            "spans": [
                {
                    "span_id": span.span_id,
                    "name": span.name,
                    "start_time": span.start_time.isoformat(),
                    "end_time": span.end_time.isoformat() if span.end_time else None,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "attributes": span.attributes,
                    "events": span.events,
                }
                for span in spans
            ],
        }

    def get_recent_traces(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent traces."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_traces = []

        for trace_id, spans in self.traces.items():
            # Check if any span in the trace is recent
            if any(span.start_time >= cutoff_time for span in spans):
                summary = self.get_trace_summary(trace_id)
                if summary:
                    recent_traces.append(summary)

        return recent_traces

    async def export_traces(self, file_path: str, hours: int = 24) -> bool:
        """Export traces to a JSON file."""
        try:
            traces = self.get_recent_traces(hours)

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "service_name": self.service_name,
                "trace_count": len(traces),
                "traces": traces,
            }

            with open(file_path, "w") as f:
                import json

                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Traces exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export traces: {e}")
            return False

    def cleanup_old_traces(self) -> int:
        """Clean up old traces to prevent memory issues."""
        cutoff_time = datetime.now() - self.max_trace_duration
        removed_count = 0

        for trace_id in list(self.traces.keys()):
            spans = self.traces[trace_id]
            # Check if all spans in the trace are old
            if all(span.start_time < cutoff_time for span in spans):
                del self.traces[trace_id]
                removed_count += 1

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old traces")

        return removed_count

    def get_tracing_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        total_spans = sum(len(spans) for spans in self.traces.values())
        active_spans = len(self.active_spans)

        return {
            "enabled": self.enabled,
            "service_name": self.service_name,
            "trace_count": len(self.traces),
            "total_spans": total_spans,
            "active_spans": active_spans,
            "sampling_rate": self.sampling_rate,
        }


# Global distributed tracing instance
distributed_tracing = DistributedTracing()


def trace_function(
    name: Optional[str] = None, trace_level: TraceLevel = TraceLevel.MEDIUM
):
    """Decorator to trace function execution."""
    return distributed_tracing.trace_function(name, trace_level)


async def get_distributed_tracing() -> DistributedTracing:
    """Get the global distributed tracing instance."""
    return distributed_tracing
