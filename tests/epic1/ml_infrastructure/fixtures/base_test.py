"""
Base Test Classes for Epic 1 ML Infrastructure Testing.

Provides common test infrastructure, utilities, and mixins for consistent
testing across all ML infrastructure components.
"""

import unittest
import time
import threading
import tempfile
import shutil
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from contextlib import contextmanager
from unittest.mock import Mock, MagicMock, patch
import pytest

# Import our fixtures
from .mock_models import MockModelFactory, MockModelLoader, MockTransformerModel
from .mock_memory import MockMemorySystem, MockMemoryMonitor, create_memory_test_scenarios
from .test_data import TestDataGenerator, ViewFrameworkTestData


class MLInfrastructureTestBase(unittest.TestCase):
    """
    Base test class for all ML infrastructure tests.
    
    Provides:
    - Common setup and teardown
    - Mock infrastructure setup
    - Logging configuration
    - Test utilities and assertions
    - Performance measurement helpers
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test resources."""
        # Configure test logging
        cls._setup_test_logging()
        
        # Store original components for cleanup
        cls._original_components = {}
        
        # Create temp directory for test artifacts
        cls.test_temp_dir = tempfile.mkdtemp(prefix='epic1_ml_test_')
        cls.test_temp_path = Path(cls.test_temp_dir)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up class-level test resources."""
        # Clean up temp directory
        if hasattr(cls, 'test_temp_dir'):
            shutil.rmtree(cls.test_temp_dir, ignore_errors=True)
        
        # Restore any patched components
        for component, original in cls._original_components.items():
            setattr(sys.modules[component.__module__], component.__name__, original)
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Reset test state
        self._test_start_time = time.time()
        self._performance_measurements = {}
        self._mock_objects = {}
        
        # Set up mock infrastructure
        self.setup_mock_infrastructure()
        
        # Set up test data
        self.setup_test_data()
        
        # Test configuration
        self.test_config = {
            'timeout_seconds': 30.0,
            'memory_budget_mb': 2048.0,
            'performance_tolerance_percent': 50.0,
            'enable_mock_failures': False,
            'mock_failure_rate': 0.1
        }
    
    def tearDown(self):
        """Clean up test fixtures after each test."""
        # Stop any running mock systems
        self.cleanup_mock_infrastructure()
        
        # Clear any allocated memory
        self.cleanup_memory_allocations()
        
        # Log test completion time
        test_duration = time.time() - self._test_start_time
        logging.debug(f"Test {self._testMethodName} completed in {test_duration:.3f}s")
    
    @classmethod
    def _setup_test_logging(cls):
        """Configure logging for tests."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Quiet down some noisy loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def setup_mock_infrastructure(self):
        """Set up mock infrastructure components."""
        # Create mock memory system
        self.mock_memory_system = MockMemorySystem()
        self.mock_memory_monitor = MockMemoryMonitor(self.mock_memory_system)
        
        # Create mock model factory
        self.mock_model_factory = MockModelFactory()
        self.mock_model_loader = MockModelLoader()
        
        # Store mocks for cleanup
        self._mock_objects.update({
            'memory_system': self.mock_memory_system,
            'memory_monitor': self.mock_memory_monitor,
            'model_factory': self.mock_model_factory,
            'model_loader': self.mock_model_loader
        })
    
    def setup_test_data(self):
        """Set up test data for the current test."""
        # Generate test queries
        self.test_queries = TestDataGenerator.generate_test_queries(10)
        
        # Generate model test configs
        self.model_test_configs = TestDataGenerator.generate_model_test_configs()
        
        # Generate view test data
        self.view_test_data = ViewFrameworkTestData.generate_view_results()
    
    def cleanup_mock_infrastructure(self):
        """Clean up mock infrastructure."""
        if hasattr(self, 'mock_memory_system'):
            self.mock_memory_system.stop_simulation()
        
        if hasattr(self, 'mock_memory_monitor'):
            self.mock_memory_monitor.stop_monitoring()
        
        if hasattr(self, 'mock_model_loader'):
            self.mock_model_loader.clear()
    
    def cleanup_memory_allocations(self):
        """Clean up any memory allocations from tests."""
        if hasattr(self, 'mock_memory_system'):
            # Reset memory system to clean state
            self.mock_memory_system.reset_to_defaults()
    
    # Utility Methods
    
    def create_test_model(self, name: str = 'test-model', **kwargs) -> MockTransformerModel:
        """Create a test model with specified characteristics."""
        return self.mock_model_factory.create_model(name, **kwargs)
    
    def simulate_memory_pressure(self, level: str = 'high') -> None:
        """Simulate memory pressure for testing."""
        pressure_levels = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.95
        }
        
        ratio = pressure_levels.get(level, 0.8)
        total_memory = self.mock_memory_system.config.total_memory_mb
        self.mock_memory_system._used_memory_mb = total_memory * ratio
    
    def measure_performance(self, operation_name: str) -> 'PerformanceMeasurement':
        """Context manager for measuring operation performance."""
        return PerformanceMeasurement(operation_name, self._performance_measurements)
    
    def get_performance_measurements(self) -> Dict[str, Dict[str, float]]:
        """Get all performance measurements from this test."""
        return self._performance_measurements.copy()
    
    # Assertion Methods
    
    def assertMemoryUsageWithin(self, expected_mb: float, tolerance_percent: float = 20.0):
        """Assert memory usage is within expected range."""
        actual_mb = self.mock_memory_system.get_memory_stats().process_mb
        tolerance_mb = expected_mb * (tolerance_percent / 100.0)
        
        self.assertGreaterEqual(
            actual_mb, 
            expected_mb - tolerance_mb,
            f"Memory usage {actual_mb:.1f}MB below expected {expected_mb:.1f}MB ±{tolerance_percent}%"
        )
        self.assertLessEqual(
            actual_mb,
            expected_mb + tolerance_mb, 
            f"Memory usage {actual_mb:.1f}MB above expected {expected_mb:.1f}MB ±{tolerance_percent}%"
        )
    
    def assertLatencyWithin(self, actual_seconds: float, expected_seconds: float, tolerance_percent: float = 50.0):
        """Assert latency is within expected range."""
        tolerance_seconds = expected_seconds * (tolerance_percent / 100.0)
        
        self.assertGreaterEqual(
            actual_seconds,
            0.0,
            "Latency cannot be negative"
        )
        self.assertLessEqual(
            actual_seconds,
            expected_seconds + tolerance_seconds,
            f"Latency {actual_seconds:.3f}s exceeds expected {expected_seconds:.3f}s ±{tolerance_percent}%"
        )
    
    def assertCacheHitRate(self, cache_stats: Dict[str, Any], min_hit_rate: float = 0.8):
        """Assert cache hit rate meets minimum threshold."""
        hit_rate = cache_stats.get('hit_rate', 0.0)
        self.assertGreaterEqual(
            hit_rate,
            min_hit_rate,
            f"Cache hit rate {hit_rate:.2%} below minimum {min_hit_rate:.2%}"
        )
    
    def assertModelLoaded(self, model_name: str, manager=None):
        """Assert that a model is loaded."""
        if manager is None:
            loaded_models = self.mock_model_loader.get_loaded_models()
            self.assertIn(model_name, loaded_models, f"Model {model_name} not loaded")
            self.assertTrue(
                loaded_models[model_name].is_loaded,
                f"Model {model_name} exists but is not in loaded state"
            )
        else:
            model_info = manager.get_model_info(model_name)
            self.assertIsNotNone(model_info, f"No info found for model {model_name}")
            self.assertEqual(model_info.status, 'loaded', f"Model {model_name} not loaded")
    
    def assertModelEvicted(self, model_name: str, manager=None):
        """Assert that a model has been evicted."""
        if manager is None:
            loaded_models = self.mock_model_loader.get_loaded_models()
            if model_name in loaded_models:
                self.assertFalse(
                    loaded_models[model_name].is_loaded,
                    f"Model {model_name} still loaded, not evicted"
                )
        else:
            model_info = manager.get_model_info(model_name)
            if model_info:
                self.assertNotEqual(
                    model_info.status, 
                    'loaded',
                    f"Model {model_name} still loaded, not evicted"
                )


