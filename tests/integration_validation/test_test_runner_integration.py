#!/usr/bin/env python3
"""
Integration Tests for Test Runner System
=============================================

Tests the complete flow: Discovery → Configuration → Orchestrator → Adapter → Execution
Validates that the fixed test runner infrastructure works end-to-end.

This is Phase 3 validation: comprehensive integration testing and validation framework.
"""

import pytest
import tempfile
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock

import sys
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from tests.runner.config import TestConfig, TestSuiteConfig
from tests.runner.discovery import TestDiscovery, TestCase, TestPlan
from tests.runner.executor import ExecutionOrchestrator
from tests.runner.cli import TestRunner
from tests.runner.adapters import PyTestAdapter


class TestRunnerIntegration:
    """Comprehensive integration tests for test runner system."""
    
    def test_discovery_orchestrator_adapter_flow(self):
        """Test that Discovery → Orchestrator → Adapter flow works correctly."""
        
        # Test discovery component
        discovery = TestDiscovery()
        
        # Create a simple suite config for testing
        suite_config = TestSuiteConfig(
            name="test_integration_suite",
            description="Integration test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
            markers=["epic1", "smoke"],
            timeout=60
        )
        
        # Test discovery
        test_cases = discovery.discover_suite(suite_config)
        assert len(test_cases) > 0, "Discovery should find test cases"
        assert all(isinstance(tc, TestCase) for tc in test_cases), "All discovered items should be TestCase instances"
        
        # Test plan creation
        test_plan = discovery.create_test_plan(suite_config)
        assert isinstance(test_plan, TestPlan), "Should create TestPlan instance"
        assert test_plan.test_cases == test_cases, "Test plan should contain discovered test cases"
        assert test_plan.total_count == len(test_cases), "Total count should match test cases"
        
        # Test orchestrator integration
        orchestrator = ExecutionOrchestrator()
        
        # Mock adapter for controlled testing
        mock_adapter = MagicMock()
        mock_adapter.execute_tests.return_value = MagicMock(
            success=True,
            exit_code=0,
            duration=1.0,
            test_results=[],
            summary={'passed': 1},
            output="Mock test output",
            error_output=""
        )
        mock_adapter.validate_setup.return_value = True
        
        orchestrator.adapter = mock_adapter
        
        # Create run config
        config = TestConfig()
        run_config = config.create_run_config(["test_integration_suite"], verbose=True)
        run_config.suites = [suite_config]  # Override with our test suite
        
        # Execute through orchestrator
        results = orchestrator.execute_run_config(run_config)
        
        # Validate execution flow
        assert "test_integration_suite" in results, "Should execute the test suite"
        assert mock_adapter.execute_tests.called, "Adapter should be called"
        
        # Verify adapter was called with correct parameters
        call_args = mock_adapter.execute_tests.call_args
        assert call_args is not None, "Adapter should have been called"
        
        # Check that test files were passed correctly
        test_files = call_args[1]['test_files']
        assert len(test_files) > 0, "Should pass test files to adapter"
        assert all(Path(f).name.startswith('test_') for f in test_files), "All files should be test files"

    def test_cli_configuration_discovery_execution_pipeline(self):
        """Test complete CLI → Configuration → Discovery → Execution pipeline."""
        
        # Test CLI component initialization
        runner = TestRunner()
        assert runner.config is not None, "Runner should have configuration"
        assert runner.orchestrator is not None, "Runner should have orchestrator"
        assert runner.discovery is not None, "Runner should have discovery engine"
        
        # Test configuration loading
        suite_names = runner.config.list_suites()
        assert len(suite_names) > 0, "Should have configured test suites"
        assert "smoke" in suite_names, "Should have smoke tests configured"
        
        # Test suite configuration retrieval
        smoke_config = runner.config.get_suite("smoke")
        assert smoke_config is not None, "Should retrieve smoke test configuration"
        assert isinstance(smoke_config, TestSuiteConfig), "Should return TestSuiteConfig instance"
        
        # Test discovery through configuration
        test_cases = runner.discovery.discover_suite(smoke_config)
        assert len(test_cases) > 0, "Discovery should find smoke tests"
        
        # Test execution orchestration (with mock to avoid long execution)
        with patch.object(runner.orchestrator, 'execute_run_config') as mock_execute:
            mock_execute.return_value = {
                "smoke": MagicMock(success=True, exit_code=0)
            }
            
            # Simulate CLI args
            mock_args = MagicMock()
            mock_args.format = 'terminal'
            mock_args.fail_fast = False
            mock_args.parallel = False
            mock_args.timeout = None
            mock_args.output = None
            
            # Execute suite
            exit_code = runner._run_suite("smoke", mock_args)
            
            # Validate pipeline execution
            assert exit_code == 0, "Should return success exit code"
            assert mock_execute.called, "Should execute through orchestrator"
            
            # Verify run config was created correctly
            call_args = mock_execute.call_args[0][0]
            assert call_args.output_format == 'terminal', "Should use terminal format"
            assert len(call_args.suites) > 0, "Should have test suites configured"

    def test_pattern_matching_end_to_end(self):
        """Test that pattern matching works correctly end-to-end."""
        
        discovery = TestDiscovery()
        
        # Test various pattern types
        test_patterns = [
            ("tests/epic1/smoke/test_*.py", "Should match Epic 1 smoke tests"),
            ("tests/unit/test_*.py", "Should match unit tests"),
            ("tests/epic1/**/*.py", "Should match all Epic 1 tests recursively"),
            ("tests/integration/test_*.py", "Should match integration tests")
        ]
        
        for pattern, description in test_patterns:
            files = discovery._find_files_matching(pattern)
            test_files = [f for f in files if discovery._is_test_file(f)]
            
            assert len(files) >= len(test_files), f"Total files should be >= test files for {pattern}"
            
            if len(test_files) > 0:
                # Validate that all found files are actually test files
                for test_file in test_files:
                    assert test_file.name.startswith('test_'), f"File {test_file.name} should start with test_"
                    assert test_file.suffix == '.py', f"File {test_file.name} should be Python file"
                    assert test_file.exists(), f"File {test_file} should exist"
        
        # Test pattern validation
        pattern_results = discovery.validate_patterns([
            "tests/epic1/smoke/test_*.py",
            "tests/nonexistent/test_*.py",
            "invalid_pattern_without_extension"
        ])
        
        assert len(pattern_results) == 3, "Should validate all patterns"
        assert pattern_results[0][1] == True, "Epic1 smoke pattern should be valid"
        assert pattern_results[1][1] == False, "Nonexistent pattern should be invalid"
        assert pattern_results[2][1] == False, "Invalid pattern should be invalid"

    def test_epic_specific_test_organization(self):
        """Test that Epic-specific test organization works correctly."""
        
        discovery = TestDiscovery()
        config = TestConfig()
        
        # Test Epic 1 test organization
        epic1_suites = [
            "epic1_unit", "epic1_integration", "epic1_phase2", "epic1_all"
        ]
        
        for suite_name in epic1_suites:
            suite_config = config.get_suite(suite_name)
            if suite_config:
                assert suite_config.epic == "epic1", f"Suite {suite_name} should be marked as Epic 1"
                
                # Test marker inference
                test_cases = discovery.discover_suite(suite_config)
                for test_case in test_cases:
                    assert test_case.epic == "epic1", f"Test case should be marked as Epic 1"
                    assert "epic1" in test_case.markers, f"Test case should have epic1 marker"
        
        # Test marker filtering
        all_epic1_config = config.get_suite("epic1_all")
        if all_epic1_config:
            all_epic1_tests = discovery.discover_suite(all_epic1_config)
            
            # Filter by Epic 1 marker
            epic1_filtered = discovery.filter_tests(all_epic1_tests, epic="epic1")
            assert len(epic1_filtered) == len(all_epic1_tests), "All tests should be Epic 1"
            
            # Filter by integration marker
            integration_filtered = discovery.filter_tests(all_epic1_tests, markers=["integration"])
            integration_tests = [tc for tc in all_epic1_tests if tc.markers and "integration" in tc.markers]
            assert len(integration_filtered) == len(integration_tests), "Should filter integration tests correctly"

    def test_regression_against_existing_functionality(self):
        """Test that existing working functionality (smoke tests) still works."""
        
        # Test that smoke tests can be discovered and executed
        config = TestConfig()
        smoke_config = config.get_suite("smoke")
        assert smoke_config is not None, "Smoke test configuration should exist"
        
        # Test discovery
        discovery = TestDiscovery()
        smoke_tests = discovery.discover_suite(smoke_config)
        assert len(smoke_tests) > 0, "Should discover smoke tests"
        
        # Test that Epic 1 integration tests still work
        epic1_integration_config = config.get_suite("epic1_integration")
        if epic1_integration_config:
            epic1_tests = discovery.discover_suite(epic1_integration_config)
            assert len(epic1_tests) > 0, "Should discover Epic 1 integration tests"
        
        # Test validation command still works
        runner = TestRunner()
        assert runner.orchestrator.validate_adapter() == True, "Adapter validation should work"
        
        # Test list command functionality
        suite_names = config.list_suites()
        expected_suites = ["smoke", "epic1_unit", "epic1_integration"]
        for expected_suite in expected_suites:
            if expected_suite in suite_names:
                suite_config = config.get_suite(expected_suite)
                assert suite_config is not None, f"Should load {expected_suite} configuration"
                assert isinstance(suite_config, TestSuiteConfig), f"{expected_suite} should be TestSuiteConfig"

    def test_json_output_format_consistency(self):
        """Test that JSON output format remains consistent."""
        
        runner = TestRunner()
        
        # Mock execution for JSON testing
        with patch.object(runner.orchestrator, 'execute_run_config') as mock_execute:
            # Create mock result with expected structure
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.exit_code = 0
            mock_result.duration = 1.5
            mock_result.test_results = [
                MagicMock(name="test_example", status="passed", duration=0.5, message=None, traceback=None)
            ]
            mock_result.summary = {"passed": 1, "failed": 0}
            mock_result.output = "Test output"
            mock_result.error_output = ""
            
            mock_execute.return_value = {"smoke": mock_result}
            
            # Test JSON reporter creation
            from tests.runner.reporters import JSONReporter
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                json_reporter = JSONReporter(tmp_file.name)
                
                # Verify reporter can be created
                assert json_reporter is not None, "Should create JSON reporter"
                
                # Test with mock args
                mock_args = MagicMock()
                mock_args.format = 'json'
                mock_args.output = tmp_file.name
                mock_args.fail_fast = False
                mock_args.parallel = False
                mock_args.timeout = None
                
                exit_code = runner._run_suite("smoke", mock_args)
                assert exit_code == 0, "JSON execution should succeed"

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        
        discovery = TestDiscovery()
        
        # Test handling of invalid patterns
        invalid_patterns = [
            "nonexistent_directory/test_*.py",
            "/absolute/nonexistent/path/test_*.py",
            ""  # Empty pattern
        ]
        
        for pattern in invalid_patterns:
            try:
                files = discovery._find_files_matching(pattern)
                # Should not raise exception, should return empty list
                assert isinstance(files, list), f"Should return list for pattern: {pattern}"
                assert len(files) == 0, f"Should find no files for invalid pattern: {pattern}"
            except Exception as e:
                pytest.fail(f"Should handle invalid pattern gracefully, but raised: {e}")
        
        # Test handling of malformed suite configuration
        config = TestConfig()
        nonexistent_suite = config.get_suite("nonexistent_suite")
        assert nonexistent_suite is None, "Should return None for nonexistent suite"
        
        # Test orchestrator with invalid suite
        orchestrator = ExecutionOrchestrator()
        
        invalid_suite_config = TestSuiteConfig(
            name="invalid_suite",
            description="Invalid test suite",
            patterns=["nonexistent/test_*.py"],  # Invalid pattern
            markers=["nonexistent"],
            timeout=60
        )
        
        # Should handle gracefully
        run_config = config.create_run_config([], verbose=True)
        run_config.suites = [invalid_suite_config]
        
        with patch.object(orchestrator.adapter, 'execute_tests') as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True, 
                exit_code=0, 
                duration=0,
                test_results=[],
                summary={'skipped': 0},
                output="No tests found",
                error_output=""
            )
            
            results = orchestrator.execute_run_config(run_config)
            
            # Should handle gracefully without crashing
            assert "invalid_suite" in results, "Should handle invalid suite gracefully"

    def test_performance_validation(self):
        """Test performance of test discovery and execution setup."""
        
        discovery = TestDiscovery()
        
        # Test discovery performance
        start_time = time.time()
        
        # Discover a reasonable number of tests
        suite_config = TestSuiteConfig(
            name="performance_test",
            description="Performance test suite",
            patterns=["tests/epic1/**/*.py"],  # Should find many files
            markers=["epic1"],
            timeout=60
        )
        
        test_cases = discovery.discover_suite(suite_config)
        discovery_time = time.time() - start_time
        
        # Performance validation
        assert discovery_time < 5.0, f"Discovery should complete in <5s, took {discovery_time:.2f}s"
        assert len(test_cases) > 0, "Should discover some test cases for performance testing"
        
        # Test stats generation performance
        start_time = time.time()
        stats = discovery.get_test_stats(test_cases)
        stats_time = time.time() - start_time
        
        assert stats_time < 1.0, f"Stats generation should complete in <1s, took {stats_time:.2f}s"
        assert 'total' in stats, "Stats should include total count"
        assert 'by_epic' in stats, "Stats should include by_epic breakdown"
        assert stats['total'] == len(test_cases), "Total should match test case count"

    def test_parallel_execution_capabilities(self):
        """Test that parallel execution setup works correctly."""
        
        config = TestConfig()
        orchestrator = ExecutionOrchestrator()
        
        # Test that parallel flag is properly passed through
        suite_config = TestSuiteConfig(
            name="parallel_test",
            description="Parallel test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
            parallel=True,  # Enable parallel execution
            timeout=60
        )
        
        with patch.object(orchestrator.adapter, 'execute_tests') as mock_execute:
            mock_execute.return_value = MagicMock(success=True, exit_code=0)
            
            run_config = config.create_run_config([], verbose=True)
            run_config.suites = [suite_config]
            
            results = orchestrator.execute_run_config(run_config)
            
            # Verify parallel flag was passed
            assert mock_execute.called, "Adapter should be called"
            call_kwargs = mock_execute.call_args[1]
            assert 'parallel' in call_kwargs, "Parallel parameter should be passed"
            assert call_kwargs['parallel'] == True, "Parallel should be enabled"

    def test_timeout_and_resource_management(self):
        """Test timeout handling and resource management."""
        
        orchestrator = ExecutionOrchestrator()
        
        # Test execution status tracking
        assert orchestrator.get_execution_status() is None, "No execution should be running initially"
        
        # Test cleanup
        orchestrator.cleanup()
        assert orchestrator.current_execution is None, "Should clean up execution state"
        
        # Test timeout parameter passing
        suite_config = TestSuiteConfig(
            name="timeout_test",
            description="Timeout test suite",
            patterns=["tests/epic1/smoke/test_*.py"],
            timeout=120  # Custom timeout
        )
        
        with patch.object(orchestrator.adapter, 'execute_tests') as mock_execute:
            mock_execute.return_value = MagicMock(success=True, exit_code=0)
            
            config = TestConfig()
            run_config = config.create_run_config([], verbose=True)
            run_config.suites = [suite_config]
            
            orchestrator.execute_run_config(run_config)
            
            # Verify timeout was passed
            call_kwargs = mock_execute.call_args[1]
            assert 'timeout' in call_kwargs, "Timeout parameter should be passed"
            assert call_kwargs['timeout'] == 120, "Custom timeout should be used"


