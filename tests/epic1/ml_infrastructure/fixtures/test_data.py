"""
Test Data Generators for Epic 1 ML Infrastructure Testing.

Provides realistic test data, configurations, and scenarios for comprehensive
testing of the ML infrastructure components.
"""

import time
import random
import string
from typing import Dict, List, Any, Generator, Tuple
from dataclasses import dataclass, asdict
import json
import numpy as np


@dataclass
class TestQuery:
    """Test query with expected complexity characteristics."""
    
    text: str
    expected_complexity: str  # 'simple', 'medium', 'complex'
    expected_score: float     # Expected complexity score [0, 1]
    technical_terms_count: int
    features: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ModelTestConfig:
    """Configuration for model testing scenarios."""
    
    name: str
    memory_budget_mb: float
    expected_models_count: int
    load_order: List[str]
    eviction_scenario: bool = False
    concurrent_loads: int = 1
    timeout_seconds: float = 30.0
    failure_injection: Dict[str, float] = None  # model -> failure_rate
    
    def __post_init__(self):
        if self.failure_injection is None:
            self.failure_injection = {}


@dataclass
class PerformanceTestData:
    """Performance test expectations and data."""
    
    scenario_name: str
    operation: str  # 'load', 'cache_hit', 'cache_miss', etc.
    expected_latency_ms: float
    expected_throughput: float
    tolerance_percent: float = 20.0
    sample_count: int = 100
    warmup_iterations: int = 10


