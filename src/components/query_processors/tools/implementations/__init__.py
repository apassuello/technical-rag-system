"""
Concrete tool implementations for RAG system.

This package provides production-ready tool implementations that extend
the BaseTool interface. Each tool is designed to be safe, reliable, and
useful for LLM-powered query processing.

Available Tools:
- CalculatorTool: Safe mathematical expression evaluation
- DocumentSearchTool: Search RAG document collection
- CodeAnalyzerTool: Analyze Python code structure and syntax

Architecture:
- All tools extend BaseTool
- Tools NEVER raise exceptions (return ToolResult with errors)
- 100% type hints for all implementations
- Comprehensive docstrings with examples
- Thread-safe operations

Usage:
    >>> from src.components.query_processors.tools.implementations import (
    ...     CalculatorTool,
    ...     DocumentSearchTool,
    ...     CodeAnalyzerTool
    ... )
    >>>
    >>> # Create tools
    >>> calculator = CalculatorTool()
    >>> search = DocumentSearchTool(retriever)
    >>> analyzer = CodeAnalyzerTool()
    >>>
    >>> # Execute tools
    >>> result = calculator.execute(expression="25 * 47")
    >>> print(result.content)  # "1175"
"""

from .calculator_tool import CalculatorTool
from .document_search_tool import DocumentSearchTool
from .code_analyzer_tool import CodeAnalyzerTool


__all__ = [
    "CalculatorTool",
    "DocumentSearchTool",
    "CodeAnalyzerTool",
]

__version__ = "1.0.0"
