"""
Test Runner System

Lightweight test execution framework built on pytest with Epic-aware enhancements.
Provides simple CLI interface for running Epic 1 tests with enhanced reporting.
"""

# Import core classes that are safe to import (no side effects)
from .discovery import TestDiscovery
from .config import TestConfig
from .reporters import TerminalReporter, JSONReporter

# NOTE: TestRunner is not imported here to avoid CLI side effects
# Access via: from tests.runner.cli import TestRunner

__all__ = [
    'TestDiscovery', 
    'TestConfig',
    'TerminalReporter',
    'JSONReporter'
]

def get_test_runner():
    """
    Lazy import of TestRunner to avoid CLI side effects.
    
    Returns:
        TestRunner: The main test runner class
    """
    from .cli import TestRunner
    return TestRunner