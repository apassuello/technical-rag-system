"""
Unit Tests for Epic 8 Query Analyzer Service.

Tests the core functionality of the QueryAnalyzerService wrapping Epic1QueryAnalyzer
for microservices deployment. Based on CT-8.1 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service crashes, health check 500s, >60s response, >8GB memory, 0% accuracy
- Quality Flags: <85% accuracy, >2s response, invalid classifications, >10% cost errors
"""

import pytest
import asyncio
import time
import unittest.mock as mock
from typing import Dict, Any
from pathlib import Path
import sys

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "query-analyzer"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from app.core.analyzer import QueryAnalyzerService
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestQueryAnalyzerServiceBasics:
    """Test basic service initialization and health checks."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that service can be initialized without crashing (Hard Fail test)."""
        try:
            service = QueryAnalyzerService()
            assert service is not None
            assert not service._initialized  # Should start uninitialized
            assert service.analyzer is None
            
            # Test with configuration
            config = {"strategy": "balanced"}
            service_with_config = QueryAnalyzerService(config=config)
            assert service_with_config.config == config
            
        except Exception as e:
            pytest.fail(f"Service initialization crashed: {e}")
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check functionality (Hard Fail test)."""
        service = QueryAnalyzerService()
        
        # Health check should not return 500 error or crash
        start_time = time.time()
        try:
            health_result = await service.health_check()
            health_check_time = time.time() - start_time
            
            # Hard fail: Health check takes >60s (clearly broken)
            assert health_check_time < 60.0, f"Health check took {health_check_time:.2f}s, service is broken"
            
            # Should return boolean
            assert isinstance(health_result, bool), "Health check should return boolean"
            
            # Flag but don't fail: Health check should ideally be fast
            if health_check_time > 2.0:
                pytest.warns(UserWarning, f"Health check slow: {health_check_time:.2f}s (flag for optimization)")
                
        except Exception as e:
            pytest.fail(f"Health check crashed (Hard Fail): {e}")


class TestQueryAnalyzerServiceComplexityClassification:
    """Test complexity classification accuracy based on CT-8.1.1 specifications."""

    # Test data from Epic 8 specifications
    TEST_QUERIES = [
        ("What is RISC-V?", "simple", 0.2),
        ("Explain interrupt handling in RISC-V with examples", "medium", 0.6),
        ("Compare RISC-V vector extensions with ARM SVE, including performance implications", "complex", 0.9)
    ]
    
    ADDITIONAL_TEST_QUERIES = [
        ("Hi", "simple", 0.1),
        ("How does machine learning work?", "medium", 0.5),
        ("Analyze the computational complexity of transformer attention mechanisms", "complex", 0.8),
        ("Yes", "simple", 0.1),
        ("What are the differences between supervised and unsupervised learning?", "medium", 0.6)
    ]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_complexity_classification_basic_queries(self):
        """Test complexity classification on basic test queries (CT-8.1.1)."""
        service = QueryAnalyzerService()
        
        correct_classifications = 0
        response_times = []
        all_results = []
        
        for query, expected_complexity, expected_confidence in self.TEST_QUERIES:
            start_time = time.time()
            
            try:
                result = await service.analyze_query(query)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Hard fail: Response time >60s (clearly broken)
                assert response_time < 60.0, f"Query analysis took {response_time:.2f}s, service is broken"
                
                # Flag for optimization: Response time >2s
                if response_time > 2.0:
                    pytest.warns(UserWarning, f"Slow analysis: {response_time:.2f}s for '{query}' (flag for optimization)")
                
                # Validate response structure
                assert "complexity" in result, "Response missing 'complexity' field"
                assert "confidence" in result, "Response missing 'confidence' field"
                
                predicted_complexity = result["complexity"]
                confidence = result["confidence"]
                
                # Hard fail: Invalid complexity classification
                assert predicted_complexity in ["simple", "medium", "complex"], f"Invalid complexity: {predicted_complexity}"
                
                # Hard fail: Invalid confidence score
                assert isinstance(confidence, (int, float)), "Confidence must be numeric"
                assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range [0,1]"
                
                # Check classification accuracy
                if predicted_complexity == expected_complexity:
                    correct_classifications += 1
                
                all_results.append({
                    "query": query,
                    "expected": expected_complexity,
                    "predicted": predicted_complexity,
                    "confidence": confidence,
                    "response_time": response_time
                })
                
            except Exception as e:
                pytest.fail(f"Query analysis crashed for '{query}': {e}")
        
        # Calculate accuracy
        accuracy = correct_classifications / len(self.TEST_QUERIES)
        
        # Hard fail: 0% accuracy (completely broken)
        assert accuracy > 0.0, "Classification accuracy is 0% - analyzer is completely broken"
        
        # Quality flag: Accuracy <85% per CT-8.1.1
        if accuracy < 0.85:
            pytest.warns(UserWarning, f"Classification accuracy {accuracy:.2%} below 85% target (flag for improvement)")
        
        # Quality check: Response time per CT-8.1.1 (should be <100ms)
        avg_response_time = sum(response_times) / len(response_times)
        if avg_response_time > 0.1:  # 100ms
            pytest.warns(UserWarning, f"Average response time {avg_response_time:.3f}s exceeds 100ms target")
        
        print(f"\nComplexity Classification Results:")
        print(f"Accuracy: {accuracy:.2%} ({correct_classifications}/{len(self.TEST_QUERIES)})")
        print(f"Average response time: {avg_response_time:.3f}s")
        for result in all_results:
            print(f"  '{result['query'][:50]}...' -> {result['predicted']} (conf: {result['confidence']:.2f})")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_complexity_classification_extended(self):
        """Test complexity classification on extended test set for robustness."""
        service = QueryAnalyzerService()
        
        correct_classifications = 0
        total_queries = len(self.ADDITIONAL_TEST_QUERIES)
        
        for query, expected_complexity, _ in self.ADDITIONAL_TEST_QUERIES:
            try:
                result = await service.analyze_query(query)
                
                predicted_complexity = result["complexity"]
                confidence = result["confidence"]
                
                # Basic validation
                assert predicted_complexity in ["simple", "medium", "complex"]
                assert 0.0 <= confidence <= 1.0
                
                if predicted_complexity == expected_complexity:
                    correct_classifications += 1
                    
            except Exception as e:
                pytest.fail(f"Extended query analysis failed for '{query}': {e}")
        
        accuracy = correct_classifications / total_queries
        
        # Hard fail: 0% accuracy
        assert accuracy > 0.0, "Extended classification accuracy is 0%"
        
        # Quality flag for extended set
        if accuracy < 0.75:  # Slightly lower threshold for extended set
            pytest.warns(UserWarning, f"Extended classification accuracy {accuracy:.2%} below 75% threshold")
        
        print(f"\nExtended Classification Accuracy: {accuracy:.2%} ({correct_classifications}/{total_queries})")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_confidence_correlation(self):
        """Test that confidence scores correlate with complexity (CT-8.1.1)."""
        service = QueryAnalyzerService()
        
        simple_confidences = []
        medium_confidences = []
        complex_confidences = []
        
        # Collect confidence scores for each complexity level
        test_cases = [
            ("Yes", "simple"),
            ("No", "simple"),
            ("What is AI?", "simple"),
            ("How does machine learning work?", "medium"),
            ("Explain neural network backpropagation", "medium"),
            ("Compare quantum computing approaches", "medium"),
            ("Analyze the computational complexity of distributed consensus algorithms", "complex"),
            ("Derive the mathematical foundations of transformer attention mechanisms", "complex")
        ]
        
        for query, expected_complexity in test_cases:
            try:
                result = await service.analyze_query(query)
                confidence = result["confidence"]
                predicted_complexity = result["complexity"]
                
                # Collect confidences by predicted complexity
                if predicted_complexity == "simple":
                    simple_confidences.append(confidence)
                elif predicted_complexity == "medium":
                    medium_confidences.append(confidence)
                elif predicted_complexity == "complex":
                    complex_confidences.append(confidence)
                    
            except Exception as e:
                pytest.fail(f"Confidence test failed for '{query}': {e}")
        
        # Basic sanity check - we should have some results
        total_results = len(simple_confidences) + len(medium_confidences) + len(complex_confidences)
        assert total_results > 0, "No confidence scores collected"
        
        # Calculate average confidences (if we have results)
        avg_simple = sum(simple_confidences) / len(simple_confidences) if simple_confidences else 0
        avg_medium = sum(medium_confidences) / len(medium_confidences) if medium_confidences else 0
        avg_complex = sum(complex_confidences) / len(complex_confidences) if complex_confidences else 0
        
        print(f"\nConfidence by Complexity:")
        print(f"Simple queries: {avg_simple:.3f} (n={len(simple_confidences)})")
        print(f"Medium queries: {avg_medium:.3f} (n={len(medium_confidences)})")
        print(f"Complex queries: {avg_complex:.3f} (n={len(complex_confidences)})")
        
        # Quality check: Higher complexity should generally have higher confidence
        # (This is not a hard requirement, but good to flag)
        if len(simple_confidences) > 0 and len(complex_confidences) > 0:
            if avg_complex < avg_simple:
                pytest.warns(UserWarning, f"Complex queries have lower confidence than simple ones")


class TestQueryAnalyzerServiceFeatureExtraction:
    """Test feature extraction functionality based on CT-8.1.2 specifications."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_feature_extraction_presence(self):
        """Test that required features are present in analysis results (CT-8.1.2)."""
        service = QueryAnalyzerService()
        
        test_query = "Complex RISC-V query with technical terms and detailed analysis requirements"
        
        try:
            result = await service.analyze_query(test_query)
            
            # Validate features field exists
            assert "features" in result, "Response missing 'features' field"
            features = result["features"]
            assert isinstance(features, dict), "Features must be a dictionary"
            
            # Check for expected feature categories (based on analyzer.py)
            expected_features = [
                "word_count",
                "technical_density", 
                "syntactic_complexity",
                "question_type",
                "ambiguity_score",
                "technical_terms"
            ]
            
            missing_features = []
            for feature in expected_features:
                if feature not in features:
                    missing_features.append(feature)
            
            # Quality check: Flag missing features
            if missing_features:
                pytest.warns(UserWarning, f"Missing expected features: {missing_features}")
            
            # Validate feature value types and ranges
            if "word_count" in features:
                word_count = features["word_count"]
                assert isinstance(word_count, (int, float)), "word_count must be numeric"
                assert word_count >= 0, "word_count must be non-negative"
                
                # Basic sanity check
                actual_word_count = len(test_query.split())
                if abs(word_count - actual_word_count) > 5:  # Allow some tolerance
                    pytest.warns(UserWarning, f"Word count {word_count} seems incorrect for query length")
            
            if "technical_density" in features:
                tech_density = features["technical_density"]
                assert isinstance(tech_density, (int, float)), "technical_density must be numeric"
                assert 0.0 <= tech_density <= 1.0, f"technical_density {tech_density} out of range [0,1]"
            
            if "syntactic_complexity" in features:
                syntax_complexity = features["syntactic_complexity"]
                assert isinstance(syntax_complexity, (int, float)), "syntactic_complexity must be numeric"
                assert syntax_complexity >= 0.0, "syntactic_complexity must be non-negative"
            
            if "technical_terms" in features:
                tech_terms = features["technical_terms"]
                assert isinstance(tech_terms, list), "technical_terms must be a list"
                # For this technical query, we should find some technical terms
                if len(tech_terms) == 0:
                    pytest.warns(UserWarning, "No technical terms found in technical query")
            
            print(f"\nFeature Extraction Results:")
            for key, value in features.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            pytest.fail(f"Feature extraction test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_feature_extraction_deterministic(self):
        """Test that feature extraction produces consistent results (CT-8.1.2)."""
        service = QueryAnalyzerService()
        
        test_query = "What are the key advantages of RISC-V architecture?"
        
        try:
            # Run analysis multiple times
            results = []
            for i in range(3):
                result = await service.analyze_query(test_query)
                results.append(result["features"])
            
            # Compare features across runs
            first_features = results[0]
            
            for i, features in enumerate(results[1:], 1):
                for key in first_features:
                    if key in features:
                        first_val = first_features[key]
                        current_val = features[key]
                        
                        # For numeric values, check they're the same
                        if isinstance(first_val, (int, float)) and isinstance(current_val, (int, float)):
                            if abs(first_val - current_val) > 1e-6:
                                pytest.warns(UserWarning, f"Non-deterministic feature {key}: {first_val} vs {current_val}")
                        
                        # For lists and strings, check exact equality
                        elif isinstance(first_val, (list, str)):
                            if first_val != current_val:
                                pytest.warns(UserWarning, f"Non-deterministic feature {key}: {first_val} vs {current_val}")
            
            print(f"Feature determinism test passed for {len(results)} runs")
            
        except Exception as e:
            pytest.fail(f"Feature determinism test failed: {e}")


class TestQueryAnalyzerServiceModelRecommendation:
    """Test model recommendation functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_model_recommendation_basic(self):
        """Test that model recommendations are provided."""
        service = QueryAnalyzerService()
        
        test_cases = [
            ("Hi", "simple"),
            ("How does machine learning work?", "medium"),
            ("Analyze distributed consensus algorithms", "complex")
        ]
        
        for query, expected_complexity in test_cases:
            try:
                result = await service.analyze_query(query)
                
                # Check recommended_models field
                assert "recommended_models" in result, "Response missing 'recommended_models'"
                recommended_models = result["recommended_models"]
                
                # Should have at least one recommendation
                assert len(recommended_models) > 0, "No model recommendations provided"
                
                # Validate recommendation structure
                for model_rec in recommended_models:
                    assert isinstance(model_rec, dict), "Model recommendation must be dict"
                    
                    # Check for expected fields
                    if "provider" in model_rec:
                        assert isinstance(model_rec["provider"], str), "Provider must be string"
                    if "name" in model_rec:
                        assert isinstance(model_rec["name"], str), "Model name must be string"
                    if "confidence" in model_rec:
                        conf = model_rec["confidence"]
                        assert isinstance(conf, (int, float)), "Confidence must be numeric"
                        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"
                
                print(f"Query: '{query}' -> {len(recommended_models)} recommendations")
                
            except Exception as e:
                pytest.fail(f"Model recommendation test failed for '{query}': {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio 
    async def test_cost_estimation(self):
        """Test cost estimation functionality."""
        service = QueryAnalyzerService()
        
        test_query = "What is machine learning?"
        
        try:
            result = await service.analyze_query(test_query)
            
            # Check cost_estimate field
            assert "cost_estimate" in result, "Response missing 'cost_estimate'"
            cost_estimate = result["cost_estimate"]
            assert isinstance(cost_estimate, dict), "Cost estimate must be dict"
            
            # Validate cost values
            for key, value in cost_estimate.items():
                if isinstance(value, (int, float)):
                    assert value >= 0.0, f"Cost estimate {key}={value} must be non-negative"
                    
                    # Quality check: Very high costs might indicate error
                    if value > 1.0:  # $1+ per query seems high
                        pytest.warns(UserWarning, f"High cost estimate: {key}=${value:.4f}")
            
            print(f"Cost estimation test passed: {cost_estimate}")
            
        except Exception as e:
            pytest.fail(f"Cost estimation test failed: {e}")


class TestQueryAnalyzerServiceStatus:
    """Test service status and monitoring functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_get_analyzer_status(self):
        """Test analyzer status reporting."""
        service = QueryAnalyzerService()
        
        try:
            # Get status before initialization
            status_before = await service.get_analyzer_status()
            assert isinstance(status_before, dict), "Status must be dict"
            assert "initialized" in status_before, "Status missing 'initialized'"
            assert status_before["initialized"] is False, "Should not be initialized initially"
            
            # Perform an analysis to initialize
            await service.analyze_query("Test query")
            
            # Get status after initialization
            status_after = await service.get_analyzer_status()
            assert status_after["initialized"] is True, "Should be initialized after analysis"
            
            # Check status fields
            expected_fields = ["initialized", "status", "analyzer_type"]
            for field in expected_fields:
                assert field in status_after, f"Status missing '{field}'"
            
            # Validate field values
            assert status_after["status"] in ["healthy", "error", "not_initialized"], "Invalid status value"
            assert isinstance(status_after["analyzer_type"], str), "analyzer_type must be string"
            
            print(f"Status test passed: {status_after['status']} ({status_after['analyzer_type']})")
            
        except Exception as e:
            pytest.fail(f"Status test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_shutdown(self):
        """Test graceful service shutdown."""
        service = QueryAnalyzerService()
        
        try:
            # Initialize service
            await service.analyze_query("Test query")
            assert service._initialized is True
            
            # Shutdown service
            await service.shutdown()
            
            # Verify shutdown state
            assert service._initialized is False, "Service should be uninitialized after shutdown"
            assert service.analyzer is None, "Analyzer should be None after shutdown"
            
            print("Service shutdown test passed")
            
        except Exception as e:
            pytest.fail(f"Service shutdown test failed: {e}")


class TestQueryAnalyzerServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_empty_query_handling(self):
        """Test handling of empty or invalid queries."""
        service = QueryAnalyzerService()
        
        test_cases = ["", "   ", "\n\t  ", None]
        
        for query in test_cases:
            try:
                if query is None:
                    with pytest.raises((ValueError, TypeError)):
                        await service.analyze_query(query)
                else:
                    # Empty queries should either handle gracefully or raise clear error
                    result = await service.analyze_query(query)
                    # If it succeeds, result should be valid
                    assert "complexity" in result
                    assert "confidence" in result
                    
            except (ValueError, TypeError, AssertionError) as e:
                # These are expected for invalid queries
                print(f"Expected error for query '{query}': {type(e).__name__}")
            except Exception as e:
                pytest.fail(f"Unexpected error for query '{query}': {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_very_long_query_handling(self):
        """Test handling of very long queries."""
        service = QueryAnalyzerService()
        
        # Create a very long query
        long_query = "What is machine learning? " * 1000  # ~26,000 characters
        
        try:
            start_time = time.time()
            result = await service.analyze_query(long_query)
            processing_time = time.time() - start_time
            
            # Hard fail: Should not take >60s
            assert processing_time < 60.0, f"Long query took {processing_time:.2f}s"
            
            # Quality flag: Should ideally handle long queries reasonably fast
            if processing_time > 10.0:
                pytest.warns(UserWarning, f"Long query processing time: {processing_time:.2f}s")
            
            # Should still produce valid results
            assert "complexity" in result
            assert "confidence" in result
            assert result["complexity"] in ["simple", "medium", "complex"]
            
            print(f"Long query test passed: {processing_time:.2f}s")
            
        except Exception as e:
            # Graceful failure is acceptable for very long queries
            if "too long" in str(e).lower() or "limit" in str(e).lower():
                print(f"Long query gracefully rejected: {e}")
            else:
                pytest.fail(f"Unexpected error for long query: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        service = QueryAnalyzerService()
        
        queries = [
            "What is AI?",
            "How does machine learning work?",
            "Explain neural networks",
            "What is deep learning?",
            "How do transformers work?"
        ]
        
        try:
            # Run 10 concurrent requests (early-stage concurrency test)
            start_time = time.time()
            tasks = [service.analyze_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Hard fail: Should not crash completely
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) > 0, "All concurrent requests failed"
            
            # Quality check: Most should succeed
            success_rate = len(successful_results) / len(queries)
            if success_rate < 0.8:
                pytest.warns(UserWarning, f"Low concurrent success rate: {success_rate:.2%}")
            
            print(f"Concurrent test: {len(successful_results)}/{len(queries)} succeeded in {total_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Concurrent request test failed: {e}")


# Memory usage test (separate class for resource monitoring)
class TestQueryAnalyzerServiceResources:
    """Test resource usage and performance characteristics."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_memory_usage_basic(self):
        """Test that service doesn't use excessive memory."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        service = QueryAnalyzerService()
        
        # Run several analyses
        for i in range(10):
            await service.analyze_query(f"Test query number {i} with some content")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Hard fail: >8GB memory usage (clearly broken)
        assert final_memory < 8000, f"Memory usage {final_memory:.1f}MB exceeds 8GB limit"
        
        # Quality flag: Large memory increase might indicate leak
        if memory_increase > 1000:  # 1GB increase
            pytest.warns(UserWarning, f"Large memory increase: {memory_increase:.1f}MB")
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestQueryAnalyzerServiceBasics", "-v"])