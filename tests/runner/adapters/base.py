"""
Base Test Adapter Interface

Defines the interface for test execution adapters.
Minimal abstraction to allow different test backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    """Result of a single test execution."""
    name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    markers: Optional[List[str]] = None


@dataclass 
class ExecutionResult:
    """Result of test execution."""
    success: bool
    exit_code: int
    duration: float
    test_results: List[TestResult]
    summary: Dict[str, int]
    output: str
    error_output: str


class TestAdapter(ABC):
    """Abstract base class for test execution adapters."""
    
    @abstractmethod
    def execute_tests(self, 
                     test_files: List[Path],
                     markers: Optional[List[str]] = None,
                     verbose: bool = True,
                     fail_fast: bool = False,
                     capture: str = "no",
                     parallel: bool = False,
                     timeout: int = 300,
                     **kwargs) -> ExecutionResult:
        """Execute tests and return results."""
        pass
    
    @abstractmethod
    def validate_setup(self) -> bool:
        """Validate that the adapter is properly set up."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get version information for the test backend."""
        pass