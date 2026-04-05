# E2E Testing Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /home/cytrex/news-microservices/tests/e2e
pip install -r requirements.txt
```

### Step 2: Verify Services Are Running

```bash
# Check all services are healthy
curl http://localhost:8000/health  # Auth
curl http://localhost:8001/health  # Feed
curl http://localhost:8002/api/v1/health  # Content Analysis
curl http://localhost:8003/api/v1/health  # Research
curl http://localhost:8004/api/v1/health  # OSINT
curl http://localhost:8005/health  # Notification
curl http://localhost:8006/health  # Search
curl http://localhost:8007/health  # Analytics
```

### Step 3: Run Your First Test

```bash
# Run smoke tests (fastest)
./run_tests.sh smoke

# Or run a simple user flow test
pytest test_user_flow.py::test_user_registration_and_login_flow -v
```

## Common Commands

### Run All Tests
```bash
./run_tests.sh all
```

### Run Specific Test Categories
```bash
./run_tests.sh user-flow      # User journey tests
./run_tests.sh auth           # Authentication tests
./run_tests.sh events         # Event flow tests
./run_tests.sh search         # Search integration tests
```

### Run with Coverage
```bash
./run_tests.sh coverage
```

### Run Tests in Parallel (Faster)
```bash
./run_tests.sh parallel
```

## Load Testing

### Locust (Web UI)
```bash
# Start Locust web interface
./run_tests.sh load-locust

# Open browser: http://localhost:8089
# Set number of users: 100
# Spawn rate: 10
# Click "Start swarming"
```

### K6 (CLI)
```bash
# Run K6 performance tests
./run_tests.sh load-k6

# Results will show:
# - Request rate
# - Response times (p95, p99)
# - Error rates
# - Pass/fail thresholds
```

## Docker Testing

### Run Tests in Container
```bash
# Complete isolated test environment
./run_tests.sh docker
```

## Test Results

After running tests, check:

1. **Console Output** - Real-time test results
2. **HTML Report** - `reports/e2e-report.html`
3. **Coverage Report** - `reports/coverage/index.html`
4. **K6 Results** - `reports/k6-results.json`

## Troubleshooting

### Services Not Ready
```bash
# Start all services
cd ../..
docker-compose up -d

# Wait 60 seconds for initialization
sleep 60

# Then run tests
cd tests/e2e
./run_tests.sh smoke
```

### Connection Refused Errors
```bash
# Check Docker containers are running
docker ps

# Restart specific service
docker-compose restart auth-service

# Check logs
docker-compose logs -f auth-service
```

### Test Failures
```bash
# Run with verbose output
pytest test_user_flow.py -vv --tb=long

# Run specific test
pytest test_user_flow.py::test_complete_user_journey -v

# Run with debugging
pytest --pdb test_user_flow.py
```

## What Gets Tested

### User Flow Tests
- ✅ Registration and login
- ✅ Feed creation and management
- ✅ Article fetching
- ✅ Content analysis
- ✅ Research queries
- ✅ OSINT monitoring
- ✅ Notifications
- ✅ Search functionality
- ✅ Analytics dashboard

### Integration Tests
- ✅ Authentication across all services
- ✅ RabbitMQ event delivery
- ✅ Redis caching
- ✅ PostgreSQL data consistency
- ✅ Service-to-service communication

### Load Tests
- ✅ 100+ concurrent users
- ✅ Response time < 500ms (p95)
- ✅ Error rate < 5%
- ✅ Database connection pooling
- ✅ Cache hit rate optimization

## Next Steps

1. **Review Test Results** - Check HTML reports
2. **Add Custom Tests** - Use existing patterns in `conftest.py`
3. **Run Load Tests** - Identify performance bottlenecks
4. **CI/CD Integration** - Add to GitHub Actions
5. **Monitor Coverage** - Aim for 80%+ coverage

## Support

- **Documentation**: See `README.md` for detailed information
- **Test Patterns**: Check existing test files for examples
- **Common Issues**: See "Troubleshooting" section above
- **Service Logs**: `docker-compose logs -f [service-name]`

## Success Metrics

After running all tests, you should see:

```
✓ 40+ tests passed
✓ All services healthy
✓ Response times < 500ms
✓ Error rate < 1%
✓ Coverage > 70%
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./run_tests.sh all` | Run all E2E tests |
| `./run_tests.sh smoke` | Quick smoke tests |
| `./run_tests.sh parallel` | Fast parallel execution |
| `./run_tests.sh load-locust` | Interactive load testing |
| `./run_tests.sh coverage` | Generate coverage reports |
| `./run_tests.sh clean` | Remove test artifacts |

---

**Ready to test?** Run: `./run_tests.sh smoke`
