/**
 * k6 Load Test - Normal Load Performance
 *
 * Purpose: Test system under normal expected load
 * Duration: 5 minutes
 * VUs: 10-50
 * RPS: ~50-100
 *
 * Tests:
 * - Cache effectiveness
 * - Circuit breaker behavior
 * - Response times under sustained load
 *
 * Run: docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/load.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Trend, Rate, Gauge } from 'k6/metrics';
import { BASE_URL, TEST_TOOLS, HEADERS, THRESHOLDS, getWeightedRandomTool } from './config.js';

// Custom metrics
const toolCallDuration = new Trend('tool_call_duration');
const toolCallSuccess = new Rate('tool_call_success');
const cacheHitRatio = new Gauge('cache_hit_ratio');
const circuitBreakerOpen = new Counter('circuit_breaker_open');

export const options = {
    stages: [
        { duration: '1m', target: 10 },   // Ramp up to 10 VUs
        { duration: '2m', target: 30 },   // Ramp up to 30 VUs
        { duration: '1m', target: 50 },   // Ramp up to 50 VUs
        { duration: '1m', target: 10 },   // Ramp down to 10 VUs
    ],
    thresholds: THRESHOLDS.load,
};

export default function() {
    // Group 1: Health and List Tools (warm-up)
    group('Health & Discovery', function() {
        const healthRes = http.get(`${BASE_URL}/health`);
        check(healthRes, { 'health check ok': (r) => r.status === 200 });
    });

    // Group 2: Tool Calls (main load)
    group('Tool Calls', function() {
        // Use weighted random to favor cacheable tools (70%)
        const tool = getWeightedRandomTool();

        const startTime = Date.now();
        const res = http.post(
            `${BASE_URL}/mcp/tools/call`,
            JSON.stringify(tool),
            { headers: HEADERS }
        );
        const duration = Date.now() - startTime;

        const success = check(res, {
            'status 200': (r) => r.status === 200,
            'no error': (r) => !JSON.parse(r.body).isError,
            'has content': (r) => {
                try {
                    return JSON.parse(r.body).content && JSON.parse(r.body).content.length > 0;
                } catch {
                    return false;
                }
            },
        });

        toolCallDuration.add(duration);
        toolCallSuccess.add(success ? 1 : 0);

        // Check if circuit breaker opened (5xx errors or timeouts)
        if (res.status >= 500 || res.status === 0) {
            circuitBreakerOpen.add(1);
        }
    });

    // Group 3: Metrics Check (periodic)
    if (Math.random() < 0.1) {  // 10% of requests
        group('Metrics Check', function() {
            const metricsRes = http.get(`${BASE_URL}/metrics`);
            if (metricsRes.status === 200) {
                // Parse cache hit ratio from metrics
                const metricsBody = metricsRes.body;
                const hitsMatch = metricsBody.match(/cache_hits_total\s+(\d+)/);
                const missesMatch = metricsBody.match(/cache_misses_total\s+(\d+)/);

                if (hitsMatch && missesMatch) {
                    const hits = parseInt(hitsMatch[1]);
                    const misses = parseInt(missesMatch[1]);
                    const total = hits + misses;
                    if (total > 0) {
                        cacheHitRatio.add(hits / total);
                    }
                }
            }
        });
    }

    sleep(Math.random() * 2); // Random think time 0-2s
}

export function handleSummary(data) {
    const summary = {
        test: 'load',
        duration_ms: data.state.testRunDurationMs,
        metrics: {
            requests: {
                total: data.metrics.http_reqs.values.count,
                rate: data.metrics.http_reqs.values.rate,
                failed: data.metrics.http_req_failed.values.rate,
            },
            response_time: {
                avg: data.metrics.http_req_duration.values.avg,
                p95: data.metrics.http_req_duration.values['p(95)'],
                p99: data.metrics.http_req_duration.values['p(99)'],
                max: data.metrics.http_req_duration.values.max,
            },
            tool_calls: {
                success_rate: data.metrics.tool_call_success ? data.metrics.tool_call_success.values.rate : 0,
                avg_duration: data.metrics.tool_call_duration ? data.metrics.tool_call_duration.values.avg : 0,
            },
            cache: {
                hit_ratio: data.metrics.cache_hit_ratio ? data.metrics.cache_hit_ratio.values.value : 0,
            },
            circuit_breaker: {
                opens: data.metrics.circuit_breaker_open ? data.metrics.circuit_breaker_open.values.count : 0,
            }
        }
    };

    console.log('\n=== Load Test Summary ===');
    console.log(JSON.stringify(summary, null, 2));

    return {
        'stdout': JSON.stringify(summary, null, 2),
        'summary.json': JSON.stringify(summary),
    };
}
