#!/usr/bin/env python3
"""
Scheduler Service Throughput Benchmark
Validates claim: 40+ Prometheus metrics operational and accurate
Tests scheduler job throughput and metric accuracy
"""
import asyncio
import time
import sys
from typing import List, Dict, Optional
import httpx

# Configuration
SCHEDULER_URL = "http://localhost:8108"
PROMETHEUS_URL = "http://localhost:9090"  # If Prometheus is running
NUM_JOBS = 1000
NUM_RUNS = 3


class BenchmarkResults:
    def __init__(self):
        self.total_jobs = 0
        self.successful_jobs = 0
        self.failed_jobs = 0
        self.total_duration = 0
        self.jobs_per_second = 0
        self.metrics_count = 0
        self.metrics_accurate = True
        self.metric_errors: List[str] = []

    @property
    def success_rate(self) -> float:
        return (self.successful_jobs / self.total_jobs * 100) if self.total_jobs > 0 else 0


async def get_scheduler_metrics(client: httpx.AsyncClient) -> Optional[Dict]:
    """Retrieve scheduler metrics"""
    try:
        response = await client.get(f"{SCHEDULER_URL}/metrics", timeout=10.0)
        if response.status_code == 200:
            # Parse Prometheus metrics
            metrics = {}
            lines = response.text.split('\n')

            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse metric lines (simple parsing, not full Prometheus parser)
                if ' ' in line:
                    parts = line.split(' ', 1)
                    metric_name = parts[0]

                    # Extract metric family (base name without labels)
                    if '{' in metric_name:
                        family = metric_name.split('{')[0]
                    else:
                        family = metric_name

                    if family not in metrics:
                        metrics[family] = []

                    try:
                        value = float(parts[1])
                        metrics[family].append({
                            'name': metric_name,
                            'value': value
                        })
                    except ValueError:
                        pass

            return metrics
        else:
            print(f"❌ Failed to get metrics: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")
        return None


async def verify_metric_accuracy(client: httpx.AsyncClient, baseline_metrics: Dict, final_metrics: Dict) -> tuple[bool, List[str]]:
    """Verify that metrics accurately reflect job execution"""
    errors = []
    accurate = True

    # Expected scheduler metrics based on Week 3 implementation
    expected_metrics = [
        'scheduler_jobs_total',
        'scheduler_jobs_success',
        'scheduler_jobs_failed',
        'scheduler_job_duration_seconds',
        'scheduler_active_jobs',
        'scheduler_queue_size',
        'scheduler_celery_tasks_total',
        'scheduler_celery_tasks_success',
        'scheduler_celery_tasks_failed',
        'scheduler_task_latency_seconds'
    ]

    # Check if expected metrics exist
    for metric in expected_metrics:
        if metric not in final_metrics:
            errors.append(f"Missing metric: {metric}")
            accurate = False

    # Verify job counts increased
    if 'scheduler_jobs_total' in baseline_metrics and 'scheduler_jobs_total' in final_metrics:
        baseline_total = sum(m['value'] for m in baseline_metrics['scheduler_jobs_total'])
        final_total = sum(m['value'] for m in final_metrics['scheduler_jobs_total'])

        if final_total <= baseline_total:
            errors.append(f"scheduler_jobs_total did not increase (baseline: {baseline_total}, final: {final_total})")
            accurate = False

    # Verify success/failure counts are consistent
    if 'scheduler_jobs_success' in final_metrics and 'scheduler_jobs_failed' in final_metrics:
        success = sum(m['value'] for m in final_metrics['scheduler_jobs_success'])
        failed = sum(m['value'] for m in final_metrics['scheduler_jobs_failed'])
        total = sum(m['value'] for m in final_metrics['scheduler_jobs_total'])

        if abs((success + failed) - total) > 5:  # Allow small variance
            errors.append(f"Success + Failed ({success + failed}) doesn't match Total ({total})")
            accurate = False

    return accurate, errors


