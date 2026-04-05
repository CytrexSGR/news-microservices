"""Tests for Prometheus Metrics"""
import pytest
from app.core.metrics import MetricsCollector, get_metrics_collector


class TestMetricsCollector:
    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_record_scrape(self, collector):
        # Should not raise
        collector.record_scrape(
            method="newspaper4k",
            status="success",
            domain="example.com",
            duration_seconds=1.5,
            content_size=5000,
            word_count=500
        )

    def test_record_scrape_minimal(self, collector):
        collector.record_scrape(
            method="playwright",
            status="error",
            domain="blocked.com",
            duration_seconds=5.0
        )

    def test_record_quality_score(self, collector):
        collector.record_quality_score("example.com", 0.85)
        collector.record_quality_score("other.com", 0.5)

    def test_record_extraction_completeness(self, collector):
        collector.record_extraction_completeness("newspaper4k", 0.9)
        collector.record_extraction_completeness("trafilatura", 0.7)

    def test_update_dlq_metrics(self, collector):
        stats = {
            "total_entries": 10,
            "by_status": {
                "pending": 5,
                "resolved": 3,
                "abandoned": 2
            },
            "by_failure_reason": {
                "timeout": 4,
                "blocked": 6
            }
        }
        collector.update_dlq_metrics(stats)

    def test_update_dlq_metrics_empty(self, collector):
        collector.update_dlq_metrics({})
        collector.update_dlq_metrics(None)

    def test_record_dlq_retry(self, collector):
        collector.record_dlq_retry("timeout", success=True)
        collector.record_dlq_retry("blocked", success=False)

    def test_update_source_metrics(self, collector):
        collector.update_source_metrics(
            total_profiles=50,
            domain_stats={
                "example.com": {"success_rate": 0.95, "avg_response_time": 250},
                "other.com": {"success_rate": 0.80, "avg_response_time": 500}
            }
        )

    def test_set_browser_contexts(self, collector):
        collector.set_browser_contexts(3)
        collector.set_browser_contexts(0)

    def test_set_http_connections(self, collector):
        collector.set_http_connections(10)

    def test_record_rate_limit_hit(self, collector):
        collector.record_rate_limit_hit("example.com")
        collector.record_rate_limit_hit("example.com")  # Multiple hits

    def test_get_metrics(self, collector):
        # Record some metrics first
        collector.record_scrape(
            method="newspaper4k",
            status="success",
            domain="example.com",
            duration_seconds=1.0
        )

        metrics = collector.get_metrics()
        assert isinstance(metrics, bytes)
        assert len(metrics) > 0
        # Check that it contains expected metric names
        metrics_str = metrics.decode('utf-8')
        assert 'scraper_' in metrics_str

    def test_get_content_type(self, collector):
        content_type = collector.get_content_type()
        assert 'text/plain' in content_type or 'text/openmetrics' in content_type

    def test_singleton_instance(self):
        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2
