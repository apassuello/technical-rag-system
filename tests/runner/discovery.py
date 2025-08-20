"""
Test Discovery Engine

Discovers and organizes tests using pytest's actual collection API.
Finds real test functions rather than just test files.
"""

import os
import re
import json
import fnmatch
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from .config import TestSuiteConfig


@dataclass
class TestCase:
    """Represents a discovered test case."""
    path: Path
    name: str
    node_id: str  # pytest node ID like tests/epic1/test_file.py::TestClass::test_method
    markers: Set[str] = None
    epic: Optional[str] = None
    suite: Optional[str] = None


@dataclass
class TestPlan:
    """Represents a complete test execution plan."""
    name: str
    description: str
    test_cases: List[TestCase]
    total_count: int
    estimated_duration: int = 300


class TestDiscovery:
    """Test discovery and organization engine using pytest collection API."""
    
    def __init__(self, root_path: Optional[Path] = None):
        """Initialize test discovery."""
        self.root_path = root_path or Path("tests")
        self._cache = {}
        
    def discover_suite(self, config: TestSuiteConfig) -> List[TestCase]:
        """Discover tests for a specific suite using pytest collection."""
        test_cases = []
        
        for pattern in config.patterns:
            # Convert glob pattern to file paths
            files = self._find_files_matching(pattern)
            
            if files:
                # Use pytest to collect actual test functions from these files
                cases = self._collect_tests_using_pytest(files, config)
                test_cases.extend(cases)
        
        return test_cases
    
    def _find_files_matching(self, pattern: str) -> List[Path]:
        """Find files matching a glob pattern."""
        # Handle different pattern types
        if '**' in pattern:
            # Recursive glob
            base_dir = Path(pattern.split('**')[0].rstrip('/'))
            if not base_dir.exists():
                return []
            pattern_suffix = pattern.split('**/', 1)[1] if '**/' in pattern else '*.py'
            return list(base_dir.rglob(pattern_suffix))
        else:
            # Simple glob
            return list(Path().glob(pattern))
    
    def _collect_tests_using_pytest(self, file_paths: List[Path], config: TestSuiteConfig) -> List[TestCase]:
        """Collect actual test functions using pytest's collection API."""
        if not file_paths:
            return []
        
        test_cases = []
        
        # Collect from each file individually to avoid import conflicts
        for file_path in file_paths:
            if not self._is_test_file(file_path):
                continue
                
            try:
                # Build pytest command for collection only - one file at a time
                cmd = [sys.executable, "-m", "pytest", "--collect-only", "--quiet", str(file_path)]
                
                # Execute pytest collection
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # Reasonable timeout for collection
                )
                
                if result.returncode == 0:
                    # Parse pytest collection output for this file
                    file_cases = self._parse_pytest_collection(result.stdout, config)
                    test_cases.extend(file_cases)
                else:
                    # Fallback to file-based discovery for this file
                    print(f"Warning: pytest collection failed for {file_path}, using file discovery")
                    file_cases = self._fallback_file_discovery([file_path], config)
                    test_cases.extend(file_cases)
                    
            except subprocess.TimeoutExpired:
                print(f"Warning: pytest collection timed out for {file_path}, using file discovery")
                file_cases = self._fallback_file_discovery([file_path], config)
                test_cases.extend(file_cases)
            except Exception as e:
                print(f"Warning: pytest collection error for {file_path} ({e}), using file discovery")
                file_cases = self._fallback_file_discovery([file_path], config)
                test_cases.extend(file_cases)
        
        return test_cases
    
    def _parse_pytest_collection(self, output: str, config: TestSuiteConfig) -> List[TestCase]:
        """Parse pytest --collect-only output to extract test node IDs."""
        test_cases = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and separator lines
            if not line or line.startswith('=') or 'warnings summary' in line:
                continue
            
            # Skip pytest warnings and other non-test lines
            if ('DeprecationWarning' in line or 
                'warnings.py' in line or 
                '-- Docs:' in line or 
                'tests collected' in line or
                '<frozen' in line or
                'miniforge3' in line or
                'PytestUnknownMarkWarning' in line):
                continue
            
            # Look for test node IDs - must contain :: and end with test function
            if '::' in line and self._is_valid_test_node(line):
                node_id = line.strip()
                
                # Extract file path and test name
                try:
                    file_path = Path(node_id.split('::')[0])
                    test_name = node_id.split('::')[-1]  # Last part is the test function/method name
                    
                    # Skip if file doesn't exist or isn't a test file
                    if not file_path.exists() or not self._is_test_file(file_path):
                        continue
                    
                    test_case = TestCase(
                        path=file_path,
                        name=test_name,
                        node_id=node_id,
                        markers=self._infer_markers(file_path),
                        epic=config.epic,
                        suite=config.name
                    )
                    test_cases.append(test_case)
                    
                except (IndexError, ValueError):
                    # Skip malformed node IDs
                    continue
        
        return test_cases
    
    def _is_valid_test_node(self, node_id: str) -> bool:
        """Check if a node ID represents a valid test."""
        # Must contain :: to be a test function/method
        if '::' not in node_id:
            return False
        
        # Must be a .py file
        if not node_id.split('::')[0].endswith('.py'):
            return False
        
        # Last part should look like a test function (starts with test_)
        test_name = node_id.split('::')[-1]
        if not test_name.startswith('test_'):
            return False
        
        # Must start with tests/ path
        if not node_id.startswith('tests/'):
            return False
        
        return True
    
    def _fallback_file_discovery(self, file_paths: List[Path], config: TestSuiteConfig) -> List[TestCase]:
        """Fallback to file-based discovery when pytest collection fails."""
        test_cases = []
        
        for file_path in file_paths:
            if not self._is_test_file(file_path):
                continue
            
            # Create a single test case per file as fallback
            test_case = TestCase(
                path=file_path,
                name=file_path.stem,
                node_id=str(file_path),  # Use file path as node ID for fallback
                markers=self._infer_markers(file_path),
                epic=config.epic,
                suite=config.name
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a Python file is actually a test file."""
        filename = file_path.name
        
        # Skip __init__.py files
        if filename == '__init__.py':
            return False
            
        # Skip conftest.py files (pytest configuration)
        if filename == 'conftest.py':
            return False
            
        # Skip files that don't start with 'test_'
        if not filename.startswith('test_'):
            return False
            
        return True
    
    def _extract_markers(self, file_path: Path, item=None) -> Set[str]:
        """Extract pytest markers from test."""
        markers = set()
        
        # Try to get markers from pytest item
        if item and hasattr(item, 'iter_markers'):
            for marker in item.iter_markers():
                markers.add(marker.name)
        
        # Infer markers from file path and content
        markers.update(self._infer_markers(file_path))
        
        return markers
    
    def _infer_markers(self, file_path: Path) -> Set[str]:
        """Infer test markers from file path and naming."""
        markers = set()
        
        # Path-based markers
        path_str = str(file_path)
        if 'epic1' in path_str:
            markers.add('epic1')
        if 'epic2' in path_str:
            markers.add('epic2')
        if 'integration' in path_str:
            markers.add('integration')
        if 'unit' in path_str:
            markers.add('unit')
        if 'smoke' in path_str:
            markers.add('smoke')
        if 'regression' in path_str:
            markers.add('regression')
        if 'phase2' in path_str:
            markers.add('phase2')
        
        # Name-based markers
        name = file_path.name
        if 'slow' in name:
            markers.add('slow')
        if 'debug' in name:
            markers.add('debug')
        if 'validation' in name:
            markers.add('validation')
            
        return markers
    
    def create_test_plan(self, config: TestSuiteConfig) -> TestPlan:
        """Create execution plan for a test suite."""
        test_cases = self.discover_suite(config)
        
        return TestPlan(
            name=config.name,
            description=config.description,
            test_cases=test_cases,
            total_count=len(test_cases),
            estimated_duration=config.timeout
        )
    
    def filter_tests(self, test_cases: List[TestCase], 
                     markers: Optional[List[str]] = None,
                     epic: Optional[str] = None,
                     pattern: Optional[str] = None) -> List[TestCase]:
        """Filter test cases based on criteria."""
        filtered = test_cases
        
        # Filter by markers
        if markers:
            marker_set = set(markers)
            filtered = [tc for tc in filtered 
                       if tc.markers and marker_set.intersection(tc.markers)]
        
        # Filter by epic
        if epic:
            filtered = [tc for tc in filtered if tc.epic == epic]
        
        # Filter by name pattern
        if pattern:
            filtered = [tc for tc in filtered 
                       if fnmatch.fnmatch(tc.name, pattern)]
        
        return filtered
    
    def get_test_stats(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """Get statistics about discovered tests."""
        stats = {
            'total': len(test_cases),
            'by_epic': {},
            'by_marker': {},
            'by_suite': {}
        }
        
        for tc in test_cases:
            # Count by epic
            if tc.epic:
                stats['by_epic'][tc.epic] = stats['by_epic'].get(tc.epic, 0) + 1
            
            # Count by markers
            if tc.markers:
                for marker in tc.markers:
                    stats['by_marker'][marker] = stats['by_marker'].get(marker, 0) + 1
            
            # Count by suite
            if tc.suite:
                stats['by_suite'][tc.suite] = stats['by_suite'].get(tc.suite, 0) + 1
        
        return stats
    
    def validate_patterns(self, patterns: List[str]) -> List[Tuple[str, bool, str]]:
        """Validate that patterns match existing files and discover actual test count."""
        results = []
        
        for pattern in patterns:
            try:
                files = self._find_files_matching(pattern)
                # Filter to only actual test files
                test_files = [f for f in files if self._is_test_file(f)]
                
                if test_files:
                    # Use pytest to get actual test count
                    actual_test_count = self._count_actual_tests(test_files)
                    results.append((pattern, True, f"Found {len(test_files)} test files with {actual_test_count} test functions"))
                else:
                    results.append((pattern, False, "No test files found"))
            except Exception as e:
                results.append((pattern, False, f"Error: {e}"))
        
        return results
    
    def _count_actual_tests(self, file_paths: List[Path]) -> int:
        """Count actual test functions using pytest collection."""
        total_count = 0
        
        # Count tests from each file individually
        for file_path in file_paths:
            try:
                cmd = [sys.executable, "-m", "pytest", "--collect-only", "--quiet", str(file_path)]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Count lines with :: that represent test functions
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line = line.strip()
                        if self._is_valid_test_node(line):
                            total_count += 1
                else:
                    # Fallback to 1 per file
                    total_count += 1
                    
            except Exception:
                # Fallback to 1 per file
                total_count += 1
                
        return total_count