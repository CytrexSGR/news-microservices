import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import redis
import json
import structlog
from app.core.config import settings
from app.core.resilience import get_resilient_client, CircuitBreakerOpenError
from app.models.analytics import AnalyticsMetric
from app.schemas.analytics import MetricCreate, OverviewResponse, ServiceMetrics

logger = structlog.get_logger()


class MetricsService:
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def collect_service_metrics(self, service_url: str, service_name: str) -> Dict[str, Any]:
        """Collect metrics from a service with resilience patterns"""
        try:
            # Get resilient client for this service
            client = get_resilient_client(
                service_name=service_name,
                timeout=5.0
            )

            response = await client.get(f"{service_url}/health")

            if response.status_code == 200:
                health_data = response.json()
                return {
                    "service": service_name,
                    "status": health_data.get("status", "unknown"),
                    "uptime": health_data.get("uptime", 0),
                    "metrics": health_data.get("metrics", {})
                }
            else:
                logger.warning(
                    "service_health_check_failed",
                    service=service_name,
                    status_code=response.status_code
                )
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }

        except CircuitBreakerOpenError as e:
            logger.warning(
                "service_circuit_breaker_open",
                service=service_name,
                error=str(e)
            )
            return {
                "service": service_name,
                "status": "circuit_open",
                "error": "Circuit breaker is open"
            }
        except Exception as e:
            logger.error(
                "service_health_check_error",
                service=service_name,
                error=str(e),
                exc_info=True
            )
            return {
                "service": service_name,
                "status": "error",
                "error": str(e)
            }

    async def store_metric(self, metric: MetricCreate) -> AnalyticsMetric:
        """Store a metric in database"""
        db_metric = AnalyticsMetric(
            service=metric.service,
            metric_name=metric.metric_name,
            value=metric.value,
            unit=metric.unit,
            labels=metric.labels,
            timestamp=metric.timestamp or datetime.utcnow()
        )
        self.db.add(db_metric)
        self.db.commit()
        self.db.refresh(db_metric)

        # Cache recent metric
        cache_key = f"metric:{metric.service}:{metric.metric_name}:latest"
        self.redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps({
                "value": metric.value,
                "timestamp": db_metric.timestamp.isoformat()
            })
        )

        return db_metric

    async def get_overview(self) -> OverviewResponse:
        """Get system-wide analytics overview"""
        cache_key = "analytics:overview"
        cached = self.redis_client.get(cache_key)

        if cached:
            return OverviewResponse(**json.loads(cached))

        # Calculate overview from recent metrics
        services_data = {}
        service_urls = {
            "auth-service": settings.AUTH_SERVICE_URL,
            "feed-service": settings.FEED_SERVICE_URL,
            "content-analysis-service": settings.ANALYSIS_SERVICE_URL,
            "research-service": settings.RESEARCH_SERVICE_URL,
            "osint-service": settings.OSINT_SERVICE_URL,
            "notification-service": settings.NOTIFICATION_SERVICE_URL,
            "search-service": settings.SEARCH_SERVICE_URL
        }

        # Single aggregated query for all services (replaces 28 individual queries)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        service_names = list(service_urls.keys())

        agg_results = self.db.query(
            AnalyticsMetric.service,
            AnalyticsMetric.metric_name,
            func.sum(AnalyticsMetric.value).label('sum_value'),
            func.avg(AnalyticsMetric.value).label('avg_value'),
            func.max(AnalyticsMetric.value).label('max_value'),
        ).filter(
            and_(
                AnalyticsMetric.service.in_(service_names),
                AnalyticsMetric.metric_name.in_(["requests_total", "errors_total", "latency_ms", "active_users"]),
                AnalyticsMetric.timestamp >= one_hour_ago
            )
        ).group_by(AnalyticsMetric.service, AnalyticsMetric.metric_name).all()

        # Build lookup: {service_name: {metric_name: {sum, avg, max}}}
        metric_lookup = {}
        for row in agg_results:
            if row.service not in metric_lookup:
                metric_lookup[row.service] = {}
            metric_lookup[row.service][row.metric_name] = {
                'sum': float(row.sum_value or 0),
                'avg': float(row.avg_value or 0),
                'max': float(row.max_value or 0),
            }

        for service_name, service_url in service_urls.items():
            metrics = await self.collect_service_metrics(service_url, service_name)

            svc_metrics = metric_lookup.get(service_name, {})
            total_requests = svc_metrics.get("requests_total", {}).get('sum', 0)
            errors = svc_metrics.get("errors_total", {}).get('sum', 0)
            avg_latency = svc_metrics.get("latency_ms", {}).get('avg', 0)
            active_users = svc_metrics.get("active_users", {}).get('max', 0)

            services_data[service_name] = ServiceMetrics(
                total_requests=int(total_requests),
                error_rate=errors / total_requests if total_requests > 0 else 0.0,
                avg_latency_ms=float(avg_latency),
                active_users=int(active_users)
            )

        # Calculate system health
        avg_error_rate = sum(s.error_rate for s in services_data.values()) / len(services_data)
        system_health = "healthy" if avg_error_rate < 0.01 else "degraded" if avg_error_rate < 0.05 else "unhealthy"

        overview = OverviewResponse(
            timestamp=datetime.utcnow(),
            services=services_data,
            system_health=system_health,
            active_alerts=0,  # Will be implemented with alerts
            total_users=sum(s.active_users for s in services_data.values()),
            total_articles=0  # Will be fetched from feed service
        )

        # Cache for 30 seconds
        self.redis_client.setex(cache_key, 30, overview.model_dump_json())

        return overview

    async def get_service_metrics(
        self,
        service_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metric_names: Optional[List[str]] = None
    ) -> List[AnalyticsMetric]:
        """Get metrics for a specific service"""
        query = self.db.query(AnalyticsMetric).filter(
            AnalyticsMetric.service == service_name
        )

        if start_date:
            query = query.filter(AnalyticsMetric.timestamp >= start_date)
        if end_date:
            query = query.filter(AnalyticsMetric.timestamp <= end_date)
        if metric_names:
            query = query.filter(AnalyticsMetric.metric_name.in_(metric_names))

        return query.order_by(AnalyticsMetric.timestamp.desc()).all()

    async def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        retention_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)

        deleted = self.db.query(AnalyticsMetric).filter(
            AnalyticsMetric.timestamp < retention_date
        ).delete()

        self.db.commit()
        return deleted
