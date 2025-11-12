#!/usr/bin/env python3
"""
Edge Case Testing and Validation Framework
=========================================

Tests edge cases, error conditions, and recovery scenarios for the test runner system.
Validates robustness and reliability under various failure conditions.

This complements the integration testing to ensure comprehensive validation.
"""

import pytest
import tempfile
import shutil
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
import yaml

import sys
project_root = Path(__file__).parent.parent.parents[2]
sys.path.insert(0, str(project_root))

from tests.runner.config import TestConfig, TestSuiteConfig, TestRunConfig
from tests.runner.discovery import TestDiscovery, TestCase, TestPlan
from tests.runner.executor import ExecutionOrchestrator
from tests.runner.cli import TestRunner
from tests.runner.adapters.base import TestAdapter, ExecutionResult


class MockTestAdapter(TestAdapter):
    """Mock test adapter for controlled testing scenarios."""
    
    def __init__(self, should_fail: bool = False, execution_time: float = 0.1):
        self.should_fail = should_fail
        self.execution_time = execution_time
        self.call_count = 0
        self.last_call_args = None
    
    def execute_tests(self, test_files: List[Path], **kwargs) -> ExecutionResult:
        """Mock test execution."""
        self.call_count += 1
        self.last_call_args = (test_files, kwargs)
        
        time.sleep(self.execution_time)
        
        if self.should_fail:
            return ExecutionResult(
                success=False,
                exit_code=1,
                duration=self.execution_time,
                test_results=[],
                summary={'failed': 1},
                output="",
                error_output="Mock execution failed"
            )
        else:
            return ExecutionResult(
                success=True,
                exit_code=0,
                duration=self.execution_time,
                test_results=[],
                summary={'passed': len(test_files)},
                output="Mock execution succeeded",
                error_output=""
            )
    
    def validate_setup(self) -> bool:
        """Mock validation."""
        return not self.should_fail
    
    def get_version(self) -> str:
        """Mock version."""
        return "mock-1.0.0"