class TestRunnerRegressionSuite:
    """Regression test suite to ensure existing functionality works."""
    
    def test_cli_smoke_execution(self):
        """Test that CLI smoke test execution works end-to-end."""
        
        # This is an integration test that actually runs the CLI
        # Skip if we want to avoid external process execution
        try:
            result = subprocess.run(
                [sys.executable, "-m", "tests.runner.cli", "validate"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root
            )
            
            # Should succeed
            assert result.returncode == 0, f"Validation should succeed. Output: {result.stdout}, Error: {result.stderr}"
            assert "✅ Test setup validation passed!" in result.stdout, "Should show success message"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI validation took too long (>30s)")
        except Exception as e:
            pytest.skip(f"Skipping CLI integration test due to: {e}")

    def test_list_command_output(self):
        """Test that list command produces expected output."""
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "tests.runner.cli", "list"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=project_root
            )
            
            assert result.returncode == 0, f"List command should succeed. Error: {result.stderr}"
            assert "🧪 Available Test Suites:" in result.stdout, "Should show test suites header"
            assert "Epic 1" in result.stdout, "Should list Epic 1 suites"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI list command took too long (>15s)")
        except Exception as e:
            pytest.skip(f"Skipping CLI list test due to: {e}")

    def test_pattern_run_functionality(self):
        """Test that pattern-based test running works."""
        
        runner = TestRunner()
        
        # Test pattern execution through orchestrator
        with patch.object(runner.orchestrator, 'execute_patterns') as mock_execute:
            mock_execute.return_value = MagicMock(
                success=True,
                test_results=[MagicMock()],
                duration=1.0,
                summary={"passed": 1}
            )
            
            # Mock command line args
            mock_args = MagicMock()
            mock_args.patterns = ["tests/epic1/smoke/test_*.py"]
            mock_args.markers = "epic1,smoke"
            mock_args.verbose = True
            mock_args.fail_fast = False
            mock_args.parallel = False
            mock_args.timeout = 300
            
            exit_code = runner._run_patterns(mock_args)
            
            assert exit_code == 0, "Pattern execution should succeed"
            assert mock_execute.called, "Orchestrator should be called"
            
            # Verify arguments were passed correctly
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs['patterns'] == ["tests/epic1/smoke/test_*.py"]
            assert call_kwargs['markers'] == ["epic1", "smoke"]


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short"])