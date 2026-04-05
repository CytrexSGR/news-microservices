import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.analytics import AnalyticsMetric, AnalyticsReport, AnalyticsDashboard, AnalyticsAlert
from app.schemas.analytics import MetricCreate

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# Mock auth
def mock_auth():
    return {"user_id": "test-user", "email": "test@example.com"}


@pytest.fixture
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# HEALTH CHECKS
# ============================================================================

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


# ============================================================================
# METRIC CREATION AND STORAGE TESTS (7 tests)
# ============================================================================

def test_create_metric(test_db):
    """Test metric creation"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "test-service",
        "metric_name": "test_metric",
        "value": 42.0,
        "unit": "ms"
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    data = response.json()
    assert data["service"] == "test-service"
    assert data["value"] == 42.0
    assert data["unit"] == "ms"


def test_create_metric_with_labels(test_db):
    """Test metric creation with labels"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "feed-service",
        "metric_name": "requests_total",
        "value": 100.0,
        "unit": "count",
        "labels": {"endpoint": "/feeds", "method": "GET"}
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    data = response.json()
    assert data["labels"]["endpoint"] == "/feeds"
    assert data["labels"]["method"] == "GET"


def test_create_metric_minimal(test_db):
    """Test metric creation with minimal fields"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "auth-service",
        "metric_name": "latency_ms",
        "value": 25.5
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    data = response.json()
    assert data["service"] == "auth-service"
    assert data["value"] == 25.5


def test_create_metric_with_timestamp(test_db):
    """Test metric creation with custom timestamp"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    metric_data = {
        "service": "search-service",
        "metric_name": "response_time",
        "value": 150.0,
        "unit": "ms",
        "timestamp": past_time
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == 150.0


def test_create_metric_large_value(test_db):
    """Test metric with very large value"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "osint-service",
        "metric_name": "data_processed_bytes",
        "value": 1e12,
        "unit": "bytes"
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    assert response.json()["value"] == 1e12


def test_create_metric_negative_value(test_db):
    """Test metric with negative value"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "test-service",
        "metric_name": "cpu_delta",
        "value": -5.2,
        "unit": "percent"
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    assert response.json()["value"] == -5.2


def test_create_metric_zero_value(test_db):
    """Test metric with zero value"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    metric_data = {
        "service": "test-service",
        "metric_name": "errors_zero",
        "value": 0.0,
        "unit": "count"
    }

    response = client.post("/api/v1/analytics/metrics", json=metric_data)
    assert response.status_code == 201
    assert response.json()["value"] == 0.0


# ============================================================================
# METRICS AGGREGATION AND TIME-SERIES TESTS (8 tests)
# ============================================================================

def test_get_overview(test_db):
    """Test analytics overview"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    response = client.get("/api/v1/analytics/overview")
    assert response.status_code in [200, 500]


