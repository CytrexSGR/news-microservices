#!/usr/bin/env python3
"""
Narrative Service Cache Benchmark
Validates claim: 13x better than target (3-5ms cached vs 2s target)
Also measures: ~150ms uncached baseline
"""
import asyncio
import time
import statistics
import sys
from typing import List, Dict
import httpx
import redis

# Configuration
NARRATIVE_URL = "http://localhost:8119"
REDIS_URL = "redis://localhost:6379/1"  # Different DB from prediction
NUM_REQUESTS = 100
NUM_RUNS = 3

# Sample test data (realistic article for narrative analysis)
TEST_ARTICLE = {
    "title": "Climate Summit Reaches Historic Agreement on Carbon Emissions",
    "content": "World leaders at the COP30 climate summit have agreed to unprecedented measures to reduce global carbon emissions by 50% by 2030. The agreement includes binding commitments from major economies and a $500 billion fund to help developing nations transition to renewable energy. Environmental groups have praised the deal as a turning point in the fight against climate change.",
    "source": "reuters",
    "article_id": 12345
}


class BenchmarkResults:
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.failures = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def add_result(self, latency: float, success: bool = True, cache_hit: bool = False):
        if success:
            self.latencies.append(latency)
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
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
    def p99_latency(self) -> float:
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[idx]

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0


async def benchmark_uncached(client: httpx.AsyncClient, redis_client: redis.Redis) -> BenchmarkResults:
    """Benchmark uncached narrative analysis requests"""
    results = BenchmarkResults("Uncached")

    print(f"\n🔥 Running {NUM_REQUESTS} UNCACHED requests...")

    for i in range(NUM_REQUESTS):
        # Clear cache before each request
        redis_client.flushdb()

        start = time.time()
        try:
            response = await client.post(
                f"{NARRATIVE_URL}/api/v1/analyze",
                json=TEST_ARTICLE,
                timeout=15.0
            )
            latency = (time.time() - start) * 1000  # Convert to ms

            if response.status_code == 200:
                results.add_result(latency, success=True, cache_hit=False)
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{NUM_REQUESTS} | Avg: {results.avg_latency:.2f}ms")
            else:
                print(f"  ❌ Request {i+1} failed: {response.status_code}")
                results.add_result(latency, success=False)
        except Exception as e:
            latency = (time.time() - start) * 1000
            print(f"  ❌ Request {i+1} error: {e}")
            results.add_result(latency, success=False)

    return results


async def benchmark_cached(client: httpx.AsyncClient) -> BenchmarkResults:
    """Benchmark cached narrative analysis requests"""
    results = BenchmarkResults("Cached")

    # Prime the cache with one request
    print("\n🔥 Priming cache...")
    response = await client.post(
        f"{NARRATIVE_URL}/api/v1/analyze",
        json=TEST_ARTICLE,
        timeout=15.0
    )
    print(f"  Cache primed: {response.status_code}")

    print(f"\n🚀 Running {NUM_REQUESTS} CACHED requests...")

    for i in range(NUM_REQUESTS):
        start = time.time()
        try:
            response = await client.post(
                f"{NARRATIVE_URL}/api/v1/analyze",
                json=TEST_ARTICLE,
                timeout=10.0
            )
            latency = (time.time() - start) * 1000  # Convert to ms

            if response.status_code == 200:
                results.add_result(latency, success=True, cache_hit=True)
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{NUM_REQUESTS} | Avg: {results.avg_latency:.2f}ms")
            else:
                print(f"  ❌ Request {i+1} failed: {response.status_code}")
                results.add_result(latency, success=False)
        except Exception as e:
            latency = (time.time() - start) * 1000
            print(f"  ❌ Request {i+1} error: {e}")
            results.add_result(latency, success=False)

    return results


async def run_benchmark_round(round_num: int) -> Dict[str, BenchmarkResults]:
    """Run one complete benchmark round"""
    print(f"\n{'='*60}")
    print(f"BENCHMARK ROUND {round_num}/{NUM_RUNS}")
    print(f"{'='*60}")

    # Connect to services
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    async with httpx.AsyncClient() as client:
        # Check service health
        try:
            health = await client.get(f"{NARRATIVE_URL}/health", timeout=5.0)
            if health.status_code != 200:
                print(f"❌ Narrative service unhealthy: {health.status_code}")
                sys.exit(1)
            print(f"✅ Narrative service healthy")
        except Exception as e:
            print(f"❌ Cannot connect to narrative service: {e}")
            sys.exit(1)

        # Run benchmarks
        uncached_results = await benchmark_uncached(client, redis_client)
        cached_results = await benchmark_cached(client)

    redis_client.close()

    return {
        "uncached": uncached_results,
        "cached": cached_results
    }


