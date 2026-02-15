"""
Unit Tests for MemoryMonitor Component.

Tests the real-time memory usage tracking and prediction functionality
of the MemoryMonitor component.
"""

import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Imports handled by conftest.py

from fixtures.base_test import MLInfrastructureTestBase, MemoryTestMixin, PerformanceTestMixin
from fixtures.mock_memory import MockMemorySystem, create_memory_test_scenarios

from components.query_processors.analyzers.ml_models.memory_monitor import (
    MemoryMonitor, MemoryStats, ModelMemoryInfo
)


class TestMemoryMonitor(MLInfrastructureTestBase, MemoryTestMixin):
    """Test cases for MemoryMonitor component."""
    
    def setUp(self):
        super().setUp()
        self.monitor = None
    
    def tearDown(self):
        if self.monitor:
            self.monitor.stop_monitoring()
        super().tearDown()
    
    def test_initialization(self):
        """Test MemoryMonitor initialization."""
        # Test default initialization
        monitor = MemoryMonitor(update_interval_seconds=1.0)
        self.assertEqual(monitor.update_interval, 1.0)
        self.assertIsNotNone(monitor._model_estimates)
        self.assertFalse(monitor._monitoring)
        
        # Test custom initialization
        monitor_custom = MemoryMonitor(update_interval_seconds=0.5)
        self.assertEqual(monitor_custom.update_interval, 0.5)
        
        self.monitor = monitor  # For cleanup
    
    def test_memory_stats_retrieval(self):
        """Test getting current memory statistics."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        stats = self.monitor.get_current_stats()
        
        # Verify MemoryStats structure
        self.assertIsInstance(stats, MemoryStats)
        self.assertGreater(stats.total_mb, 0)
        self.assertGreater(stats.used_mb, 0)
        self.assertGreater(stats.available_mb, 0)
        self.assertGreaterEqual(stats.percent_used, 0)
        self.assertLessEqual(stats.percent_used, 100)
        self.assertGreaterEqual(stats.epic1_process_mb, 0)
        
        # Verify consistency
        self.assertAlmostEqual(
            stats.used_mb + stats.available_mb,
            stats.total_mb,
            delta=stats.total_mb * 0.50  # 50% tolerance - macOS reports wired/cached separately
        )
    
    def test_background_monitoring(self):
        """Test background monitoring functionality."""
        self.monitor = MemoryMonitor(update_interval_seconds=0.1)
        
        # Start monitoring
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor._monitoring)
        self.assertIsNotNone(self.monitor._monitor_thread)
        
        # Wait for some updates
        time.sleep(0.3)
        
        # Check that stats are being updated
        stats1 = self.monitor.get_current_stats()
        time.sleep(0.2)
        stats2 = self.monitor.get_current_stats()
        
        # Stats should be updated (timestamps would differ in real implementation)
        self.assertIsInstance(stats1, MemoryStats)
        self.assertIsInstance(stats2, MemoryStats)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor._monitoring)
    
    def test_model_memory_estimation(self):
        """Test model memory footprint estimation."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Test known models
        scibert_full = self.monitor.estimate_model_memory('SciBERT', quantized=False)
        scibert_quantized = self.monitor.estimate_model_memory('SciBERT', quantized=True)
        
        # Quantized should use less memory
        self.assertGreater(scibert_full, scibert_quantized)
        self.assertGreater(scibert_quantized, 0)
        
        # Test unknown model (should use default)
        unknown_model = self.monitor.estimate_model_memory('unknown-model', quantized=True)
        self.assertGreater(unknown_model, 0)
        
        # Test all predefined models
        expected_models = ['SciBERT', 'DistilBERT', 'DeBERTa-v3', 'Sentence-BERT', 'T5-small']
        for model_name in expected_models:
            full_estimate = self.monitor.estimate_model_memory(model_name, quantized=False)
            quantized_estimate = self.monitor.estimate_model_memory(model_name, quantized=True)
            
            self.assertGreater(full_estimate, 0, f"Full estimate for {model_name} should be positive")
            self.assertGreater(quantized_estimate, 0, f"Quantized estimate for {model_name} should be positive")
            self.assertGreater(full_estimate, quantized_estimate, f"Full should be larger than quantized for {model_name}")
    
    def test_actual_memory_recording(self):
        """Test recording actual model memory usage."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        model_name = 'test-model'
        actual_memory = 256.5
        
        # Initially no record
        self.assertIsNone(self.monitor.get_actual_model_memory(model_name))
        
        # Record actual memory
        self.monitor.record_actual_model_memory(model_name, actual_memory)
        
        # Should now be recorded
        recorded_memory = self.monitor.get_actual_model_memory(model_name)
        self.assertEqual(recorded_memory, actual_memory)
    
    def test_memory_budget_checking(self):
        """Test memory budget constraint checking."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Mock current memory usage to be predictable
        with patch.object(self.monitor, 'get_epic1_memory_usage', return_value=500.0):
            memory_budget = 1024.0  # 1GB budget
            
            # Small model should not exceed budget
            would_exceed_small = self.monitor.would_exceed_budget(
                'test-small-model', memory_budget, quantized=True
            )
            
            # Large model might exceed budget
            would_exceed_large = self.monitor.would_exceed_budget(
                'DeBERTa-v3', memory_budget, quantized=False
            )
            
            # Test with very small budget
            small_budget = 100.0
            would_exceed_tiny_budget = self.monitor.would_exceed_budget(
                'SciBERT', small_budget, quantized=True
            )
            self.assertTrue(would_exceed_tiny_budget)
    
    def test_memory_pressure_levels(self):
        """Test memory pressure level calculation."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        memory_budget = 2048.0  # 2GB budget
        
        # Mock different usage levels
        test_cases = [
            (memory_budget * 0.3, 'low'),     # 30% usage
            (memory_budget * 0.6, 'medium'),  # 60% usage  
            (memory_budget * 0.8, 'high'),    # 80% usage
            (memory_budget * 0.95, 'critical') # 95% usage
        ]
        
        for usage, expected_level in test_cases:
            with patch.object(self.monitor, 'get_epic1_memory_usage', return_value=usage):
                level = self.monitor.get_memory_pressure_level(memory_budget)
                self.assertEqual(level, expected_level, 
                               f"Usage {usage:.0f}MB should be {expected_level} pressure")
    
    def test_eviction_candidates_selection(self):
        """Test eviction candidate selection."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Record several models with different memory usage
        models = [
            ('model-large', 500.0),
            ('model-medium', 300.0), 
            ('model-small', 100.0),
            ('model-tiny', 50.0)
        ]
        
        for model_name, memory_mb in models:
            self.monitor.record_actual_model_memory(model_name, memory_mb)
        
        # Get candidates to free 400MB
        candidates = self.monitor.get_eviction_candidates(400.0)
        
        # Should get models starting with largest
        self.assertIn('model-large', candidates)
        
        # Total should meet or exceed target
        total_freeable = sum(candidates.values())
        self.assertGreaterEqual(total_freeable, 400.0)
        
        # Should be ordered by size (largest first)
        candidate_sizes = list(candidates.values())
        self.assertEqual(candidate_sizes, sorted(candidate_sizes, reverse=True))
    
    def test_memory_status_logging(self):
        """Test memory status logging functionality."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Record some model memory
        self.monitor.record_actual_model_memory('test-model', 200.0)
        
        # Should not raise exception
        try:
            self.monitor.log_memory_status()
        except Exception as e:
            self.fail(f"log_memory_status raised exception: {e}")
    
    def test_context_manager(self):
        """Test MemoryMonitor as context manager."""
        # Test context manager functionality
        with MemoryMonitor(update_interval_seconds=0.1) as monitor:
            self.assertTrue(monitor._monitoring)
            
            # Should be able to get stats
            stats = monitor.get_current_stats()
            self.assertIsInstance(stats, MemoryStats)
        
        # Should stop monitoring after exit
        self.assertFalse(monitor._monitoring)
    
    def test_thread_safety(self):
        """Test thread safety of MemoryMonitor."""
        self.monitor = MemoryMonitor(update_interval_seconds=0.05)
        self.monitor.start_monitoring()
        
        # Results storage
        results = []
        exceptions = []
        
        def worker():
            try:
                for _ in range(10):
                    stats = self.monitor.get_current_stats()
                    results.append(stats.total_mb)
                    
                    # Record some memory
                    self.monitor.record_actual_model_memory(
                        f'model-{threading.current_thread().ident}',
                        100.0
                    )
                    
                    time.sleep(0.01)
            except Exception as e:
                exceptions.append(e)
        
        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have no exceptions
        self.assertEqual(len(exceptions), 0, f"Thread safety compromised: {exceptions}")
        
        # Should have results from all threads
        self.assertGreater(len(results), 0)
        
        self.monitor.stop_monitoring()
    
    def test_error_handling(self):
        """Test error handling in monitoring loop."""
        # This test would require more complex mocking to simulate
        # errors in the monitoring loop. For now, test basic error resilience
        
        self.monitor = MemoryMonitor(update_interval_seconds=0.1)
        
        # Start and stop monitoring rapidly (stress test)
        for _ in range(5):
            self.monitor.start_monitoring()
            time.sleep(0.05)
            self.monitor.stop_monitoring()
        
        # Should not crash and should be in stopped state
        self.assertFalse(self.monitor._monitoring)
    
    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility considerations."""
        # Test that MemoryMonitor works across different platforms
        # This mainly tests that it doesn't crash on import and initialization
        
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Should be able to get stats regardless of platform
        stats = self.monitor.get_current_stats()
        self.assertIsInstance(stats, MemoryStats)
        self.assertGreater(stats.total_mb, 0)
        
        # Should handle different memory reporting formats
        # (This would be more comprehensive with platform-specific mocking)


