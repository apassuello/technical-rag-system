"""
Test Orchestrator - Core execution engine for unified test system.

Manages test execution across multiple suites with support for:
- Parallel execution with configurable workers
- Plugin architecture for different test frameworks
- Comprehensive error handling and recovery
- Real-time progress tracking and reporting
- Resource management and cleanup
"""

import asyncio
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import subprocess
import sys
import logging

from src.testing.adapters.pytest_adapter import PytestAdapter
from src.testing.adapters.custom_adapter import CustomTestAdapter
from src.testing.models.test_models import TestPlan, TestResult, ExecutionConfig, TestStatus
from src.testing.utils.resource_monitor import ResourceMonitor
from src.testing.utils.progress_tracker import ProgressTracker


logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Test execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel" 
    ADAPTIVE = "adaptive"


@dataclass
class ExecutionContext:
    """Context for test execution with resource management."""
    config: ExecutionConfig
    resource_monitor: ResourceMonitor = field(default_factory=ResourceMonitor)
    progress_tracker: ProgressTracker = field(default_factory=ProgressTracker)
    start_time: float = field(default_factory=time.time)
    workers: Optional[ThreadPoolExecutor] = None
    
    def __post_init__(self):
        """Initialize execution context."""
        if self.config.parallel and self.config.workers > 1:
            self.workers = ThreadPoolExecutor(
                max_workers=self.config.workers,
                thread_name_prefix="TestWorker"
            )


