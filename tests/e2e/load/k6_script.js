/**
 * K6 Load Testing Script
 * Tests performance under various load conditions
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Stay at 100 users
    { duration: '1m', target: 200 },   // Spike to 200 users
    { duration: '1m', target: 100 },   // Scale down to 100
    { duration: '30s', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete within 500ms
    errors: ['rate<0.1'],              // Error rate must be below 10%
    http_req_failed: ['rate<0.05'],    // Failed requests must be below 5%
  },
};

const BASE_URL = 'http://localhost:8000';
const SERVICES = {
  auth: 8000,
  feed: 8001,
  content: 8002,
  research: 8003,
  osint: 8004,
  notification: 8005,
  search: 8006,
  analytics: 8007,
};

// Generate random user credentials
function generateUser() {
  const id = Math.floor(Math.random() * 1000000);
  return {
    email: `k6test_${id}@example.com`,
    password: 'K6Test123!@#',
    username: `k6test_${id}`,
    full_name: `K6 Test User ${id}`,
  };
}

// Register and login
function authenticateUser() {
  const user = generateUser();

  // Register
  const registerRes = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify(user),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'Register' },
    }
  );

  check(registerRes, {
    'registration successful': (r) => r.status === 201,
  }) || errorRate.add(1);

  // Login
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    {
      username: user.email,
      password: user.password,
    },
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      tags: { name: 'Login' },
    }
  );

  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => r.json('access_token') !== undefined,
  }) || errorRate.add(1);

  const token = loginRes.json('access_token');
  return token;
}

// Test scenarios
export default function () {
  // Authenticate
  const token = authenticateUser();
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  sleep(1);

  // Create feed
  const feedRes = http.post(
    `http://localhost:${SERVICES.feed}/api/feeds`,
    JSON.stringify({
      url: 'https://news.ycombinator.com/rss',
      name: `K6 Test Feed ${Math.random()}`,
      category: 'technology',
      fetch_interval: 3600,
    }),
    {
      headers,
      tags: { name: 'CreateFeed' },
    }
  );

  check(feedRes, {
    'feed created': (r) => r.status === 201,
  }) || errorRate.add(1);

  sleep(1);

  // View feeds
  const viewFeedsRes = http.get(
    `http://localhost:${SERVICES.feed}/api/feeds`,
    {
      headers,
      tags: { name: 'ViewFeeds' },
    }
  );

  check(viewFeedsRes, {
    'feeds retrieved': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // Search articles
  const searchRes = http.get(
    `http://localhost:${SERVICES.search}/api/search?q=technology&limit=10`,
    {
      headers,
      tags: { name: 'SearchArticles' },
    }
  );

  check(searchRes, {
    'search completed': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // View notifications
  const notifRes = http.get(
    `http://localhost:${SERVICES.notification}/api/notifications`,
    {
      headers,
      tags: { name: 'ViewNotifications' },
    }
  );

  check(notifRes, {
    'notifications retrieved': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // View analytics
  const analyticsRes = http.get(
    `http://localhost:${SERVICES.analytics}/api/analytics/dashboard`,
    {
      headers,
      tags: { name: 'ViewAnalytics' },
    }
  );

  check(analyticsRes, {
    'analytics retrieved': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(2);
}

// Health check scenario (separate)
export function healthCheck() {
  Object.entries(SERVICES).forEach(([name, port]) => {
    const res = http.get(`http://localhost:${port}/health`, {
      tags: { name: `HealthCheck_${name}` },
    });

    check(res, {
      [`${name} service healthy`]: (r) => r.status === 200 && r.json('status') === 'healthy',
    }) || errorRate.add(1);
  });
}
