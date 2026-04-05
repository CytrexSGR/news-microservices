"""
Performance Benchmarks for Narrative Service
Measures response times, cache effectiveness, concurrent load
"""
import asyncio
import time
import statistics
from typing import List, Dict
import httpx


class NarrativeBenchmark:
    """Performance benchmark suite for narrative service"""

    def __init__(self, base_url: str = "http://localhost:8119/api/v1/narrative"):
        self.base_url = base_url
        self.results: Dict[str, Dict] = {}

    async def benchmark_single_analysis(self, text: str, iterations: int = 10) -> Dict:
        """
        Benchmark single text analysis

        Returns:
            Dict with min, max, mean, median response times
        """
        print(f"\n=== Benchmark: Single Text Analysis ({iterations} iterations) ===")

        times = []
        cache_hits = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Clear cache first
            await client.post(f"{self.base_url}/cache/clear")

            for i in range(iterations):
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/analyze/text",
                    params={"text": text}
                )
                duration = time.time() - start

                if response.status_code == 200:
                    times.append(duration)
                    data = response.json()
                    if data.get("from_cache"):
                        cache_hits += 1
                else:
                    print(f"  ⚠️  Request {i+1} failed: {response.status_code}")

                # Small delay between requests
                await asyncio.sleep(0.1)

        results = {
            "min_ms": round(min(times) * 1000, 2),
            "max_ms": round(max(times) * 1000, 2),
            "mean_ms": round(statistics.mean(times) * 1000, 2),
            "median_ms": round(statistics.median(times) * 1000, 2),
            "std_dev_ms": round(statistics.stdev(times) * 1000, 2) if len(times) > 1 else 0,
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / iterations * 100, 1),
        }

        self._print_results("Single Analysis", results)
        self.results["single_analysis"] = results
        return results

    async def benchmark_cache_effectiveness(self, text: str, iterations: int = 5) -> Dict:
        """
        Benchmark cache effectiveness

        Compares first request (cold) vs subsequent (cached)
        """
        print(f"\n=== Benchmark: Cache Effectiveness ===")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Clear cache
            await client.post(f"{self.base_url}/cache/clear")

            # First request (cold cache)
            start = time.time()
            response = await client.post(
                f"{self.base_url}/analyze/text",
                params={"text": text}
            )
            cold_time = time.time() - start

            # Subsequent requests (warm cache)
            warm_times = []
            for _ in range(iterations):
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/analyze/text",
                    params={"text": text}
                )
                warm_times.append(time.time() - start)
                await asyncio.sleep(0.05)

            avg_warm_time = statistics.mean(warm_times)
            speedup = cold_time / avg_warm_time if avg_warm_time > 0 else 0

            results = {
                "cold_cache_ms": round(cold_time * 1000, 2),
                "warm_cache_ms": round(avg_warm_time * 1000, 2),
                "speedup": round(speedup, 1),
                "improvement_pct": round((1 - avg_warm_time / cold_time) * 100, 1) if cold_time > 0 else 0,
            }

            self._print_results("Cache Effectiveness", results)
            self.results["cache_effectiveness"] = results
            return results

    async def benchmark_concurrent_load(self, text: str, concurrent: int = 10) -> Dict:
        """
        Benchmark concurrent request handling

        Tests how service handles multiple simultaneous requests
        """
        print(f"\n=== Benchmark: Concurrent Load ({concurrent} concurrent) ===")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Clear cache
            await client.post(f"{self.base_url}/cache/clear")

            # Create concurrent requests
            start = time.time()
            tasks = [
                client.post(f"{self.base_url}/analyze/text", params={"text": f"{text} {i}"})
                for i in range(concurrent)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start

            # Analyze results
            success = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            errors = concurrent - success

            results = {
                "concurrent_requests": concurrent,
                "total_time_ms": round(total_time * 1000, 2),
                "requests_per_sec": round(concurrent / total_time, 2),
                "avg_time_per_request_ms": round(total_time * 1000 / concurrent, 2),
                "success": success,
                "errors": errors,
                "success_rate_pct": round(success / concurrent * 100, 1),
            }

            self._print_results("Concurrent Load", results)
            self.results["concurrent_load"] = results
            return results

    async def benchmark_overview_query(self, iterations: int = 5) -> Dict:
        """
        Benchmark overview endpoint

        Tests database query performance
        """
        print(f"\n=== Benchmark: Overview Query ===")

        times = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Clear cache first
            await client.post(f"{self.base_url}/cache/clear")

            # Cold request
            start = time.time()
            response = await client.get(f"{self.base_url}/overview?days=7")
            cold_time = time.time() - start

            # Warm requests
            warm_times = []
            for _ in range(iterations):
                start = time.time()
                response = await client.get(f"{self.base_url}/overview?days=7")
                warm_times.append(time.time() - start)
                await asyncio.sleep(0.05)

            avg_warm = statistics.mean(warm_times)

            results = {
                "cold_ms": round(cold_time * 1000, 2),
                "warm_avg_ms": round(avg_warm * 1000, 2),
                "cache_speedup": round(cold_time / avg_warm, 1) if avg_warm > 0 else 0,
            }

            self._print_results("Overview Query", results)
            self.results["overview_query"] = results
            return results

    async def benchmark_frame_detection_only(self, text: str, iterations: int = 10) -> Dict:
        """
        Benchmark frame detection performance isolated

        Tests the frame detection algorithm performance
        """
        print(f"\n=== Benchmark: Frame Detection Only ===")

        from app.services.frame_detection import frame_detection_service

        times = []
        for _ in range(iterations):
            start = time.time()
            frames = frame_detection_service.detect_frames(text)
            duration = time.time() - start
            times.append(duration)

        results = {
            "min_ms": round(min(times) * 1000, 2),
            "max_ms": round(max(times) * 1000, 2),
            "mean_ms": round(statistics.mean(times) * 1000, 2),
            "median_ms": round(statistics.median(times) * 1000, 2),
            "frames_detected": len(frames),
        }

        self._print_results("Frame Detection Only", results)
        self.results["frame_detection"] = results
        return results

    async def benchmark_bias_analysis_only(self, text: str, iterations: int = 10) -> Dict:
        """
        Benchmark bias analysis performance isolated
        """
        print(f"\n=== Benchmark: Bias Analysis Only ===")

        from app.services.bias_analysis import bias_analysis_service

        times = []
        for _ in range(iterations):
            start = time.time()
            bias = bias_analysis_service.analyze_bias(text, None)
            duration = time.time() - start
            times.append(duration)

        results = {
            "min_ms": round(min(times) * 1000, 2),
            "max_ms": round(max(times) * 1000, 2),
            "mean_ms": round(statistics.mean(times) * 1000, 2),
            "median_ms": round(statistics.median(times) * 1000, 2),
        }

        self._print_results("Bias Analysis Only", results)
        self.results["bias_analysis"] = results
        return results

    def _print_results(self, name: str, results: Dict):
        """Print formatted results"""
        print(f"\n{name} Results:")
        for key, value in results.items():
            print(f"  {key:30} {value}")

    async def run_all_benchmarks(self, sample_text: str):
        """Run all benchmarks"""
        print("=" * 70)
        print("NARRATIVE SERVICE PERFORMANCE BENCHMARKS")
        print("=" * 70)

        # Run benchmarks
        await self.benchmark_single_analysis(sample_text)
        await self.benchmark_cache_effectiveness(sample_text)
        await self.benchmark_concurrent_load(sample_text, concurrent=10)
        await self.benchmark_overview_query()
        await self.benchmark_frame_detection_only(sample_text)
        await self.benchmark_bias_analysis_only(sample_text)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print performance summary"""
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        if "single_analysis" in self.results:
            sa = self.results["single_analysis"]
            print(f"\n✅ Single Analysis: {sa['mean_ms']}ms avg (target: <2000ms)")
            if sa['mean_ms'] < 2000:
                print("   ✓ Target met!")
            else:
                print(f"   ✗ Target missed by {sa['mean_ms'] - 2000}ms")

        if "cache_effectiveness" in self.results:
            ce = self.results["cache_effectiveness"]
            print(f"\n✅ Cache Effectiveness: {ce['speedup']}x speedup ({ce['improvement_pct']}% faster)")
            if ce['speedup'] >= 10:
                print("   ✓ Excellent cache performance!")
            elif ce['speedup'] >= 5:
                print("   ✓ Good cache performance")
            else:
                print("   ⚠️  Cache performance could be improved")

        if "concurrent_load" in self.results:
            cl = self.results["concurrent_load"]
            print(f"\n✅ Concurrent Load: {cl['requests_per_sec']} req/s, {cl['success_rate_pct']}% success")
            if cl['success_rate_pct'] >= 95:
                print("   ✓ Excellent reliability!")
            elif cl['success_rate_pct'] >= 80:
                print("   ✓ Good reliability")
            else:
                print("   ⚠️  Reliability concerns")

        print("\n" + "=" * 70)


async def main():
    """Run benchmark suite"""
    # Sample article for testing
    sample_text = """
    The government announced sweeping reforms to address growing economic inequality,
    sparking fierce debate across the political spectrum. Progressive leaders praised
    the initiative as essential for social justice and protecting vulnerable communities.
    Conservative critics warned of government overreach and unsustainable spending.
    The comprehensive plan includes expanded healthcare access, education funding,
    and support for working families struggling with rising costs. Economic experts
    remain divided on the proposal's long-term impact on growth and competitiveness.
    """

    benchmark = NarrativeBenchmark()
    await benchmark.run_all_benchmarks(sample_text)


if __name__ == "__main__":
    asyncio.run(main())
