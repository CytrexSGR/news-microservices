#!/usr/bin/env python3
"""
Analytics WebSocket Stability Benchmark
Validates claim: 99.9% stability with 100+ concurrent connections
"""
import asyncio
import time
import sys
from typing import List, Dict
import websockets
from websockets.exceptions import ConnectionClosed
import statistics

# Configuration
WEBSOCKET_URL = "ws://localhost:8107/ws"
NUM_CONNECTIONS = 100
TEST_DURATION = 600  # 10 minutes
HEARTBEAT_INTERVAL = 30  # seconds
NUM_RUNS = 1  # Long-running test, only 1 run


class ConnectionStats:
    def __init__(self, conn_id: int):
        self.conn_id = conn_id
        self.connected = False
        self.connect_time = 0
        self.disconnect_time = 0
        self.reconnect_attempts = 0
        self.messages_received = 0
        self.messages_failed = 0
        self.last_heartbeat = 0
        self.errors: List[str] = []

    @property
    def uptime(self) -> float:
        if self.disconnect_time > 0:
            return self.disconnect_time - self.connect_time
        return time.time() - self.connect_time

    @property
    def success(self) -> bool:
        return self.connected and len(self.errors) == 0


class BenchmarkResults:
    def __init__(self):
        self.connections: List[ConnectionStats] = []
        self.start_time = time.time()
        self.end_time = 0

    def add_connection(self, stats: ConnectionStats):
        self.connections.append(stats)

    @property
    def total_connections(self) -> int:
        return len(self.connections)

    @property
    def successful_connections(self) -> int:
        return sum(1 for c in self.connections if c.success)

    @property
    def failed_connections(self) -> int:
        return self.total_connections - self.successful_connections

    @property
    def total_reconnects(self) -> int:
        return sum(c.reconnect_attempts for c in self.connections)

    @property
    def total_messages(self) -> int:
        return sum(c.messages_received for c in self.connections)

    @property
    def failed_messages(self) -> int:
        return sum(c.messages_failed for c in self.connections)

    @property
    def stability_rate(self) -> float:
        return (self.successful_connections / self.total_connections * 100) if self.total_connections > 0 else 0

    @property
    def avg_uptime(self) -> float:
        uptimes = [c.uptime for c in self.connections]
        return statistics.mean(uptimes) if uptimes else 0

    @property
    def message_success_rate(self) -> float:
        total = self.total_messages + self.failed_messages
        return (self.total_messages / total * 100) if total > 0 else 0


async def maintain_connection(conn_id: int, duration: int) -> ConnectionStats:
    """Maintain a single WebSocket connection for specified duration"""
    stats = ConnectionStats(conn_id)

    try:
        # Connect to WebSocket
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            stats.connected = True
            stats.connect_time = time.time()
            print(f"  ✅ Connection {conn_id} established")

            end_time = time.time() + duration
            last_heartbeat = time.time()

            while time.time() < end_time:
                try:
                    # Send heartbeat every 30 seconds
                    if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                        await websocket.send('{"type": "ping"}')
                        stats.last_heartbeat = time.time()
                        last_heartbeat = time.time()

                    # Receive messages (with timeout)
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        stats.messages_received += 1

                        # Print first message for each connection
                        if stats.messages_received == 1:
                            print(f"  📨 Connection {conn_id} received first message")

                    except asyncio.TimeoutError:
                        # No message, continue
                        pass

                except ConnectionClosed as e:
                    stats.errors.append(f"Connection closed: {e}")
                    print(f"  ❌ Connection {conn_id} closed: {e}")

                    # Attempt to reconnect
                    stats.reconnect_attempts += 1
                    print(f"  🔄 Connection {conn_id} attempting reconnect {stats.reconnect_attempts}...")

                    try:
                        websocket = await websockets.connect(WEBSOCKET_URL)
                        print(f"  ✅ Connection {conn_id} reconnected")
                    except Exception as reconnect_error:
                        stats.errors.append(f"Reconnect failed: {reconnect_error}")
                        print(f"  ❌ Connection {conn_id} reconnect failed: {reconnect_error}")
                        break

                except Exception as e:
                    stats.errors.append(f"Receive error: {e}")
                    stats.messages_failed += 1

            stats.disconnect_time = time.time()
            print(f"  ✅ Connection {conn_id} completed test (uptime: {stats.uptime:.1f}s, messages: {stats.messages_received})")

    except Exception as e:
        stats.errors.append(f"Connection error: {e}")
        print(f"  ❌ Connection {conn_id} failed to connect: {e}")

    return stats