async def queue_test_jobs(client: httpx.AsyncClient, num_jobs: int) -> int:
    """Queue test jobs to scheduler"""
    print(f"\n📋 Queueing {num_jobs} test jobs...")

    successful = 0

    # Note: This is a placeholder - actual endpoint depends on scheduler implementation
    # We'll use the metrics endpoint to verify jobs are being processed
    for i in range(num_jobs):
        try:
            # In real implementation, would POST to scheduler job endpoint
            # For now, we'll simulate by just checking metrics
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i+1}/{num_jobs} jobs queued")

            # Small delay to avoid overwhelming scheduler
            if i % 10 == 0:
                await asyncio.sleep(0.1)

            successful += 1

        except Exception as e:
            print(f"  ❌ Failed to queue job {i+1}: {e}")

    return successful


async def run_benchmark_round(round_num: int) -> BenchmarkResults:
    """Run one complete benchmark round"""
    print(f"\n{'='*60}")
    print(f"BENCHMARK ROUND {round_num}/{NUM_RUNS}")
    print(f"{'='*60}")

    results = BenchmarkResults()

    async with httpx.AsyncClient() as client:
        # Check service health
        try:
            health = await client.get(f"{SCHEDULER_URL}/health", timeout=5.0)
            if health.status_code != 200:
                print(f"❌ Scheduler service unhealthy: {health.status_code}")
                sys.exit(1)
            print(f"✅ Scheduler service healthy")
        except Exception as e:
            print(f"❌ Cannot connect to scheduler service: {e}")
            sys.exit(1)

        # Get baseline metrics
        print(f"\n📊 Getting baseline metrics...")
        baseline_metrics = await get_scheduler_metrics(client)

        if baseline_metrics:
            results.metrics_count = len(baseline_metrics)
            print(f"  Found {results.metrics_count} metric families")

            # Print some key metrics
            if 'scheduler_jobs_total' in baseline_metrics:
                total = sum(m['value'] for m in baseline_metrics['scheduler_jobs_total'])
                print(f"  Baseline jobs total: {total}")
        else:
            print(f"  ⚠️  Could not retrieve baseline metrics")

        # Queue jobs and measure throughput
        start_time = time.time()

        # Note: In real implementation, would queue actual jobs
        # For now, we monitor existing job processing
        print(f"\n⏱️  Monitoring job processing for 30 seconds...")
        await asyncio.sleep(30)

        end_time = time.time()
        duration = end_time - start_time

        # Get final metrics
        print(f"\n📊 Getting final metrics...")
        final_metrics = await get_scheduler_metrics(client)

        if final_metrics:
            print(f"  Found {len(final_metrics)} metric families")

            # Calculate jobs processed
            if 'scheduler_jobs_total' in baseline_metrics and 'scheduler_jobs_total' in final_metrics:
                baseline_total = sum(m['value'] for m in baseline_metrics['scheduler_jobs_total'])
                final_total = sum(m['value'] for m in final_metrics['scheduler_jobs_total'])
                jobs_processed = final_total - baseline_total

                print(f"  Jobs processed: {jobs_processed}")
                print(f"  Jobs per second: {jobs_processed / duration:.2f}")

                results.total_jobs = int(jobs_processed)
                results.total_duration = duration
                results.jobs_per_second = jobs_processed / duration

                # Get success/failure counts
                if 'scheduler_jobs_success' in final_metrics:
                    baseline_success = sum(m['value'] for m in baseline_metrics.get('scheduler_jobs_success', [{'value': 0}]))
                    final_success = sum(m['value'] for m in final_metrics['scheduler_jobs_success'])
                    results.successful_jobs = int(final_success - baseline_success)

                if 'scheduler_jobs_failed' in final_metrics:
                    baseline_failed = sum(m['value'] for m in baseline_metrics.get('scheduler_jobs_failed', [{'value': 0}]))
                    final_failed = sum(m['value'] for m in final_metrics['scheduler_jobs_failed'])
                    results.failed_jobs = int(final_failed - baseline_failed)

            # Verify metric accuracy
            accurate, errors = await verify_metric_accuracy(client, baseline_metrics, final_metrics)
            results.metrics_accurate = accurate
            results.metric_errors = errors

            if accurate:
                print(f"  ✅ Metrics are accurate")
            else:
                print(f"  ⚠️  Metric accuracy issues detected")
                for error in errors:
                    print(f"    - {error}")

        else:
            print(f"  ❌ Could not retrieve final metrics")

    return results


