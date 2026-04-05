# Week 4 Performance Benchmark Suite

Rigorous benchmarks to validate all performance claims from Week 2 and Week 3.

## 🎯 Purpose

Scientifically validate performance claims with reproducible benchmarks:
- **Week 2:** FMP DCC-GARCH (0.154s), Memory stability (<2GB)
- **Week 3:** Prediction cache (30-40x), Narrative cache (13x), WebSocket (99.9%), Scheduler (40+ metrics)

## 📋 Benchmark Scripts

### Automated Benchmarks

| Script | Service | Claim | Duration |
|--------|---------|-------|----------|
| `benchmark_prediction_cache.py` | Prediction | 30-40x speedup | ~5 min |
| `benchmark_narrative_cache.py` | Narrative | 13x better than target | ~5 min |
| `benchmark_websocket_stability.py` | Analytics | 99.9% stability | 10 min |
| `benchmark_scheduler_throughput.py` | Scheduler | 40+ metrics | ~3 min |
| `benchmark_fmp_dcc_garch.py` | FMP | 0.154s DCC-GARCH | ~10 min |
| `benchmark_memory_stability.sh` | Scraping | <2GB, no leaks | 1 hour |

### Master Runner

```bash
# Run all benchmarks sequentially
./run_all_benchmarks.sh
```

## 🚀 Quick Start

### Prerequisites

1. **All services running:**
   ```bash
   docker compose up -d
   ```

2. **Python dependencies:**
   ```bash
   pip install httpx redis websockets
   ```

3. **Verify services healthy:**
   ```bash
   # Quick check
   curl http://localhost:8100/health  # Auth
   curl http://localhost:8116/health  # Prediction
   curl http://localhost:8119/health  # Narrative
   curl http://localhost:8107/health  # Analytics
   curl http://localhost:8108/health  # Scheduler
   curl http://localhost:8109/health  # FMP
   ```

### Run All Benchmarks

```bash
cd /home/cytrex/news-microservices
./scripts/benchmarks/run_all_benchmarks.sh
```

**Duration:** ~35 minutes (or ~1.5 hours with memory benchmark)

### Run Individual Benchmarks

```bash
# Prediction cache speedup
python3 scripts/benchmarks/benchmark_prediction_cache.py

# Narrative cache performance
python3 scripts/benchmarks/benchmark_narrative_cache.py

# WebSocket stability
python3 scripts/benchmarks/benchmark_websocket_stability.py

# Scheduler metrics
python3 scripts/benchmarks/benchmark_scheduler_throughput.py

# FMP DCC-GARCH
python3 scripts/benchmarks/benchmark_fmp_dcc_garch.py

# Memory stability (1 hour)
./scripts/benchmarks/benchmark_memory_stability.sh
```

## 📊 Benchmark Details

### 1. Prediction Service Cache

**Claim:** 30-40x speedup (5-15ms cached vs 350-450ms uncached)

**Method:**
- Clear Redis before each uncached request
- Prime cache for cached requests
- 100 requests × 3 runs = 300 samples each
- Calculate speedup = uncached_avg / cached_avg

**Success Criteria:**
- Speedup within ±20% of 30-40x range (24-48x)
- Cached latency within 5-15ms
- Uncached latency within 350-450ms

### 2. Narrative Service Cache

**Claim:** 13x better than 2s target (3-5ms cached vs 2s target)

**Method:**
- Clear Redis before each uncached request
- Prime cache for cached requests
- 100 requests × 3 runs = 300 samples each
- Calculate target_vs_cached = 2000ms / cached_avg

**Success Criteria:**
- Performance ≥10.4x better than target (within ±20% of 13x)
- Cached latency within 3-5ms
- Uncached baseline ~150ms

### 3. Analytics WebSocket Stability

**Claim:** 99.9% stability with 100+ concurrent connections

**Method:**
- Open 100 concurrent WebSocket connections
- Maintain for 10 minutes
- Monitor: connection success, reconnects, message delivery
- Calculate stability = successful_connections / total * 100

**Success Criteria:**
- Stability ≥ 99.9% (max 0.1 failures per 100 connections)
- Heartbeat responses working
- Graceful reconnection if needed

### 4. Scheduler Prometheus Metrics

**Claim:** 40+ metrics operational and accurate

**Method:**
- Capture baseline Prometheus metrics
- Monitor scheduler for 30 seconds
- Capture final metrics
- Verify metric count and accuracy

**Success Criteria:**
- Metric families ≥ 40
- Metrics accurately reflect job execution
- Success + Failed = Total jobs

### 5. FMP DCC-GARCH Performance

**Claim:** 0.154s execution (6-7x better than <1s target)

**Method:**
- Run DCC-GARCH on 4 assets
- 50 requests × 3 runs = 150 samples
- Measure execution time

