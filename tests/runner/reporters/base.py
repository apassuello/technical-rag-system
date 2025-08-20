"""
Base Reporter Interface

Defines the interface for test result reporting.
Supports multiple output formats and real-time progress tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from ..config import TestRunConfig, TestSuiteConfig
from ..adapters.base import ExecutionResult


class Reporter(ABC):
    """Abstract base class for test result reporting."""
    
    @abstractmethod
    def start_run(self, config: TestRunConfig):
        """Called when a test run starts."""
        pass
    
    @abstractmethod
    def start_suite(self, suite_config: TestSuiteConfig):
        """Called when a test suite starts."""
        pass
    
    @abstractmethod
    def suite_complete(self, suite_config: TestSuiteConfig, result: ExecutionResult):
        """Called when a test suite completes."""
        pass
    
    @abstractmethod
    def run_complete(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when the entire test run completes."""
        pass
    
    @abstractmethod
    def run_failed(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when a test run fails (e.g., fail-fast triggered)."""
        pass