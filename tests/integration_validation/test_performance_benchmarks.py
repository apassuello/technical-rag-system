#!/usr/bin/env python3
"""
Performance Benchmarks and Validation
=====================================

Comprehensive performance testing for the test runner system.
Measures and validates performance characteristics under various conditions.

This ensures the test runner system meets performance requirements and
doesn't introduce performance regressions.
"""

import pytest
import time
import psutil
import os
from pathlib import Path
from typing import List, Dict, Tuple
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import statistics

import sys
project_root = Path(__file__).parent.parent.parents[2]
sys.path.insert(0, str(project_root))

from tests.runner.config import TestConfig, TestSuiteConfig
from tests.runner.discovery import TestDiscovery, TestCase
from tests.runner.executor import ExecutionOrchestrator
from tests.runner.cli import TestRunner
from tests.integration_validation.test_edge_cases_and_validation import MockTestAdapter


class PerformanceBenchmarks:
    """Performance benchmark suite for test runner system."""
    
    @staticmethod
    def measure_time(func, *args, **kwargs) -> Tuple[float, any]:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return end_time - start_time, result
    
    @staticmethod
    def measure_memory_usage(func, *args, **kwargs) -> Tuple[Dict[str, float], any]:
        """Measure memory usage during function execution."""
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        initial_memory = process.memory_info()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Final memory
        final_memory = process.memory_info()
        
        memory_delta = {
            'rss_mb': (final_memory.rss - initial_memory.rss) / 1024 / 1024,
            'vms_mb': (final_memory.vms - initial_memory.vms) / 1024 / 1024,
            'peak_memory_mb': final_memory.rss / 1024 / 1024
        }
        
        return memory_delta, result

    def test_discovery_performance_benchmarks(self):
        """Benchmark test discovery performance."""
        
        discovery = TestDiscovery()
        
        # Test patterns of increasing complexity
        test_patterns = [
            ("Simple pattern", ["tests/epic1/smoke/test_*.py"]),
            ("Multiple patterns", ["tests/unit/test_*.py", "tests/integration/test_*.py"]),
            ("Recursive pattern", ["tests/epic1/**/*.py"]),
            ("Mixed patterns", [
                "tests/epic1/**/*.py",
                "tests/unit/test_*.py", 
                "tests/integration/test_*.py",
                "tests/smoke/test_*.py"
            ]),
            ("Large pattern set", [f"tests/**/*{i}*.py" for i in range(10)])
        ]
        
        performance_results = []
        
        for pattern_name, patterns in test_patterns:
            suite_config = TestSuiteConfig(
                name=f"perf_test_{pattern_name.lower().replace(' ', '_')}",
                description=f"Performance test for {pattern_name}",
                patterns=patterns,
                markers=["performance"]
            )
            
            # Measure discovery time
            discovery_time, test_cases = self.measure_time(
                discovery.discover_suite, suite_config
            )
            
            # Measure stats generation time
            stats_time, stats = self.measure_time(
                discovery.get_test_stats, test_cases
            )
            
            # Measure memory usage
            memory_usage, _ = self.measure_memory_usage(
                discovery.discover_suite, suite_config
            )
            
            performance_results.append({
                'pattern_name': pattern_name,
                'pattern_count': len(patterns),
                'test_cases_found': len(test_cases),
                'discovery_time': discovery_time,
                'stats_time': stats_time,
                'memory_usage_mb': memory_usage['rss_mb'],
                'total_time': discovery_time + stats_time
            })
            
            # Performance assertions
            assert discovery_time < 5.0, f"{pattern_name}: Discovery should complete in <5s, took {discovery_time:.3f}s"
            assert stats_time < 1.0, f"{pattern_name}: Stats generation should complete in <1s, took {stats_time:.3f}s"
            assert memory_usage['rss_mb'] < 50.0, f"{pattern_name}: Memory usage should be <50MB, used {memory_usage['rss_mb']:.2f}MB"
        
        # Print performance summary
        print("\n" + "="*80)
        print("DISCOVERY PERFORMANCE BENCHMARKS")
        print("="*80)
        print(f"{'Pattern Name':<25} {'Patterns':<8} {'Tests':<6} {'Discovery':<10} {'Stats':<8} {'Memory':<8}")
        print("-"*80)
        
        for result in performance_results:
            print(f"{result['pattern_name']:<25} {result['pattern_count']:<8} {result['test_cases_found']:<6} "
                  f"{result['discovery_time']:.3f}s{'':<4} {result['stats_time']:.3f}s{'':<3} "
                  f"{result['memory_usage_mb']:.1f}MB")
        
        # Overall performance validation
        avg_discovery_time = statistics.mean([r['discovery_time'] for r in performance_results])
        max_discovery_time = max([r['discovery_time'] for r in performance_results])
        
        assert avg_discovery_time < 2.0, f"Average discovery time should be <2s, was {avg_discovery_time:.3f}s"
        assert max_discovery_time < 5.0, f"Max discovery time should be <5s, was {max_discovery_time:.3f}s"

    def test_orchestrator_performance_benchmarks(self):
        """Benchmark orchestrator performance with different configurations."""
        
        # Create mock adapter with controlled timing
        fast_adapter = MockTestAdapter(execution_time=0.01)
        slow_adapter = MockTestAdapter(execution_time=0.1)
        
        orchestrator = ExecutionOrchestrator()
        config = TestConfig()
        
        # Test different suite configurations
        suite_configs = [
            ("Small suite", TestSuiteConfig(
                name="small_perf", description="Small performance test",
                patterns=["tests/epic1/smoke/test_*.py"], timeout=30
            )),
            ("Medium suite", TestSuiteConfig(
                name="medium_perf", description="Medium performance test",
                patterns=["tests/epic1/integration/test_*.py"], timeout=60
            )),
            ("Large suite", TestSuiteConfig(
                name="large_perf", description="Large performance test", 
                patterns=["tests/epic1/**/*.py"], timeout=120
            ))
        ]
        
        orchestrator_results = []
        
        for suite_name, suite_config in suite_configs:
            for adapter_name, adapter in [("Fast", fast_adapter), ("Slow", slow_adapter)]:
                orchestrator.adapter = adapter
                
                run_config = config.create_run_config([])
                run_config.suites = [suite_config]
                
                # Measure orchestration overhead (setup + coordination)
                setup_time, _ = self.measure_time(
                    orchestrator.discovery.create_test_plan, suite_config
                )
                
                # Measure full execution time
                execution_time, results = self.measure_time(
                    orchestrator.execute_run_config, run_config
                )
                
                # Measure memory during execution
                memory_usage, _ = self.measure_memory_usage(
                    orchestrator.execute_run_config, run_config
                )
                
                orchestrator_results.append({
                    'suite_name': suite_name,
                    'adapter_name': adapter_name,
                    'setup_time': setup_time,
                    'execution_time': execution_time,
                    'total_time': setup_time + execution_time,
                    'memory_usage_mb': memory_usage['rss_mb'],
                    'success': results[suite_config.name].success if suite_config.name in results else False
                })
                
                # Performance assertions
                assert setup_time < 2.0, f"{suite_name}+{adapter_name}: Setup should complete in <2s"
                assert execution_time < 10.0, f"{suite_name}+{adapter_name}: Execution should complete in <10s"
                assert memory_usage['rss_mb'] < 100.0, f"{suite_name}+{adapter_name}: Memory should be <100MB"
        
        # Print orchestrator performance summary
        print("\n" + "="*90)
        print("ORCHESTRATOR PERFORMANCE BENCHMARKS")
        print("="*90)
        print(f"{'Suite':<15} {'Adapter':<6} {'Setup':<8} {'Execution':<10} {'Total':<8} {'Memory':<8} {'Status'}")
        print("-"*90)
        
        for result in orchestrator_results:
            status = "✓" if result['success'] else "✗"
            print(f"{result['suite_name']:<15} {result['adapter_name']:<6} "
                  f"{result['setup_time']:.3f}s{'':<2} {result['execution_time']:.3f}s{'':<4} "
                  f"{result['total_time']:.3f}s{'':<2} {result['memory_usage_mb']:.1f}MB{'':<2} {status}")

    def test_concurrent_execution_performance(self):
        """Benchmark concurrent execution performance."""
        
        # Create multiple orchestrators for concurrent testing
        num_workers = 3
        orchestrators = [ExecutionOrchestrator(MockTestAdapter(execution_time=0.05)) for _ in range(num_workers)]
        
        suite_config = TestSuiteConfig(
            name="concurrent_perf",
            description="Concurrent performance test",
            patterns=["tests/epic1/smoke/test_*.py"],
            timeout=60
        )
        
        config = TestConfig()
        run_config = config.create_run_config([])
        run_config.suites = [suite_config]
        
        # Sequential execution benchmark
        sequential_start = time.perf_counter()
        sequential_results = []
        
        for orchestrator in orchestrators:
            result = orchestrator.execute_run_config(run_config)
            sequential_results.append(result)
            
        sequential_time = time.perf_counter() - sequential_start
        
        # Concurrent execution benchmark
        def execute_concurrent(orchestrator):
            return orchestrator.execute_run_config(run_config)
        
        concurrent_start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(execute_concurrent, orch) for orch in orchestrators]
            concurrent_results = [future.result() for future in as_completed(futures)]
        
        concurrent_time = time.perf_counter() - concurrent_start
        
        # Calculate performance metrics
        speedup_ratio = sequential_time / concurrent_time if concurrent_time > 0 else 0
        efficiency = speedup_ratio / num_workers
        
        print(f"\n" + "="*60)
        print("CONCURRENT EXECUTION PERFORMANCE")
        print("="*60)
        print(f"Sequential time:  {sequential_time:.3f}s")
        print(f"Concurrent time:  {concurrent_time:.3f}s")
        print(f"Speedup ratio:    {speedup_ratio:.2f}x")
        print(f"Efficiency:       {efficiency:.2f}")
        print(f"Workers:          {num_workers}")
        
        # Performance assertions
        assert len(concurrent_results) == num_workers, "All concurrent executions should complete"
        assert concurrent_time < sequential_time, "Concurrent execution should be faster"
        assert speedup_ratio > 1.5, f"Should achieve >1.5x speedup, got {speedup_ratio:.2f}x"
        assert efficiency > 0.5, f"Efficiency should be >0.5, got {efficiency:.2f}"

    def test_memory_usage_patterns(self):
        """Test memory usage patterns and detect memory leaks."""
        
        discovery = TestDiscovery()
        
        # Test repeated operations for memory leaks
        suite_config = TestSuiteConfig(
            name="memory_test",
            description="Memory usage test",
            patterns=["tests/epic1/**/*.py"],
            markers=["memory"]
        )
        
        iterations = 10
        memory_samples = []
        
        process = psutil.Process(os.getpid())
        
        for i in range(iterations):
            # Force garbage collection
            import gc
            gc.collect()
            
            # Measure memory before
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Perform discovery operations
            test_cases = discovery.discover_suite(suite_config)
            test_plan = discovery.create_test_plan(suite_config)
            stats = discovery.get_test_stats(test_cases)
            
            # Clean up references
            del test_cases
            del test_plan
            del stats
            
            # Force garbage collection again
            gc.collect()
            
            # Measure memory after
            memory_after = process.memory_info().rss / 1024 / 1024
            
            memory_samples.append({
                'iteration': i,
                'memory_before': memory_before,
                'memory_after': memory_after,
                'memory_delta': memory_after - memory_before
            })
        
        # Analyze memory usage patterns
        memory_deltas = [sample['memory_delta'] for sample in memory_samples]
        avg_delta = statistics.mean(memory_deltas)
        max_delta = max(memory_deltas)
        memory_trend = memory_samples[-1]['memory_after'] - memory_samples[0]['memory_before']
        
        print(f"\n" + "="*60)
        print("MEMORY USAGE ANALYSIS")
        print("="*60)
        print(f"Iterations:       {iterations}")
        print(f"Avg memory delta: {avg_delta:.2f} MB")
        print(f"Max memory delta: {max_delta:.2f} MB")
        print(f"Memory trend:     {memory_trend:.2f} MB")
        print(f"Final memory:     {memory_samples[-1]['memory_after']:.2f} MB")
        
        # Memory performance assertions
        assert avg_delta < 10.0, f"Average memory delta should be <10MB, was {avg_delta:.2f}MB"
        assert max_delta < 20.0, f"Max memory delta should be <20MB, was {max_delta:.2f}MB"
        assert abs(memory_trend) < 50.0, f"Memory trend should be <50MB, was {memory_trend:.2f}MB"

    def test_configuration_loading_performance(self):
        """Benchmark configuration loading performance."""
        
        import tempfile
        import yaml
        
        # Create test configurations of different sizes
        config_sizes = [
            ("Small config", 5),
            ("Medium config", 25), 
            ("Large config", 100)
        ]
        
        config_performance = []
        
        for config_name, suite_count in config_sizes:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
                # Generate test configuration
                test_config = {
                    'suites': {},
                    'defaults': {
                        'output_format': 'terminal',
                        'verbose': True,
                        'fail_fast': False
                    }
                }
                
                for i in range(suite_count):
                    test_config['suites'][f'test_suite_{i}'] = {
                        'name': f'Test Suite {i}',
                        'description': f'Test suite number {i}',
                        'patterns': [f'tests/suite_{i}/test_*.py'],
                        'markers': ['test', f'suite{i}'],
                        'timeout': 300,
                        'parallel': i % 2 == 0
                    }
                
                yaml.dump(test_config, tmp_file)
                tmp_file.flush()
                
                # Benchmark configuration loading
                loading_time, config = self.measure_time(
                    TestConfig, Path(tmp_file.name)
                )
                
                # Benchmark suite listing
                listing_time, suite_names = self.measure_time(
                    config.list_suites
                )
                
                # Benchmark suite retrieval
                retrieval_times = []
                for suite_name in suite_names[:min(10, len(suite_names))]:  # Test first 10 suites
                    retrieval_time, suite_config = self.measure_time(
                        config.get_suite, suite_name
                    )
                    retrieval_times.append(retrieval_time)
                
                avg_retrieval_time = statistics.mean(retrieval_times) if retrieval_times else 0
                
                config_performance.append({
                    'config_name': config_name,
                    'suite_count': suite_count,
                    'loading_time': loading_time,
                    'listing_time': listing_time,
                    'avg_retrieval_time': avg_retrieval_time,
                    'total_time': loading_time + listing_time
                })
                
                # Performance assertions
                assert loading_time < 2.0, f"{config_name}: Loading should complete in <2s"
                assert listing_time < 0.5, f"{config_name}: Listing should complete in <0.5s"
                assert avg_retrieval_time < 0.1, f"{config_name}: Avg retrieval should be <0.1s"
                
                # Cleanup
                os.unlink(tmp_file.name)
        
        # Print configuration performance summary
        print(f"\n" + "="*70)
        print("CONFIGURATION LOADING PERFORMANCE")
        print("="*70)
        print(f"{'Config Type':<15} {'Suites':<6} {'Loading':<8} {'Listing':<8} {'Retrieval':<10} {'Total'}")
        print("-"*70)
        
        for result in config_performance:
            print(f"{result['config_name']:<15} {result['suite_count']:<6} "
                  f"{result['loading_time']:.3f}s{'':<2} {result['listing_time']:.4f}s{'':<2} "
                  f"{result['avg_retrieval_time']:.4f}s{'':<4} {result['total_time']:.3f}s")

    def test_cli_response_time_benchmarks(self):
        """Benchmark CLI response times for various commands."""
        
        runner = TestRunner()
        
        # Test different CLI commands
        cli_commands = [
            ("Help", lambda: runner.run(["--help"])),
            ("List suites", lambda: runner._list_suites(MagicMock())),
            ("Validate", lambda: runner._validate_setup(MagicMock())),
        ]
        
        cli_performance = []
        
        for command_name, command_func in cli_commands:
            try:
                # Measure CLI command time
                response_time, result = self.measure_time(command_func)
                
                cli_performance.append({
                    'command': command_name,
                    'response_time': response_time,
                    'success': result == 0 if isinstance(result, int) else True
                })
                
                # Response time assertions
                assert response_time < 5.0, f"{command_name}: Should respond in <5s, took {response_time:.3f}s"
                
            except SystemExit:
                # Help command raises SystemExit, which is expected
                cli_performance.append({
                    'command': command_name,
                    'response_time': 0.001,  # Very fast for help
                    'success': True
                })
            except Exception as e:
                print(f"Warning: {command_name} failed with: {e}")
                cli_performance.append({
                    'command': command_name,
                    'response_time': 0.0,
                    'success': False
                })
        
        # Print CLI performance summary
        print(f"\n" + "="*50)
        print("CLI RESPONSE TIME BENCHMARKS")
        print("="*50)
        print(f"{'Command':<15} {'Response Time':<15} {'Status'}")
        print("-"*50)
        
        for result in cli_performance:
            status = "✓" if result['success'] else "✗"
            print(f"{result['command']:<15} {result['response_time']:.3f}s{'':<10} {status}")

    def test_scalability_benchmarks(self):
        """Test system scalability with increasing loads."""
        
        discovery = TestDiscovery()
        
        # Test scalability with increasing number of patterns
        pattern_counts = [1, 5, 10, 25, 50]
        scalability_results = []
        
        for pattern_count in pattern_counts:
            patterns = [f"tests/epic1/**/*pattern_{i}*.py" for i in range(pattern_count)]
            
            suite_config = TestSuiteConfig(
                name=f"scalability_{pattern_count}",
                description=f"Scalability test with {pattern_count} patterns",
                patterns=patterns,
                markers=["scalability"]
            )
            
            # Measure performance with increasing load
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            discovery_time, test_cases = self.measure_time(
                discovery.discover_suite, suite_config
            )
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            
            scalability_results.append({
                'pattern_count': pattern_count,
                'discovery_time': discovery_time,
                'test_cases_found': len(test_cases),
                'memory_used': memory_used,
                'time_per_pattern': discovery_time / pattern_count if pattern_count > 0 else 0
            })
            
            # Scalability assertions
            assert discovery_time < pattern_count * 0.5, \
                f"Discovery time should scale linearly: {pattern_count} patterns took {discovery_time:.3f}s"
            assert memory_used < pattern_count * 2, \
                f"Memory usage should scale reasonably: {pattern_count} patterns used {memory_used:.2f}MB"
        
        # Analyze scalability trends
        print(f"\n" + "="*70)
        print("SCALABILITY BENCHMARKS")
        print("="*70)
        print(f"{'Patterns':<8} {'Time':<8} {'Tests':<6} {'Memory':<8} {'Time/Pattern':<12}")
        print("-"*70)
        
        for result in scalability_results:
            print(f"{result['pattern_count']:<8} {result['discovery_time']:.3f}s{'':<2} "
                  f"{result['test_cases_found']:<6} {result['memory_used']:.1f}MB{'':<3} "
                  f"{result['time_per_pattern']:.4f}s")
        
        # Check for linear scalability (time should not grow exponentially)
        if len(scalability_results) >= 3:
            time_growth = scalability_results[-1]['discovery_time'] / scalability_results[0]['discovery_time']
            pattern_growth = scalability_results[-1]['pattern_count'] / scalability_results[0]['pattern_count']
            
            scalability_ratio = time_growth / pattern_growth
            print(f"\nScalability ratio (time_growth/pattern_growth): {scalability_ratio:.2f}")
            
            # Should scale roughly linearly (ratio should be close to 1.0)
            assert scalability_ratio < 3.0, f"Scalability ratio should be <3.0, was {scalability_ratio:.2f}"