class TestOrchestrator:
    """
    Core orchestrator for unified test execution across all suites.
    
    Features:
    - Multi-framework support through adapters
    - Intelligent parallel execution
    - Resource monitoring and management
    - Comprehensive error handling
    - Real-time progress tracking
    """
    
    def __init__(self):
        self.adapters = self._initialize_adapters()
        self.execution_hooks: Dict[str, List[Callable]] = {
            'pre_execution': [],
            'post_execution': [],
            'pre_suite': [],
            'post_suite': [],
            'test_started': [],
            'test_completed': []
        }
        
    def _initialize_adapters(self) -> Dict[str, Any]:
        """Initialize test framework adapters."""
        return {
            'pytest': PytestAdapter(),
            'custom': CustomTestAdapter(),
        }
    
    async def execute_tests(
        self, 
        test_plan: TestPlan, 
        config: ExecutionConfig
    ) -> TestResult:
        """
        Execute test plan with comprehensive orchestration.
        
        Args:
            test_plan: Complete test execution plan
            config: Execution configuration and options
            
        Returns:
            Comprehensive test results with metrics and diagnostics
        """
        context = ExecutionContext(config)
        
        try:
            logger.info(f"Starting test execution: {test_plan.name}")
            logger.info(f"Total tests: {len(test_plan.tests)}")
            logger.info(f"Execution strategy: {self._determine_strategy(test_plan, config)}")
            
            # Execute pre-execution hooks
            await self._execute_hooks('pre_execution', context, test_plan)
            
            # Initialize progress tracking
            context.progress_tracker.initialize(test_plan)
            
            # Execute test plan
            if config.parallel and len(test_plan.tests) > 1:
                results = await self._execute_parallel(test_plan, context)
            else:
                results = await self._execute_sequential(test_plan, context)
            
            # Execute post-execution hooks
            await self._execute_hooks('post_execution', context, test_plan, results)
            
            # Compile final results
            final_result = self._compile_results(test_plan, results, context)
            
            logger.info(f"Test execution completed: {final_result.summary}")
            return final_result
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return self._create_error_result(test_plan, context, e)
            
        finally:
            # Cleanup resources
            await self._cleanup_context(context)
    
    async def _execute_parallel(
        self, 
        test_plan: TestPlan, 
        context: ExecutionContext
    ) -> List[TestResult]:
        """Execute tests in parallel with intelligent work distribution."""
        logger.info(f"Executing {len(test_plan.tests)} tests in parallel with {context.config.workers} workers")
        
        results = []
        futures = []
        
        # Group tests by suite for optimal resource utilization
        test_groups = self._group_tests_by_suite(test_plan.tests)
        
        for group_name, tests in test_groups.items():
            if context.config.fail_fast and any(r.status == TestStatus.FAILED for r in results):
                logger.info("Fail-fast mode: Skipping remaining tests due to failure")
                break
                
            # Execute suite group
            suite_future = context.workers.submit(
                self._execute_test_group,
                group_name,
                tests,
                context
            )
            futures.append(suite_future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                group_results = future.result(timeout=context.config.timeout)
                results.extend(group_results)
                
                # Update progress
                context.progress_tracker.update_progress(len(group_results))
                
            except Exception as e:
                logger.error(f"Test group execution failed: {e}")
                # Create error results for failed group
                error_result = TestResult(
                    name="Group Execution Error",
                    status=TestStatus.ERROR,
                    error=str(e),
                    duration=0.0
                )
                results.append(error_result)
        
        return results
    
    async def _execute_sequential(
        self, 
        test_plan: TestPlan, 
        context: ExecutionContext
    ) -> List[TestResult]:
        """Execute tests sequentially with progress tracking."""
        logger.info(f"Executing {len(test_plan.tests)} tests sequentially")
        
        results = []
        
        for test_spec in test_plan.tests:
            if context.config.fail_fast and any(r.status == TestStatus.FAILED for r in results):
                logger.info("Fail-fast mode: Stopping execution due to failure")
                break
            
            # Execute individual test
            result = await self._execute_single_test(test_spec, context)
            results.append(result)
            
            # Update progress
            context.progress_tracker.update_progress(1)
            
            # Log progress periodically
            if len(results) % 10 == 0:
                logger.info(f"Progress: {len(results)}/{len(test_plan.tests)} tests completed")
        
        return results
    
    def _execute_test_group(
        self, 
        group_name: str, 
        tests: List[Any], 
        context: ExecutionContext
    ) -> List[TestResult]:
        """Execute a group of tests (designed for thread pool execution)."""
        logger.debug(f"Executing test group: {group_name} ({len(tests)} tests)")
        
        results = []
        
        # Determine appropriate adapter for this test group
        adapter = self._select_adapter(tests[0] if tests else None)
        
        try:
            # Execute tests using appropriate adapter
            if adapter.supports_batch_execution:
                # Execute as batch for efficiency
                batch_results = adapter.execute_batch(tests, context.config)
                results.extend(batch_results)
            else:
                # Execute individually
                for test in tests:
                    result = adapter.execute_single(test, context.config)
                    results.append(result)
        
        except Exception as e:
            logger.error(f"Test group {group_name} execution failed: {e}")
            # Create error result for entire group
            error_result = TestResult(
                name=f"{group_name}_group_error",
                status=TestStatus.ERROR,
                error=str(e),
                duration=0.0
            )
            results.append(error_result)
        
        return results
    
    async def _execute_single_test(self, test_spec: Any, context: ExecutionContext) -> TestResult:
        """Execute a single test with comprehensive error handling."""
        adapter = self._select_adapter(test_spec)
        
        try:
            # Execute pre-test hooks
            await self._execute_hooks('test_started', context, test_spec)
            
            # Execute the test
            start_time = time.time()
            result = adapter.execute_single(test_spec, context.config)
            result.duration = time.time() - start_time
            
            # Execute post-test hooks
            await self._execute_hooks('test_completed', context, test_spec, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Test execution failed: {test_spec}, error: {e}")
            return TestResult(
                name=str(test_spec),
                status=TestStatus.ERROR,
                error=str(e),
                duration=time.time() - start_time if 'start_time' in locals() else 0.0
            )
    
    def _select_adapter(self, test_spec: Any) -> Any:
        """Select appropriate test adapter based on test specification."""
        if hasattr(test_spec, 'framework'):
            adapter_name = test_spec.framework
        elif hasattr(test_spec, 'path') and 'test_' in str(test_spec.path):
            adapter_name = 'pytest'  # Default for standard Python tests
        else:
            adapter_name = 'custom'
            
        return self.adapters.get(adapter_name, self.adapters['custom'])
    
    def _group_tests_by_suite(self, tests: List[Any]) -> Dict[str, List[Any]]:
        """Group tests by suite for optimal parallel execution."""
        groups = {}
        
        for test in tests:
            # Determine group based on test path or suite identifier
            if hasattr(test, 'suite'):
                group_key = test.suite
            elif hasattr(test, 'path'):
                path_parts = Path(test.path).parts
                # Extract suite from path (e.g., tests/epic1/unit -> epic1)
                group_key = path_parts[1] if len(path_parts) > 1 else 'default'
            else:
                group_key = 'default'
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(test)
        
        return groups
    
    def _determine_strategy(self, test_plan: TestPlan, config: ExecutionConfig) -> ExecutionStrategy:
        """Determine optimal execution strategy based on test plan and config."""
        if not config.parallel:
            return ExecutionStrategy.SEQUENTIAL
        
        if len(test_plan.tests) == 1:
            return ExecutionStrategy.SEQUENTIAL
        
        # Check if tests support parallel execution
        parallel_supported = all(
            self._select_adapter(test).supports_parallel 
            for test in test_plan.tests
        )
        
        if not parallel_supported:
            logger.info("Some tests don't support parallel execution, using sequential")
            return ExecutionStrategy.SEQUENTIAL
        
        return ExecutionStrategy.PARALLEL
    
    def _compile_results(
        self, 
        test_plan: TestPlan, 
        results: List[TestResult], 
        context: ExecutionContext
    ) -> TestResult:
        """Compile individual test results into comprehensive result."""
        total_duration = time.time() - context.start_time
        
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        success = failed == 0 and errors == 0
        
        return TestResult(
            name=test_plan.name,
            status=TestStatus.PASSED if success else TestStatus.FAILED,
            duration=total_duration,
            details={
                'total_tests': len(results),
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'errors': errors,
                'success_rate': (passed / len(results) * 100) if results else 0,
                'individual_results': results,
                'execution_config': context.config.__dict__,
                'resource_usage': context.resource_monitor.get_summary()
            },
            summary=f"Executed {len(results)} tests: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors"
        )
    
    def _create_error_result(
        self, 
        test_plan: TestPlan, 
        context: ExecutionContext, 
        error: Exception
    ) -> TestResult:
        """Create error result for failed test execution."""
        return TestResult(
            name=test_plan.name,
            status=TestStatus.ERROR,
            error=str(error),
            duration=time.time() - context.start_time,
            details={
                'error_type': type(error).__name__,
                'traceback': traceback.format_exc()
            },
            summary=f"Test execution failed: {error}"
        )
    
    async def _execute_hooks(self, hook_type: str, context: ExecutionContext, *args):
        """Execute registered hooks for specific execution events."""
        hooks = self.execution_hooks.get(hook_type, [])
        
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(context, *args)
                else:
                    hook(context, *args)
            except Exception as e:
                logger.warning(f"Hook execution failed ({hook_type}): {e}")
    
    async def _cleanup_context(self, context: ExecutionContext):
        """Clean up execution context and resources."""
        try:
            if context.workers:
                context.workers.shutdown(wait=True)
            
            context.resource_monitor.cleanup()
            context.progress_tracker.finalize()
            
        except Exception as e:
            logger.warning(f"Context cleanup failed: {e}")
    
    def register_hook(self, hook_type: str, callback: Callable):
        """Register execution hook for specific events."""
        if hook_type in self.execution_hooks:
            self.execution_hooks[hook_type].append(callback)
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")
    
    def get_supported_frameworks(self) -> List[str]:
        """Get list of supported test frameworks."""
        return list(self.adapters.keys())
    
    def add_adapter(self, name: str, adapter: Any):
        """Add custom test framework adapter."""
        self.adapters[name] = adapter