async def run_benchmark() -> BenchmarkResults:
    """Run WebSocket stability benchmark"""
    print(f"\n{'='*60}")
    print(f"WEBSOCKET STABILITY BENCHMARK")
    print(f"{'='*60}")
    print(f"Configuration:")
    print(f"  Concurrent connections: {NUM_CONNECTIONS}")
    print(f"  Test duration: {TEST_DURATION}s ({TEST_DURATION/60:.1f} minutes)")
    print(f"  Heartbeat interval: {HEARTBEAT_INTERVAL}s")
    print(f"  WebSocket URL: {WEBSOCKET_URL}")
    print(f"{'='*60}\n")

    results = BenchmarkResults()

    # Create all connections concurrently
    print(f"🚀 Establishing {NUM_CONNECTIONS} concurrent connections...")

    tasks = [
        maintain_connection(i, TEST_DURATION)
        for i in range(NUM_CONNECTIONS)
    ]

    # Wait for all connections to complete
    connection_stats = await asyncio.gather(*tasks)

    # Add results
    for stats in connection_stats:
        results.add_connection(stats)

    results.end_time = time.time()

    return results


def print_results(results: BenchmarkResults):
    """Print comprehensive benchmark results"""
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*60}")

    test_duration = results.end_time - results.start_time

    print(f"\n📊 CONNECTION STATISTICS:")
    print(f"  Total connections:      {results.total_connections}")
    print(f"  Successful:             {results.successful_connections}")
    print(f"  Failed:                 {results.failed_connections}")
    print(f"  Stability rate:         {results.stability_rate:.2f}%")
    print(f"  Total reconnects:       {results.total_reconnects}")
    print(f"  Test duration:          {test_duration:.1f}s ({test_duration/60:.1f} minutes)")
    print(f"  Average uptime:         {results.avg_uptime:.1f}s")

    print(f"\n📨 MESSAGE STATISTICS:")
    print(f"  Total messages:         {results.total_messages}")
    print(f"  Failed messages:        {results.failed_messages}")
    print(f"  Message success rate:   {results.message_success_rate:.2f}%")
    print(f"  Messages per connection:{results.total_messages / results.total_connections:.1f} avg")

    print(f"\n🎯 STABILITY ANALYSIS:")
    print(f"  Claimed stability:      99.9%")
    print(f"  Actual stability:       {results.stability_rate:.2f}%")
    print(f"  Max allowed failures:   {NUM_CONNECTIONS * 0.001:.1f} ({0.1}%)")
    print(f"  Actual failures:        {results.failed_connections}")

    # Verdict
    print(f"\n📋 VERDICT:")

    if results.stability_rate >= 99.9:
        print(f"  ✅ VALIDATED - Stability {results.stability_rate:.2f}% meets or exceeds 99.9% claim")
        verdict = "VALIDATED"
    elif results.stability_rate >= 99.0:
        print(f"  ⚠️  ADJUSTED - Stability {results.stability_rate:.2f}% is excellent but below 99.9% claim")
        verdict = "ADJUSTED"
    else:
        print(f"  ❌ FAILED - Stability {results.stability_rate:.2f}% is significantly below 99.9% claim")
        verdict = "FAILED"

    # Check reconnection behavior
    if results.total_reconnects == 0:
        print(f"  ✅ No reconnections needed - excellent stability")
    elif results.total_reconnects <= NUM_CONNECTIONS * 0.05:  # < 5% reconnects
        print(f"  ⚠️  {results.total_reconnects} reconnections occurred but were handled gracefully")
    else:
        print(f"  ❌ {results.total_reconnects} reconnections indicate connection instability")

    # Check message delivery
    if results.message_success_rate >= 99.9:
        print(f"  ✅ Message delivery {results.message_success_rate:.2f}% is excellent")
    elif results.message_success_rate >= 99.0:
        print(f"  ⚠️  Message delivery {results.message_success_rate:.2f}% is good but not perfect")
    else:
        print(f"  ❌ Message delivery {results.message_success_rate:.2f}% indicates message loss")

    # Error summary
    if results.failed_connections > 0:
        print(f"\n❌ FAILED CONNECTIONS:")
        for conn in results.connections:
            if not conn.success:
                print(f"  Connection {conn.conn_id}:")
                for error in conn.errors[:3]:  # Show first 3 errors
                    print(f"    - {error}")

    print(f"\n🏆 OVERALL VERDICT: {verdict}")


async def main():
    # Check if service is healthy before starting
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            health = await client.get("http://localhost:8107/health", timeout=5.0)
            if health.status_code != 200:
                print(f"❌ Analytics service unhealthy: {health.status_code}")
                sys.exit(1)
            print(f"✅ Analytics service healthy\n")
    except Exception as e:
        print(f"❌ Cannot connect to analytics service: {e}")
        sys.exit(1)

    results = await run_benchmark()
    print_results(results)


if __name__ == "__main__":
    asyncio.run(main())
