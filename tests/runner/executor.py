"""
Test Execution Orchestrator

Coordinates test execution across different adapters and manages resources.
Provides progress tracking and execution control.
"""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import TestRunConfig, TestSuiteConfig
from .discovery import TestDiscovery, TestPlan
from .adapters import TestAdapter, PyTestAdapter, ExecutionResult
from .reporters import Reporter


class ExecutionOrchestrator:
    """Orchestrates test execution across multiple suites and adapters."""
    
    def __init__(self, adapter: Optional[TestAdapter] = None):
        """Initialize execution orchestrator."""
        self.adapter = adapter or PyTestAdapter()
        self.discovery = TestDiscovery()
        self.current_execution = None
        
    def execute_run_config(self, config: TestRunConfig, 
                          reporter: Optional[Reporter] = None) -> Dict[str, ExecutionResult]:
        """Execute a complete test run configuration."""
        results = {}
        
        if reporter:
            reporter.start_run(config)
        
        for suite_config in config.suites:
            if reporter:
                reporter.start_suite(suite_config)
            
            try:
                result = self.execute_suite(suite_config, config)
                results[suite_config.name] = result
                
                if reporter:
                    reporter.suite_complete(suite_config, result)
                
                # Handle fail-fast
                if not result.success and config.fail_fast:
                    if reporter:
                        reporter.run_failed(config, results)
                    break
                    
            except Exception as e:
                error_result = ExecutionResult(
                    success=False,
                    exit_code=-1,
                    duration=0,
                    test_results=[],
                    summary={'error': 1},
                    output="",
                    error_output=f"Suite execution failed: {e}"
                )
                results[suite_config.name] = error_result
                
                if reporter:
                    reporter.suite_complete(suite_config, error_result)
                
                if config.fail_fast:
                    break
        
        if reporter:
            reporter.run_complete(config, results)
        
        return results
    
    def execute_suite(self, suite_config: TestSuiteConfig, 
                     run_config: TestRunConfig) -> ExecutionResult:
        """Execute a single test suite."""
        
        # Create test plan
        test_plan = self.discovery.create_test_plan(suite_config)
        
        if not test_plan.test_cases:
            return ExecutionResult(
                success=True,
                exit_code=0,
                duration=0,
                test_results=[],
                summary={'skipped': 0},
                output="No tests found",
                error_output=""
            )
        
        # Determine what to pass to pytest - use node IDs if available, otherwise file paths
        test_targets = []
        for tc in test_plan.test_cases:
            # Use node ID if it looks like a proper pytest node (contains ::)
            if hasattr(tc, 'node_id') and tc.node_id and '::' in tc.node_id:
                test_targets.append(tc.node_id)
            else:
                # Fallback to file path for compatibility
                test_targets.append(str(tc.path))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_targets = []
        for target in test_targets:
            if target not in seen:
                seen.add(target)
                unique_targets.append(target)
        
        # Execute using adapter
        start_time = time.time()
        self.current_execution = {
            'suite': suite_config.name,
            'start_time': start_time,
            'test_count': len(test_plan.test_cases)
        }
        
        try:
            result = self.adapter.execute_tests(
                test_targets=unique_targets,  # Changed from test_files to test_targets
                markers=suite_config.markers,
                verbose=run_config.verbose,
                fail_fast=run_config.fail_fast,
                capture=run_config.capture,
                parallel=suite_config.parallel,
                timeout=suite_config.timeout
            )
        finally:
            self.current_execution = None
        
        return result
    
    def execute_patterns(self, patterns: List[str], 
                        markers: Optional[List[str]] = None,
                        **execution_options) -> ExecutionResult:
        """Execute tests matching specific patterns."""
        
        # Find files matching patterns
        test_files = set()  # Use set to avoid duplicates
        for pattern in patterns:
            files = self.discovery._find_files_matching(pattern)
            # Filter to only include actual test files
            test_files.update([f for f in files if self.discovery._is_test_file(f)])
        
        test_files = list(test_files)  # Convert back to list
        
        if not test_files:
            return ExecutionResult(
                success=True,
                exit_code=0,
                duration=0,
                test_results=[],
                summary={'skipped': 0},
                output="No tests found matching patterns",
                error_output=""
            )
        
        # Convert file paths to strings for adapter
        test_targets = [str(f) for f in test_files]
        
        # Execute using adapter
        return self.adapter.execute_tests(
            test_targets=test_targets,  # Changed from test_files to test_targets
            markers=markers,
            **execution_options
        )
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """Get current execution status."""
        if not self.current_execution:
            return None
        
        elapsed = time.time() - self.current_execution['start_time']
        return {
            'suite': self.current_execution['suite'],
            'elapsed_time': elapsed,
            'test_count': self.current_execution['test_count'],
            'status': 'running'
        }
    
    def validate_adapter(self) -> bool:
        """Validate that the test adapter is working."""
        return self.adapter.validate_setup()
    
    def cleanup(self):
        """Clean up any resources."""
        self.current_execution = None