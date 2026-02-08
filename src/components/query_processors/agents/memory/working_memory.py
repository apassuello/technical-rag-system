"""
Working memory implementation.

Provides simple key-value storage for task execution context and state.
Unlike conversation memory, this stores arbitrary Python objects.

Architecture:
- Dictionary-based storage
- Type-safe getters/setters
- Context management
- Optional persistence

Usage:
    >>> from src.components.query_processors.agents.memory import WorkingMemory
    >>>
    >>> # Create working memory
    >>> working = WorkingMemory()
    >>>
    >>> # Set context variables
    >>> working.set_context("task_id", "task-123")
    >>> working.set_context("current_step", 1)
    >>> working.set_context("intermediate_results", {"step1": "done"})
    >>>
    >>> # Get context
    >>> task_id = working.get_context("task_id")
    >>> all_context = working.get_all_context()
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Working memory for task execution context.

    Stores arbitrary key-value pairs for maintaining task state,
    intermediate results, and execution context across agent steps.

    Features:
    - Set/get context variables
    - Get all context
    - Clear context
    - Type-safe operations

    Example:
        >>> working = WorkingMemory()
        >>> working.set_context("user_id", "user-123")
        >>> working.set_context("query_count", 5)
        >>> working.set_context("results", [1, 2, 3])
        >>>
        >>> user_id = working.get_context("user_id")  # "user-123"
        >>> count = working.get_context("query_count")  # 5
        >>> all_ctx = working.get_all_context()  # Full dict
    """

    def __init__(self):
        """Initialize working memory."""
        self._context: Dict[str, Any] = {}

    def set_context(self, key: str, value: Any) -> None:
        """
        Set context variable.

        Args:
            key: Context variable name
            value: Context variable value (any Python object)

        Raises:
            ValueError: If key is empty

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("task_id", "task-123")
            >>> working.set_context("step", 1)
            >>> working.set_context("data", {"key": "value"})
        """
        if not key:
            raise ValueError("Context key cannot be empty")

        self._context[key] = value
        logger.debug(f"Set context: {key} = {value}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get context variable.

        Args:
            key: Context variable name
            default: Default value if key not found

        Returns:
            Context variable value, or default if not found

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("task_id", "task-123")
            >>>
            >>> task_id = working.get_context("task_id")  # "task-123"
            >>> missing = working.get_context("nonexistent", "default")  # "default"
        """
        return self._context.get(key, default)

    def has_context(self, key: str) -> bool:
        """
        Check if context variable exists.

        Args:
            key: Context variable name

        Returns:
            True if key exists, False otherwise

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("task_id", "task-123")
            >>>
            >>> working.has_context("task_id")  # True
            >>> working.has_context("nonexistent")  # False
        """
        return key in self._context

    def remove_context(self, key: str) -> None:
        """
        Remove context variable.

        Args:
            key: Context variable name to remove

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("temp_data", [1, 2, 3])
            >>> working.remove_context("temp_data")
            >>> working.has_context("temp_data")  # False
        """
        if key in self._context:
            del self._context[key]
            logger.debug(f"Removed context: {key}")

    def get_all_context(self) -> Dict[str, Any]:
        """
        Get all context variables.

        Returns:
            Dictionary of all context variables (copy, not reference)

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("task_id", "task-123")
            >>> working.set_context("step", 1)
            >>>
            >>> all_ctx = working.get_all_context()
            >>> all_ctx  # {"task_id": "task-123", "step": 1}
        """
        return self._context.copy()

    def clear(self) -> None:
        """
        Clear all context variables.

        Example:
            >>> working = WorkingMemory()
            >>> working.set_context("task_id", "task-123")
            >>> working.set_context("step", 1)
            >>> len(working)  # 2
            >>>
            >>> working.clear()
            >>> len(working)  # 0
        """
        self._context = {}
        logger.debug("Working memory cleared")

    def update(self, context: Dict[str, Any]) -> None:
        """
        Update multiple context variables at once.

        Args:
            context: Dictionary of context variables to set

        Example:
            >>> working = WorkingMemory()
            >>> working.update({
            ...     "task_id": "task-123",
            ...     "step": 1,
            ...     "data": {"key": "value"}
            ... })
            >>> len(working)  # 3
        """
        self._context.update(context)
        logger.debug(f"Updated {len(context)} context variables")

    def __len__(self) -> int:
        """Return number of context variables."""
        return len(self._context)

    def __contains__(self, key: str) -> bool:
        """Check if key exists (supports 'in' operator)."""
        return key in self._context

    def __repr__(self) -> str:
        """String representation."""
        return f"WorkingMemory(variables={len(self._context)})"