class TestMemoryStats(MLInfrastructureTestBase):
    """Test cases for MemoryStats data structure."""
    
    def test_memory_stats_creation(self):
        """Test MemoryStats creation and validation."""
        stats = MemoryStats(
            total_mb=16384.0,
            used_mb=8192.0,
            available_mb=8192.0,
            percent_used=50.0,
            epic1_process_mb=512.0
        )
        
        self.assertEqual(stats.total_mb, 16384.0)
        self.assertEqual(stats.used_mb, 8192.0)
        self.assertEqual(stats.available_mb, 8192.0)
        self.assertEqual(stats.percent_used, 50.0)
        self.assertEqual(stats.epic1_process_mb, 512.0)
    
    def test_memory_stats_consistency(self):
        """Test MemoryStats consistency validation."""
        # Test consistent stats
        stats = MemoryStats(
            total_mb=1024.0,
            used_mb=512.0,
            available_mb=512.0,
            percent_used=50.0,
            epic1_process_mb=100.0
        )
        
        # Should be consistent
        self.assertAlmostEqual(stats.used_mb + stats.available_mb, stats.total_mb)
        self.assertAlmostEqual(stats.percent_used, (stats.used_mb / stats.total_mb) * 100, places=1)


class TestModelMemoryInfo(MLInfrastructureTestBase):
    """Test cases for ModelMemoryInfo data structure."""
    
    def test_model_memory_info_creation(self):
        """Test ModelMemoryInfo creation."""
        info = ModelMemoryInfo(
            model_name='SciBERT',
            estimated_size_mb=440.0,
            actual_size_mb=425.0,
            quantized=True
        )
        
        self.assertEqual(info.model_name, 'SciBERT')
        self.assertEqual(info.estimated_size_mb, 440.0)
        self.assertEqual(info.actual_size_mb, 425.0)
        self.assertTrue(info.quantized)
    
    def test_model_memory_info_optional_fields(self):
        """Test ModelMemoryInfo with optional fields."""
        # Test with minimal required fields
        info = ModelMemoryInfo(
            model_name='test-model',
            estimated_size_mb=300.0
        )
        
        self.assertEqual(info.model_name, 'test-model')
        self.assertEqual(info.estimated_size_mb, 300.0)
        self.assertIsNone(info.actual_size_mb)
        self.assertFalse(info.quantized)


