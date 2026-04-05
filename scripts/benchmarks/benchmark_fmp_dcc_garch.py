#!/usr/bin/env python3
"""
FMP Service DCC-GARCH Performance Benchmark
Validates claim: 0.154s execution time (6-7x better than <1s target)
"""
import asyncio
import time
import statistics
import sys
from typing import List
import httpx

# Configuration
FMP_URL = "http://localhost:8109"
NUM_REQUESTS = 50  # DCC-GARCH is expensive, fewer requests
NUM_RUNS = 3
TIMEOUT = 30.0

# Sample test data
TEST_REQUEST = {
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],  # 4 assets
    "start_date": "2024-01-01",
    "end_date": "2024-11-24"
}


class BenchmarkResults:
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.failures = 0

    def add_result(self, latency: float, success: bool = True):
        if success:
            self.latencies.append(latency)
        else:
            self.failures += 1

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def p50_latency(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx]

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0

    @property
    def success_rate(self) -> float:
        total = len(self.latencies) + self.failures
        return (len(self.latencies) / total * 100) if total > 0 else 0


async def benchmark_dcc_garch(client: httpx.AsyncClient) -> BenchmarkResults:
    """Benchmark DCC-GARCH execution time"""
    results = BenchmarkResults("DCC-GARCH")

    print(f"\n🔥 Running {NUM_REQUESTS} DCC-GARCH calculations...")

    for i in range(NUM_REQUESTS):
        start = time.time()
        try:
            # Note: Actual endpoint may differ - adjust based on FMP service API
            response = await client.post(
                f"{FMP_URL}/api/v1/dcc-garch",
                json=TEST_REQUEST,
                timeout=TIMEOUT
            )
            latency = time.time() - start

            if response.status_code == 200:
                results.add_result(latency, success=True)
                if (i + 1) % 5 == 0:
                    print(f"  Progress: {i+1}/{NUM_REQUESTS} | Avg: {results.avg_latency:.3f}s ({results.avg_latency*1000:.1f}ms)")
            else:
                print(f"  ❌ Request {i+1} failed: {response.status_code}")
                results.add_result(latency, success=False)
        except Exception as e:
            latency = time.time() - start
            print(f"  ❌ Request {i+1} error: {e}")
            results.add_result(latency, success=False)

    return results


async def run_benchmark_round(round_num: int) -> BenchmarkResults:
    """Run one complete benchmark round"""
    print(f"\n{'='*60}")
    print(f"BENCHMARK ROUND {round_num}/{NUM_RUNS}")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        # Check service health
        try:
            health = await client.get(f"{FMP_URL}/health", timeout=5.0)
            if health.status_code != 200:
                print(f"❌ FMP service unhealthy: {health.status_code}")
                sys.exit(1)
            print(f"✅ FMP service healthy")
        except Exception as e:
            print(f"❌ Cannot connect to FMP service: {e}")
            sys.exit(1)

        # Run benchmark
        results = await benchmark_dcc_garch(client)

    return results


def print_results(all_results: List[BenchmarkResults]):
    """Print comprehensive benchmark results"""
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*60}")

    # Aggregate results across all runs
    all_latencies = []
    for results in all_results:
        all_latencies.extend(results.latencies)

    if not all_latencies:
        print("❌ No successful requests")
        return

    # Calculate statistics
    avg_latency = statistics.mean(all_latencies)
    p50_latency = statistics.median(all_latencies)
    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
    min_latency = min(all_latencies)
    max_latency = max(all_latencies)

    print(f"\n📊 DCC-GARCH PERFORMANCE (n={len(all_latencies)}):")
    print(f"  Average:        {avg_latency:.3f}s ({avg_latency*1000:.1f}ms)")
    print(f"  Median:         {p50_latency:.3f}s ({p50_latency*1000:.1f}ms)")
    print(f"  P95:            {p95_latency:.3f}s ({p95_latency*1000:.1f}ms)")
    print(f"  Min:            {min_latency:.3f}s ({min_latency*1000:.1f}ms)")
    print(f"  Max:            {max_latency:.3f}s ({max_latency*1000:.1f}ms)")

    print(f"\n🎯 PERFORMANCE ANALYSIS:")
    claimed_time = 0.154  # seconds
    target_time = 1.0     # seconds
    claimed_speedup = target_time / claimed_time

    print(f"  Claimed time:       {claimed_time:.3f}s ({claimed_time*1000:.1f}ms)")
    print(f"  Actual average:     {avg_latency:.3f}s ({avg_latency*1000:.1f}ms)")
    print(f"  Target time:        {target_time:.3f}s ({target_time*1000:.1f}ms)")
    print(f"  Claimed speedup:    {claimed_speedup:.1f}x better than target")
    print(f"  Actual vs target:   {target_time/avg_latency:.1f}x better")

    # Verdict
    print(f"\n📋 VERDICT:")

    # Check if within ±20% of claimed time
    variance = abs(avg_latency - claimed_time) / claimed_time * 100

    if avg_latency <= claimed_time * 1.2:
        print(f"  ✅ VALIDATED - Average time {avg_latency:.3f}s is within 20% of claimed {claimed_time:.3f}s")
        time_verdict = "VALIDATED"
    elif avg_latency < target_time:
        print(f"  ⚠️  ADJUSTED - Average time {avg_latency:.3f}s differs from claimed {claimed_time:.3f}s but still better than {target_time}s target")
        time_verdict = "ADJUSTED"
    else:
        print(f"  ❌ FAILED - Average time {avg_latency:.3f}s exceeds target {target_time}s")
        time_verdict = "FAILED"

    # Check if meets target
    actual_vs_target = target_time / avg_latency

    if actual_vs_target >= 5:  # At least 5x better than target (close to 6-7x claim)
        print(f"  ✅ Performance {actual_vs_target:.1f}x better than target (claim: 6-7x)")
        speedup_verdict = "VALIDATED"
    elif actual_vs_target >= 3:  # Still significantly better
        print(f"  ⚠️  Performance {actual_vs_target:.1f}x better than target is good but below claimed 6-7x")
        speedup_verdict = "ADJUSTED"
    else:
        print(f"  ❌ Performance {actual_vs_target:.1f}x better than target is below expectations")
        speedup_verdict = "FAILED"

    print(f"\n🏆 OVERALL VERDICT:")
    if time_verdict == "VALIDATED" and speedup_verdict == "VALIDATED":
        print(f"  ✅ ALL CLAIMS VALIDATED")
    elif "FAILED" not in [time_verdict, speedup_verdict]:
        print(f"  ⚠️  CLAIMS ADJUSTED (performance good but not exactly as claimed)")
    else:
        print(f"  ❌ CLAIMS FAILED (performance significantly below claims)")


async def main():
    print("="*60)
    print("FMP SERVICE DCC-GARCH PERFORMANCE BENCHMARK")
    print("="*60)
    print(f"Configuration:")
    print(f"  Requests per run: {NUM_REQUESTS}")
    print(f"  Number of runs: {NUM_RUNS}")
    print(f"  Total requests: {NUM_REQUESTS * NUM_RUNS}")
    print(f"  FMP URL: {FMP_URL}")
    print(f"  Test assets: {len(TEST_REQUEST['symbols'])} symbols")
    print("="*60)

    all_results = []

    for i in range(NUM_RUNS):
        results = await run_benchmark_round(i + 1)
        all_results.append(results)

        # Short pause between runs
        if i < NUM_RUNS - 1:
            print(f"\n⏸️  Pausing 5 seconds before next run...")
            await asyncio.sleep(5)

    print_results(all_results)


if __name__ == "__main__":
    asyncio.run(main())
