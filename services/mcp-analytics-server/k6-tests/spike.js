/**
 * k6 Spike Test - Sudden Load Bursts
 *
 * Purpose: Test system behavior during sudden traffic spikes
 * Duration: 5 minutes
 * VUs: 10 → 300 → 10 (sudden spike)
 * RPS: ~50 → ~1000+ → ~50
 *
 * Tests:
 * - Circuit breaker fast-fail
 * - Cache behavior during spike
 * - Recovery after spike
 *
 * Run: docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/spike.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import { BASE_URL, TEST_TOOLS, HEADERS, THRESHOLDS, getWeightedRandomTool } from './config.js';

// Custom metrics
const toolCallDuration = new Trend('tool_call_duration');
const toolCallSuccess = new Rate('tool_call_success');
const spikeErrors = new Counter('spike_errors');
const recoveryTime = new Trend('recovery_time');

export const options = {
    stages: [
        { duration: '1m', target: 10 },     // Normal load
        { duration: '30s', target: 300 },   // Sudden spike to 300 VUs
        { duration: '1m', target: 300 },    // Hold spike
        { duration: '30s', target: 10 },    // Drop back to normal
        { duration: '1m', target: 10 },     // Recovery period
    ],
    thresholds: THRESHOLDS.spike,
};

let spikeStartTime = null;
let recoveryStartTime = null;

export default function() {
    const currentVUs = __VU;

    // Detect spike start (transition to high load)
    if (currentVUs > 100 && spikeStartTime === null) {
        spikeStartTime = Date.now();
    }

    // Detect recovery start (transition back to low load)
    if (currentVUs <= 50 && spikeStartTime !== null && recoveryStartTime === null) {
        recoveryStartTime = Date.now();
    }

    // Use weighted random during normal load, random during spike
    const tool = currentVUs > 100 ? getWeightedRandomTool() : getWeightedRandomTool();

    const startTime = Date.now();
    const res = http.post(
        `${BASE_URL}/mcp/tools/call`,
        JSON.stringify(tool),
        {
            headers: HEADERS,
            timeout: '20s'
        }
    );
    const duration = Date.now() - startTime;

    const success = check(res, {
        'status ok': (r) => r.status === 200,
        'no error': (r) => {
            try {
                return !JSON.parse(r.body).isError;
            } catch {
                return false;
            }
        },
    });

    toolCallDuration.add(duration);
    toolCallSuccess.add(success ? 1 : 0);

    // Track errors during spike
    if (currentVUs > 100 && !success) {
        spikeErrors.add(1);
    }

    // Track recovery time
    if (recoveryStartTime !== null && success) {
        const timeSinceRecovery = Date.now() - recoveryStartTime;
        if (timeSinceRecovery < 60000) {  // First minute of recovery
            recoveryTime.add(duration);
        }
    }

    // Minimal think time during spike, normal during recovery
    sleep(currentVUs > 100 ? 0.1 : Math.random());
}

export function handleSummary(data) {
    const summary = {
        test: 'spike',
        duration_ms: data.state.testRunDurationMs,
        spike_profile: '10 → 300 → 10 VUs',
        metrics: {
            requests: {
                total: data.metrics.http_reqs.values.count,
                rate_avg: data.metrics.http_reqs.values.rate,
                failed_rate: data.metrics.http_req_failed.values.rate,
            },
            response_time: {
                avg: data.metrics.http_req_duration.values.avg,
                p50: data.metrics.http_req_duration.values.med,
                p95: data.metrics.http_req_duration.values['p(95)'],
                p99: data.metrics.http_req_duration.values['p(99)'],
                max: data.metrics.http_req_duration.values.max,
            },
            spike: {
                errors_during_spike: data.metrics.spike_errors ? data.metrics.spike_errors.values.count : 0,
                success_rate: data.metrics.tool_call_success ? data.metrics.tool_call_success.values.rate : 0,
            },
            recovery: {
                avg_duration: data.metrics.recovery_time ? data.metrics.recovery_time.values.avg : 0,
                p95_duration: data.metrics.recovery_time ? data.metrics.recovery_time.values['p(95)'] : 0,
            }
        },
        analysis: {
            spike_handled_well: data.metrics.http_req_failed.values.rate < 0.20,  // <20% failure is acceptable during spike
            circuit_breaker_protected: (data.metrics.spike_errors ? data.metrics.spike_errors.values.count : 0) > 0,
            fast_recovery: (data.metrics.recovery_time ? data.metrics.recovery_time.values.avg : 0) < 2000,  // <2s avg recovery
        }
    };

    console.log('\n=== Spike Test Summary ===');
    console.log(JSON.stringify(summary, null, 2));

    return {
        'stdout': JSON.stringify(summary, null, 2),
        'spike-summary.json': JSON.stringify(summary),
    };
}
