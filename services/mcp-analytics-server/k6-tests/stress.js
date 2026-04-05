/**
 * k6 Stress Test - High Load & Breaking Point
 *
 * Purpose: Find system limits and breaking point
 * Duration: 10 minutes
 * VUs: 10-200
 * RPS: ~100-500+
 *
 * Tests:
 * - System behavior under extreme load
 * - Circuit breaker activation
 * - Cache saturation
 * - Error rates
 *
 * Run: docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/stress.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Trend, Rate, Gauge } from 'k6/metrics';
import { BASE_URL, TEST_TOOLS, HEADERS, THRESHOLDS, getRandomTool } from './config.js';

// Custom metrics
const toolCallDuration = new Trend('tool_call_duration');
const toolCallSuccess = new Rate('tool_call_success');
const circuitBreakerTrips = new Counter('circuit_breaker_trips');
const serverErrors = new Counter('server_errors');
const timeouts = new Counter('timeouts');

export const options = {
    stages: [
        { duration: '2m', target: 50 },    // Ramp up to 50 VUs
        { duration: '3m', target: 100 },   // Ramp up to 100 VUs
        { duration: '2m', target: 150 },   // Ramp up to 150 VUs
        { duration: '1m', target: 200 },   // Push to 200 VUs
        { duration: '2m', target: 0 },     // Ramp down
    ],
    thresholds: THRESHOLDS.stress,
};

export default function() {
    // Aggressive load - minimal think time
    const tool = getRandomTool();

    const startTime = Date.now();
    const res = http.post(
        `${BASE_URL}/mcp/tools/call`,
        JSON.stringify(tool),
        {
            headers: HEADERS,
            timeout: '30s'  // 30s timeout
        }
    );
    const duration = Date.now() - startTime;

    // Check response
    const success = check(res, {
        'status < 500': (r) => r.status < 500,
        'no timeout': (r) => r.status !== 0,
    });

    toolCallDuration.add(duration);
    toolCallSuccess.add(success ? 1 : 0);

    // Track different error types
    if (res.status === 503 || res.status === 429) {
        circuitBreakerTrips.add(1);
    }
    if (res.status >= 500) {
        serverErrors.add(1);
    }
    if (res.status === 0) {
        timeouts.add(1);
    }

    // Very short think time under stress
    sleep(Math.random() * 0.5);
}

export function handleSummary(data) {
    const summary = {
        test: 'stress',
        duration_ms: data.state.testRunDurationMs,
        max_vus: 200,
        metrics: {
            requests: {
                total: data.metrics.http_reqs.values.count,
                rate: data.metrics.http_reqs.values.rate,
                failed_rate: data.metrics.http_req_failed.values.rate,
            },
            response_time: {
                avg: data.metrics.http_req_duration.values.avg,
                median: data.metrics.http_req_duration.values.med,
                p95: data.metrics.http_req_duration.values['p(95)'],
                p99: data.metrics.http_req_duration.values['p(99)'],
                max: data.metrics.http_req_duration.values.max,
            },
            errors: {
                circuit_breaker_trips: data.metrics.circuit_breaker_trips ? data.metrics.circuit_breaker_trips.values.count : 0,
                server_errors: data.metrics.server_errors ? data.metrics.server_errors.values.count : 0,
                timeouts: data.metrics.timeouts ? data.metrics.timeouts.values.count : 0,
            },
            tool_calls: {
                success_rate: data.metrics.tool_call_success ? data.metrics.tool_call_success.values.rate : 0,
                avg_duration: data.metrics.tool_call_duration ? data.metrics.tool_call_duration.values.avg : 0,
                p95_duration: data.metrics.tool_call_duration ? data.metrics.tool_call_duration.values['p(95)'] : 0,
            }
        },
        analysis: {
            breaking_point_reached: data.metrics.http_req_failed.values.rate > 0.5,
            circuit_breaker_effective: (data.metrics.circuit_breaker_trips ? data.metrics.circuit_breaker_trips.values.count : 0) > 0,
        }
    };

    console.log('\n=== Stress Test Summary ===');
    console.log(JSON.stringify(summary, null, 2));

    return {
        'stdout': JSON.stringify(summary, null, 2),
        'stress-summary.json': JSON.stringify(summary),
    };
}
