"""Test suite for Adaptive Router - Epic 1 Phase 2.

Tests adaptive router functionality including:
- Query routing performance (<50ms)
- Routing decision accuracy (>90%)
- Fallback chain execution
- Integration with query analyzer
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# Import adaptive router components
from src.components.generators.routing.adaptive_router import (
    AdaptiveRouter, RoutingDecision
)
from src.components.query_processors.base import QueryAnalysis
from src.components.generators.routing.routing_strategies import (
    CostOptimizedStrategy, QualityFirstStrategy, BalancedStrategy, ModelOption
)


def create_mock_query_analysis(complexity_level="medium", complexity_score=0.55, confidence=0.85, **metadata_extras):
    """Helper function to create QueryAnalysis mock objects."""
    metadata = {
        "complexity_level": complexity_level,
        "complexity_score": complexity_score,
        "confidence": confidence
    }
    metadata.update(metadata_extras)
    
    return QueryAnalysis(
        query="test",
        complexity_score=complexity_score,
        complexity_level=complexity_level,
        confidence=confidence,
        metadata=metadata
    )


class TestAdaptiveRouter:
    """Test suite for adaptive router functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock Epic1QueryAnalyzer
        self.mock_query_analyzer = MagicMock()
        
        # Create test router
        self.router = AdaptiveRouter(
            query_analyzer=self.mock_query_analyzer,
            default_strategy="balanced"
        )
        
        # Test queries with expected routing
        self.test_cases = [
            {
                "query": "What is AI?",
                "expected_complexity": "simple",
                "optimal_model": ("ollama", "llama3.2:3b"),
                "strategy": "cost_optimized"
            },
            {
                "query": "How does OAuth 2.0 work?",
                "expected_complexity": "medium",
                "optimal_model": ("mistral", "mistral-small"),
                "strategy": "balanced"
            },
            {
                "query": "Explain transformer attention mechanisms",
                "expected_complexity": "complex",
                "optimal_model": ("openai", "gpt-4-turbo"),
                "strategy": "quality_first"
            }
        ]
        
        # Mock model registry
        self.mock_model_registry = {
            "simple": [
                ModelOption("ollama", "llama3.2:3b", Decimal('0.000'), 1.5, 0.75),
                ModelOption("openai", "gpt-3.5-turbo", Decimal('0.002'), 0.8, 0.90)
            ],
            "medium": [
                ModelOption("mistral", "mistral-small", Decimal('0.010'), 1.2, 0.85),
                ModelOption("openai", "gpt-4-turbo", Decimal('0.050'), 2.0, 0.95)
            ],
            "complex": [
                ModelOption("openai", "gpt-3.5-turbo", Decimal('0.020'), 1.5, 0.85),
                ModelOption("openai", "gpt-4-turbo", Decimal('0.100'), 3.0, 0.98)
            ]
        }
    
    # EPIC1-ROUTER-001: Query Routing Performance
    def test_routing_performance_targets(self):
        """Test routing decision performance meets <50ms requirement.
        
        Requirement: <50ms routing overhead
        PASS Criteria:
        - Average latency: <15ms
        - P95 latency: <30ms
        - P99 latency: <50ms
        - No performance degradation over time
        """
        # Configure mock analyzer for consistent responses
        self.mock_query_analyzer.analyze.return_value = create_mock_query_analysis(
            recommended_model={"provider": "mistral", "model": "mistral-small"}
        )
        
        # Warm up (exclude from measurements)
        for _ in range(10):
            self.router.route_query(
                query="Warm up query",
                strategy_override="balanced"
            )
        
        # Performance measurement
        latencies = []
        num_iterations = 100
        
        for i in range(num_iterations):
            start_time = time.perf_counter()
            
            decision = self.router.route_query(
                query=f"Test query {i}",
                strategy_override="balanced"
            )
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            # Verify decision was made
            assert decision is not None
            assert isinstance(decision, RoutingDecision)
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        latencies_sorted = sorted(latencies)
        p95_latency = latencies_sorted[int(0.95 * len(latencies))]
        p99_latency = latencies_sorted[int(0.99 * len(latencies))]
        
        print(f"Routing Performance:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        print(f"  Min: {min(latencies):.2f}ms")
        print(f"  Max: {max(latencies):.2f}ms")
        
        # Verify performance targets
        assert avg_latency < 15.0, f"Average latency {avg_latency:.2f}ms > 15ms target"
        assert p95_latency < 30.0, f"P95 latency {p95_latency:.2f}ms > 30ms target"
        assert p99_latency < 50.0, f"P99 latency {p99_latency:.2f}ms > 50ms target"
        
        # Test for performance degradation
        first_half_avg = sum(latencies[:50]) / 50
        second_half_avg = sum(latencies[50:]) / 50
        degradation = (second_half_avg - first_half_avg) / first_half_avg
        
        assert abs(degradation) < 0.20, f"Performance degradation {degradation:.2%} > 20% threshold"
    
    def test_concurrent_routing_performance(self):
        """Test routing performance under concurrent load."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Configure analyzer
        self.mock_query_analyzer.analyze.return_value = create_mock_query_analysis()
        
        def single_routing_test(thread_id: int) -> float:
            """Perform routing test from single thread."""
            start_time = time.perf_counter()
            
            decision = self.router.route_query(
                query=f"Concurrent query {thread_id}",
                strategy_override="balanced"
            )
            
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000
            
            assert decision is not None
            return latency
        
        # Test with multiple concurrent threads
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(single_routing_test, i) for i in range(num_threads)]
            concurrent_latencies = [future.result() for future in as_completed(futures)]
        
        # Verify concurrent performance
        avg_concurrent_latency = sum(concurrent_latencies) / len(concurrent_latencies)
        max_concurrent_latency = max(concurrent_latencies)
        
        print(f"Concurrent Performance ({num_threads} threads):")
        print(f"  Average: {avg_concurrent_latency:.2f}ms")
        print(f"  Maximum: {max_concurrent_latency:.2f}ms")
        
        # Concurrent performance should still meet targets
        assert avg_concurrent_latency < 25.0, f"Concurrent average {avg_concurrent_latency:.2f}ms > 25ms"
        assert max_concurrent_latency < 100.0, f"Concurrent max {max_concurrent_latency:.2f}ms > 100ms"
    
    # EPIC1-ROUTER-002: Routing Decision Accuracy
    def test_routing_decision_accuracy(self):
        """Test routing accuracy against known optimal models.
        
        Requirement: >90% routing accuracy
        PASS Criteria:
        - Overall accuracy: >90%
        - Per-strategy accuracy: >85%
        - Complexity classification: >95% correct
        - Strategy selection: Appropriate for context
        """
        correct_decisions = 0
        total_decisions = 0
        strategy_results = {"cost_optimized": [], "balanced": [], "quality_first": []}
        
        # Extended test cases for comprehensive validation
        extended_test_cases = self.test_cases * 10  # Repeat for statistical significance
        
        for i, test_case in enumerate(extended_test_cases):
            # Configure analyzer to return expected complexity
            expected_complexity = test_case["expected_complexity"]
            self.mock_query_analyzer.analyze.return_value = {
                "complexity_level": expected_complexity,
                "complexity_score": 0.45 if expected_complexity == "medium" else 0.25,
                "confidence": 0.85
            }
            
            # Route query with specified strategy
            strategy = test_case["strategy"]
            decision = self.router.route_query(
                query=test_case["query"],
                strategy_override=strategy
            )
            
            total_decisions += 1
            
            # Check if decision matches expected optimal model
            expected_provider, expected_model = test_case["optimal_model"]
            actual_selection = (decision.selected_model.provider, decision.selected_model.model)
            
            is_correct = actual_selection == (expected_provider, expected_model)
            if is_correct:
                correct_decisions += 1
            
            strategy_results[strategy].append(is_correct)
            
            # Verify decision structure
            assert isinstance(decision, RoutingDecision)
            assert decision.routing_metadata.get('complexity_analysis') is not None
            assert decision.selected_model is not None
            assert decision.strategy_used == strategy
            assert decision.decision_time_ms > 0
        
        # Calculate overall accuracy
        overall_accuracy = correct_decisions / total_decisions
        print(f"Overall Routing Accuracy: {overall_accuracy:.2%} ({correct_decisions}/{total_decisions})")
        
        # Calculate per-strategy accuracy
        for strategy, results in strategy_results.items():
            if results:  # Only if we have results for this strategy
                strategy_accuracy = sum(results) / len(results)
                print(f"{strategy.title()} Strategy Accuracy: {strategy_accuracy:.2%} ({sum(results)}/{len(results)})")
                assert strategy_accuracy >= 0.85, f"{strategy} accuracy {strategy_accuracy:.2%} < 85%"
        
        # Verify overall accuracy target
        assert overall_accuracy >= 0.90, f"Overall accuracy {overall_accuracy:.2%} < 90% target"
    
    def test_complexity_classification_accuracy(self):
        """Test accuracy of complexity classification integration."""
        complexity_tests = [
            ("What is Python?", "simple"),
            ("How does OAuth work?", "medium"),
            ("Explain transformer attention mechanisms", "complex"),
            ("List HTTP methods", "simple"),
            ("Compare microservices vs monoliths", "medium"),
            ("Analyze distributed consensus algorithms", "complex")
        ]
        
        correct_classifications = 0
        total_classifications = 0
        
        for query, expected_complexity in complexity_tests:
            # Mock analyzer to return expected result (simulating correct classification)
            self.mock_query_analyzer.analyze.return_value = {
                "complexity_level": expected_complexity,
                "complexity_score": 0.45 if expected_complexity == "medium" else 0.25,
                "confidence": 0.90
            }
            
            decision = self.router.route_query(
                query=query,
                strategy_override="balanced"
            )
            
            total_classifications += 1
            if decision.routing_metadata['complexity_analysis']["complexity_level"] == expected_complexity:
                correct_classifications += 1
        
        classification_accuracy = correct_classifications / total_classifications
        print(f"Complexity Classification Accuracy: {classification_accuracy:.2%}")
        
        assert classification_accuracy >= 0.95, f"Classification accuracy {classification_accuracy:.2%} < 95%"
    
    # EPIC1-ROUTER-003: Fallback Chain Execution
    def test_fallback_chain_activation(self):
        """Test fallback chain activation on model failures.
        
        Requirement: 100% reliability through fallbacks
        PASS Criteria:
        - Fallback activation: 100% on failure
        - Recovery success: >99%
        - Recovery time: <2 seconds
        - State preservation: Query context maintained
        """
        # Configure fallback chain
        fallback_chain = [
            ("openai", "gpt-4-turbo"),    # Primary
            ("mistral", "mistral-small"),  # Fallback 1
            ("ollama", "llama3.2:3b")     # Fallback 2 (local)
        ]
        
        self.router.configure_fallback_chain(fallback_chain)
        
        # Configure analyzer
        self.mock_query_analyzer.analyze.return_value = {
            "complexity_level": "medium",
            "complexity_score": 0.55,
            "confidence": 0.85
        }
        
        # Test scenarios with different failure types
        failure_scenarios = [
            "rate_limit_exceeded",
            "model_unavailable", 
            "network_timeout",
            "authentication_failure"
        ]
        
        successful_recoveries = 0
        total_failure_tests = 0
        
        for scenario in failure_scenarios:
            print(f"Testing fallback for scenario: {scenario}")
            
            # Simulate primary model failure
            with patch.object(self.router, '_attempt_model_request') as mock_request:
                def mock_request_with_failure(model_option, query, context=None):
                    if model_option.provider == "openai":  # Primary fails
                        if scenario == "rate_limit_exceeded":
                            raise Exception("Rate limit exceeded")
                        elif scenario == "model_unavailable":
                            raise Exception("Model temporarily unavailable")
                        elif scenario == "network_timeout":
                            raise TimeoutError("Request timeout")
                        elif scenario == "authentication_failure":
                            raise Exception("Authentication failed")
                    else:
                        # Fallback succeeds
                        return MagicMock(content="Fallback response", metadata={})
                
                mock_request.side_effect = mock_request_with_failure
                
                start_time = time.perf_counter()
                
                try:
                    # Enable fallback and use regular route_query
                    self.router.enable_fallback = True
                    decision = self.router.route_query(
                        query="Test query requiring fallback",
                        strategy_override="balanced"
                    )
                    
                    end_time = time.perf_counter()
                    recovery_time = end_time - start_time
                    
                    # Verify successful fallback
                    assert decision is not None
                    assert decision.selected_model.provider != "openai"  # Fell back
                    assert decision.fallback_used is True
                    assert recovery_time < 2.0, f"Recovery time {recovery_time:.2f}s > 2s target"
                    
                    # Verify query context preserved
                    assert "Test query requiring fallback" in decision.original_query
                    
                    successful_recoveries += 1
                    
                except Exception as e:
                    print(f"Fallback failed for {scenario}: {e}")
                
                total_failure_tests += 1
        
        # Verify fallback success rate
        recovery_rate = successful_recoveries / total_failure_tests
        print(f"Fallback Recovery Rate: {recovery_rate:.2%} ({successful_recoveries}/{total_failure_tests})")
        
        assert recovery_rate >= 0.99, f"Recovery rate {recovery_rate:.2%} < 99% target"
    
    def test_fallback_chain_exhaustion(self):
        """Test behavior when all fallback options are exhausted."""
        # Configure fallback chain
        fallback_chain = [("openai", "gpt-4"), ("mistral", "mistral-small")]
        self.router.configure_fallback_chain(fallback_chain)
        
        # Mock all models to fail
        with patch.object(self.router, '_attempt_model_request') as mock_request:
            mock_request.side_effect = Exception("All models unavailable")
            
            # Configure analyzer
            self.mock_query_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85
            }
            
            # Should handle gracefully when all fallbacks fail
            with pytest.raises(Exception) as exc_info:
                # Enable fallback and use regular route_query
                self.router.enable_fallback = True
                decision = self.router.route_query(
                    query="Test query with all fallbacks failing",
                    strategy_override="balanced"
                )
            
            # Should indicate fallback chain exhaustion
            assert "fallback" in str(exc_info.value).lower() or "unavailable" in str(exc_info.value).lower()
    
    def test_state_preservation_during_fallback(self):
        """Test that query context is preserved during fallback."""
        original_query = "Complex query requiring state preservation"
        original_context = "Important context that must be preserved"
        
        # Configure fallback
        fallback_chain = [("openai", "gpt-4"), ("ollama", "llama3.2:3b")]
        self.router.configure_fallback_chain(fallback_chain)
        
        with patch.object(self.router, '_attempt_model_request') as mock_request:
            def fallback_request(model_option, query, context=None):
                if model_option.provider == "openai":
                    raise Exception("Primary model failed")
                else:
                    # Verify state was preserved
                    assert query == original_query
                    assert context == original_context
                    return MagicMock(content="Success with preserved state", metadata={})
            
            mock_request.side_effect = fallback_request
            
            self.mock_query_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85
            }
            
            # Enable fallback and use regular route_query with context_documents
            self.router.enable_fallback = True
            decision = self.router.route_query(
                query=original_query,
                context_documents=original_context,
                strategy_override="balanced"
            )
            
            # Verify state preservation in decision
            assert decision.original_query == original_query
            assert decision.fallback_used is True
            assert decision.selected_model.provider == "ollama"
    
    # Integration and Edge Case Tests
    def test_routing_decision_metadata(self):
        """Test completeness of routing decision metadata."""
        self.mock_query_analyzer.analyze.return_value = create_mock_query_analysis(
            features={"technical_terms": 3, "clause_count": 2}
        )
        
        decision = self.router.route_query(
            query="Test query for metadata",
            strategy_override="balanced"
        )
        
        # Verify complete decision metadata
        required_fields = [
            "routing_metadata", "selected_model", "strategy_used", 
            "decision_time_ms", "alternatives_considered"
        ]
        
        for field in required_fields:
            assert hasattr(decision, field), f"Missing required field: {field}"
        
        # Verify specific content
        assert decision.routing_metadata['complexity_analysis']["complexity_level"] == "medium"
        assert decision.strategy_used == "balanced"
        assert decision.decision_time_ms > 0
        assert len(decision.alternatives_considered) > 0
    
    def test_invalid_strategy_handling(self):
        """Test handling of invalid routing strategies."""
        self.mock_query_analyzer.analyze.return_value = {
            "complexity_level": "medium",
            "complexity_score": 0.55,
            "confidence": 0.85
        }
        
        # Test with invalid strategy
        with pytest.raises(ValueError, match="Unknown strategy"):
            decision = self.router.route_query(
                query="Test query",
                strategy_override="invalid_strategy"
            )
    
    def test_empty_model_registry_handling(self):
        """Test handling of empty model registry."""
        self.mock_query_analyzer.analyze.return_value = {
            "complexity_level": "medium",
            "complexity_score": 0.55,
            "confidence": 0.85
        }
        
        # Should handle gracefully
        decision = self.router.route_query(
            query="Test query",
            strategy_override="balanced"
        )
        
        assert decision is None or decision.selected_model is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])