def print_results(all_results: List[Dict[str, BenchmarkResults]]):
    """Print comprehensive benchmark results"""
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*60}")

    # Aggregate results across all runs
    uncached_latencies = []
    cached_latencies = []

    for run_results in all_results:
        uncached_latencies.extend(run_results["uncached"].latencies)
        cached_latencies.extend(run_results["cached"].latencies)

    # Calculate aggregate statistics
    uncached_avg = statistics.mean(uncached_latencies)
    uncached_p50 = statistics.median(uncached_latencies)
    uncached_p95 = sorted(uncached_latencies)[int(len(uncached_latencies) * 0.95)]
    uncached_min = min(uncached_latencies)
    uncached_max = max(uncached_latencies)

    cached_avg = statistics.mean(cached_latencies)
    cached_p50 = statistics.median(cached_latencies)
    cached_p95 = sorted(cached_latencies)[int(len(cached_latencies) * 0.95)]
    cached_min = min(cached_latencies)
    cached_max = max(cached_latencies)

    speedup = uncached_avg / cached_avg
    target_vs_cached = 2000 / cached_avg  # 2s target vs actual cached

    print(f"\n📊 UNCACHED REQUESTS (n={len(uncached_latencies)}):")
    print(f"  Average:    {uncached_avg:.2f}ms")
    print(f"  Median:     {uncached_p50:.2f}ms")
    print(f"  P95:        {uncached_p95:.2f}ms")
    print(f"  Min:        {uncached_min:.2f}ms")
    print(f"  Max:        {uncached_max:.2f}ms")

    print(f"\n⚡ CACHED REQUESTS (n={len(cached_latencies)}):")
    print(f"  Average:    {cached_avg:.2f}ms")
    print(f"  Median:     {cached_p50:.2f}ms")
    print(f"  P95:        {cached_p95:.2f}ms")
    print(f"  Min:        {cached_min:.2f}ms")
    print(f"  Max:        {cached_max:.2f}ms")

    print(f"\n🎯 SPEEDUP ANALYSIS:")
    print(f"  Uncached→Cached speedup: {speedup:.1f}x")
    print(f"  Target (2s) vs Cached: {target_vs_cached:.1f}x better")
    print(f"  Claimed: 13x better than target")

    # Verdict
    print(f"\n📋 VERDICT:")

    # Check cached latency target (3-5ms claimed)
    target_cached_min = 3
    target_cached_max = 5

    if target_cached_min <= cached_avg <= target_cached_max:
        print(f"  ✅ Cached latency {cached_avg:.2f}ms is within target range {target_cached_min}-{target_cached_max}ms")
        cached_verdict = "VALIDATED"
    elif cached_avg <= target_cached_max * 1.5:  # Within 50% of max
        print(f"  ⚠️  Cached latency {cached_avg:.2f}ms is slightly higher than target {target_cached_min}-{target_cached_max}ms")
        cached_verdict = "ADJUSTED"
    else:
        print(f"  ❌ Cached latency {cached_avg:.2f}ms is significantly higher than target {target_cached_min}-{target_cached_max}ms")
        cached_verdict = "FAILED"

    # Check 13x better than 2s target
    if target_vs_cached >= 13 * 0.8:  # Within 20% of 13x
        print(f"  ✅ Performance {target_vs_cached:.1f}x better than 2s target is within claimed 13x range")
        target_verdict = "VALIDATED"
    elif target_vs_cached >= 10:  # Still > 10x
        print(f"  ⚠️  Performance {target_vs_cached:.1f}x better than 2s target is below claimed 13x but still excellent")
        target_verdict = "ADJUSTED"
    else:
        print(f"  ❌ Performance {target_vs_cached:.1f}x better than 2s target is significantly below claimed 13x")
        target_verdict = "FAILED"

    # Check uncached baseline (~150ms claimed)
    claimed_uncached_baseline = 150

    if abs(uncached_avg - claimed_uncached_baseline) <= claimed_uncached_baseline * 0.2:
        print(f"  ✅ Uncached latency {uncached_avg:.2f}ms matches claimed ~{claimed_uncached_baseline}ms baseline")
    else:
        print(f"  ℹ️  Uncached latency {uncached_avg:.2f}ms differs from claimed ~{claimed_uncached_baseline}ms baseline")

    # Overall verdict
    print(f"\n🏆 OVERALL VERDICT:")
    if cached_verdict == "VALIDATED" and target_verdict == "VALIDATED":
        print(f"  ✅ ALL CLAIMS VALIDATED")
    elif "FAILED" not in [cached_verdict, target_verdict]:
        print(f"  ⚠️  CLAIMS ADJUSTED (performance good but not exactly as claimed)")
    else:
        print(f"  ❌ CLAIMS FAILED (performance significantly below claims)")


async def main():
    print("="*60)
    print("NARRATIVE SERVICE CACHE BENCHMARK")
    print("="*60)
    print(f"Configuration:")
    print(f"  Requests per run: {NUM_REQUESTS}")
    print(f"  Number of runs: {NUM_RUNS}")
    print(f"  Total requests: {NUM_REQUESTS * NUM_RUNS * 2}")
    print(f"  Narrative URL: {NARRATIVE_URL}")
    print(f"  Redis URL: {REDIS_URL}")
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