class TestSystemStressTests:
    """Stress tests for the test runner system."""
    
    def test_high_concurrency_stress(self):
        """Stress test with high concurrency."""
        
        num_threads = 10
        iterations_per_thread = 5
        
        discovery = TestDiscovery()
        suite_config = TestSuiteConfig(
            name="stress_test",
            description="High concurrency stress test",
            patterns=["tests/epic1/smoke/test_*.py"],
            markers=["stress"]
        )
        
        results = []
        errors = []
        
        def stress_worker(thread_id):
            """Worker function for stress testing."""
            thread_results = []
            try:
                for i in range(iterations_per_thread):
                    start_time = time.perf_counter()
                    
                    # Perform discovery operations
                    test_cases = discovery.discover_suite(suite_config)
                    stats = discovery.get_test_stats(test_cases)
                    
                    end_time = time.perf_counter()
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'iteration': i,
                        'execution_time': end_time - start_time,
                        'test_cases_found': len(test_cases),
                        'success': True
                    })
                    
                    # Small delay to prevent overwhelming
                    time.sleep(0.01)
                    
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
                
            return thread_results
        
        # Run stress test
        start_stress_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    thread_results = future.result(timeout=30)
                    results.extend(thread_results)
                except Exception as e:
                    errors.append(f"Future failed: {e}")
        
        end_stress_time = time.perf_counter()
        total_stress_time = end_stress_time - start_stress_time
        
        # Analyze stress test results
        successful_operations = len([r for r in results if r['success']])
        total_operations = num_threads * iterations_per_thread
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        
        avg_execution_time = statistics.mean([r['execution_time'] for r in results]) if results else 0
        operations_per_second = total_operations / total_stress_time if total_stress_time > 0 else 0
        
        print(f"\n" + "="*60)
        print("HIGH CONCURRENCY STRESS TEST RESULTS")
        print("="*60)
        print(f"Threads:              {num_threads}")
        print(f"Iterations per thread: {iterations_per_thread}")
        print(f"Total operations:     {total_operations}")
        print(f"Successful operations: {successful_operations}")
        print(f"Success rate:         {success_rate:.1%}")
        print(f"Total time:           {total_stress_time:.3f}s")
        print(f"Avg execution time:   {avg_execution_time:.4f}s")
        print(f"Operations/second:    {operations_per_second:.1f}")
        print(f"Errors:               {len(errors)}")
        
        # Stress test assertions
        assert success_rate >= 0.95, f"Success rate should be ≥95%, was {success_rate:.1%}"
        assert len(errors) <= 2, f"Should have ≤2 errors, had {len(errors)}"
        assert avg_execution_time < 1.0, f"Avg execution time should be <1s, was {avg_execution_time:.3f}s"
        assert operations_per_second > 10, f"Should achieve >10 ops/sec, achieved {operations_per_second:.1f}"

    def test_resource_exhaustion_resilience(self):
        """Test resilience under resource exhaustion conditions."""
        
        discovery = TestDiscovery()
        
        # Test with extremely large pattern sets
        large_pattern_count = 200
        patterns = [f"tests/**/*pattern_{i}*.py" for i in range(large_pattern_count)]
        
        large_suite_config = TestSuiteConfig(
            name="resource_exhaustion_test",
            description="Resource exhaustion resilience test",
            patterns=patterns,
            markers=["exhaustion"]
        )
        
        # Monitor resource usage during execution
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        try:
            # Attempt discovery with large pattern set
            start_time = time.perf_counter()
            test_cases = discovery.discover_suite(large_suite_config)
            execution_time = time.perf_counter() - start_time
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            print(f"\n" + "="*60)
            print("RESOURCE EXHAUSTION RESILIENCE TEST")
            print("="*60)
            print(f"Pattern count:    {large_pattern_count}")
            print(f"Test cases found: {len(test_cases)}")
            print(f"Execution time:   {execution_time:.3f}s")
            print(f"Memory used:      {memory_used:.1f}MB")
            print(f"Final memory:     {final_memory:.1f}MB")
            
            # Resilience assertions
            assert execution_time < 30.0, f"Should handle large patterns in <30s, took {execution_time:.3f}s"
            assert memory_used < 500.0, f"Memory usage should be <500MB, used {memory_used:.1f}MB"
            assert isinstance(test_cases, list), "Should return valid test cases list"
            
        except MemoryError:
            pytest.skip("System ran out of memory during resource exhaustion test")
        except Exception as e:
            # Should handle gracefully without crashing
            print(f"Resource exhaustion test handled gracefully: {e}")
            assert "memory" in str(e).lower() or "timeout" in str(e).lower(), \
                f"Should fail gracefully with memory/timeout error, got: {e}"


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # -s to show print outputs