class MemoryTestMixin:
    """Mixin providing memory-specific test utilities."""
    
    def setUp(self):
        super().setUp() if hasattr(super(), 'setUp') else None
        self._memory_snapshots = []
    
    def take_memory_snapshot(self, label: str = '') -> Dict[str, Any]:
        """Take a snapshot of current memory state."""
        if not hasattr(self, 'mock_memory_system'):
            return {}
        
        snapshot = {
            'label': label,
            'timestamp': time.time(),
            'stats': self.mock_memory_system.get_memory_stats(),
            'allocations': self.mock_memory_system.get_total_allocations(),
            'allocation_count': self.mock_memory_system.get_allocation_count()
        }
        
        self._memory_snapshots.append(snapshot)
        return snapshot
    
    def get_memory_snapshots(self) -> List[Dict[str, Any]]:
        """Get all memory snapshots from this test."""
        return self._memory_snapshots.copy()
    
    def assert_memory_not_leaked(self, start_snapshot: Dict[str, Any], end_snapshot: Dict[str, Any], tolerance_mb: float = 10.0):
        """Assert no significant memory leak between snapshots."""
        start_usage = start_snapshot['stats'].process_mb
        end_usage = end_snapshot['stats'].process_mb
        
        increase = end_usage - start_usage
        self.assertLessEqual(
            increase,
            tolerance_mb,
            f"Memory leak detected: increased by {increase:.1f}MB (tolerance: {tolerance_mb:.1f}MB)"
        )
    
    def simulate_memory_allocation(self, size_mb: float) -> str:
        """Simulate memory allocation and return allocation ID."""
        return self.mock_memory_system.allocate_memory(size_mb)
    
    def simulate_memory_deallocation(self, allocation_id: str) -> float:
        """Simulate memory deallocation and return freed size."""
        return self.mock_memory_system.deallocate_memory(allocation_id)


