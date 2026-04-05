/**
 * k6 Load Testing - Shared Configuration
 *
 * Configuration for MCP Intelligence Server load tests.
 */

// Base URL for MCP Intelligence Server
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:9001';

// Test data for tool calls
export const TEST_TOOLS = {
    // Intelligence tools
    GET_EVENT_CLUSTERS: {
        name: 'get_event_clusters',
        arguments: { limit: 20, min_articles: 2 }
    },
    GET_LATEST_EVENTS: {
        name: 'get_latest_events',
        arguments: { limit: 10, hours: 24 }
    },
    GET_INTELLIGENCE_OVERVIEW: {
        name: 'get_intelligence_overview',
        arguments: {}
    },
    GET_CLUSTER_DETAILS: {
        name: 'get_cluster_details',
        arguments: { cluster_id: 'test-cluster-1' }
    },

    // Narrative tools
    ANALYZE_TEXT_NARRATIVE: {
        name: 'analyze_text_narrative',
        arguments: {
            text: 'Breaking news: Major tech company announces breakthrough in AI technology.',
            include_bias: true
        }
    },
    GET_NARRATIVE_FRAMES: {
        name: 'get_narrative_frames',
        arguments: { limit: 15 }
    },
    GET_BIAS_ANALYSIS: {
        name: 'get_bias_analysis',
        arguments: { timeframe_days: 7 }
    },
    GET_NARRATIVE_OVERVIEW: {
        name: 'get_narrative_overview',
        arguments: {}
    },

    // Entity tools
    CANONICALIZE_ENTITY: {
        name: 'canonicalize_entity',
        arguments: {
            entity_name: 'Tesla',
            entity_type: 'ORG'
        }
    },
    GET_ENTITY_CLUSTERS: {
        name: 'get_entity_clusters',
        arguments: { limit: 20 }
    },

    // OSINT tools
    DETECT_INTELLIGENCE_PATTERNS: {
        name: 'detect_intelligence_patterns',
        arguments: { timeframe_days: 30 }
    },
    ANALYZE_GRAPH_QUALITY: {
        name: 'analyze_graph_quality',
        arguments: {}
    }
};

// Request headers
export const HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
};

// Thresholds for different test types
export const THRESHOLDS = {
    smoke: {
        http_req_duration: ['p(95)<2000'],  // 95% under 2s
        http_req_failed: ['rate<0.01'],      // <1% failures
    },
    load: {
        http_req_duration: ['p(95)<3000', 'p(99)<5000'],
        http_req_failed: ['rate<0.05'],      // <5% failures
        http_reqs: ['rate>10'],               // >10 req/s
    },
    stress: {
        http_req_duration: ['p(95)<5000', 'p(99)<10000'],
        http_req_failed: ['rate<0.10'],      // <10% failures
        http_reqs: ['rate>20'],               // >20 req/s
    },
    spike: {
        http_req_duration: ['p(95)<8000'],
        http_req_failed: ['rate<0.15'],      // <15% failures during spike
    }
};

// Helper function to get random tool
export function getRandomTool() {
    const tools = Object.values(TEST_TOOLS);
    return tools[Math.floor(Math.random() * tools.length)];
}

// Helper function to get weighted random tool (prefer cached tools)
export function getWeightedRandomTool() {
    // 70% chance to use cacheable tools
    const cacheableTools = [
        TEST_TOOLS.GET_EVENT_CLUSTERS,
        TEST_TOOLS.GET_INTELLIGENCE_OVERVIEW,
        TEST_TOOLS.GET_NARRATIVE_FRAMES,
        TEST_TOOLS.GET_ENTITY_CLUSTERS,
        TEST_TOOLS.ANALYZE_GRAPH_QUALITY
    ];

    const nonCacheableTools = [
        TEST_TOOLS.GET_LATEST_EVENTS,
        TEST_TOOLS.ANALYZE_TEXT_NARRATIVE,
        TEST_TOOLS.CANONICALIZE_ENTITY,
        TEST_TOOLS.DETECT_INTELLIGENCE_PATTERNS
    ];

    if (Math.random() < 0.7) {
        return cacheableTools[Math.floor(Math.random() * cacheableTools.length)];
    } else {
        return nonCacheableTools[Math.floor(Math.random() * nonCacheableTools.length)];
    }
}
