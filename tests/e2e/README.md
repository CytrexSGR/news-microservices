# End-to-End Test Suite

Comprehensive E2E testing for the News MCP microservices platform.

## Overview

This test suite provides complete end-to-end testing coverage for all 8 microservices:

1. **Auth Service** (8000) - Authentication and authorization
2. **Feed Service** (8001) - RSS feed management
3. **Content Analysis Service** (8002) - Article analysis
4. **Research Service** (8003) - Research queries
5. **OSINT Service** (8004) - Open-source intelligence
6. **Notification Service** (8005) - Notifications
7. **Search Service** (8006) - Article search
8. **Analytics Service** (8007) - Analytics dashboard

## Test Categories

### Functional Tests

- **test_user_flow.py** - Complete user journeys
- **test_auth_integration.py** - Authentication across services
- **test_event_flow.py** - RabbitMQ event communication
- **test_search_integration.py** - Search functionality
- **test_notification_flow.py** - Notification delivery
- **test_analytics_flow.py** - Analytics data collection

### Load Tests

- **load/locustfile.py** - Locust load testing (100+ concurrent users)
- **load/k6_script.js** - K6 performance testing

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start all services
cd ../..
docker-compose up -d

# Wait for services to be healthy (60 seconds)
```

## Running Tests

### Run All E2E Tests

```bash
pytest -v
```

### Run Specific Test Categories

```bash
# User flow tests only
pytest test_user_flow.py -v

# Authentication tests
pytest test_auth_integration.py -v

# Event flow tests
pytest test_event_flow.py -v

# Search integration tests
pytest test_search_integration.py -v
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### Run in Parallel

```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

### Run Smoke Tests Only

```bash
pytest -m smoke -v
```

## Load Testing

### Using Locust

```bash
# Start Locust web interface
cd load
locust -f locustfile.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Configure users and spawn rate
# Click "Start swarming"
```

### Using K6

```bash
# Run K6 load test
cd load
k6 run k6_script.js

# Run with custom configuration
k6 run k6_script.js --vus 100 --duration 5m

# Generate HTML report
k6 run k6_script.js --out json=results.json
```

## Test with Docker

### Run E2E Tests in Container

```bash
# Build and run test container
docker-compose -f docker-compose.test.yml up --build e2e-tests

# View test reports
open reports/e2e-report.html
open reports/coverage/index.html
```

### Run Load Tests in Container

```bash
# Locust
docker-compose -f docker-compose.test.yml --profile load-testing up load-tests-locust
# Open: http://localhost:8089

# K6
docker-compose -f docker-compose.test.yml --profile load-testing up load-tests-k6
```

## Test Data

Test fixtures are located in `fixtures/`:

- **users.json** - Test user accounts
- **feeds.json** - Sample RSS feeds
- **articles.json** - Sample articles

## Configuration

### Environment Variables

```bash
# Database
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=news_user
export POSTGRES_PASSWORD=your_db_password
export POSTGRES_DB=news_mcp

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=redis_secret_2024

# RabbitMQ
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USER=admin
export RABBITMQ_PASS=rabbit_secret_2024
export RABBITMQ_VHOST=news_mcp
```

### Test Configuration (pytest.ini)

See `pytest.ini` for test discovery, markers, and coverage settings.

## Test Scenarios

### Complete User Journey

1. User registration and login
2. Add RSS feed
3. Fetch articles
4. Automatic content analysis
5. Create research query
6. Create OSINT instance
7. Receive notifications
8. Search articles
9. View analytics dashboard

### Performance Baselines

- **Response Time**: p95 < 500ms
- **Error Rate**: < 5%
- **Concurrent Users**: 100+
- **Database Connections**: Pool tested
- **Cache Hit Rate**: > 70%

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run E2E tests
        run: |
          cd tests/e2e
          pip install -r requirements.txt
          pytest -v --html=reports/e2e-report.html
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: tests/e2e/reports/
```

## Troubleshooting

### Services Not Ready

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
# ... for all services

# Check Docker logs
docker-compose logs -f [service-name]
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker exec -it news-postgres psql -U news_user -d news_mcp

# Check if tables exist
\dt
```

### RabbitMQ Issues

```bash
# Check RabbitMQ management UI
open http://localhost:15672
# Login: admin / rabbit_secret_2024

# Check queues and exchanges
```

### Redis Issues

```bash
# Test Redis connection
docker exec -it news-redis redis-cli -a redis_secret_2024

# Check keys
KEYS *
```

## Reports

After running tests, reports are generated in `reports/`:

- **test-report.html** - HTML test report
- **coverage/index.html** - Coverage report
- **k6-results.json** - K6 load test results

## Best Practices

1. **Isolation**: Each test creates unique data
2. **Cleanup**: Tests clean up after themselves
3. **Idempotence**: Tests can run multiple times
4. **Fast Feedback**: Smoke tests run first
5. **Realistic Data**: Use actual RSS feeds
6. **Load Testing**: Test under realistic load

## Contributing

When adding new tests:

1. Follow existing patterns in `conftest.py`
2. Use fixtures for common setup
3. Add appropriate markers
4. Document test scenarios
5. Update this README

## Support

For issues or questions:
- Check service logs: `docker-compose logs -f`
- Review test output: `pytest -v --tb=long`
- Check test reports in `reports/`