# Integration test for MemoryMonitor with mock memory system
class TestMemoryMonitorWithMockSystem(MLInfrastructureTestBase, MemoryTestMixin):
    """Test MemoryMonitor integration with mock memory systems."""
    
    def test_integration_with_mock_memory(self):
        """Test MemoryMonitor with controlled mock memory system."""
        # Create memory monitor with mock system
        memory_scenarios = create_memory_test_scenarios()
        mock_system = memory_scenarios['memory_pressure']
        
        # This would require modification of MemoryMonitor to accept
        # a custom memory backend, which is beyond the scope of unit tests
        # but would be valuable for integration tests
        
        # For now, test that the mock system provides expected interface
        mock_monitor = self.mock_memory_monitor
        
        stats = mock_monitor.get_current_stats()
        # Use class-name check instead of isinstance to avoid dual-import-path
        # mismatch (components. vs src.components. resolve to different classes)
        self.assertEqual(type(stats).__name__, 'MemoryStats')
        self.assertGreater(stats.total_mb, 0)
        
        # Test memory estimation
        estimate = mock_monitor.estimate_model_memory('SciBERT')
        self.assertGreater(estimate, 0)
        
        # Test budget checking
        would_exceed = mock_monitor.would_exceed_budget('SciBERT', 1024.0)
        self.assertIsInstance(would_exceed, bool)


# Performance tests
class TestMemoryMonitorPerformance(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test MemoryMonitor performance characteristics."""
    
    def test_memory_stats_retrieval_performance(self):
        """Test performance of memory stats retrieval."""
        self.monitor = MemoryMonitor(update_interval_seconds=1.0)
        
        # Benchmark stats retrieval
        def get_stats():
            return self.monitor.get_current_stats()
        
        with self.measure_performance('memory_stats_retrieval'):
            results = self.benchmark_operation(get_stats, iterations=100, warmup=10)
        
        # Should be fast (< 10ms p95)
        self.assertLess(results['p95_latency_ms'], 10.0)
        self.assertGreater(results['success_rate'], 0.95)
    
    def test_background_monitoring_overhead(self):
        """Test overhead of background monitoring."""
        self.monitor = MemoryMonitor(update_interval_seconds=0.1)
        
        # Measure baseline performance
        def baseline_operation():
            time.sleep(0.001)  # Minimal operation
            return True
        
        baseline_results = self.benchmark_operation(baseline_operation, iterations=50)
        
        # Start monitoring and measure performance
        self.monitor.start_monitoring()
        time.sleep(0.5)  # Let monitoring settle
        
        monitoring_results = self.benchmark_operation(baseline_operation, iterations=50)
        
        # Monitoring should not significantly impact performance
        overhead_ratio = (monitoring_results['mean_latency_ms'] / baseline_results['mean_latency_ms'])
        self.assertLess(overhead_ratio, 1.1, "Monitoring overhead should be < 10%")


if __name__ == '__main__':
    # Run tests when script is executed directly
    import unittest
    unittest.main()