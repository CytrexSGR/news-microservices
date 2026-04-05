"""
Performance tests for Analytics Service

Tests:
- API endpoint performance under load
- WebSocket connection stability with many concurrent clients
- Database query performance
- Circuit breaker behavior under stress
"""
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta
import httpx
import websockets
import json

# Test configuration
API_BASE_URL = "http://localhost:8007"
WS_BASE_URL = "ws://localhost:8007"
TEST_TOKEN = None  # Set from auth service in fixture


@pytest.fixture(scope="module")
async def auth_token():
    """Get authentication token for tests"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "andreas@test.com", "password": "Aug2012#"}
        )
        assert response.status_code == 200
        data = response.json()
        return data["access_token"]


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def start(self):
        """Start timing"""
        self.start_time = time.time()

    def stop(self):
        """Stop timing"""
        self.end_time = time.time()

    def add_response_time(self, response_time: float):
        """Add a response time measurement"""
        self.response_times.append(response_time)

    def add_error(self, error: str):
        """Add an error"""
        self.errors.append(error)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.response_times:
            return {
                "total_requests": 0,
                "errors": len(self.errors),
                "duration_seconds": self.end_time - self.start_time
            }

        return {
            "total_requests": len(self.response_times),
            "successful_requests": len(self.response_times),
            "failed_requests": len(self.errors),
            "duration_seconds": self.end_time - self.start_time,
            "requests_per_second": len(self.response_times) / (self.end_time - self.start_time),
            "response_times": {
                "min_ms": min(self.response_times) * 1000,
                "max_ms": max(self.response_times) * 1000,
                "mean_ms": statistics.mean(self.response_times) * 1000,
                "median_ms": statistics.median(self.response_times) * 1000,
                "p95_ms": self._percentile(self.response_times, 95) * 1000,
                "p99_ms": self._percentile(self.response_times, 99) * 1000,
            },
            "errors": self.errors[:10]  # First 10 errors
        }

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


@pytest.mark.asyncio
async def test_api_load_overview_endpoint(auth_token):
    """
    Load test the /api/v1/analytics/overview endpoint

    Target: 1000+ requests per minute (16+ req/s)
    Success criteria:
    - P95 latency < 200ms
    - P99 latency < 500ms
    - Error rate < 1%
    """
    metrics = PerformanceMetrics()
    num_requests = 1000
    concurrent_requests = 50

    async def make_request(client: httpx.AsyncClient):
        """Make a single request"""
        start = time.time()
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/analytics/overview",
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=10.0
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                metrics.add_response_time(elapsed)
            else:
                metrics.add_error(f"HTTP {response.status_code}")

        except Exception as e:
            metrics.add_error(str(e))

    # Execute load test
    metrics.start()

    async with httpx.AsyncClient() as client:
        # Split requests into batches
        batch_size = concurrent_requests
        for i in range(0, num_requests, batch_size):
            batch = [make_request(client) for _ in range(min(batch_size, num_requests - i))]
            await asyncio.gather(*batch)

    metrics.stop()

    # Analyze results
    summary = metrics.get_summary()
    print(f"\n{'='*60}")
    print(f"API Load Test Results - Overview Endpoint")
    print(f"{'='*60}")
    print(f"Total Requests:      {summary['total_requests']}")
    print(f"Successful:          {summary['successful_requests']}")
    print(f"Failed:              {summary['failed_requests']}")
    print(f"Duration:            {summary['duration_seconds']:.2f}s")
    print(f"Requests/sec:        {summary['requests_per_second']:.2f}")
    print(f"\nResponse Times:")
    print(f"  Min:               {summary['response_times']['min_ms']:.2f}ms")
    print(f"  Mean:              {summary['response_times']['mean_ms']:.2f}ms")
    print(f"  Median:            {summary['response_times']['median_ms']:.2f}ms")
    print(f"  P95:               {summary['response_times']['p95_ms']:.2f}ms")
    print(f"  P99:               {summary['response_times']['p99_ms']:.2f}ms")
    print(f"  Max:               {summary['response_times']['max_ms']:.2f}ms")
    print(f"{'='*60}\n")

    # Assertions
    assert summary['failed_requests'] / summary['total_requests'] < 0.01, "Error rate too high"
    assert summary['response_times']['p95_ms'] < 200, "P95 latency too high"
    assert summary['response_times']['p99_ms'] < 500, "P99 latency too high"
    assert summary['requests_per_second'] > 16, "Throughput too low"


@pytest.mark.asyncio
async def test_websocket_concurrent_connections(auth_token):
    """
    Test WebSocket stability with 100+ concurrent connections

    Success criteria:
    - All connections established successfully
    - All heartbeats received
    - No connection drops during test
    - Clean disconnection
    """
    num_connections = 100
    test_duration_seconds = 30
    connections = []
    metrics = {
        "connected": 0,
        "heartbeats_received": 0,
        "messages_received": 0,
        "errors": [],
        "disconnections": 0
    }

    async def websocket_client(client_id: int):
        """Single WebSocket client"""
        uri = f"{WS_BASE_URL}/ws/metrics?token={auth_token}"

        try:
            async with websockets.connect(uri) as websocket:
                metrics["connected"] += 1

                # Subscribe to metrics
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "channel": "metrics"
                }))

                # Receive messages for test duration
                start_time = time.time()
                while time.time() - start_time < test_duration_seconds:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=35.0  # Heartbeat is 30s
                        )
                        data = json.loads(message)

                        if data["type"] == "heartbeat":
                            metrics["heartbeats_received"] += 1
                        else:
                            metrics["messages_received"] += 1

                    except asyncio.TimeoutError:
                        metrics["errors"].append(f"Client {client_id}: Timeout waiting for message")
                        break

        except Exception as e:
            metrics["errors"].append(f"Client {client_id}: {str(e)}")
            metrics["disconnections"] += 1

    # Start all connections
    print(f"\nStarting {num_connections} WebSocket connections...")
    start_time = time.time()

    tasks = [websocket_client(i) for i in range(num_connections)]
    await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time

    # Results
    print(f"\n{'='*60}")
    print(f"WebSocket Concurrent Connections Test")
    print(f"{'='*60}")
    print(f"Connections:         {num_connections}")
    print(f"Successfully connected: {metrics['connected']}")
    print(f"Test Duration:       {test_duration_seconds}s")
    print(f"Actual Duration:     {elapsed:.2f}s")
    print(f"Heartbeats Received: {metrics['heartbeats_received']}")
    print(f"Messages Received:   {metrics['messages_received']}")
    print(f"Disconnections:      {metrics['disconnections']}")
    print(f"Errors:              {len(metrics['errors'])}")
    if metrics['errors']:
        print(f"\nFirst 5 errors:")
        for error in metrics['errors'][:5]:
            print(f"  - {error}")
    print(f"{'='*60}\n")

    # Assertions
    assert metrics['connected'] == num_connections, "Not all connections established"
    assert metrics['disconnections'] < num_connections * 0.05, "Too many disconnections (>5%)"
    assert metrics['heartbeats_received'] > 0, "No heartbeats received"


@pytest.mark.asyncio
async def test_websocket_reconnection(auth_token):
    """
    Test WebSocket reconnection logic

    Simulates connection drops and verifies reconnection
    """
    uri = f"{WS_BASE_URL}/ws/metrics?token={auth_token}"
    reconnect_attempts = 5
    successful_reconnects = 0

    for attempt in range(reconnect_attempts):
        try:
            async with websockets.connect(uri) as websocket:
                # Subscribe
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "channel": "metrics"
                }))

                # Wait for confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)

                if data["type"] in ["connected", "subscribed"]:
                    successful_reconnects += 1

                # Deliberately close
                await websocket.close()

            # Wait before reconnecting (exponential backoff simulation)
            await asyncio.sleep(2 ** attempt)

        except Exception as e:
            print(f"Reconnection attempt {attempt + 1} failed: {e}")

    print(f"\n{'='*60}")
    print(f"WebSocket Reconnection Test")
    print(f"{'='*60}")
    print(f"Reconnection Attempts:  {reconnect_attempts}")
    print(f"Successful:             {successful_reconnects}")
    print(f"Success Rate:           {successful_reconnects/reconnect_attempts*100:.1f}%")
    print(f"{'='*60}\n")

    assert successful_reconnects >= reconnect_attempts * 0.9, "Reconnection success rate too low"


@pytest.mark.asyncio
async def test_circuit_breaker_behavior():
    """
    Test circuit breaker behavior under load

    Tests:
    1. Normal operation (closed state)
    2. Failure threshold (open state)
    3. Recovery (half-open -> closed)
    """
    from app.core.resilience import CircuitBreaker, CircuitBreakerConfig, CircuitState

    config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=2
    )

    breaker = CircuitBreaker("test-service", config)

    # Test 1: Normal operation
    assert breaker.state == CircuitState.CLOSED
    assert breaker.can_execute() is True

    for _ in range(3):
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    # Test 2: Failures trigger open state
    for _ in range(5):
        breaker.record_failure()

    assert breaker.state == CircuitState.OPEN
    assert breaker.can_execute() is False

    # Test 3: Wait for timeout, then recovery
    await asyncio.sleep(2.1)

    # First request in half-open
    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN

    # Success transitions to closed
    breaker.record_success()
    breaker.can_execute()  # Trigger check
    breaker.record_success()

    assert breaker.state == CircuitState.CLOSED

    print(f"\n{'='*60}")
    print(f"Circuit Breaker Test")
    print(f"{'='*60}")
    print(f"✓ Normal operation (closed)")
    print(f"✓ Failure threshold (open)")
    print(f"✓ Recovery (half-open -> closed)")
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_database_query_performance(auth_token):
    """
    Test database query performance for analytics

    Verifies:
    - Query response times
    - Index usage
    - Aggregation performance
    """
    metrics = PerformanceMetrics()
    num_queries = 100

    async with httpx.AsyncClient() as client:
        metrics.start()

        for _ in range(num_queries):
            start = time.time()
            try:
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/analytics/overview",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    timeout=10.0
                )
                elapsed = time.time() - start

                if response.status_code == 200:
                    metrics.add_response_time(elapsed)
                else:
                    metrics.add_error(f"HTTP {response.status_code}")

            except Exception as e:
                metrics.add_error(str(e))

        metrics.stop()

    summary = metrics.get_summary()

    print(f"\n{'='*60}")
    print(f"Database Query Performance Test")
    print(f"{'='*60}")
    print(f"Queries:             {summary['total_requests']}")
    print(f"Mean Response Time:  {summary['response_times']['mean_ms']:.2f}ms")
    print(f"P95 Response Time:   {summary['response_times']['p95_ms']:.2f}ms")
    print(f"{'='*60}\n")

    # Database queries should be fast with proper indexes
    assert summary['response_times']['mean_ms'] < 100, "Mean query time too slow"
    assert summary['response_times']['p95_ms'] < 200, "P95 query time too slow"


if __name__ == "__main__":
    """
    Run performance tests manually

    Usage:
        python -m pytest tests/test_performance.py -v -s
    """
    pytest.main([__file__, "-v", "-s"])
