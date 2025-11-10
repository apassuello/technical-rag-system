package epic8.platform

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._
import scala.util.Random

/**
 * Epic 8 Comprehensive Load Testing Suite - Gatling Implementation
 * Swiss engineering precision with advanced auto-scaling validation
 *
 * Test Scenarios:
 * 1. Baseline Load (100 users)
 * 2. Peak Load (500 users)
 * 3. Stress Test (1000 users)
 * 4. Spike Test (1500 users burst)
 * 5. Endurance Test (200 users for 30 minutes)
 * 6. Auto-scaling Validation
 */
class Epic8LoadTestSuite extends Simulation {

  // Configuration
  val baseUrl = System.getProperty("epic8.baseUrl", "https://api.epic8.platform")
  val apiVersion = System.getProperty("epic8.apiVersion", "v1")
  val apiKey = System.getProperty("epic8.apiKey", "test-api-key")
  val environment = System.getProperty("epic8.environment", "staging")

  // HTTP Protocol Configuration
  val httpProtocol = http
    .baseUrl(baseUrl)
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")
    .authorizationHeader(s"Bearer $apiKey")
    .userAgentHeader("Epic8-Gatling-LoadTest/1.0")
    .header("X-Epic8-Test", "gatling-load-testing")
    .header("X-Epic8-Environment", environment)
    // Swiss engineering precision - detailed connection settings
    .connectionHeader("keep-alive")
    .maxConnectionsPerHost(10)
    .shareConnections

  // Test Data - Realistic RAG queries with complexity classification
  val queries = Array(
    ("What are the best practices for Kubernetes auto-scaling?", "complex"),
    ("How do I optimize vector search performance in production?", "complex"),
    ("Explain the differences between HPA and VPA in Kubernetes", "medium"),
    ("What are the cost optimization strategies for multi-cloud deployments?", "complex"),
    ("How does model routing work in multi-model RAG systems?", "complex"),
    ("What are the Swiss engineering principles for system reliability?", "medium"),
    ("How to implement circuit breaker patterns in microservices?", "medium"),
    ("What metrics should I monitor for ML model performance?", "complex"),
    ("How to handle cache invalidation in distributed systems?", "medium"),
    ("What are the best practices for prompt engineering in RAG?", "medium"),
    ("How to implement proper observability in cloud-native applications?", "complex"),
    ("What are the security considerations for RAG systems?", "complex"),
    ("How to optimize database queries for vector similarity search?", "complex"),
    ("What are the trade-offs between accuracy and latency in ML systems?", "complex"),
    ("How to implement blue-green deployments with zero downtime?", "medium"),
    ("What is Kubernetes?", "simple"),
    ("How to scale pods?", "simple"),
    ("What is a RAG system?", "simple"),
    ("How to monitor applications?", "simple"),
    ("What is auto-scaling?", "simple")
  )

  // Model preferences for realistic testing
  val modelPreferences = Array("auto", "fast", "balanced", "quality")

  // Feeders for test data
  val queryFeeder = queries.circular
  val modelFeeder = modelPreferences.circular
  val userIdFeeder = Iterator.continually(Map("userId" -> s"gatling_user_${Random.nextInt(10000)}"))

  // Scenarios