class TestDataGenerator:
    """Generator for realistic test data and scenarios."""
    
    @staticmethod
    def generate_test_queries(count: int = 20) -> List[TestQuery]:
        """Generate a variety of test queries with known characteristics."""
        queries = []
        
        # Simple queries (low complexity)
        simple_queries = [
            "What is RISC-V?",
            "Define CPU.",
            "How does memory work?", 
            "What is a register?",
            "Explain cache.",
            "What is assembly?",
            "Define instruction set.",
            "What is a processor?",
            "How do computers work?",
            "What is binary?"
        ]
        
        # Medium complexity queries
        medium_queries = [
            "How does RISC-V instruction encoding work for arithmetic operations?",
            "What are the differences between privileged and unprivileged instructions?",
            "Explain the RISC-V memory management unit architecture.",
            "How do RISC-V vector extensions improve performance?",
            "What is the role of the supervisor mode in RISC-V?",
            "How does RISC-V handle interrupts and exceptions?",
            "Explain RISC-V atomic memory operations.",
            "What are the benefits of RISC-V custom extensions?",
            "How does RISC-V compare to ARM and x86 architectures?",
            "Explain RISC-V calling conventions and ABI."
        ]
        
        # Complex queries (high complexity)  
        complex_queries = [
            "How can we implement a cache-coherent multiprocessor system using RISC-V with custom extensions for cryptographic acceleration, considering the trade-offs between performance, power consumption, and security vulnerabilities?",
            "Design a RISC-V-based SoC architecture that implements hardware-software co-design principles for machine learning workloads, including custom vector instructions, memory hierarchy optimization, and real-time scheduling constraints.",
            "Analyze the microarchitectural implications of implementing out-of-order execution in RISC-V processors while maintaining compatibility with existing software and considering the impact on power consumption, area overhead, and verification complexity.",
            "How would you design a fault-tolerant RISC-V system for space applications that can handle radiation-induced errors, implement triple modular redundancy, and provide real-time guarantees for mission-critical tasks?",
            "Implement a secure boot mechanism for RISC-V systems that uses hardware root of trust, cryptographic attestation, and secure enclaves while considering side-channel attack resistance and performance overhead.",
        ]
        
        # Generate queries with expected characteristics
        for i, query_text in enumerate(simple_queries[:count//3]):
            queries.append(TestQuery(
                text=query_text,
                expected_complexity='simple',
                expected_score=random.uniform(0.0, 0.3),
                technical_terms_count=random.randint(1, 3),
                features={
                    'word_count': len(query_text.split()),
                    'char_count': len(query_text),
                    'question_marks': query_text.count('?'),
                    'technical_density': random.uniform(0.1, 0.3)
                },
                metadata={'category': 'simple', 'source': 'generated'}
            ))
        
        for i, query_text in enumerate(medium_queries[:count//3]):
            queries.append(TestQuery(
                text=query_text,
                expected_complexity='medium', 
                expected_score=random.uniform(0.3, 0.7),
                technical_terms_count=random.randint(4, 8),
                features={
                    'word_count': len(query_text.split()),
                    'char_count': len(query_text),
                    'question_marks': query_text.count('?'),
                    'technical_density': random.uniform(0.4, 0.7)
                },
                metadata={'category': 'medium', 'source': 'generated'}
            ))
        
        for i, query_text in enumerate(complex_queries[:count//3]):
            queries.append(TestQuery(
                text=query_text,
                expected_complexity='complex',
                expected_score=random.uniform(0.7, 1.0),
                technical_terms_count=random.randint(10, 20),
                features={
                    'word_count': len(query_text.split()),
                    'char_count': len(query_text),
                    'question_marks': query_text.count('?'),
                    'technical_density': random.uniform(0.7, 1.0)
                },
                metadata={'category': 'complex', 'source': 'generated'}
            ))
        
        return queries[:count]
    
    @staticmethod
    def generate_model_test_configs() -> List[ModelTestConfig]:
        """Generate model testing configurations for various scenarios."""
        configs = []
        
        # Basic loading scenario
        configs.append(ModelTestConfig(
            name="basic_loading",
            memory_budget_mb=2048,
            expected_models_count=3,
            load_order=['test-model-small', 'DistilBERT', 'SciBERT'],
            concurrent_loads=1
        ))
        
        # Memory pressure scenario
        configs.append(ModelTestConfig(
            name="memory_pressure", 
            memory_budget_mb=1024,  # Small budget to force eviction
            expected_models_count=2,
            load_order=['test-model-large', 'DeBERTa-v3', 'SciBERT'],
            eviction_scenario=True,
            concurrent_loads=1
        ))
        
        # Concurrent loading scenario
        configs.append(ModelTestConfig(
            name="concurrent_loading",
            memory_budget_mb=4096,
            expected_models_count=5,
            load_order=['SciBERT', 'DistilBERT', 'Sentence-BERT', 'T5-small', 'test-model-small'],
            concurrent_loads=3,
            timeout_seconds=60.0
        ))
        
        # Failure handling scenario
        configs.append(ModelTestConfig(
            name="failure_handling",
            memory_budget_mb=2048,
            expected_models_count=2,  # Some will fail
            load_order=['test-model-unreliable', 'SciBERT', 'test-model-no-quantization'],
            failure_injection={'test-model-unreliable': 0.5},
            concurrent_loads=1
        ))
        
        # Large-scale scenario
        configs.append(ModelTestConfig(
            name="large_scale",
            memory_budget_mb=8192,
            expected_models_count=8,
            load_order=[
                'SciBERT', 'DistilBERT', 'DeBERTa-v3', 'Sentence-BERT',
                'T5-small', 'test-model-small', 'test-model-large',
                'test-model-no-quantization'
            ],
            concurrent_loads=4,
            timeout_seconds=120.0
        ))
        
        return configs
    
    @staticmethod
    def generate_performance_test_data() -> List[PerformanceTestData]:
        """Generate performance test expectations."""
        return [
            # Memory monitor performance
            PerformanceTestData(
                scenario_name="memory_monitoring",
                operation="get_memory_stats", 
                expected_latency_ms=1.0,
                expected_throughput=1000.0,  # ops/sec
                tolerance_percent=50.0,
                sample_count=1000
            ),
            
            # Model cache performance
            PerformanceTestData(
                scenario_name="cache_hit",
                operation="cache_get_hit",
                expected_latency_ms=0.1,
                expected_throughput=10000.0,
                tolerance_percent=30.0,
                sample_count=10000
            ),
            
            PerformanceTestData(
                scenario_name="cache_miss",
                operation="cache_get_miss", 
                expected_latency_ms=0.5,
                expected_throughput=2000.0,
                tolerance_percent=50.0,
                sample_count=1000
            ),
            
            # Model loading performance
            PerformanceTestData(
                scenario_name="model_loading_small",
                operation="load_small_model",
                expected_latency_ms=500.0,
                expected_throughput=2.0,
                tolerance_percent=100.0,  # High tolerance for loading
                sample_count=10
            ),
            
            PerformanceTestData(
                scenario_name="model_loading_large",
                operation="load_large_model",
                expected_latency_ms=5000.0,
                expected_throughput=0.2,
                tolerance_percent=100.0,
                sample_count=5
            ),
            
            # Quantization performance
            PerformanceTestData(
                scenario_name="quantization",
                operation="quantize_model",
                expected_latency_ms=100.0,
                expected_throughput=10.0,
                tolerance_percent=200.0,  # Very high tolerance
                sample_count=20
            )
        ]
    
    @staticmethod
    def generate_stress_test_scenarios() -> List[Dict[str, Any]]:
        """Generate stress test scenarios."""
        return [
            {
                'name': 'memory_exhaustion',
                'description': 'Load models until memory budget exhausted',
                'memory_budget_mb': 1024,
                'models_to_load': 20,
                'expected_evictions': True,
                'max_runtime_seconds': 120
            },
            {
                'name': 'rapid_loading_unloading',
                'description': 'Rapidly load and unload models',
                'memory_budget_mb': 2048,
                'load_unload_cycles': 100,
                'models_per_cycle': 3,
                'expected_cache_thrashing': True,
                'max_runtime_seconds': 180
            },
            {
                'name': 'concurrent_access',
                'description': 'High concurrent model access',
                'memory_budget_mb': 4096,
                'concurrent_threads': 20,
                'operations_per_thread': 50,
                'operation_types': ['load', 'access', 'unload'],
                'max_runtime_seconds': 300
            },
            {
                'name': 'memory_pressure_simulation',
                'description': 'Simulate external memory pressure',
                'memory_budget_mb': 2048,
                'external_memory_pressure': True,
                'pressure_changes_per_second': 5,
                'test_duration_seconds': 60,
                'expected_adaptive_behavior': True
            }
        ]


class ViewFrameworkTestData:
    """Test data specifically for view framework testing."""
    
    @staticmethod
    def generate_view_results() -> List[Dict[str, Any]]:
        """Generate realistic view analysis results."""
        view_results = []
        
        views = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        methods = ['algorithmic', 'ml', 'hybrid', 'fallback']
        
        for i in range(50):  # Generate 50 test results
            result = {
                'view_name': random.choice(views),
                'score': random.uniform(0.0, 1.0),
                'confidence': random.uniform(0.5, 1.0),
                'method': random.choice(methods),
                'latency_ms': random.uniform(1.0, 100.0),
                'features': {
                    'feature_1': random.uniform(0.0, 1.0),
                    'feature_2': random.randint(0, 10),
                    'feature_3': random.choice(['high', 'medium', 'low'])
                },
                'metadata': {
                    'timestamp': time.time() - random.uniform(0, 3600),
                    'model_used': random.choice(['SciBERT', 'DistilBERT', None]),
                    'fallback_reason': random.choice([None, 'model_error', 'timeout'])
                }
            }
            view_results.append(result)
        
        return view_results
    
    @staticmethod
    def generate_analysis_scenarios() -> List[Dict[str, Any]]:
        """Generate multi-view analysis scenarios."""
        return [
            {
                'name': 'all_views_success',
                'query': 'How does RISC-V instruction encoding work?',
                'expected_views': 5,
                'expected_failures': 0,
                'expected_ml_views': 3,
                'expected_algorithmic_views': 2,
                'expected_confidence_range': (0.8, 1.0)
            },
            {
                'name': 'partial_view_failure',
                'query': 'Complex query with some view failures',
                'expected_views': 5,
                'expected_failures': 2,
                'expected_ml_views': 1,
                'expected_algorithmic_views': 2,
                'expected_confidence_range': (0.6, 0.8)
            },
            {
                'name': 'ml_fallback_scenario', 
                'query': 'Query where ML models fail',
                'expected_views': 5,
                'expected_failures': 0,
                'expected_ml_views': 0,  # All fall back
                'expected_algorithmic_views': 5,
                'expected_confidence_range': (0.4, 0.7)
            },
            {
                'name': 'high_confidence_scenario',
                'query': 'Simple technical query',
                'expected_views': 3,  # Early stopping
                'expected_failures': 0,
                'expected_ml_views': 2,
                'expected_algorithmic_views': 1,
                'expected_confidence_range': (0.9, 1.0)
            }
        ]


def generate_realistic_memory_usage_pattern(duration_seconds: int = 60) -> Generator[Tuple[float, float], None, None]:
    """
    Generate realistic memory usage pattern over time.
    
    Yields:
        Tuple of (timestamp, memory_usage_mb)
    """
    start_time = time.time()
    base_usage = 1000.0  # 1GB base usage
    
    for i in range(duration_seconds * 10):  # 10 samples per second
        current_time = start_time + (i / 10.0)
        
        # Simulate realistic usage pattern
        # - Base usage with trend
        trend = i * 2.0  # Gradual increase
        
        # - Periodic fluctuations
        periodic = 200 * np.sin(2 * np.pi * i / 100)  # 10-second period
        
        # - Random noise
        noise = random.uniform(-50, 50)
        
        # - Occasional spikes (model loading events)
        spike = 500 if random.random() < 0.01 else 0
        
        memory_usage = base_usage + trend + periodic + noise + spike
        memory_usage = max(500, min(memory_usage, 8000))  # Bound within realistic limits
        
        yield (current_time, memory_usage)
        
        time.sleep(0.1)  # 10 Hz update rate


def create_test_configurations() -> Dict[str, Dict[str, Any]]:
    """Create comprehensive test configurations."""
    return {
        'unit_test_config': {
            'memory_monitor': {
                'update_interval_seconds': 0.1,  # Fast updates for testing
                'mock_memory_system': True,
                'cross_platform_tests': True
            },
            'model_cache': {
                'maxsize': 5,
                'memory_threshold_mb': 1024,
                'enable_stats': True,
                'test_thread_safety': True
            },
            'quantization': {
                'enable_validation': True,
                'test_compression_ratios': True,
                'test_quality_preservation': True,
                'mock_models': True
            },
            'performance_monitor': {
                'enable_alerts': True,
                'metrics_retention_hours': 1,  # Short retention for testing
                'alert_thresholds': {
                    'latency_p95_ms': 100,
                    'error_rate_percent': 5.0,
                    'memory_usage_mb': 2048
                }
            }
        },
        'integration_test_config': {
            'model_manager': {
                'memory_budget_gb': 2.0,
                'cache_size': 10,
                'enable_quantization': True,
                'model_timeout_seconds': 30.0,
                'max_concurrent_loads': 3
            },
            'memory_management': {
                'test_eviction_strategies': True,
                'test_pressure_handling': True,
                'test_concurrent_access': True
            },
            'view_framework': {
                'test_all_view_types': True,
                'test_result_aggregation': True,
                'test_error_propagation': True
            }
        },
        'performance_test_config': {
            'memory_benchmarks': {
                'sample_sizes': [100, 1000, 10000],
                'measurement_duration_seconds': 10,
                'warmup_iterations': 50
            },
            'loading_benchmarks': {
                'model_sizes': ['small', 'medium', 'large'],
                'concurrent_loads': [1, 2, 4, 8],
                'timeout_seconds': 60
            },
            'cache_benchmarks': {
                'cache_sizes': [5, 10, 20, 50],
                'access_patterns': ['sequential', 'random', 'lru_worst_case'],
                'measurement_iterations': 10000
            }
        }
    }


def save_test_data_to_files(output_dir: str = "test_data_output") -> None:
    """Save generated test data to files for inspection and reuse."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and save test queries
    queries = TestDataGenerator.generate_test_queries(100)
    with open(f"{output_dir}/test_queries.json", 'w') as f:
        json.dump([asdict(q) for q in queries], f, indent=2)
    
    # Generate and save model configs
    model_configs = TestDataGenerator.generate_model_test_configs()
    with open(f"{output_dir}/model_test_configs.json", 'w') as f:
        json.dump([asdict(c) for c in model_configs], f, indent=2)
    
    # Generate and save performance data
    perf_data = TestDataGenerator.generate_performance_test_data()
    with open(f"{output_dir}/performance_test_data.json", 'w') as f:
        json.dump([asdict(p) for p in perf_data], f, indent=2)
    
    # Generate and save view framework data
    view_results = ViewFrameworkTestData.generate_view_results()
    with open(f"{output_dir}/view_results.json", 'w') as f:
        json.dump(view_results, f, indent=2)
    
    # Save test configurations
    configs = create_test_configurations()
    with open(f"{output_dir}/test_configurations.json", 'w') as f:
        json.dump(configs, f, indent=2)
    
    print(f"Test data saved to {output_dir}/")


if __name__ == "__main__":
    # Generate and save test data when run directly
    save_test_data_to_files()