"""
Performance tests for Metrics Collector component.

This module contains performance tests for the Metrics Collector,
testing metrics collection, aggregation, and export performance 
with large datasets and high-frequency operations.
"""

import pytest
import time
import tempfile
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from unittest.mock import patch

from src.components.calibration.metrics_collector import (
    MetricsCollector,
    QueryMetrics
)


class TestMetricsCollectorPerformance:
    """Performance test suite for MetricsCollector."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.collector = MetricsCollector()
        self.large_query_dataset = self._create_large_query_dataset(1000)
    
    def _create_large_query_dataset(self, count: int) -> List[Dict[str, Any]]:
        """Create a large dataset of synthetic query metrics for performance testing."""
        queries = []
        
        for i in range(count):
            # Generate synthetic retrieval results
            retrieval_results = [(j, np.random.random() * 0.5 + 0.5) for j in range(np.random.randint(3, 15))]
            dense_results = [(j, np.random.random() * 0.3 + 0.7) for j in range(len(retrieval_results) // 2)]
            sparse_results = [(j, np.random.random() * 10 + 5) for j in range(len(retrieval_results) // 2)]
            
            # Generate synthetic answer
            answer_length = np.random.randint(50, 300)
            answer = f"Synthetic answer {i:04d} " * (answer_length // 20)
            
            # Generate synthetic citations
            citation_count = np.random.randint(1, 5)
            citations = [
                {
                    "source": f"document_{j:03d}.pdf",
                    "relevance": np.random.random() * 0.3 + 0.7,
                    "page": np.random.randint(1, 100)
                }
                for j in range(citation_count)
            ]
            
            query_data = {
                "query_id": f"PERF_{i:05d}",
                "query_text": f"Performance test query {i:05d}",
                "retrieval_results": retrieval_results,
                "dense_results": dense_results,
                "sparse_results": sparse_results,
                "retrieval_time": np.random.random() * 0.5 + 0.1,
                "answer": answer,
                "confidence": np.random.random() * 0.4 + 0.6,
                "generation_time": np.random.random() * 2.0 + 0.5,
                "citations": citations,
                "model_info": {
                    "model_name": f"model_{i % 3}",
                    "temperature": 0.3,
                    "max_tokens": 2048
                },
                "total_time": np.random.random() * 3.0 + 1.0,
                "memory_peak": np.random.random() * 200 + 100,
                "cpu_usage": np.random.random() * 50 + 25
            }
            queries.append(query_data)
        
        return queries
    
    def test_high_frequency_query_collection_performance(self):
        """Test performance of collecting metrics for many queries rapidly."""
        query_subset = self.large_query_dataset[:200]
        
        start_time = time.time()
        
        query_metrics_list = []
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            query_metrics_list.append(metrics)
        
        duration = time.time() - start_time
        
        # Should start collection for 200 queries in under 0.1 seconds
        assert duration < 0.1
        assert len(self.collector.query_metrics) == 200
        assert len(query_metrics_list) == 200
        
        print(f"Started metrics collection for {len(query_subset)} queries in {duration:.3f}s "
              f"({len(query_subset) / duration:.0f} queries/sec)")
    
    def test_bulk_retrieval_metrics_collection_performance(self):
        """Test performance of collecting retrieval metrics in bulk."""
        query_subset = self.large_query_dataset[:500]
        
        # Start all query collections first
        query_metrics_list = []
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            query_metrics_list.append((metrics, query_data))
        
        # Test bulk retrieval metrics collection
        start_time = time.time()
        
        for metrics, query_data in query_metrics_list:
            self.collector.collect_retrieval_metrics(
                metrics,
                query_data["retrieval_results"],
                dense_results=query_data["dense_results"],
                sparse_results=query_data["sparse_results"],
                retrieval_time=query_data["retrieval_time"]
            )
        
        duration = time.time() - start_time
        
        # Should collect retrieval metrics for 500 queries in under 1 second
        assert duration < 1.0
        
        # Verify all metrics were collected
        for metrics, _ in query_metrics_list:
            assert metrics.retrieval_metrics["documents_retrieved"] > 0
            assert metrics.retrieval_metrics["retrieval_time"] > 0
        
        print(f"Collected retrieval metrics for {len(query_subset)} queries in {duration:.3f}s "
              f"({len(query_subset) / duration:.0f} collections/sec)")
    
    def test_bulk_generation_metrics_collection_performance(self):
        """Test performance of collecting generation metrics in bulk."""
        query_subset = self.large_query_dataset[:500]
        
        # Set up query metrics
        query_metrics_list = []
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            query_metrics_list.append((metrics, query_data))
        
        # Test bulk generation metrics collection
        start_time = time.time()
        
        for metrics, query_data in query_metrics_list:
            self.collector.collect_generation_metrics(
                metrics,
                query_data["answer"],
                query_data["confidence"],
                query_data["generation_time"],
                citations=query_data["citations"],
                model_info=query_data["model_info"]
            )
        
        duration = time.time() - start_time
        
        # Should collect generation metrics for 500 queries in under 1 second
        assert duration < 1.0
        
        # Verify all metrics were collected
        for metrics, _ in query_metrics_list:
            assert metrics.generation_metrics["confidence_score"] > 0
            assert metrics.generation_metrics["generation_time"] > 0
            assert metrics.generation_metrics["citations_used"] > 0
        
        print(f"Collected generation metrics for {len(query_subset)} queries in {duration:.3f}s "
              f"({len(query_subset) / duration:.0f} collections/sec)")
    
    def test_large_scale_validation_results_performance(self):
        """Test performance of collecting validation results for many queries."""
        query_subset = self.large_query_dataset[:300]
        
        # Set up query metrics
        query_metrics_list = []
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            query_metrics_list.append((metrics, query_data))
        
        # Create varied expected behaviors and actual results
        expected_behaviors = [
            {
                "min_confidence": 0.6,
                "max_confidence": 1.0,
                "must_contain_terms": ["test", "performance"],
                "must_not_contain": ["error", "fail"],
                "min_citations": 1
            }
            for _ in query_subset
        ]
        
        # Test bulk validation collection
        start_time = time.time()
        
        for (metrics, query_data), expected in zip(query_metrics_list, expected_behaviors):
            actual_results = {
                "confidence": query_data["confidence"],
                "answer": query_data["answer"],
                "citations": query_data["citations"]
            }
            
            self.collector.collect_validation_results(
                metrics,
                expected,
                actual_results
            )
        
        duration = time.time() - start_time
        
        # Should process validation for 300 queries in under 0.5 seconds
        assert duration < 0.5
        
        # Verify validation results
        valid_results = 0
        for metrics, _ in query_metrics_list:
            if "answer_quality_score" in metrics.validation_results:
                valid_results += 1
        
        assert valid_results == len(query_subset)
        
        print(f"Processed validation results for {len(query_subset)} queries in {duration:.3f}s "
              f"({len(query_subset) / duration:.0f} validations/sec)")
    
    def test_large_dataset_aggregate_calculation_performance(self):
        """Test performance of calculating aggregates for large datasets."""
        # Create comprehensive metrics for large dataset
        query_subset = self.large_query_dataset[:1000]
        
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            
            # Add all metric types
            metrics.retrieval_metrics.update({
                "documents_retrieved": len(query_data["retrieval_results"]),
                "retrieval_time": query_data["retrieval_time"],
                "fusion_score_spread": 0.3
            })
            
            metrics.generation_metrics.update({
                "confidence_score": query_data["confidence"],
                "generation_time": query_data["generation_time"],
                "answer_length": len(query_data["answer"])
            })
            
            metrics.validation_results.update({
                "answer_quality_score": 0.8,
                "meets_expectations": True
            })
            
            metrics.performance_metrics.update({
                "total_time": query_data["total_time"],
                "memory_peak_mb": query_data["memory_peak"],
                "cpu_usage_percent": query_data["cpu_usage"]
            })
        
        # Test aggregate calculation performance
        start_time = time.time()
        aggregates = self.collector.calculate_aggregate_metrics()
        duration = time.time() - start_time
        
        # Should calculate aggregates for 1000 queries in under 0.5 seconds
        assert duration < 0.5
        
        # Verify aggregate quality
        assert aggregates["total_queries"] == 1000
        assert "retrieval_aggregates" in aggregates
        assert "generation_aggregates" in aggregates
        assert "validation_aggregates" in aggregates
        assert "performance_aggregates" in aggregates
        
        # Verify statistical calculations
        ret_agg = aggregates["retrieval_aggregates"]
        gen_agg = aggregates["generation_aggregates"]
        val_agg = aggregates["validation_aggregates"]
        perf_agg = aggregates["performance_aggregates"]
        
        assert ret_agg["avg_retrieval_time"] > 0
        assert gen_agg["avg_confidence"] > 0
        assert val_agg["success_rate"] > 0
        assert perf_agg["throughput_queries_per_sec"] > 0
        
        print(f"Calculated aggregates for {len(query_subset)} queries in {duration:.3f}s")
        print(f"Average retrieval time: {ret_agg['avg_retrieval_time']:.3f}s")
        print(f"Average confidence: {gen_agg['avg_confidence']:.3f}")
        print(f"Success rate: {val_agg['success_rate']:.1%}")
    
    def test_high_volume_metrics_export_performance(self):
        """Test performance of exporting large volumes of metrics."""
        # Create metrics for large dataset
        query_subset = self.large_query_dataset[:800]
        
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            
            # Add comprehensive metrics
            metrics.retrieval_metrics.update({
                "documents_retrieved": len(query_data["retrieval_results"]),
                "avg_semantic_score": np.mean([score for _, score in query_data["retrieval_results"]]),
                "retrieval_time": query_data["retrieval_time"]
            })
            
            metrics.generation_metrics.update({
                "confidence_score": query_data["confidence"],
                "answer_length": len(query_data["answer"]),
                "citations_used": len(query_data["citations"]),
                "generation_time": query_data["generation_time"]
            })
            
            metrics.validation_results.update({
                "meets_expectations": True,
                "answer_quality_score": 0.85
            })
            
            metrics.performance_metrics.update({
                "total_time": query_data["total_time"],
                "memory_peak_mb": query_data["memory_peak"]
            })
        
        # Test export performance
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            start_time = time.time()
            self.collector.export_metrics(export_path)
            duration = time.time() - start_time
            
            # Should export 800 queries in under 2 seconds
            assert duration < 2.0
            
            # Verify export file
            assert export_path.exists()
            
            # Load and verify exported data
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data["query_metrics"]) == 800
            assert "aggregate_metrics" in exported_data
            assert exported_data["aggregate_metrics"]["total_queries"] == 800
            
            file_size_mb = export_path.stat().st_size / (1024 * 1024)
            
            print(f"Exported {len(query_subset)} query metrics in {duration:.3f}s")
            print(f"Export file size: {file_size_mb:.1f} MB")
            print(f"Export rate: {len(query_subset) / duration:.0f} queries/sec")
            
        finally:
            export_path.unlink(missing_ok=True)
    
    def test_concurrent_metrics_collection_simulation(self):
        """Simulate concurrent metrics collection patterns."""
        query_subset = self.large_query_dataset[:200]
        
        start_time = time.time()
        
        # Simulate overlapping query processing
        active_queries = {}
        
        for i, query_data in enumerate(query_subset):
            # Start query
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            active_queries[query_data["query_id"]] = (metrics, query_data)
            
            # Process some previously started queries
            if i % 5 == 0 and len(active_queries) > 5:
                # Process 3 random active queries
                query_ids_to_process = list(active_queries.keys())[:3]
                
                for query_id in query_ids_to_process:
                    metrics, data = active_queries.pop(query_id)
                    
                    # Collect all metrics
                    self.collector.collect_retrieval_metrics(
                        metrics, data["retrieval_results"], retrieval_time=data["retrieval_time"]
                    )
                    
                    self.collector.collect_generation_metrics(
                        metrics, data["answer"], data["confidence"], data["generation_time"]
                    )
                    
                    self.collector.collect_performance_metrics(
                        metrics, data["total_time"], data["memory_peak"], data["cpu_usage"]
                    )
        
        # Process remaining active queries
        for metrics, data in active_queries.values():
            self.collector.collect_retrieval_metrics(
                metrics, data["retrieval_results"], retrieval_time=data["retrieval_time"]
            )
            
            self.collector.collect_generation_metrics(
                metrics, data["answer"], data["confidence"], data["generation_time"]
            )
            
            self.collector.collect_performance_metrics(
                metrics, data["total_time"], data["memory_peak"], data["cpu_usage"]
            )
        
        duration = time.time() - start_time
        
        # Should handle concurrent simulation in reasonable time
        assert duration < 2.0
        assert len(self.collector.query_metrics) == 200
        
        print(f"Simulated concurrent processing of {len(query_subset)} queries in {duration:.3f}s")
    
    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large metric datasets."""
        import sys
        
        # Baseline memory usage
        baseline_collector = MetricsCollector()
        
        # Process large dataset
        query_subset = self.large_query_dataset[:1000]
        
        start_time = time.time()
        
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            
            # Add minimal but complete metrics to test memory efficiency
            metrics.retrieval_metrics.update({
                "documents_retrieved": len(query_data["retrieval_results"]),
                "retrieval_time": query_data["retrieval_time"]
            })
            
            metrics.generation_metrics.update({
                "confidence_score": query_data["confidence"],
                "generation_time": query_data["generation_time"]
            })
        
        processing_duration = time.time() - start_time
        
        # Test memory-efficient operations
        start_time = time.time()
        
        # Operations that should be memory-efficient
        query_count = len(self.collector.query_metrics)
        aggregates = self.collector.calculate_aggregate_metrics()
        summary = self.collector.get_metrics_summary()
        
        operations_duration = time.time() - start_time
        
        # Verify results
        assert query_count == 1000
        assert aggregates["total_queries"] == 1000
        assert "1000" in summary
        
        # Should process efficiently
        assert processing_duration < 1.0
        assert operations_duration < 0.5
        
        print(f"Memory-efficient processing of {query_count} queries: {processing_duration:.3f}s")
        print(f"Memory-efficient operations: {operations_duration:.3f}s")
    
    def test_streaming_metrics_collection_performance(self):
        """Test performance of streaming metrics collection (one at a time)."""
        query_subset = self.large_query_dataset[:500]
        
        start_time = time.time()
        
        for query_data in query_subset:
            # Start and complete each query sequentially (streaming pattern)
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            
            # Collect all metrics for this query before moving to next
            self.collector.collect_retrieval_metrics(
                metrics,
                query_data["retrieval_results"],
                dense_results=query_data["dense_results"],
                sparse_results=query_data["sparse_results"],
                retrieval_time=query_data["retrieval_time"]
            )
            
            self.collector.collect_generation_metrics(
                metrics,
                query_data["answer"],
                query_data["confidence"],
                query_data["generation_time"],
                citations=query_data["citations"],
                model_info=query_data["model_info"]
            )
            
            self.collector.collect_performance_metrics(
                metrics,
                query_data["total_time"],
                query_data["memory_peak"],
                query_data["cpu_usage"]
            )
        
        duration = time.time() - start_time
        
        # Should handle streaming collection efficiently
        assert duration < 3.0  # More time allowed for complete processing
        assert len(self.collector.query_metrics) == 500
        
        # Verify all queries have complete metrics
        for metrics in self.collector.query_metrics:
            assert metrics.retrieval_metrics["documents_retrieved"] > 0
            assert metrics.generation_metrics["confidence_score"] > 0
            assert metrics.performance_metrics["total_time"] > 0
        
        print(f"Streaming collection of {len(query_subset)} complete queries in {duration:.3f}s "
              f"({len(query_subset) / duration:.1f} queries/sec)")
    
    def test_statistical_computation_performance(self):
        """Test performance of statistical computations on large datasets."""
        # Generate large dataset with varied metrics
        query_subset = self.large_query_dataset[:1500]
        
        for query_data in query_subset:
            metrics = self.collector.start_query_collection(
                query_data["query_id"],
                query_data["query_text"]
            )
            
            # Add metrics with statistical variety
            metrics.retrieval_metrics.update({
                "retrieval_time": query_data["retrieval_time"],
                "documents_retrieved": len(query_data["retrieval_results"]),
                "fusion_score_spread": np.random.random() * 0.5
            })
            
            metrics.generation_metrics.update({
                "generation_time": query_data["generation_time"],
                "confidence_score": query_data["confidence"],
                "answer_length": len(query_data["answer"])
            })
            
            metrics.performance_metrics.update({
                "total_time": query_data["total_time"]
            })
        
        # Test statistical computations
        start_time = time.time()
        aggregates = self.collector.calculate_aggregate_metrics()
        duration = time.time() - start_time
        
        # Should compute statistics for 1500 queries quickly
        assert duration < 0.8
        
        # Verify statistical calculations
        ret_agg = aggregates["retrieval_aggregates"]
        gen_agg = aggregates["generation_aggregates"]
        perf_agg = aggregates["performance_aggregates"]
        
        # Verify percentile calculations
        assert "p95_retrieval_time" in ret_agg
        assert "p95_total_time" in perf_agg
        
        # Verify averages make sense
        assert 0 < ret_agg["avg_retrieval_time"] < 1.0
        assert 0 < gen_agg["avg_confidence"] <= 1.0
        assert 0 < perf_agg["throughput_queries_per_sec"] < 10000
        
        print(f"Statistical computation on {len(query_subset)} queries: {duration:.3f}s")
        print(f"P95 retrieval time: {ret_agg['p95_retrieval_time']:.3f}s")
        print(f"Average confidence: {gen_agg['avg_confidence']:.3f}")
        print(f"Throughput: {perf_agg['throughput_queries_per_sec']:.1f} queries/sec")