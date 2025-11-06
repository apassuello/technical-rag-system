/**
 * Epic 8 Comprehensive Load Testing Suite
 * K6 script for testing auto-scaling and performance under load
 * Swiss engineering precision with detailed metrics collection
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Epic 8 Custom Metrics
const epic8Latency = new Trend('epic8_end_to_end_latency', true);
const epic8ErrorRate = new Rate('epic8_error_rate');
const epic8Throughput = new Counter('epic8_requests_total');
const epic8ConcurrentUsers = new Gauge('epic8_concurrent_users');
const epic8CostPerQuery = new Trend('epic8_cost_per_query_usd');
const epic8SuccessRate = new Rate('epic8_success_rate');

// Service-specific metrics
const apiGatewayLatency = new Trend('epic8_api_gateway_latency');
const generatorLatency = new Trend('epic8_generator_latency');
const analyzerLatency = new Trend('epic8_analyzer_latency');
const retrieverLatency = new Trend('epic8_retriever_latency');
const cacheHitRate = new Rate('epic8_cache_hit_rate');

// Configuration
const BASE_URL = __ENV.EPIC8_BASE_URL || 'https://api.epic8.platform';
const API_VERSION = __ENV.API_VERSION || 'v1';
const API_KEY = __ENV.EPIC8_API_KEY || 'test-api-key';

// Test data - Realistic RAG queries
const testQueries = [
  "What are the best practices for Kubernetes auto-scaling?",
  "How do I optimize vector search performance in production?",
  "Explain the differences between HPA and VPA in Kubernetes",
  "What are the cost optimization strategies for multi-cloud deployments?",
  "How does model routing work in multi-model RAG systems?",
  "What are the Swiss engineering principles for system reliability?",
  "How to implement circuit breaker patterns in microservices?",
  "What metrics should I monitor for ML model performance?",
  "How to handle cache invalidation in distributed systems?",
  "What are the best practices for prompt engineering in RAG?",
  "How to implement proper observability in cloud-native applications?",
  "What are the security considerations for RAG systems?",
  "How to optimize database queries for vector similarity search?",
  "What are the trade-offs between accuracy and latency in ML systems?",
  "How to implement blue-green deployments with zero downtime?"
];

// Load test scenarios configuration
export let options = {
  scenarios: {
    // Baseline load test - Normal traffic pattern
    baseline_load: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up to 50 users
        { duration: '5m', target: 50 },   // Stay at 50 users
        { duration: '2m', target: 100 },  // Ramp up to 100 users
        { duration: '10m', target: 100 }, // Stay at 100 users
        { duration: '2m', target: 0 },    // Ramp down
      ],
    },

    // Peak load test - Traffic spikes
    peak_load: {
      executor: 'ramping-vus',
      startVUs: 50,
      stages: [
        { duration: '1m', target: 200 },  // Quick ramp to 200 users
        { duration: '3m', target: 500 },  // Spike to 500 users
        { duration: '5m', target: 500 },  // Sustain peak load
        { duration: '2m', target: 200 },  // Gradual decrease
        { duration: '1m', target: 0 },    // Ramp down
      ],
      startTime: '15m', // Start after baseline
    },

    // Stress test - Beyond normal capacity
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '2m', target: 500 },  // Ramp to 500 users
        { duration: '3m', target: 1000 }, // Stress to 1000 users
        { duration: '5m', target: 1000 }, // Sustain stress
        { duration: '2m', target: 500 },  // Step down
        { duration: '2m', target: 0 },    // Ramp down
      ],
      startTime: '25m', // Start after peak load
    },

    // Spike test - Sudden load increase
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '30s', target: 100 }, // Normal load
        { duration: '30s', target: 1500 }, // Sudden spike
        { duration: '1m', target: 1500 },  // Sustain spike
        { duration: '30s', target: 100 },  // Return to normal
        { duration: '30s', target: 0 },    // Ramp down
      ],
      startTime: '40m', // Start after stress test
    },

    // Endurance test - Long duration
    endurance_test: {
      executor: 'constant-vus',
      vus: 200,
      duration: '30m',
      startTime: '45m', // Start after spike test
    },

    // Auto-scaling validation test
    autoscaling_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      stages: [
        { duration: '2m', target: 20 },   // 20 RPS
        { duration: '2m', target: 50 },   // 50 RPS
        { duration: '2m', target: 100 },  // 100 RPS
        { duration: '2m', target: 200 },  // 200 RPS - Should trigger scaling
        { duration: '5m', target: 200 },  // Sustain to validate scaling
        { duration: '2m', target: 50 },   // Scale down
        { duration: '2m', target: 10 },   // Return to baseline
      ],
      startTime: '80m', // Start after endurance
    }
  },

  // Global thresholds for Swiss engineering precision
  thresholds: {
    // System-wide SLOs
    'epic8_end_to_end_latency': [
      'p(95)<2000',     // 95% under 2s (SLO requirement)
      'p(99)<5000',     // 99% under 5s
    ],
    'epic8_error_rate': ['rate<0.01'],      // Error rate < 1%
    'epic8_success_rate': ['rate>0.995'],   // Success rate > 99.5%

    // Service-specific thresholds
    'epic8_api_gateway_latency': ['p(95)<500'],  // API Gateway < 500ms
    'epic8_generator_latency': ['p(95)<1500'],   // Generator < 1.5s
    'epic8_analyzer_latency': ['p(95)<200'],     // Analyzer < 200ms
    'epic8_retriever_latency': ['p(95)<100'],    // Retriever < 100ms
    'epic8_cache_hit_rate': ['rate>0.90'],       // Cache hit rate > 90%

    // Cost and efficiency thresholds
    'epic8_cost_per_query_usd': ['p(95)<0.01'], // Cost < $0.01 per query

    // HTTP-level thresholds
    'http_req_duration': ['p(95)<2000'],
    'http_req_failed': ['rate<0.01'],
  },
};

// Setup function - runs once before test
export function setup() {
  console.log('🚀 Starting Epic 8 Load Testing Suite');
  console.log(`📍 Target: ${BASE_URL}`);
  console.log(`🔑 API Version: ${API_VERSION}`);

  // Validate API connectivity
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'API is healthy': (r) => r.status === 200,
  });

  return {
    baseUrl: BASE_URL,
    apiVersion: API_VERSION,
    timestamp: new Date().toISOString(),
  };
}

// Main test function
export default function(data) {
  const startTime = Date.now();

  // Update concurrent users metric
  epic8ConcurrentUsers.add(__VU);

  // Select random query for realistic testing
  const query = randomItem(testQueries);
  const complexity = getQueryComplexity(query);

  // Construct request
  const payload = JSON.stringify({
    query: query,
    options: {
      max_tokens: 500,
      temperature: 0.7,
      include_sources: true,
      model_preference: randomItem(['auto', 'fast', 'balanced', 'quality']),
    },
    metadata: {
      user_id: `load_test_user_${__VU}`,
      session_id: `session_${__ITER}`,
      complexity: complexity,
      timestamp: new Date().toISOString(),
    }
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'X-Epic8-Test': 'load-testing',
      'X-Epic8-VU': __VU.toString(),
      'X-Epic8-Iteration': __ITER.toString(),
    },
    timeout: '30s',
  };

  // Execute end-to-end RAG query
  const response = http.post(`${BASE_URL}/${API_VERSION}/query`, payload, params);

  const endTime = Date.now();
  const duration = endTime - startTime;

  // Record metrics
  epic8Latency.add(duration);
  epic8Throughput.add(1);

  // Validate response
  const success = check(response, {
    'Status is 200': (r) => r.status === 200,
    'Response has answer': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.answer && body.answer.length > 0;
      } catch {
        return false;
      }
    },
    'Response has sources': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.sources && Array.isArray(body.sources);
      } catch {
        return false;
      }
    },
    'Response time acceptable': (r) => r.timings.duration < 5000,
    'No server errors': (r) => r.status < 500,
  });

  // Record success/error metrics
  epic8SuccessRate.add(success);
  epic8ErrorRate.add(!success);

  // Parse response for detailed metrics
  if (response.status === 200) {
    try {
      const body = JSON.parse(response.body);

      // Service-specific latencies (if provided in response)
      if (body.metrics) {
        if (body.metrics.api_gateway_latency) {
          apiGatewayLatency.add(body.metrics.api_gateway_latency);
        }
        if (body.metrics.generator_latency) {
          generatorLatency.add(body.metrics.generator_latency);
        }
        if (body.metrics.analyzer_latency) {
          analyzerLatency.add(body.metrics.analyzer_latency);
        }
        if (body.metrics.retriever_latency) {
          retrieverLatency.add(body.metrics.retriever_latency);
        }
        if (body.metrics.cache_hit !== undefined) {
          cacheHitRate.add(body.metrics.cache_hit ? 1 : 0);
        }
        if (body.metrics.cost_usd) {
          epic8CostPerQuery.add(body.metrics.cost_usd);
        }
      }
    } catch (e) {
      console.warn(`Failed to parse response metrics: ${e.message}`);
    }
  } else {
    console.warn(`Request failed: ${response.status} - ${response.body}`);
  }

  // Realistic user behavior - think time
  const thinkTime = getThinkTime(complexity);
  sleep(thinkTime);
}

// Utility functions
function getQueryComplexity(query) {
  const length = query.length;
  const keywords = ['best practices', 'optimization', 'performance', 'architecture'];
  const hasComplexKeywords = keywords.some(keyword => query.toLowerCase().includes(keyword));

  if (length > 80 || hasComplexKeywords) {
    return 'complex';
  } else if (length > 40) {
    return 'medium';
  } else {
    return 'simple';
  }
}

function getThinkTime(complexity) {
  switch (complexity) {
    case 'simple':
      return randomIntBetween(1, 3);  // 1-3 seconds
    case 'medium':
      return randomIntBetween(2, 5);  // 2-5 seconds
    case 'complex':
      return randomIntBetween(3, 8);  // 3-8 seconds
    default:
      return randomIntBetween(2, 4);  // 2-4 seconds
  }
}

// Teardown function - runs once after test
export function teardown(data) {
  console.log('🏁 Epic 8 Load Testing Complete');
  console.log(`📊 Test started at: ${data.timestamp}`);
  console.log(`🎯 Target: ${data.baseUrl}`);

  // Additional cleanup or reporting could go here
}

// Health check scenario for continuous monitoring
export function healthCheck() {
  const response = http.get(`${BASE_URL}/health`);
  check(response, {
    'Health check successful': (r) => r.status === 200,
    'Health check fast': (r) => r.timings.duration < 1000,
  });
}

// Auto-scaling trigger scenario
export function autoScalingTrigger() {
  // Simulate load pattern that should trigger HPA scaling
  const burst = 10; // Number of concurrent requests
  const promises = [];

  for (let i = 0; i < burst; i++) {
    const query = randomItem(testQueries);
    const payload = JSON.stringify({
      query: query,
      options: { max_tokens: 500 },
      metadata: { trigger_test: true }
    });

    promises.push(
      http.asyncRequest('POST', `${BASE_URL}/${API_VERSION}/query`, payload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`,
          'X-Epic8-Test': 'autoscaling-trigger',
        }
      })
    );
  }

  // Wait for all requests to complete
  const responses = Promise.all(promises);

  check(responses, {
    'Burst requests successful': (rs) => rs.every(r => r.status === 200),
  });
}