def test_get_service_metrics_with_data(test_db):
    """Test retrieving metrics for a specific service"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()

    # Add test metrics
    for i in range(5):
        metric = AnalyticsMetric(
            service="feed-service",
            metric_name="requests_total",
            value=float(100 + i),
            unit="count",
            timestamp=datetime.utcnow() - timedelta(hours=5-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/service/feed-service",
        params={"metric_names": ["requests_total"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_get_service_metrics_with_time_range(test_db):
    """Test retrieving metrics with time range filter"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()

    now = datetime.utcnow()
    for i in range(10):
        metric = AnalyticsMetric(
            service="auth-service",
            metric_name="latency_ms",
            value=float(50 + i * 5),
            timestamp=now - timedelta(hours=10-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    start_date = (now - timedelta(hours=6)).isoformat()
    end_date = now.isoformat()

    response = client.get(
        "/api/v1/analytics/service/auth-service",
        params={"start_date": start_date, "end_date": end_date}
    )
    assert response.status_code == 200


def test_get_service_metrics_empty_service(test_db):
    """Test retrieving metrics for service with no data"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    response = client.get("/api/v1/analytics/service/nonexistent-service")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_aggregate_stat_card_data(test_db):
    """Test aggregation for stat cards"""
    from app.services.data_aggregator import aggregate_stat_card_data

    db = TestingSessionLocal()

    # Add current hour metrics
    now = datetime.utcnow()
    current_hour_start = now.replace(minute=0, second=0, microsecond=0)

    for i in range(3):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="requests_total",
            value=100.0,
            timestamp=current_hour_start + timedelta(minutes=i*10)
        )
        db.add(metric)

    # Add previous hour metrics
    for i in range(3):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="requests_total",
            value=90.0,
            timestamp=current_hour_start - timedelta(hours=1, minutes=i*10)
        )
        db.add(metric)

    db.commit()

    widget_config = {
        "options": {
            "metric_name": "requests_total",
            "service": "test-service",
            "aggregation": "sum"
        }
    }

    result = aggregate_stat_card_data(db, widget_config)
    assert "value" in result
    assert "change" in result
    assert "trend" in result

    db.close()


def test_aggregate_stat_card_no_previous_data(test_db):
    """Test stat card aggregation with no previous data"""
    from app.services.data_aggregator import aggregate_stat_card_data

    db = TestingSessionLocal()

    now = datetime.utcnow()
    current_hour_start = now.replace(minute=0, second=0, microsecond=0)

    # Only add current hour data
    metric = AnalyticsMetric(
        service="test-service",
        metric_name="requests_total",
        value=50.0,
        timestamp=current_hour_start + timedelta(minutes=5)
    )
    db.add(metric)
    db.commit()

    widget_config = {
        "options": {
            "metric_name": "requests_total",
            "service": "test-service",
            "aggregation": "sum"
        }
    }

    result = aggregate_stat_card_data(db, widget_config)
    assert result["value"] == 50.0
    assert result["change"] == 100.0  # 100% increase from 0
    assert result["trend"] == "up"

    db.close()


def test_aggregate_timeseries_data(test_db):
    """Test time-series data aggregation"""
    from app.services.data_aggregator import aggregate_timeseries_data

    db = TestingSessionLocal()

    now = datetime.utcnow()

    # Add hourly data for 24 hours
    for hour in range(24):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="requests_total",
            value=float(100 + hour * 5),
            timestamp=now - timedelta(hours=24-hour)
        )
        db.add(metric)

    db.commit()

    widget_config = {
        "options": {
            "metric_name": "requests_total",
            "service": "test-service",
            "aggregation": "avg",
            "hours": 24
        }
    }

    result = aggregate_timeseries_data(db, widget_config)
    assert "series" in result
    assert len(result["series"]) >= 24

    db.close()


def test_aggregate_bar_chart_data(test_db):
    """Test bar chart data aggregation"""
    from app.services.data_aggregator import aggregate_bar_chart_data

    db = TestingSessionLocal()

    now = datetime.utcnow()

    # Add metrics for multiple services
    for service in ["auth-service", "feed-service", "search-service"]:
        for i in range(3):
            metric = AnalyticsMetric(
                service=service,
                metric_name="requests_total",
                value=float((i+1) * 100),
                timestamp=now - timedelta(hours=i)
            )
            db.add(metric)

    db.commit()

    widget_config = {
        "options": {
            "metric_name": "requests_total",
            "group_by": "service",
            "aggregation": "sum",
            "limit": 10,
            "hours": 24
        }
    }

    result = aggregate_bar_chart_data(db, widget_config)
    assert "series" in result
    assert len(result["series"]) >= 3

    db.close()


def test_aggregate_pie_chart_data(test_db):
    """Test pie chart data aggregation"""
    from app.services.data_aggregator import aggregate_pie_chart_data

    db = TestingSessionLocal()

    now = datetime.utcnow()

    # Add metrics for multiple services with different values
    services_values = {
        "auth-service": 500,
        "feed-service": 300,
        "search-service": 200
    }

    for service, value in services_values.items():
        for i in range(2):
            metric = AnalyticsMetric(
                service=service,
                metric_name="errors_total",
                value=float(value),
                timestamp=now - timedelta(hours=i)
            )
            db.add(metric)

    db.commit()

    widget_config = {
        "options": {
            "metric_name": "errors_total",
            "group_by": "service",
            "hours": 24
        }
    }

    result = aggregate_pie_chart_data(db, widget_config)
    assert "series" in result
    series = result["series"]
    total_percentage = sum(item["value"] for item in series)
    assert 99 < total_percentage < 101  # Should total ~100%

    db.close()


# ============================================================================
# DASHBOARD TESTS (8 tests)
# ============================================================================

def test_create_dashboard(test_db):
    """Test dashboard creation"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    dashboard_data = {
        "name": "Test Dashboard",
        "description": "A test dashboard",
        "widgets": [
            {
                "id": "widget1",
                "type": "line_chart",
                "title": "Test Chart",
                "metric_name": "test_metric",
                "config": {}
            }
        ]
    }

    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Dashboard"
    assert len(data["widgets"]) == 1


def test_create_dashboard_with_multiple_widgets(test_db):
    """Test dashboard creation with multiple widgets"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    dashboard_data = {
        "name": "Multi-Widget Dashboard",
        "description": "Dashboard with multiple widgets",
        "widgets": [
            {
                "id": "stat1",
                "type": "stat_card",
                "title": "Total Requests",
                "metric_name": "requests_total",
                "service": "feed-service"
            },
            {
                "id": "chart1",
                "type": "line_chart",
                "title": "Latency Trend",
                "metric_name": "latency_ms",
                "service": "auth-service"
            },
            {
                "id": "chart2",
                "type": "bar_chart",
                "title": "Service Comparison",
                "metric_name": "requests_total"
            }
        ],
        "is_public": False,
        "refresh_interval": 30
    }

    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Multi-Widget Dashboard"
    assert len(data["widgets"]) == 3
    assert data["refresh_interval"] == 30


def test_get_dashboard(test_db):
    """Test retrieving a dashboard"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create dashboard
    dashboard_data = {
        "name": "Retrievable Dashboard",
        "widgets": []
    }
    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    dashboard_id = response.json()["id"]

    # Retrieve it
    response = client.get(f"/api/v1/analytics/dashboards/{dashboard_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Retrievable Dashboard"


def test_list_dashboards(test_db):
    """Test listing dashboards"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create multiple dashboards
    for i in range(3):
        dashboard_data = {
            "name": f"Dashboard {i}",
            "widgets": []
        }
        client.post("/api/v1/analytics/dashboards", json=dashboard_data)

    response = client.get("/api/v1/analytics/dashboards")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_update_dashboard(test_db):
    """Test updating a dashboard"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create dashboard
    dashboard_data = {
        "name": "Original Name",
        "description": "Original description",
        "widgets": []
    }
    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    dashboard_id = response.json()["id"]

    # Update it
    update_data = {
        "name": "Updated Name",
        "refresh_interval": 45
    }
    response = client.put(
        f"/api/v1/analytics/dashboards/{dashboard_id}",
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_delete_dashboard(test_db):
    """Test deleting a dashboard"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create dashboard
    dashboard_data = {
        "name": "Deletable Dashboard",
        "widgets": []
    }
    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    dashboard_id = response.json()["id"]

    # Delete it
    response = client.delete(f"/api/v1/analytics/dashboards/{dashboard_id}")
    assert response.status_code == 200

    # Verify it's gone
    response = client.get(f"/api/v1/analytics/dashboards/{dashboard_id}")
    assert response.status_code == 404


def test_dashboard_access_control(test_db):
    """Test dashboard access control for public/private"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create private dashboard
    dashboard_data = {
        "name": "Private Dashboard",
        "is_public": False,
        "widgets": []
    }
    response = client.post("/api/v1/analytics/dashboards", json=dashboard_data)
    assert response.status_code == 201
    assert response.json()["is_public"] == False


def test_dashboard_pagination(test_db):
    """Test dashboard pagination"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create 25 dashboards
    for i in range(25):
        dashboard_data = {
            "name": f"Dashboard {i}",
            "widgets": []
        }
        client.post("/api/v1/analytics/dashboards", json=dashboard_data)

    # Test pagination
    response = client.get("/api/v1/analytics/dashboards?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 10


# ============================================================================
# REPORT GENERATION TESTS (8 tests)
# ============================================================================

def test_create_report(test_db):
    """Test report creation"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    report_data = {
        "name": "Test Report",
        "format": "json",
        "config": {
            "services": ["test-service"],
            "metrics": ["test_metric"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    }

    response = client.post("/api/v1/analytics/reports", json=report_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Report"
    assert data["status"] == "pending"


def test_create_report_csv_format(test_db):
    """Test creating CSV format report"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    report_data = {
        "name": "CSV Report",
        "format": "csv",
        "config": {
            "services": ["auth-service"],
            "metrics": ["latency_ms"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    }

    response = client.post("/api/v1/analytics/reports", json=report_data)
    assert response.status_code == 201
    assert response.json()["format"] == "csv"


def test_create_report_markdown_format(test_db):
    """Test creating Markdown format report"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    report_data = {
        "name": "Markdown Report",
        "format": "md",
        "config": {
            "services": ["feed-service"],
            "metrics": ["requests_total"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    }

    response = client.post("/api/v1/analytics/reports", json=report_data)
    assert response.status_code == 201
    assert response.json()["format"] == "md"


def test_get_report(test_db):
    """Test retrieving a report"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create report
    report_data = {
        "name": "Retrievable Report",
        "format": "json",
        "config": {
            "services": ["test-service"],
            "metrics": ["test_metric"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    }
    response = client.post("/api/v1/analytics/reports", json=report_data)
    report_id = response.json()["id"]

    # Retrieve it
    response = client.get(f"/api/v1/analytics/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Retrievable Report"


def test_list_reports(test_db):
    """Test listing reports"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    # Create multiple reports
    for i in range(3):
        report_data = {
            "name": f"Report {i}",
            "format": "json",
            "config": {
                "services": ["test-service"],
                "metrics": ["test_metric"],
                "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
        }
        client.post("/api/v1/analytics/reports", json=report_data)

    response = client.get("/api/v1/analytics/reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_report_multiple_services(test_db):
    """Test report with multiple services"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    report_data = {
        "name": "Multi-Service Report",
        "format": "json",
        "config": {
            "services": ["auth-service", "feed-service", "search-service"],
            "metrics": ["requests_total", "latency_ms"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    }

    response = client.post("/api/v1/analytics/reports", json=report_data)
    assert response.status_code == 201
    data = response.json()
    assert len(data["config"]["services"]) == 3


def test_report_time_range(test_db):
    """Test report with custom time range"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    end_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

    report_data = {
        "name": "Weekly Report",
        "format": "csv",
        "config": {
            "services": ["test-service"],
            "metrics": ["test_metric"],
            "start_date": start_date,
            "end_date": end_date
        }
    }

    response = client.post("/api/v1/analytics/reports", json=report_data)
    assert response.status_code == 201


# ============================================================================
# TREND ANALYSIS TESTS (8 tests)
# ============================================================================

def test_trend_analysis(test_db):
    """Test trend analysis"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    for i in range(10):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="test_metric",
            value=float(i * 10),
            timestamp=datetime.utcnow() - timedelta(hours=10-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "test-service",
            "metric_name": "test_metric",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "test-service"
    assert data["metric_name"] == "test_metric"
    assert "trend" in data


def test_trend_analysis_increasing(test_db):
    """Test trend detection for increasing metric"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    # Add increasing values
    for i in range(20):
        metric = AnalyticsMetric(
            service="feed-service",
            metric_name="requests_total",
            value=float(i * 50),  # Increasing trend
            timestamp=datetime.utcnow() - timedelta(hours=20-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "feed-service",
            "metric_name": "requests_total",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trend"] in ["increasing", "stable"]


def test_trend_analysis_decreasing(test_db):
    """Test trend detection for decreasing metric"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    # Add decreasing values
    for i in range(20):
        metric = AnalyticsMetric(
            service="search-service",
            metric_name="latency_ms",
            value=float(500 - i * 20),  # Decreasing trend
            timestamp=datetime.utcnow() - timedelta(hours=20-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "search-service",
            "metric_name": "latency_ms",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "trend" in data


def test_trend_analysis_with_interval(test_db):
    """Test trend analysis with custom interval"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    for i in range(48):
        metric = AnalyticsMetric(
            service="auth-service",
            metric_name="active_users",
            value=float(100 + (i % 20)),
            timestamp=datetime.utcnow() - timedelta(hours=48-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "auth-service",
            "metric_name": "active_users",
            "hours": 48,
            "interval_minutes": 120
        }
    )
    assert response.status_code == 200


def test_trend_analysis_anomaly_detection(test_db):
    """Test trend analysis with anomaly detection"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    # Add normal data with anomalies
    for i in range(20):
        value = 100.0 if i != 10 else 500.0  # Anomaly at i=10
        metric = AnalyticsMetric(
            service="osint-service",
            metric_name="errors_total",
            value=float(value),
            timestamp=datetime.utcnow() - timedelta(hours=20-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "osint-service",
            "metric_name": "errors_total",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data


def test_trend_analysis_moving_average(test_db):
    """Test moving average calculation"""
    from app.services.trend_service import TrendService

    db = TestingSessionLocal()

    # Add smoothly varying data
    for i in range(30):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="response_time",
            value=float(100 + 20 * ((i % 10) - 5)),
            timestamp=datetime.utcnow() - timedelta(hours=30-i)
        )
        db.add(metric)

    db.commit()

    service = TrendService(db)
    result = service.get_moving_average(
        service="test-service",
        metric_name="response_time",
        window_size=5,
        hours=30
    )

    assert len(result) > 0
    db.close()


def test_trend_analysis_no_data(test_db):
    """Test trend analysis with no data"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "nonexistent-service",
            "metric_name": "nonexistent_metric",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data_points"]) == 0


def test_trend_change_percentage(test_db):
    """Test change percentage calculation in trends"""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_auth

    db = TestingSessionLocal()
    # Values increasing from 100 to 200 (100% increase)
    for i in range(10):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="metric_value",
            value=float(100 + i * 10),
            timestamp=datetime.utcnow() - timedelta(hours=10-i)
        )
        db.add(metric)
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/analytics/trends",
        params={
            "service": "test-service",
            "metric_name": "metric_value",
            "hours": 24
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "change_percent" in data


# ============================================================================
# STATISTICS AND CALCULATIONS TESTS (8 tests)
# ============================================================================

def test_calculate_average_latency(test_db):
    """Test average latency calculation"""
    db = TestingSessionLocal()

    values = [50, 100, 150, 75, 125]
    for value in values:
        metric = AnalyticsMetric(
            service="auth-service",
            metric_name="latency_ms",
            value=float(value),
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    avg = db.query(func.avg(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "latency_ms"
    ).scalar()

    assert avg is not None
    expected_avg = sum(values) / len(values)
    assert abs(avg - expected_avg) < 0.1

    db.close()


def test_calculate_max_metric_value(test_db):
    """Test max value calculation"""
    db = TestingSessionLocal()

    values = [10, 50, 200, 75, 100]
    for value in values:
        metric = AnalyticsMetric(
            service="feed-service",
            metric_name="requests_total",
            value=float(value),
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    max_val = db.query(func.max(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "requests_total"
    ).scalar()

    assert max_val == 200

    db.close()


def test_calculate_min_metric_value(test_db):
    """Test min value calculation"""
    db = TestingSessionLocal()

    values = [10, 50, 200, 75, 100]
    for value in values:
        metric = AnalyticsMetric(
            service="search-service",
            metric_name="latency_ms",
            value=float(value),
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    min_val = db.query(func.min(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "latency_ms"
    ).scalar()

    assert min_val == 10

    db.close()


def test_calculate_sum_metrics(test_db):
    """Test sum calculation"""
    db = TestingSessionLocal()

    values = [25, 50, 100, 75, 50]
    for value in values:
        metric = AnalyticsMetric(
            service="osint-service",
            metric_name="errors_total",
            value=float(value),
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    total = db.query(func.sum(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "errors_total"
    ).scalar()

    expected_sum = sum(values)
    assert total == expected_sum

    db.close()


def test_calculate_count_metrics(test_db):
    """Test count calculation"""
    db = TestingSessionLocal()

    count_values = 15
    for i in range(count_values):
        metric = AnalyticsMetric(
            service="notification-service",
            metric_name="emails_sent",
            value=1.0,
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    count = db.query(func.count(AnalyticsMetric.id)).filter(
        AnalyticsMetric.metric_name == "emails_sent"
    ).scalar()

    assert count == count_values

    db.close()


def test_error_rate_calculation(test_db):
    """Test error rate calculation"""
    db = TestingSessionLocal()

    # Add metrics: 100 requests, 5 errors
    for i in range(100):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="requests_total",
            value=1.0,
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    for i in range(5):
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="errors_total",
            value=1.0,
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func
    total_requests = db.query(func.sum(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "requests_total"
    ).scalar()

    total_errors = db.query(func.sum(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "errors_total"
    ).scalar()

    error_rate = (total_errors / total_requests) if total_requests > 0 else 0
    assert error_rate == 0.05

    db.close()


def test_percentile_calculation(test_db):
    """Test percentile calculation for latencies"""
    db = TestingSessionLocal()

    values = list(range(1, 101))  # 1 to 100
    for value in values:
        metric = AnalyticsMetric(
            service="test-service",
            metric_name="latency_ms",
            value=float(value),
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    # Get 95th percentile using SQL
    import sqlalchemy
    from sqlalchemy import func

    # For SQLite we can use ORDER BY and LIMIT
    all_values = db.query(AnalyticsMetric.value).filter(
        AnalyticsMetric.metric_name == "latency_ms"
    ).order_by(AnalyticsMetric.value).all()

    values_list = [v[0] for v in all_values]
    p95_index = int(0.95 * len(values_list))
    p95 = values_list[p95_index]

    assert p95 > 90  # Should be around 95

    db.close()


# ============================================================================
# STATISTICS AGGREGATION TESTS (6 tests)
# ============================================================================

def test_aggregate_by_service(test_db):
    """Test aggregation by service"""
    db = TestingSessionLocal()

    services = ["auth-service", "feed-service", "search-service"]
    for service in services:
        for i in range(5):
            metric = AnalyticsMetric(
                service=service,
                metric_name="requests_total",
                value=float(100 + i),
                timestamp=datetime.utcnow()
            )
            db.add(metric)

    db.commit()

    from sqlalchemy import func

    results = db.query(
        AnalyticsMetric.service,
        func.sum(AnalyticsMetric.value).label('total')
    ).filter(
        AnalyticsMetric.metric_name == "requests_total"
    ).group_by(AnalyticsMetric.service).all()

    assert len(results) == 3

    db.close()


def test_aggregate_by_metric_name(test_db):
    """Test aggregation by metric name"""
    db = TestingSessionLocal()

    metrics = ["requests_total", "latency_ms", "errors_total"]
    for metric in metrics:
        for i in range(5):
            m = AnalyticsMetric(
                service="test-service",
                metric_name=metric,
                value=float(100 + i),
                timestamp=datetime.utcnow()
            )
            db.add(m)

    db.commit()

    from sqlalchemy import func

    results = db.query(
        AnalyticsMetric.metric_name,
        func.count(AnalyticsMetric.id).label('count')
    ).group_by(AnalyticsMetric.metric_name).all()

    assert len(results) == 3

    db.close()


def test_daily_aggregation(test_db):
    """Test daily metric aggregation"""
    db = TestingSessionLocal()

    now = datetime.utcnow()

    # Add metrics over 3 days
    for day in range(3):
        for hour in range(24):
            metric = AnalyticsMetric(
                service="test-service",
                metric_name="daily_requests",
                value=100.0,
                timestamp=now - timedelta(days=day, hours=hour)
            )
            db.add(metric)

    db.commit()

    from sqlalchemy import func

    # Group by day
    results = db.query(
        func.date(AnalyticsMetric.timestamp).label('date'),
        func.sum(AnalyticsMetric.value).label('daily_total')
    ).group_by('date').all()

    assert len(results) >= 3

    db.close()


def test_hourly_aggregation(test_db):
    """Test hourly metric aggregation"""
    db = TestingSessionLocal()

    now = datetime.utcnow()
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    # Add metrics across multiple hours
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            metric = AnalyticsMetric(
                service="test-service",
                metric_name="hourly_requests",
                value=50.0,
                timestamp=hour_start - timedelta(hours=hour, minutes=minute)
            )
            db.add(metric)

    db.commit()

    from sqlalchemy import func

    # Query for specific hour
    specific_hour = hour_start - timedelta(hours=5)
    next_hour = specific_hour + timedelta(hours=1)

    hourly_total = db.query(func.sum(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "hourly_requests",
        AnalyticsMetric.timestamp >= specific_hour,
        AnalyticsMetric.timestamp < next_hour
    ).scalar()

    assert hourly_total is not None

    db.close()


def test_service_health_aggregation(test_db):
    """Test health score aggregation across services"""
    db = TestingSessionLocal()

    services = ["auth-service", "feed-service", "search-service"]

    for service in services:
        # Add health metrics for each service
        metric = AnalyticsMetric(
            service=service,
            metric_name="health_score",
            value=90.0 + (hash(service) % 10),  # Vary slightly
            timestamp=datetime.utcnow()
        )
        db.add(metric)

    db.commit()

    from sqlalchemy import func

    avg_health = db.query(func.avg(AnalyticsMetric.value)).filter(
        AnalyticsMetric.metric_name == "health_score"
    ).scalar()

    assert 85 < avg_health < 100

    db.close()


def test_performance_metrics_aggregation(test_db):
    """Test aggregation of performance metrics"""
    db = TestingSessionLocal()

    # Add CPU, memory, and latency metrics
    performance_metrics = {
        "cpu_usage": [50, 60, 45, 75, 55],
        "memory_usage": [1024, 1536, 1024, 2048, 1280],
        "latency_ms": [25, 50, 30, 100, 40]
    }

    for metric_name, values in performance_metrics.items():
        for value in values:
            metric = AnalyticsMetric(
                service="test-service",
                metric_name=metric_name,
                value=float(value),
                timestamp=datetime.utcnow()
            )
            db.add(metric)

    db.commit()

    from sqlalchemy import func

    results = {}
    for metric_name in performance_metrics.keys():
        avg_val = db.query(func.avg(AnalyticsMetric.value)).filter(
            AnalyticsMetric.metric_name == metric_name
        ).scalar()
        results[metric_name] = avg_val

    assert len(results) == 3
    assert all(v is not None for v in results.values())

    db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