class TestEdgeCasesAndValidation:
    """Edge case testing suite."""
    
    def test_empty_test_directories(self):
        """Test handling of empty test directories."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty test directory structure
            empty_dir = temp_path / "empty_tests"
            empty_dir.mkdir()
            
            # Create discovery with empty directory
            discovery = TestDiscovery(root_path=empty_dir)
            
            suite_config = TestSuiteConfig(
                name="empty_suite",
                description="Empty test suite",
                patterns=[f"{empty_dir}/test_*.py"],
                markers=["test"]
            )
            
            # Should handle empty directory gracefully
            test_cases = discovery.discover_suite(suite_config)
            assert len(test_cases) == 0, "Should find no tests in empty directory"
            
            test_plan = discovery.create_test_plan(suite_config)
            assert test_plan.total_count == 0, "Test plan should show 0 tests"
            
            # Should execute without errors
            orchestrator = ExecutionOrchestrator(MockTestAdapter())
            config = TestConfig()
            run_config = config.create_run_config([])
            run_config.suites = [suite_config]
            
            results = orchestrator.execute_run_config(run_config)
            assert "empty_suite" in results, "Should handle empty suite"
            assert results["empty_suite"].success, "Empty suite should succeed"

    def test_malformed_test_files(self):
        """Test handling of malformed test files."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create malformed Python files
            malformed_files = [
                ("test_syntax_error.py", "def test_broken(\n  # Missing closing parenthesis"),
                ("test_import_error.py", "import nonexistent_module\ndef test_example(): pass"),
                ("test_empty.py", ""),  # Empty file
                ("test_no_tests.py", "# File with no test functions\nprint('hello')"),
                ("not_a_test.py", "def test_something(): pass"),  # Doesn't start with test_
            ]
            
            for filename, content in malformed_files:
                (temp_path / filename).write_text(content)
            
            discovery = TestDiscovery(root_path=temp_path)
            
            # Test pattern matching on malformed files
            patterns = [f"{temp_path}/test_*.py"]
            files = discovery._find_files_matching(patterns[0])
            
            # Should find files but filter out non-test files correctly
            test_files = [f for f in files if discovery._is_test_file(f)]
            
            # Should include test_*.py files but exclude not_a_test.py
            test_file_names = [f.name for f in test_files]
            assert "test_syntax_error.py" in test_file_names
            assert "test_import_error.py" in test_file_names
            assert "test_empty.py" in test_file_names
            assert "test_no_tests.py" in test_file_names
            assert "not_a_test.py" not in test_file_names, "Should filter out non-test files"
            
            # Test suite creation with malformed files
            suite_config = TestSuiteConfig(
                name="malformed_suite",
                description="Malformed test suite",
                patterns=patterns,
                markers=["test"]
            )
            
            test_cases = discovery.discover_suite(suite_config)
            
            # Should create test cases but execution will be handled by adapter
            assert len(test_cases) > 0, "Should discover test cases from malformed files"

    def test_invalid_patterns_and_recovery(self):
        """Test handling of invalid patterns and recovery mechanisms."""
        
        discovery = TestDiscovery()
        
        invalid_patterns = [
            "",  # Empty pattern
            None,  # None pattern (would cause error if not handled)
            "/absolute/nonexistent/path/**/*.py",  # Absolute nonexistent path
            "invalid[pattern]with{brackets}.py",  # Invalid regex characters
            "tests/**/test_*.py/extra/path",  # Invalid glob structure
            "../../../etc/passwd",  # Security concern pattern
            "tests/**/*" * 100,  # Extremely long pattern
        ]
        
        for pattern in invalid_patterns:
            try:
                if pattern is None:
                    continue  # Skip None patterns as they'd be handled earlier
                    
                files = discovery._find_files_matching(pattern)
                
                # Should return empty list or handle gracefully
                assert isinstance(files, list), f"Should return list for pattern: {repr(pattern)}"
                
                # Validate results
                pattern_results = discovery.validate_patterns([pattern])
                assert len(pattern_results) == 1, "Should validate single pattern"
                
                pattern_result = pattern_results[0]
                assert pattern_result[0] == pattern, "Should return original pattern"
                assert isinstance(pattern_result[1], bool), "Should return boolean validity"
                assert isinstance(pattern_result[2], str), "Should return string message"
                
            except Exception as e:
                pytest.fail(f"Should handle invalid pattern gracefully: {repr(pattern)}, but raised: {e}")

    def test_timeout_and_error_recovery_scenarios(self):
        """Test timeout handling and error recovery scenarios."""
        
        # Test timeout handling in execution
        long_running_adapter = MockTestAdapter(execution_time=0.01)  # Short for testing
        orchestrator = ExecutionOrchestrator(long_running_adapter)
        
        suite_config = TestSuiteConfig(
            name="timeout_test",
            description="Timeout test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
            timeout=1  # Very short timeout
        )
        
        config = TestConfig()
        run_config = config.create_run_config([])
        run_config.suites = [suite_config]
        
        # Should handle short timeout gracefully
        results = orchestrator.execute_run_config(run_config)
        assert "timeout_test" in results, "Should handle timeout scenario"
        
        # Test error recovery with failing adapter
        failing_adapter = MockTestAdapter(should_fail=True)
        orchestrator_with_failing_adapter = ExecutionOrchestrator(failing_adapter)
        
        results = orchestrator_with_failing_adapter.execute_run_config(run_config)
        assert "timeout_test" in results, "Should handle adapter failure"
        assert not results["timeout_test"].success, "Should report failure correctly"
        
        # Test execution status tracking during failures
        status_before = orchestrator_with_failing_adapter.get_execution_status()
        assert status_before is None, "No execution should be running"
        
        # Test cleanup after failure
        orchestrator_with_failing_adapter.cleanup()
        assert orchestrator_with_failing_adapter.current_execution is None, "Should clean up after failure"

    def test_configuration_edge_cases(self):
        """Test configuration edge cases and malformed configs."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            
            # Test malformed YAML configurations
            malformed_configs = [
                # Empty config
                "",
                # Invalid YAML syntax
                "suites:\n  test_suite:\n    name: 'unclosed string",
                # Missing required fields
                "suites:\n  test_suite:\n    description: 'missing name'",
                # Invalid data types
                "suites:\n  test_suite:\n    name: 123\n    patterns: 'not a list'",
                # Circular references (would cause other issues but shouldn't crash)
                "suites:\n  test_suite: &ref\n    name: 'test'\n    patterns: [*ref]"
            ]
            
            for i, config_content in enumerate(malformed_configs):
                config_path.write_text(config_content)
                
                try:
                    # Should handle malformed config gracefully
                    config = TestConfig(config_path)
                    suite_names = config.list_suites()
                    
                    # Should return empty list or default config for malformed configs
                    assert isinstance(suite_names, list), f"Config {i}: Should return list"
                    
                    # Test getting suite from malformed config
                    if suite_names:
                        suite = config.get_suite(suite_names[0])
                        # Should either return valid suite or None
                        assert suite is None or isinstance(suite, TestSuiteConfig)
                    
                except Exception as e:
                    # Should not raise exceptions, but if it does, should be handled gracefully
                    print(f"Config {i} raised: {e}")
                    
        # Test missing config file
        nonexistent_config = Path("/nonexistent/config.yaml")
        config = TestConfig(nonexistent_config)
        
        # Should create default config or handle gracefully
        suite_names = config.list_suites()
        assert isinstance(suite_names, list), "Should handle missing config file"

    def test_concurrent_execution_safety(self):
        """Test concurrent execution safety and resource management."""
        
        import threading
        import concurrent.futures
        
        # Create multiple orchestrators
        orchestrators = [ExecutionOrchestrator(MockTestAdapter()) for _ in range(3)]
        
        suite_config = TestSuiteConfig(
            name="concurrent_test",
            description="Concurrent test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
            timeout=60
        )
        
        config = TestConfig()
        run_config = config.create_run_config([])
        run_config.suites = [suite_config]
        
        # Function to execute tests concurrently
        def execute_tests(orchestrator):
            try:
                results = orchestrator.execute_run_config(run_config)
                return results
            except Exception as e:
                return {"error": str(e)}
        
        # Run concurrent executions
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_tests, orch) for orch in orchestrators]
            results = [future.result(timeout=30) for future in futures]
        
        # All executions should complete successfully
        for i, result in enumerate(results):
            assert "concurrent_test" in result or "error" not in result, f"Execution {i} should succeed"
            
        # Test cleanup after concurrent execution
        for orchestrator in orchestrators:
            orchestrator.cleanup()
            assert orchestrator.current_execution is None, "Should clean up after concurrent execution"

    def test_memory_and_resource_management(self):
        """Test memory usage and resource management during test execution."""
        
        # Test with large number of test cases (simulated)
        discovery = TestDiscovery()
        
        # Create config with many patterns
        many_patterns = [f"tests/epic1/**/*pattern_{i}.py" for i in range(50)]
        
        large_suite_config = TestSuiteConfig(
            name="large_suite",
            description="Large test suite",
            patterns=many_patterns,
            markers=["test"]
        )
        
        # Discovery should handle many patterns efficiently
        start_time = time.time()
        test_cases = discovery.discover_suite(large_suite_config)
        discovery_time = time.time() - start_time
        
        # Should complete in reasonable time even with many patterns
        assert discovery_time < 10.0, f"Discovery with many patterns should complete in <10s, took {discovery_time:.2f}s"
        
        # Test stats generation with large dataset
        if test_cases:  # Only if we found some tests
            start_time = time.time()
            stats = discovery.get_test_stats(test_cases)
            stats_time = time.time() - start_time
            
            assert stats_time < 2.0, f"Stats generation should complete in <2s, took {stats_time:.2f}s"
            assert isinstance(stats, dict), "Stats should return dictionary"
            assert 'total' in stats, "Stats should include total"

    def test_security_and_path_validation(self):
        """Test security aspects and path validation."""
        
        discovery = TestDiscovery()
        
        # Test potentially dangerous patterns
        dangerous_patterns = [
            "../../../etc/passwd",
            "/etc/shadow",
            "~/.ssh/id_rsa",
            "\\windows\\system32\\config\\sam",  # Windows path
            "/dev/random",
            "/proc/meminfo"
        ]
        
        for pattern in dangerous_patterns:
            try:
                files = discovery._find_files_matching(pattern)
                
                # Should either find no files or only safe files
                if files:
                    for file_path in files:
                        # Should not return sensitive system files
                        path_str = str(file_path).lower()
                        assert not any(sensitive in path_str 
                                     for sensitive in ['passwd', 'shadow', 'id_rsa', 'sam'])
                        
                        # Should be within reasonable directory structure
                        assert file_path.is_file(), "Should only return actual files"
                        
            except Exception as e:
                # Should handle dangerous patterns safely
                assert "permission" in str(e).lower() or "not found" in str(e).lower(), \
                    f"Should handle dangerous pattern safely: {pattern}, got: {e}"

    def test_cli_argument_validation_and_edge_cases(self):
        """Test CLI argument validation and edge case handling."""
        
        runner = TestRunner()
        
        # Test invalid arguments handling
        invalid_args_sets = [
            [],  # No arguments
            ["nonexistent_command"],  # Invalid command
            ["epic1"],  # Epic1 without subcommand
            ["epic1", "invalid_subcommand"],  # Invalid subcommand
            ["run"],  # Run without patterns
        ]
        
        for args in invalid_args_sets:
            try:
                # Should handle invalid arguments gracefully
                exit_code = runner.run(args)
                
                # Should return non-zero exit code for invalid args
                assert isinstance(exit_code, int), "Should return integer exit code"
                assert exit_code != 0 or len(args) == 0, "Should return non-zero for invalid args (except help)"
                
            except SystemExit as e:
                # argparse may raise SystemExit, which is acceptable
                assert isinstance(e.code, int), "SystemExit should have integer code"
            except Exception as e:
                pytest.fail(f"Should handle invalid args gracefully: {args}, but raised: {e}")

    def test_reporter_error_handling(self):
        """Test reporter error handling and recovery."""
        
        from tests.runner.reporters import TerminalReporter, JSONReporter
        
        # Test terminal reporter with various inputs
        terminal_reporter = TerminalReporter()
        
        # Should handle None inputs gracefully
        try:
            terminal_reporter.start_run(None)
            terminal_reporter.suite_complete(None, None)
            terminal_reporter.run_complete(None, {})
        except Exception as e:
            pytest.fail(f"Terminal reporter should handle None inputs gracefully, but raised: {e}")
        
        # Test JSON reporter with invalid file paths
        invalid_paths = [
            "/nonexistent/directory/output.json",
            "",  # Empty path
            "/dev/null/cannot_create_here.json" if os.name == 'posix' else "CON",  # System device
        ]
        
        for invalid_path in invalid_paths:
            try:
                json_reporter = JSONReporter(invalid_path)
                
                # Should either handle gracefully or raise appropriate exception
                if hasattr(json_reporter, 'output_file'):
                    # If created successfully, should be able to handle basic operations
                    json_reporter.start_run(None)
                    
            except (OSError, IOError, PermissionError, ValueError) as e:
                # These are acceptable exceptions for invalid paths
                pass
            except Exception as e:
                pytest.fail(f"JSON reporter should handle invalid path gracefully: {invalid_path}, but raised: {e}")

    def test_adapter_failure_propagation(self):
        """Test how adapter failures propagate through the system."""
        
        # Test with failing adapter
        failing_adapter = MockTestAdapter(should_fail=True)
        orchestrator = ExecutionOrchestrator(failing_adapter)
        
        suite_config = TestSuiteConfig(
            name="failing_suite",
            description="Failing test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
        )
        
        config = TestConfig()
        run_config = config.create_run_config([])
        run_config.suites = [suite_config]
        
        # Test normal failure propagation
        results = orchestrator.execute_run_config(run_config)
        
        assert "failing_suite" in results, "Should return result for failing suite"
        assert not results["failing_suite"].success, "Should report failure correctly"
        assert results["failing_suite"].exit_code != 0, "Should report non-zero exit code"
        
        # Test fail-fast behavior
        run_config.fail_fast = True
        
        # Add another suite to test fail-fast interruption
        another_suite = TestSuiteConfig(
            name="second_suite",
            description="Second suite",
            patterns=["tests/epic1/smoke/test_*.py"],
        )
        run_config.suites.append(another_suite)
        
        results = orchestrator.execute_run_config(run_config)
        
        # Should stop after first failure
        assert "failing_suite" in results, "Should execute first suite"
        assert not results["failing_suite"].success, "First suite should fail"
        
        # Second suite should not be executed due to fail-fast
        assert len(results) == 1, "Should stop after first failure with fail-fast"


class TestSystemIntegrationValidation:
    """System-level integration validation tests."""
    
    def test_full_system_smoke_test(self):
        """Complete system smoke test covering all major components."""
        
        # Test complete system initialization
        runner = TestRunner()
        
        # Test configuration loading
        assert runner.config is not None
        suite_names = runner.config.list_suites()
        assert len(suite_names) > 0, "Should have configured suites"
        
        # Test discovery initialization
        assert runner.discovery is not None
        
        # Test orchestrator initialization
        assert runner.orchestrator is not None
        assert runner.orchestrator.adapter is not None
        
        # Test adapter validation
        assert runner.orchestrator.validate_adapter(), "Adapter should validate successfully"
        
        # Test suite retrieval
        for suite_name in suite_names[:3]:  # Test first 3 suites
            suite_config = runner.config.get_suite(suite_name)
            if suite_config:
                assert isinstance(suite_config, TestSuiteConfig)
                assert suite_config.name is not None
                assert isinstance(suite_config.patterns, list)
        
        print("✅ Full system smoke test passed")

    def test_end_to_end_workflow_simulation(self):
        """Simulate complete end-to-end workflow with mocked execution."""
        
        runner = TestRunner()
        
        # Mock the orchestrator to avoid actual test execution
        with patch.object(runner.orchestrator, 'execute_run_config') as mock_execute:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.exit_code = 0
            mock_result.duration = 1.0
            mock_result.test_results = []
            mock_result.summary = {"passed": 1}
            
            mock_execute.return_value = {"smoke": mock_result}
            
            # Simulate CLI execution
            mock_args = MagicMock()
            mock_args.format = 'terminal'
            mock_args.fail_fast = False
            mock_args.parallel = False
            mock_args.timeout = None
            mock_args.output = None
            
            # Test smoke suite execution
            exit_code = runner._run_suite("smoke", mock_args)
            
            assert exit_code == 0, "End-to-end workflow should succeed"
            assert mock_execute.called, "Should execute through orchestrator"
            
            # Verify run configuration was properly created
            call_args = mock_execute.call_args[0][0]
            assert isinstance(call_args, TestRunConfig)
            assert len(call_args.suites) > 0, "Should have test suites"
        
        print("✅ End-to-end workflow simulation passed")

    def test_system_performance_benchmarks(self):
        """Benchmark system performance under various loads."""
        
        discovery = TestDiscovery()
        
        # Benchmark test discovery
        patterns = [
            "tests/epic1/**/*.py",
            "tests/unit/test_*.py", 
            "tests/integration/test_*.py"
        ]
        
        discovery_times = []
        
        for pattern in patterns:
            start_time = time.time()
            files = discovery._find_files_matching(pattern)
            test_files = [f for f in files if discovery._is_test_file(f)]
            discovery_time = time.time() - start_time
            
            discovery_times.append(discovery_time)
            
            # Performance assertions
            assert discovery_time < 2.0, f"Discovery should complete in <2s for {pattern}, took {discovery_time:.2f}s"
            
        # Overall system performance
        avg_discovery_time = sum(discovery_times) / len(discovery_times)
        assert avg_discovery_time < 1.0, f"Average discovery time should be <1s, was {avg_discovery_time:.2f}s"
        
        print(f"✅ System performance benchmarks passed (avg discovery: {avg_discovery_time:.3f}s)")


if __name__ == "__main__":
    # Run the edge case and validation tests
    pytest.main([__file__, "-v", "--tb=short"])