  // Core RAG Query Scenario
  val ragQueryScenario = scenario("RAG Query")
    .feed(queryFeeder)
    .feed(modelFeeder)
    .feed(userIdFeeder)
    .exec(
      http("Execute RAG Query")
        .post(s"/$apiVersion/query")
        .body(StringBody(session => {
          val (query, complexity) = session("queries").as[(String, String)]
          val modelPref = session("modelPreferences").as[String]
          val userId = session("userId").as[String]

          s"""
          {
            "query": "$query",
            "options": {
              "max_tokens": 500,
              "temperature": 0.7,
              "include_sources": true,
              "model_preference": "$modelPref"
            },
            "metadata": {
              "user_id": "$userId",
              "session_id": "gatling_session_${System.currentTimeMillis()}",
              "complexity": "$complexity",
              "timestamp": "${java.time.Instant.now()}"
            }
          }
          """
        }))
        .check(
          status.is(200),
          jsonPath("$.answer").exists,
          jsonPath("$.sources").exists,
          responseTimeInMillis.lte(5000),
          // Epic 8 SLO validations
          jsonPath("$.metrics.end_to_end_latency").optional.saveAs("endToEndLatency"),
          jsonPath("$.metrics.cost_usd").optional.saveAs("costUsd"),
          jsonPath("$.metrics.cache_hit").optional.saveAs("cacheHit"),
          jsonPath("$.metrics.api_gateway_latency").optional.saveAs("apiGatewayLatency"),
          jsonPath("$.metrics.generator_latency").optional.saveAs("generatorLatency"),
          jsonPath("$.metrics.analyzer_latency").optional.saveAs("analyzerLatency"),
          jsonPath("$.metrics.retriever_latency").optional.saveAs("retrieverLatency")
        )
    )
    .exec(session => {
      // Swiss engineering precision - log detailed metrics
      val endToEndLatency = session.attributes.get("endToEndLatency")
      val costUsd = session.attributes.get("costUsd")
      val cacheHit = session.attributes.get("cacheHit")

      if (endToEndLatency.isDefined) {
        println(s"End-to-end latency: ${endToEndLatency.get}ms")
      }
      if (costUsd.isDefined) {
        println(s"Cost per query: $${costUsd.get}")
      }
      if (cacheHit.isDefined) {
        println(s"Cache hit: ${cacheHit.get}")
      }

      session
    })
    .pause(2, 8) // Realistic think time

  // Health Check Scenario
  val healthCheckScenario = scenario("Health Check")
    .exec(
      http("Health Check")
        .get("/health")
        .check(
          status.is(200),
          responseTimeInMillis.lte(1000)
        )
    )
    .pause(30) // Check every 30 seconds

  // Auto-scaling Trigger Scenario
  val autoScalingTriggerScenario = scenario("Auto-scaling Trigger")
    .feed(queryFeeder)
    .feed(userIdFeeder)
    .exec(
      // Burst of requests to trigger HPA scaling
      repeat(10, "burstIndex") {
        exec(
          http("Burst Request ${burstIndex}")
            .post(s"/$apiVersion/query")
            .body(StringBody(session => {
              val (query, complexity) = session("queries").as[(String, String)]
              val userId = session("userId").as[String]

              s"""
              {
                "query": "$query",
                "options": {
                  "max_tokens": 500,
                  "model_preference": "fast"
                },
                "metadata": {
                  "user_id": "$userId",
                  "test_type": "autoscaling_trigger",
                  "burst_index": "${session("burstIndex").as[String]}",
                  "complexity": "$complexity"
                }
              }
              """
            }))
            .check(status.in(200, 429)) // Accept rate limiting
        ).pause(100.milliseconds) // Minimal pause between burst requests
      }
    )
    .pause(5) // Wait between burst groups

  // Cost Optimization Scenario
  val costOptimizationScenario = scenario("Cost Optimization")
    .feed(queryFeeder)
    .feed(userIdFeeder)
    .exec(
      http("Cost-Optimized Query")
        .post(s"/$apiVersion/query")
        .body(StringBody(session => {
          val (query, complexity) = session("queries").as[(String, String)]
          val userId = session("userId").as[String]

          s"""
          {
            "query": "$query",
            "options": {
              "max_tokens": 300,
              "model_preference": "fast",
              "cost_optimization": true
            },
            "metadata": {
              "user_id": "$userId",
              "test_type": "cost_optimization",
              "complexity": "$complexity"
            }
          }
          """
        }))
        .check(
          status.is(200),
          jsonPath("$.metrics.cost_usd").lte(0.01), // Cost SLO validation
          responseTimeInMillis.lte(2000) // Faster response for cost-optimized
        )
    )
    .pause(3, 6)

