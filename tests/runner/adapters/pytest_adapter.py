"""
PyTest Adapter

Adapter for executing tests using pytest.
Wraps pytest execution with enhanced reporting and Epic-specific features.
"""

import re
import sys
import subprocess
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .base import TestAdapter, ExecutionResult, TestResult


class PyTestAdapter(TestAdapter):
    """Adapter for pytest test execution."""
    
    def __init__(self):
        """Initialize pytest adapter."""
        self.pytest_version = self._get_pytest_version()
    
    def execute_tests(self, 
                     test_targets: Optional[List[Union[str, Path]]] = None,
                     test_files: Optional[List[Path]] = None,  # Legacy compatibility
                     markers: Optional[List[str]] = None,
                     verbose: bool = True,
                     fail_fast: bool = False,
                     capture: str = "no",
                     parallel: bool = False,
                     timeout: int = 300,
                     **kwargs) -> ExecutionResult:
        """Execute tests using pytest."""
        
        # Handle both new test_targets and legacy test_files parameters
        targets = test_targets if test_targets is not None else test_files
        if not targets:
            return ExecutionResult(
                success=True,
                exit_code=0,
                duration=0,
                test_results=[],
                summary={'skipped': 0},
                output="No test targets provided",
                error_output=""
            )
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        # Add test targets (files or node IDs)
        for target in targets:
            cmd.append(str(target))
        
        # Add pytest options
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        
        if fail_fast:
            cmd.append("-x")
        
        if capture == "no":
            cmd.append("-s")
        elif capture == "all":
            cmd.append("--capture=no")
        
        # Add marker selection (but only if the tests have markers)
        # For now, skip marker filtering to avoid deselecting all tests
        # TODO: Implement smart marker detection
        # if markers:
        #     marker_expr = " or ".join(markers)
        #     cmd.extend(["-m", marker_expr])
        
        # Add parallel execution
        if parallel:
            try:
                import pytest_xdist
                cmd.extend(["-n", "auto"])
            except ImportError:
                print("Warning: pytest-xdist not available, running sequentially")
        
        # Add timeout if plugin is available
        try:
            import pytest_timeout
            cmd.extend(["--timeout", str(timeout)])
        except ImportError:
            # Timeout plugin not available
            pass
        
        # Add JSON output for parsing if plugin is available
        try:
            import pytest_json_report
            cmd.extend(["--json-report", "--json-report-file=/tmp/pytest_report.json"])
        except ImportError:
            # JSON reporting not available, will fallback to text parsing
            pass
        
        # Add additional arguments
        for key, value in kwargs.items():
            if key.startswith("pytest_"):
                option = f"--{key[7:].replace('_', '-')}"
                if value is True:
                    cmd.append(option)
                elif value is not False:
                    cmd.extend([option, str(value)])
        
        # Execute pytest
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 30  # Add buffer for pytest overhead
            )
            
            # Parse results
            execution_result = self._parse_pytest_output(
                result.returncode,
                result.stdout,
                result.stderr,
                result
            )
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                duration=timeout,
                test_results=[],
                summary={'timeout': 1},
                output="",
                error_output=f"Test execution timed out after {timeout} seconds"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                duration=0,
                test_results=[],
                summary={'error': 1},
                output="",
                error_output=f"Test execution failed: {e}"
            )
    
    def _get_pytest_version(self) -> str:
        """Get pytest version."""
        try:
            return pytest.__version__
        except:
            return "unknown"
    
    def _parse_pytest_output(self, exit_code: int, stdout: str, stderr: str, 
                           process_result) -> ExecutionResult:
        """Parse pytest output into structured results."""
        
        # Always use text parsing for now (JSON plugin not reliably available)
        test_results, summary, duration = self._parse_text_output(stdout)
        
        return ExecutionResult(
            success=(exit_code == 0),
            exit_code=exit_code,
            duration=duration,
            test_results=test_results,
            summary=summary,
            output=stdout,
            error_output=stderr
        )
    
    def _parse_text_output(self, output: str) -> tuple:
        """Enhanced text parsing of pytest output with detailed error extraction."""
        test_results = []
        summary = {'passed': 0, 'failed': 0, 'skipped': 0, 'error': 0}
        duration = 0
        
        lines = output.split('\n')
        current_test_failure = None
        collecting_traceback = False
        traceback_lines = []
        
        for i, line in enumerate(lines):
            # Parse test results - looking for different patterns
            if '::' in line:
                if ' PASSED' in line:
                    test_name = line.split()[0]
                    test_results.append(TestResult(name=test_name, status='passed', duration=0))
                    summary['passed'] += 1
                elif ' FAILED' in line:
                    test_name = line.split()[0]
                    # Look ahead for error message and traceback
                    error_message, traceback = self._extract_error_details(lines, i + 1)
                    test_results.append(TestResult(
                        name=test_name, 
                        status='failed', 
                        duration=0,
                        message=error_message,
                        traceback=traceback
                    ))
                    summary['failed'] += 1
                elif ' ERROR' in line:
                    test_name = line.split()[0]
                    error_message, traceback = self._extract_error_details(lines, i + 1)
                    test_results.append(TestResult(
                        name=test_name, 
                        status='error', 
                        duration=0,
                        message=error_message,
                        traceback=traceback
                    ))
                    summary['error'] += 1
                elif ' SKIPPED' in line:
                    test_name = line.split()[0]
                    test_results.append(TestResult(name=test_name, status='skipped', duration=0)) 
                    summary['skipped'] += 1
            
            # Parse summary line (e.g., "27 passed, 7 failed in 10.23s")
            summary_match = re.search(r'(\d+) passed.*?(\d+) failed.*?in ([\d.]+)s', line)
            if summary_match:
                summary['passed'] = int(summary_match.group(1))
                summary['failed'] = int(summary_match.group(2))
                duration = float(summary_match.group(3))
            
            # Alternative summary patterns
            if 'passed' in line and 'in' in line and 's' in line:
                duration_match = re.search(r'in ([\d.]+)s', line)
                if duration_match:
                    duration = float(duration_match.group(1))
                
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    summary['passed'] = int(passed_match.group(1))
                    
                failed_match = re.search(r'(\d+) failed', line)
                if failed_match:
                    summary['failed'] = int(failed_match.group(1))
                    
                skipped_match = re.search(r'(\d+) skipped', line)
                if skipped_match:
                    summary['skipped'] = int(skipped_match.group(1))
                    
                error_match = re.search(r'(\d+) error', line)
                if error_match:
                    summary['error'] = int(error_match.group(1))
        
        return test_results, summary, duration
    
    def _extract_error_details(self, lines: List[str], start_index: int) -> tuple:
        """Extract error message and traceback from pytest output."""
        error_message = ""
        traceback_lines = []
        
        # Find the FAILURES section in the output
        failures_start = -1
        for i in range(len(lines)):
            if lines[i].startswith('=') and 'FAILURES' in lines[i]:
                failures_start = i
                break
        
        if failures_start == -1:
            return "", ""
        
        # Look for our specific test failure in the FAILURES section
        test_name_from_start = lines[start_index - 1].split()[0] if start_index > 0 else ""
        test_name_clean = test_name_from_start.split("::")[-1] if "::" in test_name_from_start else ""
        
        i = failures_start
        found_test_failure = False
        
        while i < len(lines):
            line = lines[i]
            
            # Look for the specific test failure header (starts with _)
            if line.startswith('_') and (test_name_clean in line or test_name_from_start in line):
                found_test_failure = True
                i += 1
                continue
            
            # If we found our test failure, start collecting details
            if found_test_failure:
                # Stop at next test failure or end of failures section
                if (line.startswith('_') and '::' in line and not (test_name_clean in line or test_name_from_start in line)) or \
                   line.startswith('=') or \
                   'short test summary' in line.lower():
                    break
                
                # Skip separator lines
                if line.strip() and not all(c in '=_-' for c in line.strip()):
                    traceback_lines.append(line)
                    
                    # Look for the final exception message (typically ends with 'Error:' or 'Exception:')
                    if line.startswith('E   ') and ('Error:' in line or 'Exception:' in line):
                        error_message = line[4:].strip()  # Remove 'E   ' prefix
            
            i += 1
        
        # Clean up traceback
        traceback = '\n'.join(traceback_lines) if traceback_lines else ""
        
        # If no error message found, try to extract from the last meaningful traceback line
        if not error_message and traceback_lines:
            for line in reversed(traceback_lines):
                if line.startswith('E   '):
                    error_message = line[4:].strip()
                    break
            
            # Fallback to any line with Exception or Error
            if not error_message:
                for line in traceback_lines:
                    if 'Error:' in line or 'Exception:' in line:
                        error_message = line.strip()
                        break
        
        return error_message, traceback
    
    def validate_setup(self) -> bool:
        """Validate pytest is available and working."""
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_version(self) -> str:
        """Get pytest version."""
        return self.pytest_version