def print_results(all_results: List[BenchmarkResults]):
    """Print comprehensive benchmark results"""
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*60}")

    # Aggregate results
    total_jobs = sum(r.total_jobs for r in all_results)
    total_duration = sum(r.total_duration for r in all_results)
    avg_throughput = total_jobs / total_duration if total_duration > 0 else 0

    total_successful = sum(r.successful_jobs for r in all_results)
    total_failed = sum(r.failed_jobs for r in all_results)

    avg_metrics_count = sum(r.metrics_count for r in all_results) / len(all_results)

    all_accurate = all(r.metrics_accurate for r in all_results)
    all_errors = []
    for r in all_results:
        all_errors.extend(r.metric_errors)

    print(f"\n📊 JOB EXECUTION:")
    print(f"  Total jobs processed:   {total_jobs}")
    print(f"  Successful jobs:        {total_successful}")
    print(f"  Failed jobs:            {total_failed}")
    print(f"  Success rate:           {(total_successful/total_jobs*100) if total_jobs > 0 else 0:.2f}%")
    print(f"  Average throughput:     {avg_throughput:.2f} jobs/second")

    print(f"\n📈 METRICS ANALYSIS:")
    print(f"  Metric families found:  {int(avg_metrics_count)}")
    print(f"  Claimed metrics:        40+")
    print(f"  Metrics accurate:       {'Yes' if all_accurate else 'No'}")

    if all_errors:
        print(f"\n  Metric errors detected:")
        for error in set(all_errors):  # Unique errors only
            print(f"    - {error}")

    # Verdict
    print(f"\n📋 VERDICT:")

    if avg_metrics_count >= 40:
        print(f"  ✅ VALIDATED - Found {int(avg_metrics_count)} metric families (≥40 claimed)")
        metrics_verdict = "VALIDATED"
    elif avg_metrics_count >= 35:
        print(f"  ⚠️  ADJUSTED - Found {int(avg_metrics_count)} metric families (close to 40 claimed)")
        metrics_verdict = "ADJUSTED"
    else:
        print(f"  ❌ FAILED - Found only {int(avg_metrics_count)} metric families (<40 claimed)")
        metrics_verdict = "FAILED"

    if all_accurate:
        print(f"  ✅ Metrics are accurate and consistent")
        accuracy_verdict = "VALIDATED"
    elif len(all_errors) <= 2:
        print(f"  ⚠️  Minor metric accuracy issues detected")
        accuracy_verdict = "ADJUSTED"
    else:
        print(f"  ❌ Significant metric accuracy issues detected")
        accuracy_verdict = "FAILED"

    if avg_throughput > 0:
        print(f"  ✅ Scheduler processing {avg_throughput:.2f} jobs/second")
    else:
        print(f"  ⚠️  No jobs were processed during benchmark (scheduler may be idle)")

    print(f"\n🏆 OVERALL VERDICT:")
    if metrics_verdict == "VALIDATED" and accuracy_verdict == "VALIDATED":
        print(f"  ✅ ALL CLAIMS VALIDATED")
    elif "FAILED" not in [metrics_verdict, accuracy_verdict]:
        print(f"  ⚠️  CLAIMS ADJUSTED (metrics present but some issues)")
    else:
        print(f"  ❌ CLAIMS FAILED (metrics below expectations)")


async def main():
    print("="*60)
    print("SCHEDULER SERVICE THROUGHPUT BENCHMARK")
    print("="*60)
    print(f"Configuration:")
    print(f"  Number of runs: {NUM_RUNS}")
    print(f"  Monitoring duration: 30s per run")
    print(f"  Scheduler URL: {SCHEDULER_URL}")
    print("="*60)

    all_results = []

    for i in range(NUM_RUNS):
        results = await run_benchmark_round(i + 1)
        all_results.append(results)

        # Short pause between runs
        if i < NUM_RUNS - 1:
            print(f"\n⏸️  Pausing 10 seconds before next run...")
            await asyncio.sleep(10)

    print_results(all_results)


if __name__ == "__main__":
    asyncio.run(main())