  // Load Testing Simulation Setup
  setUp(
    // 1. Baseline Load Test (Normal traffic)
    ragQueryScenario.inject(
      rampUsers(50).during(2.minutes),
      constantUsersPerSec(25).during(10.minutes),
      rampUsers(100).during(2.minutes),
      constantUsersPerSec(50).during(10.minutes),
      rampUsersPerSec(0).to(0).during(2.minutes)
    ).protocols(httpProtocol),

    // 2. Peak Load Test (Traffic spikes)
    ragQueryScenario.inject(
      nothingFor(15.minutes), // Start after baseline
      rampUsers(200).during(1.minute),
      rampUsers(500).during(2.minutes),
      constantUsersPerSec(250).during(5.minutes),
      rampUsersPerSec(250).to(100).during(2.minutes),
      rampUsersPerSec(100).to(0).during(1.minute)
    ).protocols(httpProtocol),

    // 3. Stress Test (Beyond normal capacity)
    ragQueryScenario.inject(
      nothingFor(25.minutes), // Start after peak load
      rampUsers(500).during(2.minutes),
      rampUsers(1000).during(3.minutes),
      constantUsersPerSec(500).during(5.minutes),
      rampUsersPerSec(500).to(250).during(2.minutes),
      rampUsersPerSec(250).to(0).during(2.minutes)
    ).protocols(httpProtocol),

    // 4. Spike Test (Sudden load increase)
    ragQueryScenario.inject(
      nothingFor(40.minutes), // Start after stress test
      constantUsersPerSec(50).during(30.seconds),
      rampUsersPerSec(50).to(750).during(30.seconds), // Sudden spike
      constantUsersPerSec(750).during(1.minute),
      rampUsersPerSec(750).to(50).during(30.seconds),
      constantUsersPerSec(50).during(30.seconds),
      rampUsersPerSec(50).to(0).during(30.seconds)
    ).protocols(httpProtocol),

    // 5. Endurance Test (Long duration)
    ragQueryScenario.inject(
      nothingFor(45.minutes), // Start after spike test
      rampUsers(200).during(2.minutes),
      constantUsersPerSec(100).during(30.minutes),
      rampUsersPerSec(100).to(0).during(2.minutes)
    ).protocols(httpProtocol),

    // 6. Auto-scaling Validation
    autoScalingTriggerScenario.inject(
      nothingFor(80.minutes), // Start after endurance
      constantUsersPerSec(10).during(2.minutes),
      rampUsersPerSec(10).to(50).during(2.minutes),
      constantUsersPerSec(50).during(5.minutes), // Should trigger HPA scaling
      rampUsersPerSec(50).to(10).during(2.minutes),
      constantUsersPerSec(10).during(2.minutes)
    ).protocols(httpProtocol),

    // 7. Cost Optimization Testing
    costOptimizationScenario.inject(
      nothingFor(95.minutes), // Start after autoscaling
      rampUsers(100).during(1.minute),
      constantUsersPerSec(50).during(10.minutes),
      rampUsersPerSec(50).to(0).during(1.minute)
    ).protocols(httpProtocol),

    // 8. Continuous Health Monitoring
    healthCheckScenario.inject(
      constantUsersPerSec(1).during(120.minutes) // Run throughout entire test
    ).protocols(httpProtocol)

  ).assertions(
    // Swiss Engineering SLO Assertions
    global.responseTime.percentile3.lte(2000), // P95 < 2s (Epic 8 SLO)
    global.responseTime.percentile4.lte(5000), // P99 < 5s
    global.successfulRequests.percent.gte(99.5), // Success rate > 99.5%
    global.responseTime.mean.lte(1000), // Mean response time < 1s

    // Service-specific assertions
    forAll.responseTime.percentile3.lte(5000), // All services P95 < 5s
    forAll.failedRequests.percent.lte(1), // Error rate < 1%

    // Resource efficiency assertions
    global.requestsPerSec.gte(10), // Minimum throughput

    // Cost optimization assertions (would need custom metrics)
    details("Cost-Optimized Query").responseTime.percentile3.lte(2000)
  ).protocols(httpProtocol)

  // Setup and teardown
  before {
    println("🚀 Starting Epic 8 Gatling Load Testing Suite")
    println(s"📍 Target: $baseUrl")
    println(s"🔑 API Version: $apiVersion")
    println(s"🌍 Environment: $environment")
    println("🇨🇭 Swiss Engineering Standards: Precision, Efficiency, Reliability")
  }

  after {
    println("🏁 Epic 8 Gatling Load Testing Complete")
    println("📊 Check reports for detailed Swiss engineering metrics")
  }
}