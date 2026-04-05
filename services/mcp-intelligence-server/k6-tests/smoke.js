/**
 * k6 Smoke Test - Basic Functionality Verification
 *
 * Purpose: Verify system works under minimal load
 * Duration: 1 minute
 * VUs: 1-2
 * RPS: ~5-10
 *
 * Run: docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/smoke.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import { BASE_URL, TEST_TOOLS, HEADERS, THRESHOLDS } from './config.js';

// Custom metrics
const toolCallDuration = new Trend('tool_call_duration');
const toolCallSuccess = new Rate('tool_call_success');
const cacheHits = new Counter('cache_hits');

export const options = {
    stages: [
        { duration: '30s', target: 1 },  // Ramp up to 1 VU
        { duration: '30s', target: 2 },  // Ramp up to 2 VUs
    ],
    thresholds: THRESHOLDS.smoke,
};

export default function() {
    // Test 1: Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
        'health check status 200': (r) => r.status === 200,
        'health check is healthy': (r) => JSON.parse(r.body).status === 'healthy',
    });

    // Test 2: List tools (GET request)
    const listRes = http.get(`${BASE_URL}/mcp/tools/list`);
    check(listRes, {
        'list tools status 200': (r) => r.status === 200,
        'list tools has tools': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.tools && body.tools.length > 0;
            } catch {
                return false;
            }
        },
    });

    // Test 3: Call intelligence overview (cacheable)
    const startTime = Date.now();
    const toolRes = http.post(
        `${BASE_URL}/mcp/tools/call`,
        JSON.stringify(TEST_TOOLS.GET_INTELLIGENCE_OVERVIEW),
        { headers: HEADERS }
    );
    const duration = Date.now() - startTime;

    const success = check(toolRes, {
        'tool call status 200': (r) => r.status === 200,
        'tool call no error': (r) => !JSON.parse(r.body).isError,
        'tool call has content': (r) => JSON.parse(r.body).content && JSON.parse(r.body).content.length > 0,
    });

    toolCallDuration.add(duration);
    toolCallSuccess.add(success ? 1 : 0);

    // Test 4: Metrics endpoint
    const metricsRes = http.get(`${BASE_URL}/metrics`);
    check(metricsRes, {
        'metrics endpoint status 200': (r) => r.status === 200,
        'metrics has data': (r) => r.body.length > 0,
    });

    sleep(1); // Think time
}

export function handleSummary(data) {
    return {
        'stdout': JSON.stringify({
            test: 'smoke',
            duration: data.state.testRunDurationMs,
            requests: data.metrics.http_reqs.values.count,
            failures: data.metrics.http_req_failed.values.rate,
            p95: data.metrics.http_req_duration.values['p(95)'],
            p99: data.metrics.http_req_duration.values['p(99)'],
            tool_call_success: data.metrics.tool_call_success ? data.metrics.tool_call_success.values.rate : 0,
        }, null, 2)
    };
}
