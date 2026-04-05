# Testing news-mcp-common

## Test Coverage

- ✅ **test_circuit_breaker.py** - Circuit breaker pattern tests
  - State transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
  - Threshold enforcement
  - Context manager pattern
  - Registry pattern
  - Statistics tracking
  - Concurrency handling
  - Edge cases

## Running Tests

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=news_mcp_common --cov-report=html
```

### Option 2: Docker Container

```bash
# Build test container
docker build -f Dockerfile.test -t news-mcp-common-test .

# Run tests
docker run --rm news-mcp-common-test pytest tests/ -v
```

### Option 3: tox (Multi-Python Testing)

```bash
# Install tox
pip install tox

# Run tests for all Python versions
tox
```

## Test Structure

```
tests/
├── __init__.py
├── test_circuit_breaker.py       # Circuit breaker tests
└── README.md                      # This file
```

## Adding New Tests

1. Create test file: `test_<module>.py`
2. Import fixtures if needed
3. Use descriptive class/function names
4. Run tests locally before committing

## CI/CD Integration

Tests run automatically on:
- Every commit (GitHub Actions)
- Pull requests
- Before deployment

## Test Results

Expected: **All 30+ tests pass**

Coverage target: **> 90%**