class PerformanceTestMixin:
    """Mixin providing performance testing utilities."""
    
    def setUp(self):
        super().setUp() if hasattr(super(), 'setUp') else None
        self._performance_results = {}
    
    def benchmark_operation(self, operation: Callable, iterations: int = 100, warmup: int = 10) -> Dict[str, float]:
        """Benchmark an operation and return performance statistics."""
        # Warmup
        for _ in range(warmup):
            try:
                operation()
            except Exception:
                pass  # Ignore warmup errors
        
        # Measure
        latencies = []
        start_time = time.time()
        
        for _ in range(iterations):
            op_start = time.time()
            try:
                operation()
                op_end = time.time()
                latencies.append((op_end - op_start) * 1000)  # Convert to ms
            except Exception as e:
                # Record failed operations
                latencies.append(float('inf'))
        
        end_time = time.time()
        
        # Calculate statistics
        valid_latencies = [l for l in latencies if l != float('inf')]
        
        if not valid_latencies:
            return {
                'success_rate': 0.0,
                'total_time_seconds': end_time - start_time,
                'iterations': iterations,
                'errors': len(latencies)
            }
        
        valid_latencies.sort()
        n = len(valid_latencies)
        
        return {
            'mean_latency_ms': sum(valid_latencies) / n,
            'median_latency_ms': valid_latencies[n // 2],
            'p95_latency_ms': valid_latencies[int(n * 0.95)],
            'p99_latency_ms': valid_latencies[int(n * 0.99)],
            'min_latency_ms': valid_latencies[0],
            'max_latency_ms': valid_latencies[-1],
            'success_rate': len(valid_latencies) / iterations,
            'throughput_ops_per_second': len(valid_latencies) / (end_time - start_time),
            'total_time_seconds': end_time - start_time,
            'iterations': iterations,
            'errors': iterations - len(valid_latencies)
        }
    
    def assert_performance_within_bounds(self, results: Dict[str, float], expected_latency_ms: float, tolerance_percent: float = 50.0):
        """Assert performance results are within expected bounds."""
        actual_latency = results.get('p95_latency_ms', float('inf'))
        tolerance_ms = expected_latency_ms * (tolerance_percent / 100.0)
        
        self.assertLessEqual(
            actual_latency,
            expected_latency_ms + tolerance_ms,
            f"P95 latency {actual_latency:.2f}ms exceeds expected {expected_latency_ms:.2f}ms ±{tolerance_percent}%"
        )
        
        # Also check success rate
        success_rate = results.get('success_rate', 0.0)
        self.assertGreaterEqual(
            success_rate,
            0.95,  # Expect 95% success rate
            f"Success rate {success_rate:.2%} below 95%"
        )


class ConcurrencyTestMixin:
    """Mixin providing concurrency testing utilities."""
    
    def run_concurrent_operations(self, operation: Callable, num_threads: int = 4, operations_per_thread: int = 10) -> Dict[str, Any]:
        """Run operations concurrently and collect results."""
        results = []
        exceptions = []
        
        def worker():
            worker_results = []
            worker_exceptions = []
            
            for _ in range(operations_per_thread):
                try:
                    start_time = time.time()
                    result = operation()
                    end_time = time.time()
                    
                    worker_results.append({
                        'result': result,
                        'latency_seconds': end_time - start_time,
                        'thread_id': threading.current_thread().ident
                    })
                except Exception as e:
                    worker_exceptions.append(e)
            
            results.extend(worker_results)
            exceptions.extend(worker_exceptions)
        
        # Start threads
        threads = []
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Analyze results
        total_operations = len(results) + len(exceptions)
        success_rate = len(results) / total_operations if total_operations > 0 else 0.0
        
        latencies = [r['latency_seconds'] for r in results]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        return {
            'total_operations': total_operations,
            'successful_operations': len(results),
            'failed_operations': len(exceptions),
            'success_rate': success_rate,
            'total_time_seconds': end_time - start_time,
            'average_latency_seconds': avg_latency,
            'throughput_ops_per_second': len(results) / (end_time - start_time),
            'exceptions': exceptions,
            'results': results
        }
    
    def assert_thread_safety(self, concurrent_results: Dict[str, Any], min_success_rate: float = 0.9):
        """Assert that concurrent operations maintained thread safety."""
        success_rate = concurrent_results['success_rate']
        self.assertGreaterEqual(
            success_rate,
            min_success_rate,
            f"Thread safety compromised: success rate {success_rate:.2%} below {min_success_rate:.2%}"
        )
        
        # Check for race condition indicators
        exceptions = concurrent_results['exceptions']
        race_condition_exceptions = [
            e for e in exceptions 
            if any(keyword in str(e).lower() for keyword in ['race', 'lock', 'concurrent', 'thread'])
        ]
        
        self.assertEqual(
            len(race_condition_exceptions),
            0,
            f"Detected {len(race_condition_exceptions)} race condition exceptions"
        )


class PerformanceMeasurement:
    """Context manager for measuring operation performance."""
    
    def __init__(self, operation_name: str, storage_dict: Dict[str, Dict[str, float]]):
        self.operation_name = operation_name
        self.storage_dict = storage_dict
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if self.operation_name not in self.storage_dict:
            self.storage_dict[self.operation_name] = {}
        
        measurements = self.storage_dict[self.operation_name]
        measurements['duration_seconds'] = duration
        measurements['duration_ms'] = duration * 1000
        measurements['success'] = exc_type is None
        
        if exc_type:
            measurements['error'] = str(exc_val)


# Pytest fixtures for use with pytest-based tests

@pytest.fixture
def mock_memory_system():
    """Pytest fixture providing mock memory system."""
    memory_system = MockMemorySystem()
    memory_system.start_simulation()
    yield memory_system
    memory_system.stop_simulation()


@pytest.fixture
def mock_model_factory():
    """Pytest fixture providing mock model factory."""
    return MockModelFactory()


@pytest.fixture
def test_queries():
    """Pytest fixture providing test queries."""
    return TestDataGenerator.generate_test_queries(20)


@pytest.fixture
def performance_test_data():
    """Pytest fixture providing performance test data."""
    return TestDataGenerator.generate_performance_test_data()


@contextmanager
def temporary_directory():
    """Context manager providing temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix='epic1_test_')
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@contextmanager
def mock_transformers_loading():
    """Context manager that mocks transformers model loading."""
    mock_loader = MockModelLoader()
    
    def mock_from_pretrained(model_name, **kwargs):
        return mock_loader.load_model(model_name, **kwargs)
    
    with patch('transformers.AutoModel.from_pretrained', side_effect=mock_from_pretrained):
        with patch('transformers.AutoTokenizer.from_pretrained', return_value=Mock()):
            yield mock_loader