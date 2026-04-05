from celery import Task
from datetime import datetime, timedelta
import httpx
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.analytics import AnalyticsMetric


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def collect_metrics_task(self):
    """Collect metrics from all services"""
    service_urls = {
        "auth-service": settings.AUTH_SERVICE_URL,
        "feed-service": settings.FEED_SERVICE_URL,
        "content-analysis-service": settings.ANALYSIS_SERVICE_URL,
        "research-service": settings.RESEARCH_SERVICE_URL,
        "osint-service": settings.OSINT_SERVICE_URL,
        "notification-service": settings.NOTIFICATION_SERVICE_URL,
        "search-service": settings.SEARCH_SERVICE_URL
    }

    collected_count = 0
    timestamp = datetime.utcnow()

    for service_name, service_url in service_urls.items():
        try:
            # Fetch health/metrics endpoint
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{service_url}/health")

                if response.status_code == 200:
                    data = response.json()

                    # Store basic health metric
                    db_metric = AnalyticsMetric(
                        service=service_name,
                        metric_name="service_status",
                        value=1.0 if data.get("status") == "healthy" else 0.0,
                        timestamp=timestamp
                    )
                    self.db.add(db_metric)
                    collected_count += 1

                    # Extract additional metrics if available
                    if "metrics" in data:
                        for metric_name, value in data["metrics"].items():
                            if isinstance(value, (int, float)):
                                db_metric = AnalyticsMetric(
                                    service=service_name,
                                    metric_name=metric_name,
                                    value=float(value),
                                    timestamp=timestamp
                                )
                                self.db.add(db_metric)
                                collected_count += 1

                    # Commit after each service to ensure partial success
                    self.db.commit()

        except Exception as e:
            # Log error but continue with other services
            print(f"Error collecting metrics from {service_name}: {str(e)}")

            # Store error metric
            try:
                error_metric = AnalyticsMetric(
                    service=service_name,
                    metric_name="service_status",
                    value=0.0,
                    labels={"error": str(e)[:100]},
                    timestamp=timestamp
                )
                self.db.add(error_metric)
                self.db.commit()
            except Exception as db_error:
                print(f"Error storing error metric for {service_name}: {str(db_error)}")
                self.db.rollback()

    return {"collected_metrics": collected_count}


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_metrics_task(self):
    """Remove old metrics beyond retention period"""
    retention_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)

    deleted = self.db.query(AnalyticsMetric).filter(
        AnalyticsMetric.timestamp < retention_date
    ).delete()

    self.db.commit()

    return {"deleted_metrics": deleted}


@celery_app.task(base=DatabaseTask, bind=True)
def generate_report_task(self, report_id: int):
    """Generate analytics report"""
    from app.services.report_service import ReportService

    report_service = ReportService(self.db)

    # Use sync version
    report = report_service.generate_report.__wrapped__(
        report_service, report_id
    )

    return {
        "report_id": report.id,
        "status": report.status,
        "file_path": report.file_path
    }