**Success Criteria:**
- Average ≤ 0.185s (within ±20% of 0.154s)
- Performance ≥5x better than 1s target
- Consistent across runs

### 6. Scraping Service Memory

**Claim:** Memory stable < 2GB, no leaks

**Method:**
- Monitor container memory every 30 seconds
- Run for 1 hour
- Track: average, peak, trend

**Success Criteria:**
- Peak memory < 2GB (2048MB)
- Hourly growth rate < 200MB/hour
- No memory leak pattern

## 📈 Results & Reporting

### Output Files

```
reports/performance/week4/
├── WEEK4_BENCHMARK_RESULTS.md          # Main report (update after run)
├── benchmark_run_<timestamp>.log        # Raw log from all benchmarks
└── memory_stability_results.csv         # Memory monitoring CSV
```

### Viewing Results

```bash
# View full log
less reports/performance/week4/benchmark_run_<timestamp>.log

# View memory CSV
column -t -s, reports/performance/week4/memory_stability_results.csv | less

# Check service logs if benchmark fails
docker logs prediction-service
docker logs narrative-service
docker logs analytics-service
```

### Update Report

After benchmarks complete, update `WEEK4_BENCHMARK_RESULTS.md`:
1. Fill in "Results" tables with actual numbers
2. Update "Verdict" columns
3. Complete "Conclusion" section
4. Document any failures or adjustments

## 🔬 Troubleshooting

### Services Not Responding

```bash
# Check service status
docker compose ps

# Restart unhealthy services
docker compose restart <service-name>

# Check logs
docker logs <service-name>
```

### Redis Connection Issues

```bash
# Check Redis
docker compose ps redis

# Flush Redis manually
docker exec -it redis redis-cli FLUSHDB

# Restart Redis
docker compose restart redis
```

### High Latency Results

**Check:**
1. CPU load: `htop` - should be < 80%
2. Memory: `free -h` - should have free RAM
3. Network: `ping localhost` - should be <1ms
4. Other processes competing for resources

**Fix:**
- Close other applications
- Restart Docker
- Run benchmarks when system is idle

### Benchmark Script Errors

```bash
# Check Python dependencies
pip install httpx redis websockets

# Check script permissions
chmod +x scripts/benchmarks/*.py scripts/benchmarks/*.sh

# Run with verbose output
python3 -v scripts/benchmarks/benchmark_prediction_cache.py
```

## 📐 Statistical Methodology

### Sample Size

- **Cache benchmarks:** 100 requests × 3 runs = 300 samples
  - Sufficient for <5% margin of error at 95% confidence
- **WebSocket:** 100 connections × 10 minutes = large sample
- **Memory:** 120 samples (30s interval × 1 hour)

### Variance Acceptance

- **±20% variance** = claims validated
- **Example:** Claimed 30-40x speedup
  - Accept: 24-48x (20% margin)
  - Adjusted: 20-24x or 48-60x (good but not exact)
  - Failed: <20x (significantly below)

### Statistical Measures

- **Average (Mean):** Primary metric
- **Median (P50):** Central tendency, robust to outliers
- **P95:** 95th percentile, excludes extreme outliers
- **Min/Max:** Range check

## 🎯 Acceptance Criteria Summary

| Verdict | Criteria |
|---------|----------|
| ✅ **VALIDATED** | Within ±20% of claimed performance |
| ⚠️ **ADJUSTED** | Performance good but outside ±20% variance |
| ❌ **FAILED** | Performance significantly below claims |

## 🔄 Reproducibility

**To reproduce results:**

1. **Same environment:**
   - Docker Compose setup (same docker-compose.yml)
   - Same service versions (git commit)
   - Similar hardware specs

2. **Same methodology:**
   - Same test data (hardcoded in scripts)
   - Same request counts
   - Same test duration

3. **Run multiple times:**
   - Each benchmark has 3 runs built-in
   - Re-run entire suite if results vary >10%

**Expected variance:**
- Cache benchmarks: ±5% between runs
- WebSocket: ±0.1% stability
- Memory: ±10% peak memory

## 📞 Support

**If benchmarks fail:**

1. Check `reports/performance/week4/benchmark_run_<timestamp>.log`
2. Review service logs: `docker logs <service-name>`
3. Verify services healthy: `./scripts/health_check.sh` (if exists)
4. Check [POSTMORTEMS.md](/home/cytrex/news-microservices/POSTMORTEMS.md) for known issues

**For questions:**
- Review Week 2/3 retrospectives
- Check service-specific README files
- See [ARCHITECTURE.md](/home/cytrex/news-microservices/ARCHITECTURE.md)

---

**Created:** 2025-11-24
**Status:** Ready to run
**Next:** Execute `./run_all_benchmarks.sh` and update results report
