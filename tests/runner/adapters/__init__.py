"""
Test Execution Adapters

Minimal adapter system for different test execution backends.
Built as thin wrappers around existing tools like pytest.
"""

from .base import TestAdapter, ExecutionResult
from .pytest_adapter import PyTestAdapter

__all__ = [
    'TestAdapter',
    'ExecutionResult', 
    'PyTestAdapter'
]